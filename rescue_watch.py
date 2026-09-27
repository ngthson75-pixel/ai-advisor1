"""
AI ADVISOR - RESCUE WATCH (Canh gác danh mục VIP + Telegram)
============================================================
File: rescue_watch.py
Version: 1.0 (2026-09-25)

Mục đích
--------
Mở rộng Portfolio Rescue từ "user tự bấm nút" sang "hệ thống tự canh gác mỗi ngày":
sau phiên, quét danh mục của từng khách VIP, phát hiện thay đổi đáng chú ý và gửi
1 bản tin Telegram (chỉ khi có sự kiện). Bản tin là LỜI NHẮC, không phải phán quyết:
cuối tin luôn mời khách mở VIP Dashboard và tự bấm "🆘 Giải cứu danh mục".

Không đụng vào logic cũ: chỉ ĐỌC các bảng có sẵn (vip_users, portfolios,
cash_positions, eod_prices, signals, market_risk) và GHI vào 2 bảng mới của riêng
module này (rescue_watch_state, rescue_watch_log) — tự tạo bằng CREATE TABLE IF NOT EXISTS.

Sự kiện theo dõi (so với lần chạy trước, lưu trong rescue_watch_state)
----------------------------------------------------------------------
  LEVEL_UP     Mã chuyển sang mức cảnh báo nặng hơn: Vàng -10% / Cam -15% / Đỏ -20% (so giá vốn)
  DROP         Giảm >= 5% so với giá ở lần kiểm tra trước (chỉ khi đã có phiên mới)
  GIVEBACK     Mã đang lãi >= 20% nhưng đã rời đỉnh (từ lúc bắt đầu canh gác) >= 10%
  SYSTEM_SELL  Hệ thống vừa phát tín hiệu BÁN cho mã khách đang giữ
  CONCENTRATION Tỷ trọng mã lớn nhất vừa vượt 35% tổng tài sản

Lần chạy đầu tiên cho mỗi mã chỉ ghi "trạng thái gốc" (baseline), không báo — tránh
spam ngày đầu. Chẩn đoán ban đầu dùng nút Giải cứu danh mục.

Chế độ chạy
-----------
  preview  Chỉ tính và trả JSON. KHÔNG gửi, KHÔNG ghi trạng thái.       (an toàn để thử)
  admin    Gửi BẢN NHÁP của từng khách vào Telegram admin (ADMIN_TELEGRAM_CHAT_ID),
           ghi trạng thái + log. Admin đọc, duyệt rồi chuyển tiếp.        (tuần đầu)
  live     Gửi thẳng cho khách có telegram_chat_id và đã bật nhận thông báo
           (vip_users.is_push_enabled), ghi trạng thái + log, gửi tóm tắt cho admin.

Tích hợp vào backend_api.py (sau init_vip_system):
    from rescue_watch import init_rescue_watch_routes
    init_rescue_watch_routes(app, engine, Session)

Endpoints (header X-Admin-Key):
    POST /api/admin/rescue-watch/run   body: {"mode": "preview|admin|live", "user": "email (tùy chọn)"}
    GET  /api/admin/rescue-watch/log?days=30

Env:
    TELEGRAM_BOT_TOKEN        (đã có)
    ADMIN_SECRET              (đã có)
    ADMIN_TELEGRAM_CHAT_ID    (MỚI — chat_id Telegram của admin, nhận bản nháp + tóm tắt)
"""

import os
import html
import hmac
import logging
from datetime import datetime, date, timedelta
from functools import wraps

from flask import request, jsonify
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

ADMIN_SECRET       = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID      = os.getenv('ADMIN_TELEGRAM_CHAT_ID', '')

