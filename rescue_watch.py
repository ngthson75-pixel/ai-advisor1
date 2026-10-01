"""
AI ADVISOR - RESCUE WATCH v2 · GIÁM SÁT DANH MỤC VIP (Telegram + Email)
=======================================================================
File: rescue_watch.py
Version: 2.1 (2026-10-01) — mở gửi thật THEO TỪNG KHÁCH (stage draft|live), mặc định bản nháp

Mục đích
--------
Hệ thống tự quét danh mục của từng khách VIP mỗi ngày và CHỈ lên tiếng khi có biến cố
đột biến, kèm gợi ý hành động theo 2 kịch bản (giống cách admin nhắn khách: "BSR lên vùng
cản, nếu không vượt 33 thì bán bớt"). Tối đa 1 bản tin / khách / ngày (gộp lúc ~16h),
riêng biến cố trong phiên (⚡) được gửi ngay.

v2 thay đổi so với v1 (đã được admin duyệt 01/10/2026)
  - BỎ cảnh báo theo % lãi/lỗ (-10/-15/-20%) — gây nhiễu với khách đang kẹt sâu.
  - BỎ "DROP so với lần kiểm tra trước" — thay bằng phân tích nến ngày (watch_ta.py).
  - THÊM biến cố kỹ thuật: thủng hỗ trợ, bán đột biến, giảm mạnh, vùng đỉnh cũ,
    áp sát/chạm cản, vượt cản có KL, biến động mạnh trong phiên, thị trường hạ tỷ trọng.
  - GIỮ: rời đỉnh khi đang lãi (GIVEBACK), tín hiệu BÁN của hệ thống, vượt ngưỡng tập trung 35%.
  - Mốc giá do admin nhập tay (theo từng khách hoặc chung) — ưu tiên hơn mốc tự động.
  - Khách tự bật/tắt + chọn kênh (Telegram / Email / cả hai). Tắt = dừng hẳn.
  - Chống làm phiền: mỗi biến cố trên cùng 1 mốc chỉ báo 1 lần trong 7 ngày.

Dữ liệu: bảng price_history (nến ngày, VND) do update_price_history.py (GitHub Actions 16:00)
nạp. Module chỉ ĐỌC các bảng sẵn có (vip_users, portfolios, cash_positions, eod_prices,
signals, market_risk) và GHI vào bảng riêng (tự tạo, IF NOT EXISTS).

Chế độ chạy
-----------
  preview  Chỉ tính, trả JSON. Không gửi, không ghi.
  admin    Gửi BẢN NHÁP từng khách vào Telegram admin, ghi trạng thái + log.   (tuần đầu)
  live     Khách admin ĐÃ MỞ (stage=live) + đã bật nhận tin: gửi thật theo kênh khách chọn.
           Khách chưa mở (stage=draft, mặc định): vẫn chỉ là bản nháp gửi admin.
           => Có thể để biến RESCUE_WATCH_MODE=live thường trực; đặt =admin là CÔNG TẮC KHẨN dừng gửi mọi khách.
Phạm vi (scope)
  eod       Sau cập nhật giá 16:00 + lịch sử nến: đủ mọi biến cố.
  intraday  Sau các lần cập nhật giá trong phiên: chỉ biến cố ⚡ (giảm >=5% / xuyên hỗ trợ >2%).

Endpoints
  POST /api/admin/rescue-watch/run        {"mode","scope","user","email_test"}   [ADMIN]
  GET  /api/admin/rescue-watch/log?days=30                                        [ADMIN]
  GET  /api/admin/watch/levels  · POST /api/admin/watch/levels {ticker,price,note,user?}
  POST /api/admin/watch/levels/delete {id}                                         [ADMIN]
  GET  /api/admin/watch/analyze?ticker=HDG   (mốc tự động + biến cố phiên gần nhất) [ADMIN]
  GET  /api/vip/watch/prefs · POST /api/vip/watch/prefs {enabled, channel}          [VIP]
Telegram: khách gõ /tat hoặc /bat (xử lý trong webhook của backend_api.py -> set_prefs_by_chat).

Env: TELEGRAM_BOT_TOKEN, ADMIN_SECRET, ADMIN_TELEGRAM_CHAT_ID (hoặc TELEGRAM_CHAT_ID),
     GMAIL_* (đã có — dùng chung hàm gửi email mật khẩu trong campaign_api.py), ADMIN_EMAIL.
"""

import os
import html
import hmac
import logging
from datetime import datetime, date, timedelta
from functools import wraps

from flask import request, jsonify
from sqlalchemy import text

import watch_ta as ta

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

ADMIN_SECRET       = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID      = os.getenv('ADMIN_TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')
ADMIN_EMAIL        = os.getenv('ADMIN_EMAIL', '')
DASHBOARD_URL      = os.getenv('FRONTEND_URL', 'https://ai-advisor.vn')

GIVEBACK_MIN_PROFIT = float(os.getenv('RW_GIVEBACK_MIN_PROFIT', '20'))
GIVEBACK_PCT       = float(os.getenv('RW_GIVEBACK_PCT', '10'))
CONCENTRATION_PCT  = float(os.getenv('RW_CONCENTRATION_PCT', '35'))
MARKET_DROP_PTS    = float(os.getenv('RW_MARKET_DROP_PTS', '15'))   # tỷ trọng khuyến nghị giảm >= 15 điểm %
COOLDOWN_DAYS      = int(os.getenv('RW_COOLDOWN_DAYS', '7'))          # ~5 phiên
STALE_DAYS         = int(os.getenv('RW_STALE_DAYS', '4'))
# Biến cố "theo phiên" lặp lại sớm hơn biến cố "theo mốc" (mốc dùng khóa riêng theo giá nên vẫn báo khi thủng mốc mới)
TYPE_COOLDOWN      = {'INTRADAY': 1, 'SHARP_DROP': 2, 'SELL_VOLUME': 3}
HISTORY_DAYS       = 420                                              # nến tải cho phân tích (~1 năm + đệm)
MAX_EVENTS_PER_MSG = 8
PORTFOLIO_ROW      = '*'
CHANNELS           = ('telegram', 'email', 'both')
DISCLAIMER         = 'Công cụ hỗ trợ quyết định, không phải tư vấn đầu tư. Quyết định thuộc về nhà đầu tư.'