# Ngưỡng — trùng với Risk Shield trong spec (Yellow/Orange/Red) và nút Giải cứu (35%)
LEVELS             = [(-20.0, 'red'), (-15.0, 'orange'), (-10.0, 'yellow')]
LEVEL_RANK         = {'none': 0, 'yellow': 1, 'orange': 2, 'red': 3}
LEVEL_LABEL        = {'yellow': 'VÀNG (lỗ ≥10%)', 'orange': 'CAM (lỗ ≥15%)', 'red': 'ĐỎ (lỗ ≥20%)'}
LEVEL_EMOJI        = {'yellow': '🟡', 'orange': '🟠', 'red': '🔴'}
DROP_PCT           = float(os.getenv('RW_DROP_PCT', '5'))           # giảm so với lần kiểm tra trước
GIVEBACK_MIN_PROFIT = float(os.getenv('RW_GIVEBACK_MIN_PROFIT', '20'))
GIVEBACK_PCT       = float(os.getenv('RW_GIVEBACK_PCT', '10'))      # rời đỉnh
CONCENTRATION_PCT  = float(os.getenv('RW_CONCENTRATION_PCT', '35'))
STALE_DAYS         = int(os.getenv('RW_STALE_DAYS', '4'))           # giá EOD cũ hơn -> không gửi khách
MAX_EVENTS_PER_MSG = 8
PORTFOLIO_ROW      = '*'   # dòng trạng thái cấp danh mục trong rescue_watch_state

EVENT_ORDER = {'LEVEL_UP': 0, 'SYSTEM_SELL': 1, 'DROP': 2, 'GIVEBACK': 3, 'CONCENTRATION': 4}


# ============================================================
# DB HELPERS
# ============================================================

def ensure_tables(engine):
    """Tạo 2 bảng riêng của module (idempotent, chạy được trên PostgreSQL và SQLite)."""
    is_sqlite = engine.dialect.name == 'sqlite'
    id_col = 'INTEGER PRIMARY KEY AUTOINCREMENT' if is_sqlite else 'SERIAL PRIMARY KEY'
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rescue_watch_state (
                user_id           VARCHAR(255) NOT NULL,
                ticker            VARCHAR(10)  NOT NULL,
                last_price        DOUBLE PRECISION,
                last_trade_date   VARCHAR(20),
                peak_price        DOUBLE PRECISION,
                alert_level       VARCHAR(10),
                giveback_alerted  BOOLEAN DEFAULT FALSE,
                top_pct           DOUBLE PRECISION,
                updated_at        TIMESTAMP,
                PRIMARY KEY (user_id, ticker)
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS rescue_watch_log (
                id          {id_col},
                user_id     VARCHAR(255),
                ticker      VARCHAR(10),
                event_type  VARCHAR(30),
                detail      TEXT,
                price       DOUBLE PRECISION,
                pl_pct      DOUBLE PRECISION,
                mode        VARCHAR(10),
                sent        BOOLEAN,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))


def _rows(session, sql, **params):
    return session.execute(text(sql), params).mappings().all()


def _level_of(pl_pct):
    for threshold, name in LEVELS:
        if pl_pct <= threshold:
            return name
    return 'none'


def _fmt_price(v):
    return f"{v:,.0f}".replace(',', '.')


def _fmt_pct(v, sign=True):
    s = f"{v:+.1f}" if sign else f"{v:.1f}"
    return s.replace('.', ',') + '%'


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


# ============================================================
# CORE — tính sự kiện cho 1 khách
# ============================================================

def _load_common(session):
    prices = {}
    for r in _rows(session, "SELECT ticker, price, trade_date FROM eod_prices"):
        if r['ticker'] and r['price']:
            prices[r['ticker'].upper().strip()] = (float(r['price']), str(r['trade_date'] or ''))

    market = None
    try:
        m = _rows(session, """SELECT market_mode, mode_label, risk_score, allocation, date
                              FROM market_risk ORDER BY date DESC LIMIT 1""")
        market = dict(m[0]) if m else None
    except Exception:
        session.rollback()
    return prices, market


def _load_state(session, user_id):
    rows = _rows(session, "SELECT * FROM rescue_watch_state WHERE user_id = :u", u=user_id)
    return {r['ticker']: dict(r) for r in rows}


def _load_sells(session, since_date):
    """Tín hiệu BÁN của hệ thống từ sau since_date (chuỗi YYYY-MM-DD, không bao gồm)."""
    try:
        rows = _rows(session, """
            SELECT ticker, exit_reason, exit_price, date FROM signals
            WHERE action = 'SELL' AND date > :d
        """, d=since_date)
    except Exception:
        session.rollback()
        return {}
    out = {}
    for r in rows:
        out.setdefault((r['ticker'] or '').upper(), []).append(dict(r))
    return out


def evaluate_user(session, user, prices, market, today=None):
    """
    Trả về dict:
      events         danh sách sự kiện (đã sắp xếp theo mức độ)
      warnings       vấn đề dữ liệu (chỉ gửi admin, không gửi khách)
      new_state      các dòng trạng thái cần ghi
      summary        số liệu tổng quan danh mục
    """
    today = today or date.today()
    uid = user['email']
    holdings = _rows(session, "SELECT ticker, quantity, avg_price FROM portfolios WHERE user_id = :u", u=uid)
    cash_rows = _rows(session, "SELECT cash_amount FROM cash_positions WHERE user_id = :u", u=uid)
    cash = float(cash_rows[0]['cash_amount'] or 0) if cash_rows else 0.0
    state = _load_state(session, uid)

    events, warnings, new_state, lines = [], [], [], []
    stale = False
    total_value = total_cost = 0.0

    for h in holdings:
        t = (h['ticker'] or '').upper().strip()
        qty = float(h['quantity'] or 0)
        avg = float(h['avg_price'] or 0)
        if not t or qty <= 0 or avg <= 0:
            continue
        if t not in prices:
            warnings.append(f"{t}: không có giá EOD — mã chưa nằm trong danh sách cập nhật giá, P/L sẽ sai")
            total_cost += qty * avg
            total_value += qty * avg
            continue
        price, tdate = prices[t]
        if avg < 1000 <= price or price / avg > 50:
            warnings.append(f"{t}: giá vốn {avg:,.0f} có vẻ nhập theo đơn vị nghìn đồng — kiểm tra lại, bỏ qua mã này")
            continue
        d = _parse_date(tdate)
        if d is None or (today - d).days > STALE_DAYS:
            stale = True

        cost, value = qty * avg, qty * price
        pl = (price / avg - 1) * 100
        total_cost += cost
        total_value += value
        lines.append({'ticker': t, 'value': value, 'pl_pct': pl, 'price': price})

        level = _level_of(pl)
        st = state.get(t)
        peak = max(float(st['peak_price'] or price), price) if st else price
        giveback_alerted = bool(st['giveback_alerted']) if st else False
        if st and price >= peak:            # đỉnh mới -> cho phép cảnh báo rời đỉnh lần sau
            giveback_alerted = False

        if st:  # đã có trạng thái gốc -> so sánh
            # Biến động so với lần kiểm tra trước (chỉ khi đã sang phiên mới)
            chg, chg_txt = None, ''
            last_p, last_d = st['last_price'], st['last_trade_date']
            if last_p and last_d and tdate and tdate != last_d:
                chg = (price / float(last_p) - 1) * 100
                chg_txt = f" (phiên này {_fmt_pct(chg)}: {_fmt_price(float(last_p))} → {_fmt_price(price)})"
            big_drop = chg is not None and chg <= -DROP_PCT
            merged = False   # 1 mã chỉ 1 dòng: biến động được gộp vào sự kiện chính

            if LEVEL_RANK[level] > LEVEL_RANK.get(st['alert_level'] or 'none', 0):
                events.append({'type': 'LEVEL_UP', 'ticker': t, 'price': price, 'pl_pct': pl,
                               'text': f"{LEVEL_EMOJI[level]} <b>{t}</b> vừa chuyển sang mức {LEVEL_LABEL[level]}: "
                                       f"{_fmt_pct(pl)} so với giá vốn" + (chg_txt if big_drop else '')})
                merged = True
            from_peak = (price / peak - 1) * 100
            if pl >= GIVEBACK_MIN_PROFIT and from_peak <= -GIVEBACK_PCT and not giveback_alerted:
                giveback_alerted = True
                events.append({'type': 'GIVEBACK', 'ticker': t, 'price': price, 'pl_pct': pl,
                               'text': f"💰 <b>{t}</b> đã rời đỉnh {_fmt_pct(abs(from_peak), sign=False)}, "
                                       f"lãi còn {_fmt_pct(pl)} — nên xem lại kịch bản giữ lãi"
                                       + (chg_txt if big_drop and not merged else '')})
                merged = True
            if big_drop and not merged:
                events.append({'type': 'DROP', 'ticker': t, 'price': price, 'pl_pct': pl,
                               'text': f"📉 <b>{t}</b> giảm {_fmt_pct(abs(chg), sign=False)} so với lần kiểm tra trước "
                                       f"({_fmt_price(float(last_p))} → {_fmt_price(price)}), lãi/lỗ hiện {_fmt_pct(pl)}"})

        new_state.append({'user_id': uid, 'ticker': t, 'last_price': price, 'last_trade_date': tdate,
                          'peak_price': peak, 'alert_level': level, 'giveback_alerted': giveback_alerted,
                          'top_pct': None})

    # Tín hiệu BÁN của hệ thống cho mã đang giữ (từ sau lần kiểm tra trước)
    held = {l['ticker'] for l in lines}
    last_checks = [s['last_trade_date'] for k, s in state.items() if k != PORTFOLIO_ROW and s.get('last_trade_date')]
    if last_checks:
        sells = _load_sells(session, min(last_checks))
        for t in sorted(held & set(sells)):
            s = sells[t][-1]
            reason = {'STOP_LOSS': 'cắt lỗ', 'TAKE_PROFIT': 'chốt lời', 'MA20_STRICT': 'gãy MA20'}.get(
                s.get('exit_reason') or '', s.get('exit_reason') or 'hệ thống')
            p = next((l for l in lines if l['ticker'] == t), None)
            events.append({'type': 'SYSTEM_SELL', 'ticker': t, 'price': p['price'] if p else None,
                           'pl_pct': p['pl_pct'] if p else None,
                           'text': f"🔔 <b>{t}</b>: hệ thống vừa phát tín hiệu BÁN ({reason})"})

    # Cấp danh mục: tập trung
    total_assets = total_value + cash
    top = max(lines, key=lambda l: l['value']) if lines else None
    top_pct = (top['value'] / total_assets * 100) if (top and total_assets > 0) else 0.0
    prev_row = state.get(PORTFOLIO_ROW)
    prev_top = prev_row['top_pct'] if prev_row else None
    if prev_top is not None and prev_top <= CONCENTRATION_PCT < top_pct:
        events.append({'type': 'CONCENTRATION', 'ticker': top['ticker'], 'price': top['price'], 'pl_pct': top['pl_pct'],
                       'text': f"🎯 Tỷ trọng <b>{top['ticker']}</b> vừa vượt {CONCENTRATION_PCT:.0f}% tổng tài sản "
                               f"(hiện {_fmt_pct(top_pct, sign=False)})"})
    new_state.append({'user_id': uid, 'ticker': PORTFOLIO_ROW, 'last_price': None, 'last_trade_date': None,
                      'peak_price': None, 'alert_level': None, 'giveback_alerted': False, 'top_pct': top_pct})

    events.sort(key=lambda e: EVENT_ORDER.get(e['type'], 9))
    stock_pct = (total_value / total_assets * 100) if total_assets > 0 else 0.0
    return {
        'user': uid,
        'name': user.get('full_name') or uid,
        'baseline': not any(k != PORTFOLIO_ROW for k in state),
        'stale_prices': stale,
        'events': events,
        'warnings': warnings,
        'new_state': new_state,
        'summary': {
            'holdings': len(lines), 'stock_pct': round(stock_pct, 1),
            'top_ticker': top['ticker'] if top else None, 'top_pct': round(top_pct, 1),
            'total_pl_pct': round((total_value / total_cost - 1) * 100, 1) if total_cost > 0 else 0.0,
            'red': sum(1 for l in lines if l['pl_pct'] <= -20),
            'market_mode': (market or {}).get('market_mode'),
            'allocation': (market or {}).get('allocation'),
        },
    }