# ============================================================
# DB
# ============================================================

def ensure_tables(engine):
    is_sqlite = engine.dialect.name == 'sqlite'
    id_col = 'INTEGER PRIMARY KEY AUTOINCREMENT' if is_sqlite else 'SERIAL PRIMARY KEY'
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rescue_watch_state (
                user_id VARCHAR(255) NOT NULL, ticker VARCHAR(10) NOT NULL,
                last_price DOUBLE PRECISION, last_trade_date VARCHAR(20), peak_price DOUBLE PRECISION,
                alert_level VARCHAR(10), giveback_alerted BOOLEAN DEFAULT FALSE, top_pct DOUBLE PRECISION,
                updated_at TIMESTAMP, PRIMARY KEY (user_id, ticker))"""))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS rescue_watch_log (
                id {id_col}, user_id VARCHAR(255), ticker VARCHAR(10), event_type VARCHAR(30),
                detail TEXT, price DOUBLE PRECISION, pl_pct DOUBLE PRECISION, mode VARCHAR(10),
                sent BOOLEAN, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""))
        # v2
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS price_history (
                ticker VARCHAR(10) NOT NULL, trade_date VARCHAR(10) NOT NULL,
                open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION,
                close DOUBLE PRECISION, volume DOUBLE PRECISION,
                PRIMARY KEY (ticker, trade_date))"""))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS watch_levels (
                id {id_col}, user_id VARCHAR(255), ticker VARCHAR(10) NOT NULL,
                price DOUBLE PRECISION NOT NULL, note TEXT, created_at TIMESTAMP)"""))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS watch_alert_state (
                user_id VARCHAR(255) NOT NULL, ticker VARCHAR(10) NOT NULL, ekey VARCHAR(60) NOT NULL,
                last_date VARCHAR(10), value DOUBLE PRECISION, PRIMARY KEY (user_id, ticker, ekey))"""))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS watch_prefs (
                user_id VARCHAR(255) PRIMARY KEY, enabled BOOLEAN DEFAULT TRUE,
                channel VARCHAR(10) DEFAULT 'both', updated_at TIMESTAMP,
                stage VARCHAR(10) DEFAULT 'draft')"""))
    # v2.1: cột stage (draft | live) — admin mở gửi thật cho TỪNG khách
    try:
        with engine.begin() as conn:
            if is_sqlite:
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(watch_prefs)")).fetchall()]
                if 'stage' not in cols:
                    conn.execute(text("ALTER TABLE watch_prefs ADD COLUMN stage VARCHAR(10) DEFAULT 'draft'"))
            else:
                conn.execute(text("ALTER TABLE watch_prefs ADD COLUMN IF NOT EXISTS stage VARCHAR(10) DEFAULT 'draft'"))
    except Exception as e:
        logger.warning(f'[RescueWatch] watch_prefs.stage: {e}')


def _rows(session, sql, **params):
    return [dict(r) for r in session.execute(text(sql), params).mappings().all()]


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def _strip_tags(s):
    return html.unescape(s.replace('<b>', '').replace('</b>', ''))


# ============================================================
# PREFS (bật/tắt + kênh) — dùng bởi API VIP và lệnh /tat /bat
# ============================================================

STAGES = ('draft', 'live')


def get_prefs(session, email):
    """enabled/channel: lựa chọn của KHÁCH. stage: quyết định của ADMIN — 'draft' (mặc định: tin chỉ là bản nháp
    gửi admin) hoặc 'live' (admin đã mở gửi thật cho khách này)."""
    r = _rows(session, "SELECT enabled, channel, stage FROM watch_prefs WHERE user_id = :u", u=email)
    if not r:
        return {'enabled': True, 'channel': 'both', 'stage': 'draft', 'default': True}
    return {'enabled': bool(r[0]['enabled']), 'channel': r[0]['channel'] or 'both',
            'stage': r[0]['stage'] if r[0]['stage'] in STAGES else 'draft', 'default': False}


def set_stage(session, email, stage):
    if stage not in STAGES:
        raise ValueError('stage phải là draft | live')
    if not _rows(session, "SELECT 1 AS x FROM vip_users WHERE email = :u", u=email):
        raise ValueError(f'Không có tài khoản {email}')
    return set_prefs(session, email, stage=stage, _admin=True)


def set_prefs(session, email, enabled=None, channel=None, stage=None, _admin=False):
    cur = get_prefs(session, email)
    if stage is not None:
        if not _admin or stage not in STAGES:
            raise ValueError('stage chỉ admin được đổi (draft | live)')
        cur['stage'] = stage
    if enabled is not None:
        cur['enabled'] = bool(enabled)
    if channel is not None:
        if channel not in CHANNELS:
            raise ValueError('channel phải là telegram | email | both')
        cur['channel'] = channel
    session.execute(text("DELETE FROM watch_prefs WHERE user_id = :u"), {'u': email})
    session.execute(text("""INSERT INTO watch_prefs (user_id, enabled, channel, stage, updated_at)
                            VALUES (:u, :e, :c, :s, :now)"""),
                    {'u': email, 'e': cur['enabled'], 'c': cur['channel'], 's': cur['stage'], 'now': datetime.now()})
    # Khách tắt = dừng hẳn MỌI khuyến nghị tự động (cả tín hiệu Telegram hằng ngày); bật lại = nhận lại.
    # (Admin đổi stage thì KHÔNG đụng vào is_push_enabled.)
    if not _admin:
        try:
            session.execute(text("UPDATE vip_users SET is_push_enabled = :e WHERE email = :u"),
                            {'e': cur['enabled'], 'u': email})
        except Exception:
            pass
    session.commit()
    cur.pop('default', None)
    return cur


def set_prefs_by_chat(Session, chat_id, enabled):
    """Cho webhook Telegram: /tat, /bat. Trả (email, prefs) hoặc (None, None) nếu chat chưa gắn tài khoản."""
    session = Session()
    try:
        r = _rows(session, "SELECT email FROM vip_users WHERE telegram_chat_id = :c", c=str(chat_id))
        if not r:
            return None, None
        return r[0]['email'], set_prefs(session, r[0]['email'], enabled=enabled)
    finally:
        session.close()


# ============================================================
# DỮ LIỆU CHUNG
# ============================================================

def _load_common(session):
    prices = {}
    for r in _rows(session, "SELECT ticker, price, trade_date FROM eod_prices"):
        if r['ticker'] and r['price']:
            prices[r['ticker'].upper().strip()] = (float(r['price']), str(r['trade_date'] or '')[:10])
    market = None
    try:
        m = _rows(session, """SELECT market_mode, mode_label, risk_score, allocation, date
                              FROM market_risk ORDER BY date DESC LIMIT 1""")
        market = m[0] if m else None
    except Exception:
        session.rollback()
    return prices, market


def load_bars(session, ticker, until=None):
    since = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    sql = """SELECT trade_date, open, high, low, close, volume FROM price_history
             WHERE ticker = :t AND trade_date >= :s""" + (" AND trade_date <= :u" if until else "") + \
          " ORDER BY trade_date"
    rows = _rows(session, sql, t=ticker, s=since, u=until)
    return [{'date': r['trade_date'], 'open': float(r['open'] or r['close']), 'high': float(r['high'] or r['close']),
             'low': float(r['low'] or r['close']), 'close': float(r['close']), 'volume': float(r['volume'] or 0)}
            for r in rows if r['close']]


def load_levels(session, ticker, email=None):
    return _rows(session, """SELECT id, user_id, ticker, price, note FROM watch_levels
                             WHERE ticker = :t AND (user_id IS NULL OR user_id = '' OR user_id = :u)
                             ORDER BY price""", t=ticker, u=email or '')


def _load_sells(session, since_date):
    try:
        rows = _rows(session, "SELECT ticker, exit_reason, date FROM signals WHERE action = 'SELL' AND date > :d",
                     d=since_date)
    except Exception:
        session.rollback()
        return {}
    out = {}
    for r in rows:
        out.setdefault((r['ticker'] or '').upper(), []).append(r)
    return out


def _alert_state(session, uid):
    return {(r['ticker'], r['ekey']): r for r in
            _rows(session, "SELECT ticker, ekey, last_date, value FROM watch_alert_state WHERE user_id = :u", u=uid)}


def _cooled(astate, ticker, ekey, today, days=COOLDOWN_DAYS):
    r = astate.get((ticker, ekey))
    d = _parse_date(r['last_date']) if r else None
    return d is not None and (today - d).days < days


# ============================================================
# ĐÁNH GIÁ 1 KHÁCH
# ============================================================

def evaluate_user(session, user, prices, market, today=None, scope='eod'):
    today = today or date.today()
    uid = user['email']
    holdings = _rows(session, "SELECT ticker, quantity, avg_price FROM portfolios WHERE user_id = :u", u=uid)
    cash_rows = _rows(session, "SELECT cash_amount FROM cash_positions WHERE user_id = :u", u=uid)
    cash = float(cash_rows[0]['cash_amount'] or 0) if cash_rows else 0.0
    state = {r['ticker']: r for r in _rows(session, "SELECT * FROM rescue_watch_state WHERE user_id = :u", u=uid)}
    astate = _alert_state(session, uid)

    events, warnings, new_state, marks, lines = [], [], [], [], []
    stale = False

    # --- định giá danh mục (giá hiện tại từ eod_prices)
    for h in holdings:
        t = (h['ticker'] or '').upper().strip()
        qty, avg = float(h['quantity'] or 0), float(h['avg_price'] or 0)
        if not t or qty <= 0 or avg <= 0:
            continue
        if t not in prices:
            warnings.append(f"{t}: chưa có giá — job giá sẽ tự thêm mã từ danh mục khách ở lần chạy tới")
            continue
        price, tdate = prices[t]
        if avg < 1000 <= price or price / avg > 50:
            warnings.append(f"{t}: giá vốn {avg:,.0f} có vẻ nhập theo nghìn đồng — kiểm tra lại, bỏ qua mã này")
            continue
        d = _parse_date(tdate)
        if d is None or (today - d).days > STALE_DAYS:
            stale = True
        lines.append({'ticker': t, 'qty': qty, 'avg': avg, 'price': price, 'tdate': tdate,
                      'value': qty * price, 'pl_pct': (price / avg - 1) * 100})
    total_value = sum(l['value'] for l in lines)
    total_assets = total_value + cash
    for l in lines:
        l['weight'] = l['value'] / total_assets * 100 if total_assets > 0 else 0

    def push(ev):
        """Áp dụng chống lặp; ghi lại mốc đã báo."""
        cd = TYPE_COOLDOWN.get(ev['type'], COOLDOWN_DAYS)
        if _cooled(astate, ev['ticker'], ev['key'], today, cd):
            return
        events.append(ev)
        marks.append({'user_id': uid, 'ticker': ev['ticker'], 'ekey': ev['key'], 'last_date': today.isoformat(),
                      'value': ev.get('level')})

    # --- biến cố theo từng mã
    for l in lines:
        t = l['ticker']
        pos = {'qty': l['qty'], 'pl_pct': l['pl_pct'], 'weight': l['weight']}
        manual = load_levels(session, t, uid)
        if scope == 'intraday':
            if l['tdate'] != today.isoformat():
                continue                                    # chưa có giá phiên hôm nay
            bars = load_bars(session, t, until=(today - timedelta(days=1)).isoformat())
            for ev in ta.detect_intraday(t, bars, l['price'], pos, manual):
                push(ev)
            continue

        bars = load_bars(session, t, until=today.isoformat())
        if not bars or bars[-1]['date'] != l['tdate']:
            warnings.append(f"{t}: lịch sử nến chưa có phiên {l['tdate']} — bỏ qua phân tích kỹ thuật hôm nay")
        else:
            evs, info = ta.detect_eod(t, bars, pos, manual)
            if info.get('skip'):
                warnings.append(f"{t}: {info['skip']}")
            for ev in evs:
                push(ev)

        # GIVEBACK: đang lãi lớn nhưng rời đỉnh (đỉnh theo dõi từ lúc giám sát)
        st = state.get(t)
        peak = max(float(st['peak_price'] or l['price']), l['price']) if st else l['price']
        alerted = bool(st['giveback_alerted']) if st else False
        if st and l['price'] >= peak:
            alerted = False
        from_peak = (l['price'] / peak - 1) * 100
        if st and l['pl_pct'] >= GIVEBACK_MIN_PROFIT and from_peak <= -GIVEBACK_PCT and not alerted:
            alerted = True
            push({'type': 'GIVEBACK', 'ticker': t, 'key': 'GIVEBACK', 'level': peak, 'price': l['price'],
                  'headline': f"<b>{t}</b> {ta.fp(l['price'])} đã rời đỉnh {ta.fp(peak)} {ta.fpct(abs(from_peak), sign=False)}"
                              f" — lãi còn {ta.fpct(l['pl_pct'])}",
                  'context': ta._ctx(pos),
                  'actions': [f"Bảo vệ lãi: cân nhắc chốt {ta._fraction(l['weight'])} hoặc đặt điểm dừng ~{ta.fp(l['price'] * 0.95)}",
                              "Lấy lại đỉnh cũ với KL tốt → giữ tiếp"]})
        new_state.append({'user_id': uid, 'ticker': t, 'last_price': l['price'], 'last_trade_date': l['tdate'],
                          'peak_price': peak, 'alert_level': None, 'giveback_alerted': alerted, 'top_pct': None})

    if scope == 'eod':
        # Tín hiệu BÁN của hệ thống cho mã đang giữ
        last_checks = [s['last_trade_date'] for k, s in state.items() if k != PORTFOLIO_ROW and s.get('last_trade_date')]
        if last_checks:
            sells = _load_sells(session, min(last_checks))
            for l in lines:
                if l['ticker'] in sells:
                    s = sells[l['ticker']][-1]
                    reason = {'STOP_LOSS': 'chạm cắt lỗ', 'TAKE_PROFIT': 'chốt lời', 'MA20_STRICT': 'gãy MA20'}.get(
                        s.get('exit_reason') or '', s.get('exit_reason') or 'hệ thống')
                    push({'type': 'SYSTEM_SELL', 'ticker': l['ticker'], 'key': f"SYSTEM_SELL:{s.get('date')}",
                          'level': None, 'price': l['price'],
                          'headline': f"<b>{l['ticker']}</b>: hệ thống AI vừa phát tín hiệu BÁN ({reason})",
                          'context': ta._ctx({'pl_pct': l['pl_pct'], 'weight': l['weight']}),
                          'actions': ["Xem lại vị thế, cân nhắc giảm theo tín hiệu hệ thống"]})

        # Tập trung
        top = max(lines, key=lambda x: x['value']) if lines else None
        top_pct = top['weight'] if top else 0.0
        prev = state.get(PORTFOLIO_ROW)
        prev_top = prev['top_pct'] if prev else None
        if prev_top is not None and prev_top <= CONCENTRATION_PCT < top_pct:
            push({'type': 'CONCENTRATION', 'ticker': top['ticker'], 'key': 'CONCENTRATION', 'level': None,
                  'price': top['price'],
                  'headline': f"Tỷ trọng <b>{top['ticker']}</b> vừa vượt {CONCENTRATION_PCT:.0f}% tổng tài sản "
                              f"(hiện {ta.fpct(top_pct, sign=False)})",
                  'context': '',
                  'actions': ["Cân nhắc đưa về dưới 35% vào các nhịp hồi để một mã không quyết định cả tài sản"]})
        new_state.append({'user_id': uid, 'ticker': PORTFOLIO_ROW, 'last_price': None, 'last_trade_date': None,
                          'peak_price': None, 'alert_level': None, 'giveback_alerted': False, 'top_pct': top_pct})

        # Thị trường hạ tỷ trọng khuyến nghị
        alloc = float(market['allocation']) if market and market.get('allocation') is not None else None
        prev_alloc = astate.get((PORTFOLIO_ROW, 'MARKET_ALLOC'))
        if alloc is not None:
            if prev_alloc and prev_alloc['value'] is not None and alloc <= float(prev_alloc['value']) - MARKET_DROP_PTS and lines:
                stock_pct = total_value / total_assets * 100 if total_assets else 0
                weak = sorted(lines, key=lambda x: x['pl_pct'])[:2]
                events.append({'type': 'MARKET', 'ticker': PORTFOLIO_ROW, 'key': 'MARKET', 'level': alloc,
                               'price': None,
                               'headline': f"Thị trường chuyển <b>{html.escape(str(market.get('mode_label') or market.get('market_mode')))}</b>: "
                                           f"tỷ trọng cổ phiếu khuyến nghị {float(prev_alloc['value']):.0f}% → {alloc:.0f}%",
                               'context': f"Danh mục đang {ta.fpct(stock_pct, sign=False)} cổ phiếu.",
                               'actions': [f"Ưu tiên giảm mã yếu nhất: " + ', '.join(f"{w['ticker']} ({ta.fpct(w['pl_pct'])})" for w in weak)
                                           if stock_pct > alloc + 5 else "Tỷ trọng hiện tại đã phù hợp — giữ kỷ luật, chưa mở mua mới"]})
            marks.append({'user_id': uid, 'ticker': PORTFOLIO_ROW, 'ekey': 'MARKET_ALLOC',
                          'last_date': today.isoformat(), 'value': alloc})

    events.sort(key=lambda e: ta.SEVERITY.get(e['type'], 9))
    stock_pct = (total_value / total_assets * 100) if total_assets > 0 else 0.0
    return {
        'user': uid, 'name': user.get('full_name') or uid, 'scope': scope,
        'baseline': not any(k != PORTFOLIO_ROW for k in state),
        'stale_prices': stale, 'events': events, 'warnings': warnings,
        'new_state': new_state, 'marks': marks,
        'summary': {'holdings': len(lines), 'stock_pct': round(stock_pct, 1),
                    'market_mode': (market or {}).get('market_mode'), 'allocation': (market or {}).get('allocation')},
    }


# ============================================================
# BẢN TIN
# ============================================================

def build_message(result, market, today=None):
    """Telegram (HTML)."""
    events = result['events']
    if not events:
        return None
    today = today or date.today()
    intraday = result.get('scope') == 'intraday'
    out = [f"{'⚡' if intraday else '🛡️'} <b>AI Advisor · Giám sát danh mục</b> — {today.strftime('%d/%m')}"
           + (" (trong phiên)" if intraday else ""),
           f"Chào anh/chị {html.escape(str(result['name']))},"]
    if market and not intraday:
        emoji = {'BULL': '🟢', 'BEAR': '🔴'}.get(market.get('market_mode'), '🟡')
        out.append(f"{emoji} Thị trường: {html.escape(str(market.get('mode_label') or market.get('market_mode')))} · "
                   f"khuyến nghị cổ phiếu {market.get('allocation')}% · danh mục đang "
                   f"{ta.fpct(result['summary']['stock_pct'], sign=False)}")
    for e in events[:MAX_EVENTS_PER_MSG]:
        out.append("")
        out.append(f"{ta.EMOJI.get(e['type'], '•')} {e['headline']}")
        if e.get('context'):
            out.append(f"<i>{html.escape(e['context'])}</i>")
        for a in e['actions']:
            out.append(f"▸ {html.escape(a)}")
    if len(events) > MAX_EVENTS_PER_MSG:
        out.append(f"\n… và {len(events) - MAX_EVENTS_PER_MSG} điểm khác trên VIP Dashboard")
    out.append("")
    out.append(f"👉 <a href=\"{DASHBOARD_URL}\">VIP Dashboard</a> · hỏi AI Advisor trước khi đặt lệnh")
    out.append(f"<i>{DISCLAIMER}</i>")
    out.append("Tắt nhận tin: gõ /tat")
    return "\n".join(out)


def build_email(result, market, today=None):
    """(subject, html) cho email. None nếu không có biến cố."""
    events = result['events']
    if not events:
        return None
    today = today or date.today()
    tickers = list(dict.fromkeys(e['ticker'] for e in events if e['ticker'] != PORTFOLIO_ROW))
    subject = (f"AI Advisor · Giám sát danh mục {today.strftime('%d/%m')}: "
               f"{len(events)} điểm cần chú ý" + (f" ({', '.join(tickers[:4])})" if tickers else ""))
    color = {1: '#b91c1c', 2: '#c2410c', 3: '#b45309', 4: '#b45309', 5: '#15803d'}
    blocks = []
    for e in events[:MAX_EVENTS_PER_MSG]:
        c = color.get(ta.SEVERITY.get(e['type'], 4), '#334155')
        acts = ''.join(f"<li style='margin:2px 0'>{html.escape(a)}</li>" for a in e['actions'])
        blocks.append(
            f"<div style='border-left:4px solid {c};background:#f8fafc;padding:12px 14px;margin:0 0 12px;border-radius:4px'>"
            f"<div style='font-size:15px;color:#0f172a'>{ta.EMOJI.get(e['type'], '')} {e['headline']}</div>"
            + (f"<div style='font-size:13px;color:#64748b;margin-top:4px'>{html.escape(e['context'])}</div>" if e.get('context') else '')
            + f"<ul style='margin:8px 0 0;padding-left:18px;font-size:14px;color:#334155'>{acts}</ul></div>")
    mk = ''
    if market:
        mk = (f"<p style='font-size:13px;color:#475569;margin:0 0 14px'>Thị trường: <b>{html.escape(str(market.get('mode_label') or market.get('market_mode')))}</b>"
              f" · khuyến nghị cổ phiếu {market.get('allocation')}% · danh mục đang {ta.fpct(result['summary']['stock_pct'], sign=False)}</p>")
    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#ffffff">
      <div style="background:#0d2b5e;padding:18px 22px;border-top:4px solid #e8a020">
        <div style="color:#e8a020;font-size:12px;font-weight:700;letter-spacing:1px">AI ADVISOR</div>
        <div style="color:#ffffff;font-size:18px;font-weight:700;margin-top:4px">Giám sát danh mục — {today.strftime('%d/%m/%Y')}</div>
      </div>
      <div style="padding:20px 22px">
        <p style="font-size:14px;color:#334155">Chào anh/chị <b>{html.escape(str(result['name']))}</b>,</p>
        {mk}{''.join(blocks)}
        <div style="text-align:center;margin:18px 0">
          <a href="{DASHBOARD_URL}" style="background:#0d2b5e;color:#fff;padding:11px 22px;border-radius:6px;text-decoration:none;font-weight:700;font-size:14px">Mở VIP Dashboard</a>
        </div>
        <p style="font-size:12px;color:#94a3b8;line-height:1.6">{DISCLAIMER}<br>
          Không muốn nhận tin? Tắt tại VIP Dashboard (nút 🛡️ Giám sát) hoặc gõ /tat trong Telegram.</p>
      </div>
    </div>"""
    return subject, body