def build_message(result, market, today=None):
    """Bản tin Telegram (HTML) cho khách. None nếu không có sự kiện."""
    events = result['events']
    if not events:
        return None
    today = today or date.today()
    s = result['summary']
    name = html.escape(str(result['name']))
    lines = [f"🛡️ <b>AI Advisor · Canh gác danh mục</b> — {today.strftime('%d/%m')}",
             f"Chào anh/chị {name},"]
    if market:
        emoji = {'BULL': '🟢', 'BEAR': '🔴'}.get(market.get('market_mode'), '🟡')
        lines.append(f"{emoji} Thị trường: {html.escape(str(market.get('mode_label') or market.get('market_mode')))} · "
                     f"khuyến nghị cổ phiếu {market.get('allocation')}% · danh mục đang {_fmt_pct(s['stock_pct'], sign=False)}")
    lines.append("")
    lines.append("⚠️ <b>Cần chú ý</b>")
    for e in events[:MAX_EVENTS_PER_MSG]:
        lines.append(e['text'])
    if len(events) > MAX_EVENTS_PER_MSG:
        lines.append(f"… và {len(events) - MAX_EVENTS_PER_MSG} thay đổi khác trên dashboard")
    lines.append("")
    lines.append("👉 Mở <a href=\"https://ai-advisor.vn\">VIP Dashboard</a> → 💼 Quản trị đầu tư → "
                 "bấm <b>🆘 Giải cứu danh mục</b> để xem chẩn đoán đầy đủ.")
    lines.append("<i>Công cụ hỗ trợ quyết định, không phải tư vấn đầu tư. Quyết định thuộc về nhà đầu tư.</i>")
    return "\n".join(lines)