# ============================================================
# GỬI + LƯU
# ============================================================

def send_telegram(chat_id, message):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        import requests
        ok = True
        for c in [message[i:i + 3900] for i in range(0, len(message), 3900)] or ['']:
            r = requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                              json={'chat_id': chat_id, 'text': c, 'parse_mode': 'HTML',
                                    'disable_web_page_preview': True}, timeout=15)
            ok = ok and r.status_code == 200
            if r.status_code != 200:
                logger.error(f'[RescueWatch] Telegram {chat_id}: {r.text[:200]}')
        return ok
    except Exception as e:
        logger.error(f'[RescueWatch] Telegram error: {e}')
        return False


def send_email(to, subject, body):
    """Dùng chung hàm gửi email (Gmail API) với email mật khẩu khách — campaign_api._send_email."""
    if not to:
        return False
    try:
        from campaign_api import _send_email
        return bool(_send_email(to, subject, body))
    except Exception as e:
        logger.error(f'[RescueWatch] Email error {to}: {e}')
        return False


def _save_state(session, rows):
    now = datetime.now()
    for r in rows:
        session.execute(text("DELETE FROM rescue_watch_state WHERE user_id = :user_id AND ticker = :ticker"), r)
        session.execute(text("""
            INSERT INTO rescue_watch_state (user_id, ticker, last_price, last_trade_date, peak_price, alert_level,
                                            giveback_alerted, top_pct, updated_at)
            VALUES (:user_id, :ticker, :last_price, :last_trade_date, :peak_price, :alert_level,
                    :giveback_alerted, :top_pct, :now)"""), {**r, 'now': now})