# ============================================================
# SEND + PERSIST
# ============================================================

def send_telegram(chat_id, message):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        import requests
        chunks = [message[i:i + 3900] for i in range(0, len(message), 3900)] or ['']
        ok = True
        for c in chunks:
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


def _save_state(session, rows):
    now = datetime.now()
    for r in rows:
        session.execute(text("""
            INSERT INTO rescue_watch_state
                (user_id, ticker, last_price, last_trade_date, peak_price, alert_level,
                 giveback_alerted, top_pct, updated_at)
            VALUES (:user_id, :ticker, :last_price, :last_trade_date, :peak_price, :alert_level,
                    :giveback_alerted, :top_pct, :now)
            ON CONFLICT (user_id, ticker) DO UPDATE SET
                last_price = EXCLUDED.last_price, last_trade_date = EXCLUDED.last_trade_date,
                peak_price = EXCLUDED.peak_price, alert_level = EXCLUDED.alert_level,
                giveback_alerted = EXCLUDED.giveback_alerted, top_pct = EXCLUDED.top_pct,
                updated_at = EXCLUDED.updated_at
        """), {**r, 'now': now})


def _log_events(session, result, mode, sent):
    for e in result['events']:
        session.execute(text("""
            INSERT INTO rescue_watch_log (user_id, ticker, event_type, detail, price, pl_pct, mode, sent, created_at)
            VALUES (:u, :t, :et, :d, :p, :pl, :m, :s, :now)
        """), {'u': result['user'], 't': e['ticker'], 'et': e['type'],
               'd': html.unescape(e['text'].replace('<b>', '').replace('</b>', '')),
               'p': e.get('price'), 'pl': e.get('pl_pct'), 'm': mode, 's': bool(sent), 'now': datetime.now()})


def run_watch(Session, mode='preview', only_user=None, today=None):
    if mode not in ('preview', 'admin', 'live'):
        raise ValueError('mode phải là preview | admin | live')
    if mode == 'admin' and not ADMIN_CHAT_ID:
        raise ValueError('Chưa đặt biến môi trường ADMIN_TELEGRAM_CHAT_ID')

    today = today or date.today()
    session = Session()
    report = {'mode': mode, 'date': today.isoformat(), 'users': []}
    try:
        prices, market = _load_common(session)
        sql = """SELECT email, full_name, telegram_chat_id, is_push_enabled, tier
                 FROM vip_users WHERE is_active = :a"""
        users = [dict(u) for u in _rows(session, sql, a=True)]
        users = [u for u in users if (u.get('tier') or '').lower() == 'vip']
        if only_user:
            users = [u for u in users if u['email'].lower() == only_user.lower()]

        for u in users:
            has_pf = _rows(session, "SELECT 1 AS x FROM portfolios WHERE user_id = :u LIMIT 1", u=u['email'])
            if not has_pf:
                continue
            res = evaluate_user(session, u, prices, market, today=today)
            msg = build_message(res, market, today=today)
            sent, skipped = False, None

            if res['stale_prices']:
                skipped = f'Giá EOD cũ hơn {STALE_DAYS} ngày — không gửi (kiểm tra job cập nhật giá)'
            elif msg and mode == 'admin':
                sent = send_telegram(ADMIN_CHAT_ID, f"📝 <b>BẢN NHÁP cho {html.escape(u['email'])}</b>\n\n{msg}")
            elif msg and mode == 'live':
                if u.get('telegram_chat_id') and u.get('is_push_enabled'):
                    sent = send_telegram(u['telegram_chat_id'], msg)
                else:
                    skipped = 'Khách chưa có Telegram chat_id hoặc chưa bật nhận thông báo'

            if mode != 'preview' and not res['stale_prices']:
                _save_state(session, res['new_state'])
                _log_events(session, res, mode, sent)
                session.commit()

            report['users'].append({
                'user': u['email'], 'baseline': res['baseline'], 'events': len(res['events']),
                'sent': sent, 'skipped': skipped, 'warnings': res['warnings'],
                'summary': res['summary'], 'message': msg,
            })

        # Tóm tắt cho admin (admin/live) — để biết job đã chạy kể cả ngày yên ắng
        if mode in ('admin', 'live') and ADMIN_CHAT_ID:
            n_ev = sum(1 for x in report['users'] if x['events'])
            warn = [f"• {x['user']}: {w}" for x in report['users'] for w in x['warnings']]
            skip = [f"• {x['user']}: {x['skipped']}" for x in report['users'] if x['skipped']]
            base = [x['user'] for x in report['users'] if x['baseline']]
            text_ = (f"🛡️ <b>Rescue Watch {today.strftime('%d/%m')}</b> ({mode})\n"
                     f"Khách được quét: {len(report['users'])} · có sự kiện: {n_ev}")
            if base:
                text_ += f"\nLần đầu (ghi trạng thái gốc, không báo): {html.escape(', '.join(base))}"
            if skip:
                text_ += "\n\n<b>Không gửi:</b>\n" + html.escape("\n".join(skip))
            if warn:
                text_ += "\n\n<b>Cảnh báo dữ liệu:</b>\n" + html.escape("\n".join(warn[:15]))
            send_telegram(ADMIN_CHAT_ID, text_)
        return report
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ============================================================
# ROUTES
# ============================================================

def _require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key', '')
        if not hmac.compare_digest(key, ADMIN_SECRET):
            return jsonify({'error': 'Unauthorized - Admin key required'}), 401
        return f(*args, **kwargs)
    return decorated


def init_rescue_watch_routes(app, engine, Session):
    # Tạo bảng lúc khởi động; nếu DB chưa sẵn sàng (vd Supabase staging bị pause)
    # vẫn đăng ký routes — mỗi lần /run sẽ tự tạo lại bảng (IF NOT EXISTS).
    try:
        ensure_tables(engine)
    except Exception as e:
        print(f"⚠️  Rescue Watch: chưa tạo được bảng lúc khởi động ({e}) — sẽ thử lại khi chạy")

    @app.route('/api/admin/rescue-watch/run', methods=['POST'])
    @_require_admin
    def rescue_watch_run():
        data = request.get_json(silent=True) or {}
        mode = (data.get('mode') or request.args.get('mode') or 'preview').lower()
        only_user = data.get('user') or request.args.get('user')
        try:
            ensure_tables(engine)
            return jsonify({'success': True, **run_watch(Session, mode=mode, only_user=only_user)})
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            logger.exception('[RescueWatch] run error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/rescue-watch/log', methods=['GET'])
    @_require_admin
    def rescue_watch_log():
        """Nhật ký thông báo + giá hiện tại để đánh giá sau 1 tháng: cảnh báo có 'đáng tiền' không."""
        days = int(request.args.get('days', 30))
        session = Session()
        try:
            since = datetime.now() - timedelta(days=days)
            rows = _rows(session, """
                SELECT l.created_at, l.user_id, l.ticker, l.event_type, l.detail, l.price, l.mode, l.sent,
                       e.price AS price_now
                FROM rescue_watch_log l LEFT JOIN eod_prices e ON e.ticker = l.ticker
                WHERE l.created_at >= :s ORDER BY l.created_at DESC
            """, s=since)
            out = []
            for r in rows:
                r = dict(r)
                if r.get('price') and r.get('price_now'):
                    r['change_since_alert_pct'] = round((r['price_now'] / r['price'] - 1) * 100, 2)
                r['created_at'] = str(r['created_at'])
                out.append(r)
            return jsonify({'success': True, 'days': days, 'total': len(out), 'log': out})
        finally:
            session.close()

    print("✅ Rescue Watch routes registered:")
    print("   POST /api/admin/rescue-watch/run   [ADMIN] mode=preview|admin|live")
    print("   GET  /api/admin/rescue-watch/log   [ADMIN]")