def _save_marks(session, marks):
    for m in marks:
        session.execute(text("DELETE FROM watch_alert_state WHERE user_id = :user_id AND ticker = :ticker AND ekey = :ekey"), m)
        session.execute(text("""INSERT INTO watch_alert_state (user_id, ticker, ekey, last_date, value)
                                VALUES (:user_id, :ticker, :ekey, :last_date, :value)"""), m)


def _log_events(session, result, mode, sent):
    for e in result['events']:
        detail = _strip_tags(e['headline']) + (' | ' + ' | '.join(e['actions']) if e['actions'] else '')
        session.execute(text("""
            INSERT INTO rescue_watch_log (user_id, ticker, event_type, detail, price, pl_pct, mode, sent, created_at)
            VALUES (:u, :t, :et, :d, :p, NULL, :m, :s, :now)"""),
            {'u': result['user'], 't': e['ticker'], 'et': e['type'], 'd': detail[:2000], 'p': e.get('price'),
             'm': mode, 's': bool(sent), 'now': datetime.now()})


def run_watch(Session, mode='preview', only_user=None, today=None, scope='eod', email_test=False):
    if mode not in ('preview', 'admin', 'live'):
        raise ValueError('mode phải là preview | admin | live')
    if scope not in ('eod', 'intraday'):
        raise ValueError('scope phải là eod | intraday')
    if mode == 'admin' and not ADMIN_CHAT_ID:
        raise ValueError('Chưa có chat_id admin: đặt TELEGRAM_CHAT_ID hoặc ADMIN_TELEGRAM_CHAT_ID trên Render')

    if scope == 'intraday' and today is None:
        vn_now = datetime.utcnow() + timedelta(hours=7)
        if not (9 <= vn_now.hour < 15) or vn_now.weekday() >= 5:
            # GitHub đôi khi chạy lịch trễ hàng giờ — ngoài giờ giao dịch thì "trong phiên" không còn ý nghĩa
            return {'mode': mode, 'scope': scope, 'date': vn_now.date().isoformat(), 'users': [],
                    'note': f'Bỏ qua: ngoài giờ giao dịch ({vn_now.strftime("%H:%M")} giờ VN) — để lần quét cuối ngày xử lý'}
    today = today or date.today()
    session = Session()
    report = {'mode': mode, 'scope': scope, 'date': today.isoformat(), 'users': []}
    try:
        prices, market = _load_common(session)
        users = _rows(session, """SELECT email, full_name, telegram_chat_id, is_push_enabled, tier
                                  FROM vip_users WHERE is_active = :a""", a=True)
        users = [u for u in users if (u.get('tier') or '').lower() == 'vip']
        if only_user:
            users = [u for u in users if u['email'].lower() == only_user.lower()]

        for u in users:
            if not _rows(session, "SELECT 1 AS x FROM portfolios WHERE user_id = :u LIMIT 1", u=u['email']):
                continue
            prefs = get_prefs(session, u['email'])
            res = evaluate_user(session, u, prices, market, today=today, scope=scope)
            msg = build_message(res, market, today=today)
            mail = build_email(res, market, today=today)
            sent, skipped, channels = False, None, []

            if res['stale_prices']:
                skipped = f'Giá cũ hơn {STALE_DAYS} ngày — không gửi (kiểm tra job cập nhật giá)'
            elif msg and mode == 'admin':
                ch = prefs['channel'] if prefs['enabled'] else 'TẮT'
                sent = send_telegram(ADMIN_CHAT_ID, f"📝 <b>BẢN NHÁP cho {html.escape(u['email'])}</b> (kênh khách chọn: {ch})\n\n{msg}")
                if email_test and mail and ADMIN_EMAIL:
                    send_email(ADMIN_EMAIL, '[BẢN NHÁP] ' + mail[0], mail[1])
            elif msg and mode == 'live' and prefs['stage'] != 'live':
                # Khách CHƯA được admin mở gửi thật -> vẫn là bản nháp gửi admin
                ch = prefs['channel'] if prefs['enabled'] else 'TẮT'
                sent = send_telegram(ADMIN_CHAT_ID, f"📝 <b>BẢN NHÁP cho {html.escape(u['email'])}</b> "
                                                    f"(chưa mở gửi thật · kênh khách chọn: {ch})\n\n{msg}")
                skipped = 'Chưa mở gửi thật cho khách này — đã gửi bản nháp về admin'
            elif msg and mode == 'live':
                if not prefs['enabled']:
                    skipped = 'Khách đã TẮT nhận khuyến nghị'
                else:
                    if prefs['channel'] in ('telegram', 'both') and u.get('telegram_chat_id'):
                        if send_telegram(u['telegram_chat_id'], msg):
                            channels.append('telegram')
                    if prefs['channel'] in ('email', 'both') and mail:
                        if send_email(u['email'], *mail):
                            channels.append('email')
                    sent = bool(channels)
                    if not sent:
                        skipped = 'Không gửi được (khách chưa có Telegram và email lỗi?)'

            if mode != 'preview' and not res['stale_prices']:
                if scope == 'eod':
                    _save_state(session, res['new_state'])
                _save_marks(session, res['marks'])
                _log_events(session, res, mode, sent)
                session.commit()

            report['users'].append({
                'user': u['email'], 'baseline': res['baseline'], 'events': len(res['events']),
                'event_types': [f"{e['ticker']}:{e['type']}" for e in res['events']],
                'sent': sent, 'channels': channels, 'skipped': skipped, 'prefs': prefs,
                'warnings': res['warnings'], 'summary': res['summary'], 'message': msg,
            })

        # Tóm tắt cho admin (cả ngày yên ắng, để biết job đã chạy) — chỉ lần EOD
        if mode in ('admin', 'live') and ADMIN_CHAT_ID and scope == 'eod':
            n_ev = sum(1 for x in report['users'] if x['events'])
            warn = [f"• {x['user']}: {w}" for x in report['users'] for w in x['warnings']]
            skip = [f"• {x['user']}: {x['skipped']}" for x in report['users'] if x['skipped']]
            t_ = (f"🛡️ <b>Giám sát danh mục {today.strftime('%d/%m')}</b> ({mode})\n"
                  f"Khách được quét: {len(report['users'])} · có biến cố: {n_ev}")
            n_live = sum(1 for x in report['users'] if x['prefs'].get('stage') == 'live')
            t_ += f"\nĐã mở gửi thật: {n_live}/{len(report['users'])} khách" if mode == 'live' else ''
            if mode == 'live':
                t_ += "\n" + "\n".join(f"• {html.escape(x['user'])}: {', '.join(x['event_types']) or '—'}"
                                       f"{' → ' + '+'.join(x['channels']) if x['channels'] else ''}"
                                       for x in report['users'] if x['events'])
            if skip:
                t_ += "\n\n<b>Không gửi:</b>\n" + html.escape("\n".join(skip))
            if warn:
                t_ += "\n\n<b>Cảnh báo dữ liệu:</b>\n" + html.escape("\n".join(warn[:15]))
            send_telegram(ADMIN_CHAT_ID, t_)
        return report
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def analyze_ticker(Session, ticker, email=None):
    """Cho admin kiểm tra: mốc tự động + mốc tay + biến cố của phiên gần nhất."""
    session = Session()
    try:
        t = ticker.upper().strip()
        bars = load_bars(session, t)
        manual = load_levels(session, t, email)
        if len(bars) < ta.MIN_BARS:
            return {'ticker': t, 'bars': len(bars), 'error': f'Chưa đủ lịch sử nến ({len(bars)} phiên)'}
        evs, info = ta.detect_eod(t, bars, None, manual)
        key = ta.key_levels(info['levels'])
        c = info['close']
        fmt = lambda l: {'price': round(l['price']), 'zone': ta._zone_txt(l), 'label': l['label'], 'source': l['source']}
        return {'ticker': t, 'bars': len(bars), 'last_date': bars[-1]['date'], 'close': c, 'chg': info['chg'],
                'vol_ratio': info['vol_ratio'],
                'resistances': [fmt(l) for l in key if l['price'] > c][:4],
                'supports': [fmt(l) for l in reversed(key) if l['price'] < c][:4],
                'ma': {l['label']: round(l['price']) for l in info['levels'] if l['source'] == 'ma'},
                'old_peak': info['peak'], 'manual': manual,
                'events_last_session': [{'type': e['type'], 'headline': _strip_tags(e['headline']), 'actions': e['actions']}
                                        for e in evs]}
    finally:
        session.close()


# ============================================================
# ROUTES
# ============================================================

def _require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hmac.compare_digest(request.headers.get('X-Admin-Key', ''), ADMIN_SECRET):
            return jsonify({'error': 'Unauthorized - Admin key required'}), 401
        return f(*args, **kwargs)
    return decorated


def init_rescue_watch_routes(app, engine, Session):
    try:
        ensure_tables(engine)
    except Exception as e:
        print(f"⚠️  Rescue Watch: chưa tạo được bảng lúc khởi động ({e}) — sẽ thử lại khi chạy")

    @app.route('/api/admin/rescue-watch/run', methods=['POST'])
    @_require_admin
    def rescue_watch_run():
        data = request.get_json(silent=True) or {}
        try:
            ensure_tables(engine)
            return jsonify({'success': True, **run_watch(
                Session, mode=(data.get('mode') or 'preview').lower(), only_user=data.get('user'),
                scope=(data.get('scope') or 'eod').lower(), email_test=bool(data.get('email_test')))})
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            logger.exception('[RescueWatch] run error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/rescue-watch/log', methods=['GET'])
    @_require_admin
    def rescue_watch_log():
        days = int(request.args.get('days', 30))
        session = Session()
        try:
            rows = _rows(session, """
                SELECT l.created_at, l.user_id, l.ticker, l.event_type, l.detail, l.price, l.mode, l.sent,
                       e.price AS price_now
                FROM rescue_watch_log l LEFT JOIN eod_prices e ON e.ticker = l.ticker
                WHERE l.created_at >= :s ORDER BY l.created_at DESC""", s=datetime.now() - timedelta(days=days))
            for r in rows:
                if r.get('price') and r.get('price_now'):
                    r['change_since_alert_pct'] = round((r['price_now'] / r['price'] - 1) * 100, 2)
                r['created_at'] = str(r['created_at'])
            return jsonify({'success': True, 'days': days, 'total': len(rows), 'log': rows})
        finally:
            session.close()

    @app.route('/api/admin/watch/levels', methods=['GET', 'POST'])
    @_require_admin
    def watch_levels():
        session = Session()
        try:
            ensure_tables(engine)
            if request.method == 'GET':
                t = (request.args.get('ticker') or '').upper().strip()
                sql = "SELECT id, user_id, ticker, price, note FROM watch_levels" + (" WHERE ticker = :t" if t else "") + \
                      " ORDER BY ticker, price"
                return jsonify({'success': True, 'levels': _rows(session, sql, t=t)})
            d = request.get_json(silent=True) or {}
            t = (d.get('ticker') or '').upper().strip()
            try:
                p = float(d.get('price'))
            except (TypeError, ValueError):
                p = 0
            if not t or p <= 0:
                return jsonify({'success': False, 'error': 'Cần ticker và price (VND, vd 15000)'}), 400
            if p < 500:
                p *= 1000                                   # nhập 15 hoặc 15.0 -> 15.000
            uid = (d.get('user') or '').strip().lower() or None
            dup = _rows(session, """SELECT id FROM watch_levels WHERE ticker = :t AND ABS(price - :p) < 1
                                     AND COALESCE(user_id, '') = :u""", t=t, p=p, u=uid or '')
            if dup:
                return jsonify({'success': True, 'ticker': t, 'price': p, 'duplicate': True})
            session.execute(text("""INSERT INTO watch_levels (user_id, ticker, price, note, created_at)
                                    VALUES (:u, :t, :p, :n, :now)"""),
                            {'u': uid, 't': t, 'p': p,
                             'n': (d.get('note') or '').strip(), 'now': datetime.now()})
            session.commit()
            return jsonify({'success': True, 'ticker': t, 'price': p})
        finally:
            session.close()

    @app.route('/api/admin/watch/levels/delete', methods=['POST'])
    @_require_admin
    def watch_levels_delete():
        d = request.get_json(silent=True) or {}
        session = Session()
        try:
            n = session.execute(text("DELETE FROM watch_levels WHERE id = :i"), {'i': int(d.get('id') or 0)}).rowcount
            session.commit()
            return jsonify({'success': bool(n), 'deleted': n})
        finally:
            session.close()

    @app.route('/api/admin/watch/users', methods=['GET'])
    @_require_admin
    def watch_users():
        """Khách VIP đã nhập danh mục + trạng thái giám sát (admin mở/khóa gửi thật)."""
        session = Session()
        try:
            ensure_tables(engine)
            out = []
            for u in _rows(session, """SELECT email, full_name, telegram_chat_id, tier FROM vip_users
                                       WHERE is_active = :a ORDER BY email""", a=True):
                if (u.get('tier') or '').lower() != 'vip':
                    continue
                n = _rows(session, "SELECT COUNT(*) AS n FROM portfolios WHERE user_id = :u", u=u['email'])[0]['n']
                p = get_prefs(session, u['email'])
                p.pop('default', None)
                out.append({'email': u['email'], 'name': u.get('full_name'), 'holdings': int(n),
                            'telegram': bool(u.get('telegram_chat_id')), **p})
            return jsonify({'success': True, 'users': out})
        finally:
            session.close()

    @app.route('/api/admin/watch/stage', methods=['POST'])
    @_require_admin
    def watch_stage():
        d = request.get_json(silent=True) or {}
        session = Session()
        try:
            ensure_tables(engine)
            p = set_stage(session, (d.get('user') or '').strip().lower(), (d.get('stage') or '').strip().lower())
            return jsonify({'success': True, 'user': d.get('user'), **p})
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        finally:
            session.close()

    @app.route('/api/admin/watch/analyze', methods=['GET'])
    @_require_admin
    def watch_analyze():
        t = request.args.get('ticker') or ''
        if not t:
            return jsonify({'success': False, 'error': 'Thiếu ticker'}), 400
        ensure_tables(engine)
        return jsonify({'success': True, **analyze_ticker(Session, t, request.args.get('user'))})

    # --- VIP: bật/tắt + kênh
    try:
        from vip_auth import require_vip_auth
    except Exception:
        require_vip_auth = None

    if require_vip_auth:
        from flask import g

        @app.route('/api/vip/watch/prefs', methods=['GET', 'POST'])
        @require_vip_auth
        def vip_watch_prefs():
            session = Session()
            try:
                ensure_tables(engine)
                email = g.email
                if request.method == 'POST':
                    d = request.get_json(silent=True) or {}
                    p = set_prefs(session, email, enabled=d.get('enabled'), channel=d.get('channel'))
                else:
                    p = get_prefs(session, email)
                    p.pop('default', None)
                tg = _rows(session, "SELECT telegram_chat_id FROM vip_users WHERE email = :u", u=email)
                live = p.pop('stage', 'draft') == 'live'
                return jsonify({'success': True, **p, 'live': live,
                                'telegram_connected': bool(tg and tg[0]['telegram_chat_id'])})
            except ValueError as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            finally:
                session.close()

    print("✅ Rescue Watch v2 (Giám sát danh mục) routes registered:")
    print("   POST /api/admin/rescue-watch/run   [ADMIN] mode=preview|admin|live scope=eod|intraday")
    print("   GET  /api/admin/rescue-watch/log   [ADMIN]")
    print("   GET/POST /api/admin/watch/levels · POST /api/admin/watch/levels/delete · GET /api/admin/watch/analyze [ADMIN]")
    print("   GET  /api/admin/watch/users · POST /api/admin/watch/stage {user, stage: draft|live} [ADMIN]")
    print("   GET/POST /api/vip/watch/prefs      [VIP] bật/tắt + kênh nhận")
