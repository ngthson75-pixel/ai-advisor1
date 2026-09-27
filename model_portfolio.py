"""
AI ADVISOR - LƯỚT SÓNG AI MODEL PORTFOLIO (danh mục mẫu VIP)
=============================================================
File: model_portfolio.py
Version: 1.0 (2026-09-27)

Một danh mục MẪU (mô phỏng, không phải lệnh thật) vốn 1 tỷ VND, tự vận hành theo tín hiệu
VIP của hệ thống — học theo mô hình "danh mục mẫu để làm theo" của iCopy, nhưng mọi quyết định
đều có lý do và tỷ trọng tiền/cổ phiếu đi theo Market Dashboard.

QUY TẮC (cố định, công khai cho khách)
--------------------------------------
Phân bổ
  - Tỷ trọng cổ phiếu mục tiêu = allocation của Market Dashboard (vd 40%) × NAV.
  - Chia ĐỀU thành MP_MAX_POSITIONS ô (mặc định 5) -> mỗi mã = allocation / 5 (vd 8% NAV).
    Ô chưa có mã phù hợp -> giữ tiền mặt (không dồn tiền vào ít mã).
Vào lệnh (1 lần/ngày, lần quét giá đầu tiên của phiên)
  - Ứng viên: tín hiệu MUA đang mở theo bộ lọc VIP (VN30 & điểm ≥ 65, hoặc điểm ≥ 75),
    phát ra trong MP_SIGNAL_MAX_AGE ngày lịch gần nhất (mặc định 5, ~3 phiên).
  - Không mua đuổi: giá hiện tại ≤ giá tín hiệu × (1 + MP_MAX_CHASE%), và > giá cắt lỗ.
  - Ưu tiên điểm VIP cao nhất (điểm + 20 nếu VN30 + thưởng R/R) — giống vip_signal_scanner.
Thoát lệnh
  - Cắt lỗ: giá ≤ SL của tín hiệu (kiểm tra ở MỌI lần quét trong phiên).
  - Đi theo hệ thống: khi tín hiệu MUA gốc giảm position_pct (bán 1 phần) hoặc đóng -> bán theo tỷ lệ đó.
  - Lướt sóng: giữ tối đa MP_MAX_HOLD phiên (mặc định 15) rồi bán.
  - Market Dashboard giảm tỷ trọng -> bán mã yếu nhất cho tới khi về đúng mục tiêu.
  - T+2: không bán trước 2 phiên kể từ ngày mua.
Chi phí mô phỏng: phí mua 0,15%; phí bán 0,15% + thuế 0,1%; khớp theo lô 100 cp.

Giá: đọc bảng eod_prices (được job "Update EOD Prices" cập nhật 6 lần/ngày) -> khách thấy
giá trị danh mục thay đổi trong phiên.

Tích hợp backend_api.py:
    from model_portfolio import init_model_portfolio_routes
    init_model_portfolio_routes(app, engine, Session)

Endpoints:
    GET  /api/vip/model-portfolio            [VIP JWT / admin key]  tổng quan + vị thế + lịch sử + NAV
    POST /api/admin/model-portfolio/run      [ADMIN]  {"dry_run": false}  — gọi sau mỗi lần cập nhật giá
    POST /api/admin/model-portfolio/reset    [ADMIN]  {"capital": 1000000000, "confirm": "RESET"}
"""

import os
import hmac
import html
import logging
from datetime import datetime, date
from functools import wraps

from flask import request, jsonify
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================
ADMIN_SECRET      = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')
JWT_SECRET        = os.getenv('JWT_SECRET', 'ai-advisor-jwt-secret-2026')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID     = os.getenv('ADMIN_TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')
MP_NOTIFY         = os.getenv('MP_NOTIFY', 'admin').lower()     # off | admin (gửi khách: làm ở bước sau)

MP_CAPITAL        = float(os.getenv('MP_CAPITAL', '1000000000'))
MP_MAX_POSITIONS  = int(os.getenv('MP_MAX_POSITIONS', '5'))
MP_MAX_HOLD       = int(os.getenv('MP_MAX_HOLD', '15'))         # số phiên tối đa (lướt sóng)
MP_SIGNAL_MAX_AGE = int(os.getenv('MP_SIGNAL_MAX_AGE', '5'))    # ngày lịch (~3 phiên); tín hiệu cũ hơn -> không mua
MP_MAX_CHASE      = float(os.getenv('MP_MAX_CHASE', '3'))       # % tối đa trên giá tín hiệu
MP_MIN_HOLD       = 2                                            # T+2
MP_TRIM_TOLERANCE = 5.0                                          # % NAV vượt mục tiêu mới bán bớt
MP_DEFAULT_ALLOC  = float(os.getenv('MP_DEFAULT_ALLOC', '50'))  # khi chưa có Market Dashboard
VIP_MIN_CONF      = 65
VIP_HIGH_CONF     = 75
FEE_BUY, FEE_SELL, TAX_SELL = 0.0015, 0.0015, 0.001

VN30 = {'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG', 'MBB', 'MSN', 'MWG', 'PLX', 'POW',
        'SAB', 'SHB', 'SSB', 'SSI', 'STB', 'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'}


# ============================================================
# DB
# ============================================================

def ensure_tables(engine):
    sqlite = engine.dialect.name == 'sqlite'
    pk = 'INTEGER PRIMARY KEY AUTOINCREMENT' if sqlite else 'SERIAL PRIMARY KEY'
    with engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS mp_state (
                id                  INTEGER PRIMARY KEY,
                capital             DOUBLE PRECISION,
                cash                DOUBLE PRECISION,
                started_at          TIMESTAMP,
                last_rebalance_date VARCHAR(20),
                updated_at          TIMESTAMP
            )"""))
        c.execute(text(f"""
            CREATE TABLE IF NOT EXISTS mp_positions (
                id            {pk},
                ticker        VARCHAR(10),
                signal_code   VARCHAR(50),
                qty           INTEGER,
                init_qty      INTEGER,
                entry_price   DOUBLE PRECISION,
                entry_date    VARCHAR(20),
                cost          DOUBLE PRECISION,
                stop_loss     DOUBLE PRECISION,
                take_profit   DOUBLE PRECISION,
                confidence    DOUBLE PRECISION,
                status        VARCHAR(10),
                closed_at     VARCHAR(20)
            )"""))
        c.execute(text(f"""
            CREATE TABLE IF NOT EXISTS mp_trades (
                id          {pk},
                trade_date  VARCHAR(20),
                created_at  TIMESTAMP,
                action      VARCHAR(10),
                ticker      VARCHAR(10),
                qty         INTEGER,
                price       DOUBLE PRECISION,
                value       DOUBLE PRECISION,
                fee         DOUBLE PRECISION,
                pnl         DOUBLE PRECISION,
                pnl_pct     DOUBLE PRECISION,
                reason      TEXT
            )"""))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS mp_nav (
                trade_date   VARCHAR(20) PRIMARY KEY,
                nav          DOUBLE PRECISION,
                cash         DOUBLE PRECISION,
                stock_value  DOUBLE PRECISION,
                allocation   DOUBLE PRECISION,
                market_mode  VARCHAR(20),
                updated_at   TIMESTAMP
            )"""))


def _rows(s, sql, **p):
    return [dict(r) for r in s.execute(text(sql), p).mappings().all()]


def _one(s, sql, **p):
    r = _rows(s, sql, **p)
    return r[0] if r else None


def _prices(s):
    out, latest = {}, ''
    for r in _rows(s, "SELECT ticker, price, trade_date FROM eod_prices"):
        if r['ticker'] and r['price']:
            out[r['ticker'].upper().strip()] = float(r['price'])
            latest = max(latest, str(r['trade_date'] or ''))
    return out, latest


def _market(s):
    try:
        return _one(s, """SELECT market_mode, mode_label, risk_score, allocation, date, vnindex_value
                          FROM market_risk ORDER BY date DESC LIMIT 1""")
    except Exception:
        s.rollback()
        return None


def _state(s):
    return _one(s, "SELECT * FROM mp_state WHERE id = 1")


def _open_positions(s):
    return _rows(s, "SELECT * FROM mp_positions WHERE status = 'open' ORDER BY entry_date, id")


def _sessions_held(s, entry_date, trade_date):
    """Số phiên đã giữ = số ngày giao dịch có trong mp_nav sau ngày mua (+ hôm nay nếu chưa ghi)."""
    n = _one(s, "SELECT COUNT(*) AS n FROM mp_nav WHERE trade_date > :e AND trade_date < :t",
             e=entry_date, t=trade_date)['n']
    return int(n) + (1 if trade_date > entry_date else 0)


def _fmt(v):
    return f"{v:,.0f}".replace(',', '.')


# ============================================================
# CANDIDATES (tín hiệu VIP)
# ============================================================

def _vip_candidates(s, prices, trade_date):
    rows = _rows(s, """
        SELECT ticker, signal_code, entry_price, stop_loss, take_profit, strength, risk_reward, date, status
        FROM signals
        WHERE action = 'BUY' AND (status IS NULL OR status IN ('open', 'partial'))
    """)
    try:
        today = datetime.strptime(trade_date[:10], '%Y-%m-%d').date()
    except Exception:
        today = date.today()
    out = []
    for r in rows:
        t = (r['ticker'] or '').upper().strip()
        conf = float(r['strength'] or 0)
        if not t or not ((t in VN30 and conf >= VIP_MIN_CONF) or conf >= VIP_HIGH_CONF):
            continue
        try:
            age = (today - datetime.strptime(str(r['date'])[:10], '%Y-%m-%d').date()).days
        except Exception:
            continue
        if age < 0 or age > MP_SIGNAL_MAX_AGE:
            continue
        px, entry, sl = prices.get(t), float(r['entry_price'] or 0), float(r['stop_loss'] or 0)
        if not px or entry <= 0 or px <= sl or px > entry * (1 + MP_MAX_CHASE / 100):
            continue
        rr = float(r['risk_reward'] or 0)
        score = conf + (20 if t in VN30 else 0) + (10 if rr >= 2 else 5 if rr >= 1.5 else 0)
        out.append({**r, 'ticker': t, 'price': px, 'score': score, 'confidence': conf})
    out.sort(key=lambda x: -x['score'])
    return out


# ============================================================
# TRADING PRIMITIVES
# ============================================================

def _record_trade(s, trade_date, action, ticker, qty, price, fee, reason, pnl=None, pnl_pct=None):
    s.execute(text("""
        INSERT INTO mp_trades (trade_date, created_at, action, ticker, qty, price, value, fee, pnl, pnl_pct, reason)
        VALUES (:d, :now, :a, :t, :q, :p, :v, :f, :pnl, :pp, :r)
    """), dict(d=trade_date, now=datetime.now(), a=action, t=ticker, q=int(qty), p=price, v=qty * price,
               f=fee, pnl=pnl, pp=pnl_pct, r=reason))


def _sell(s, st, pos, qty, price, trade_date, reason, log):
    qty = min(int(qty // 100 * 100) if qty < pos['qty'] else pos['qty'], pos['qty'])
    if qty <= 0:
        return 0.0
    gross = qty * price
    fee = gross * (FEE_SELL + TAX_SELL)
    cost_part = pos['cost'] * qty / pos['qty']
    pnl = gross - fee - cost_part
    pnl_pct = pnl / cost_part * 100 if cost_part else 0
    remaining = pos['qty'] - qty
    s.execute(text("""UPDATE mp_positions SET qty = :q, cost = :c, status = :st, closed_at = :ca WHERE id = :id"""),
              dict(q=remaining, c=pos['cost'] - cost_part, st='open' if remaining > 0 else 'closed',
                   ca=None if remaining > 0 else trade_date, id=pos['id']))
    st['cash'] += gross - fee
    label = 'BÁN HẾT' if remaining == 0 else 'BÁN 1 PHẦN'
    _record_trade(s, trade_date, 'SELL', pos['ticker'], qty, price, fee, reason, pnl, pnl_pct)
    log.append(f"{label} {pos['ticker']} {qty:,} cp @ {_fmt(price)} — {reason} ({pnl_pct:+.1f}%)")
    pos['qty'], pos['cost'] = remaining, pos['cost'] - cost_part
    return gross - fee


def _buy(s, st, cand, budget, trade_date, log):
    price = cand['price']
    qty = int(budget / (price * (1 + FEE_BUY)) // 100 * 100)
    if qty <= 0 or qty * price * (1 + FEE_BUY) > st['cash']:
        return False
    fee = qty * price * FEE_BUY
    cost = qty * price + fee
    s.execute(text("""
        INSERT INTO mp_positions (ticker, signal_code, qty, init_qty, entry_price, entry_date, cost,
                                  stop_loss, take_profit, confidence, status)
        VALUES (:t, :sc, :q, :q, :p, :d, :c, :sl, :tp, :cf, 'open')
    """), dict(t=cand['ticker'], sc=cand.get('signal_code'), q=qty, p=price, d=trade_date, c=cost,
               sl=float(cand['stop_loss'] or 0), tp=float(cand['take_profit'] or 0), cf=cand['confidence']))
    st['cash'] -= cost
    reason = (f"Tín hiệu VIP {cand['confidence']:.0f}% · cắt lỗ {_fmt(float(cand['stop_loss'] or 0))}"
              f" · mục tiêu {_fmt(float(cand['take_profit'] or 0))}")
    _record_trade(s, trade_date, 'BUY', cand['ticker'], qty, price, fee, reason)
    log.append(f"MUA {cand['ticker']} {qty:,} cp @ {_fmt(price)} — {reason}")
    return True


# ============================================================
# ENGINE
# ============================================================

def reset_portfolio(Session, capital=MP_CAPITAL):
    s = Session()
    try:
        for t in ('mp_positions', 'mp_trades', 'mp_nav', 'mp_state'):
            s.execute(text(f"DELETE FROM {t}"))
        s.execute(text("""INSERT INTO mp_state (id, capital, cash, started_at, last_rebalance_date, updated_at)
                          VALUES (1, :c, :c, :now, NULL, :now)"""), dict(c=capital, now=datetime.now()))
        s.commit()
        return {'capital': capital}
    finally:
        s.close()


def run_model(Session, dry_run=False, force_rebalance=False):
    """
    Gọi sau MỖI lần cập nhật giá:
      - Luôn: định giá lại + kiểm tra cắt lỗ + đi theo tín hiệu bán của hệ thống.
      - Lần đầu tiên trong phiên (hoặc force_rebalance): mua mới / bán theo thời gian / cân lại tỷ trọng.
    """
    s = Session()
    log = []
    try:
        st = _state(s)
        if not st:
            s.execute(text("""INSERT INTO mp_state (id, capital, cash, started_at, last_rebalance_date, updated_at)
                              VALUES (1, :c, :c, :now, NULL, :now)"""), dict(c=MP_CAPITAL, now=datetime.now()))
            st = _state(s)
        st = dict(st)
        prices, trade_date = _prices(s)
        if not trade_date:
            return {'success': False, 'error': 'Chưa có giá trong eod_prices'}
        market = _market(s) or {}
        alloc = float(market.get('allocation') or MP_DEFAULT_ALLOC)
        rebalance = force_rebalance or (st.get('last_rebalance_date') or '') < trade_date

        positions = _open_positions(s)

        # 1) Cắt lỗ — mọi lần quét
        for p in positions:
            px = prices.get(p['ticker'])
            if not px or p['qty'] <= 0:
                continue
            if _sessions_held(s, p['entry_date'], trade_date) < MP_MIN_HOLD:
                continue
            if p['stop_loss'] and px <= p['stop_loss']:
                _sell(s, st, p, p['qty'], px, trade_date, f"Chạm cắt lỗ {_fmt(p['stop_loss'])}", log)

        # 2) Đi theo tín hiệu hệ thống (tín hiệu MUA gốc bị đóng / bán 1 phần) — mọi lần quét
        for p in [p for p in positions if p['qty'] > 0 and p.get('signal_code')]:
            sig = _one(s, "SELECT status, position_pct FROM signals WHERE signal_code = :c", c=p['signal_code'])
            px = prices.get(p['ticker'])
            if not sig or not px or _sessions_held(s, p['entry_date'], trade_date) < MP_MIN_HOLD:
                continue
            target_frac = 0.0 if sig['status'] == 'closed' else float(sig['position_pct'] or 100) / 100
            target_qty = int(p['init_qty'] * target_frac // 100 * 100)
            if p['qty'] > target_qty:
                why = 'Hệ thống đóng tín hiệu' if target_frac == 0 else f"Hệ thống bán bớt (còn {target_frac * 100:.0f}%)"
                _sell(s, st, p, p['qty'] - target_qty, px, trade_date, why, log)

        if rebalance:
            positions = [p for p in _open_positions(s) if p['qty'] > 0]

            # 3) Lướt sóng: quá số phiên tối đa
            for p in positions:
                px = prices.get(p['ticker'])
                if px and _sessions_held(s, p['entry_date'], trade_date) >= MP_MAX_HOLD:
                    _sell(s, st, p, p['qty'], px, trade_date, f"Hết {MP_MAX_HOLD} phiên nắm giữ (lướt sóng)", log)
            positions = [p for p in positions if p['qty'] > 0]

            # 4) Cân tỷ trọng theo Market Dashboard: bán mã yếu nhất nếu vượt mục tiêu
            def stock_value():
                return sum(p['qty'] * prices.get(p['ticker'], p['entry_price']) for p in positions if p['qty'] > 0)
            nav = st['cash'] + stock_value()
            target = nav * alloc / 100
            for p in sorted(positions, key=lambda p: prices.get(p['ticker'], p['entry_price']) / p['entry_price']):
                if stock_value() <= target + nav * MP_TRIM_TOLERANCE / 100:
                    break
                if _sessions_held(s, p['entry_date'], trade_date) < MP_MIN_HOLD:
                    continue
                _sell(s, st, p, p['qty'], prices.get(p['ticker'], p['entry_price']), trade_date,
                      f"Market Dashboard {market.get('market_mode', '')} khuyến nghị {alloc:.0f}% cổ phiếu — giảm tỷ trọng",
                      log)
            positions = [p for p in positions if p['qty'] > 0]

            # 5) Mua mới vào ô trống — mỗi mã = alloc / MAX_POSITIONS % NAV
            # Không mua lại mã vừa bán trong cùng phiên (tránh mua đi bán lại vô lý)
            sold_today = {r['ticker'] for r in _rows(
                s, "SELECT DISTINCT ticker FROM mp_trades WHERE action = 'SELL' AND trade_date = :d", d=trade_date)}
            held = {p['ticker'] for p in positions} | sold_today
            nav = st['cash'] + stock_value()
            slot = nav * alloc / 100 / MP_MAX_POSITIONS
            free_slots = int(max(0, min(MP_MAX_POSITIONS - len(positions),
                                        (nav * alloc / 100 - stock_value()) // (slot * 0.9) if slot else 0)))
            for c in [c for c in _vip_candidates(s, prices, trade_date) if c['ticker'] not in held][:free_slots]:
                _buy(s, st, c, min(slot, st['cash']), trade_date, log)

            st['last_rebalance_date'] = trade_date

        # 6) Định giá + lưu NAV của phiên
        positions = _open_positions(s)
        stock_val = sum(p['qty'] * prices.get(p['ticker'], p['entry_price']) for p in positions)
        nav = st['cash'] + stock_val

        if dry_run:
            s.rollback()
        else:
            s.execute(text("""UPDATE mp_state SET cash = :c, last_rebalance_date = :d, updated_at = :now WHERE id = 1"""),
                      dict(c=st['cash'], d=st.get('last_rebalance_date'), now=datetime.now()))
            s.execute(text("""
                INSERT INTO mp_nav (trade_date, nav, cash, stock_value, allocation, market_mode, updated_at)
                VALUES (:d, :n, :c, :sv, :a, :m, :now)
                ON CONFLICT (trade_date) DO UPDATE SET nav = EXCLUDED.nav, cash = EXCLUDED.cash,
                    stock_value = EXCLUDED.stock_value, allocation = EXCLUDED.allocation,
                    market_mode = EXCLUDED.market_mode, updated_at = EXCLUDED.updated_at
            """), dict(d=trade_date, n=nav, c=st['cash'], sv=stock_val, a=alloc, m=market.get('market_mode'),
                       now=datetime.now()))
            s.commit()
            if log:
                _notify(log, nav, st['capital'], trade_date)

        return {'success': True, 'dry_run': dry_run, 'trade_date': trade_date, 'rebalanced': rebalance,
                'nav': round(nav), 'cash': round(st['cash']), 'stock_value': round(stock_val),
                'allocation': alloc, 'actions': log}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def _notify(log, nav, capital, trade_date):
    """Báo giao dịch của danh mục mẫu qua Telegram cho admin (MP_NOTIFY=off để tắt)."""
    if MP_NOTIFY == 'off' or not TELEGRAM_BOT_TOKEN:
        return
    msg = (f"📈 <b>Lướt sóng AI · Danh mục mẫu</b> — {html.escape(trade_date)}\n"
           + "\n".join("• " + html.escape(x) for x in log)
           + f"\n\nGiá trị danh mục: <b>{_fmt(nav)}</b> đ ({(nav / capital - 1) * 100:+.2f}% từ đầu)"
           + "\n<i>Danh mục mô phỏng để tham khảo, không phải khuyến nghị đầu tư.</i>")
    try:
        import requests
        for chat in ([ADMIN_CHAT_ID] if ADMIN_CHAT_ID else []):
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                          json={'chat_id': chat, 'text': msg, 'parse_mode': 'HTML',
                                'disable_web_page_preview': True}, timeout=15)
    except Exception as e:
        logger.error(f'[ModelPortfolio] notify error: {e}')


def get_overview(Session):
    s = Session()
    try:
        st = _state(s)
        if not st:
            return {'initialized': False}
        prices, trade_date = _prices(s)
        market = _market(s) or {}
        pos = []
        stock_val = 0.0
        for p in _open_positions(s):
            px = prices.get(p['ticker'], p['entry_price'])
            val = p['qty'] * px
            stock_val += val
            pos.append({'ticker': p['ticker'], 'qty': p['qty'], 'entry_price': p['entry_price'],
                        'entry_date': p['entry_date'], 'price': px, 'value': val,
                        'pl': val - p['cost'], 'pl_pct': (val / p['cost'] - 1) * 100 if p['cost'] else 0,
                        'stop_loss': p['stop_loss'], 'take_profit': p['take_profit'],
                        'sessions': _sessions_held(s, p['entry_date'], trade_date)})
        nav = st['cash'] + stock_val
        for p in pos:
            p['weight'] = p['value'] / nav * 100 if nav else 0

        navs = _rows(s, "SELECT trade_date, nav, allocation, market_mode FROM mp_nav ORDER BY trade_date")
        prev_nav = navs[-2]['nav'] if len(navs) >= 2 and navs[-1]['trade_date'] == trade_date else \
            (navs[-1]['nav'] if navs and navs[-1]['trade_date'] != trade_date else st['capital'])
        # VN-Index cùng kỳ (từ market_risk) để so sánh
        vni = {}
        try:
            for r in _rows(s, "SELECT date, vnindex_value FROM market_risk WHERE vnindex_value IS NOT NULL"):
                vni[str(r['date'])[:10]] = float(r['vnindex_value'])
        except Exception:
            s.rollback()
        series = [{'date': n['trade_date'], 'nav': round(n['nav']), 'vnindex': vni.get(str(n['trade_date'])[:10])}
                  for n in navs]
        vn_first = next((x['vnindex'] for x in series if x['vnindex']), None)
        vn_last = next((x['vnindex'] for x in reversed(series) if x['vnindex']), None)

        trades = _rows(s, """SELECT trade_date, action, ticker, qty, price, value, pnl, pnl_pct, reason
                             FROM mp_trades ORDER BY id DESC LIMIT 50""")
        closed = _rows(s, "SELECT pnl FROM mp_trades WHERE action = 'SELL' AND pnl IS NOT NULL")
        wins = sum(1 for c in closed if c['pnl'] > 0)
        alloc = float(market.get('allocation') or MP_DEFAULT_ALLOC)
        return {
            'initialized': True,
            'as_of': trade_date,
            'started_at': str(st['started_at'])[:10],
            'capital': st['capital'],
            'nav': round(nav), 'cash': round(st['cash']), 'stock_value': round(stock_val),
            'total_return_pct': round((nav / st['capital'] - 1) * 100, 2),
            'today_return_pct': round((nav / prev_nav - 1) * 100, 2) if prev_nav else 0,
            'vnindex_return_pct': round((vn_last / vn_first - 1) * 100, 2) if vn_first and vn_last else None,
            'stock_pct': round(stock_val / nav * 100, 1) if nav else 0,
            'target_stock_pct': alloc,
            'market_mode': market.get('market_mode'), 'mode_label': market.get('mode_label'),
            'positions': sorted(pos, key=lambda p: -p['value']),
            'trades': trades,
            'nav_series': series[-120:],
            'stats': {'closed_trades': len(closed), 'win_rate_pct': round(wins / len(closed) * 100, 1) if closed else None},
            'rules': {
                'max_positions': MP_MAX_POSITIONS, 'slot_pct': round(alloc / MP_MAX_POSITIONS, 1),
                'max_hold_sessions': MP_MAX_HOLD, 'max_chase_pct': MP_MAX_CHASE,
                'fees': 'Phí mua 0,15%; phí bán 0,15% + thuế 0,1%',
            },
        }
    finally:
        s.close()


# ============================================================
# ROUTES
# ============================================================

def _is_admin():
    return hmac.compare_digest(request.headers.get('X-Admin-Key', ''), ADMIN_SECRET)


def _require_admin(f):
    @wraps(f)
    def d(*a, **k):
        if not _is_admin():
            return jsonify({'error': 'Unauthorized - Admin key required'}), 401
        return f(*a, **k)
    return d


def _require_vip(f):
    @wraps(f)
    def d(*a, **k):
        if _is_admin():
            return f(*a, **k)
        auth = request.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        if token:
            try:
                import jwt
                jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                return f(*a, **k)
            except Exception:
                pass
        if os.getenv('ENVIRONMENT', 'production') == 'staging':
            return f(*a, **k)
        return jsonify({'error': 'VIP access required'}), 403
    return d


def init_model_portfolio_routes(app, engine, Session):
    try:
        ensure_tables(engine)
    except Exception as e:
        print(f"⚠️  Model Portfolio: chưa tạo được bảng ({e}) — sẽ thử lại khi chạy")

    @app.route('/api/vip/model-portfolio', methods=['GET'])
    @_require_vip
    def mp_overview():
        try:
            ensure_tables(engine)
            return jsonify({'success': True, **get_overview(Session)})
        except Exception as e:
            logger.exception('[ModelPortfolio] overview error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/model-portfolio/run', methods=['POST'])
    @_require_admin
    def mp_run():
        data = request.get_json(silent=True) or {}
        try:
            ensure_tables(engine)
            return jsonify(run_model(Session, dry_run=bool(data.get('dry_run')),
                                     force_rebalance=bool(data.get('force_rebalance'))))
        except Exception as e:
            logger.exception('[ModelPortfolio] run error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/model-portfolio/reset', methods=['POST'])
    @_require_admin
    def mp_reset():
        data = request.get_json(silent=True) or {}
        if data.get('confirm') != 'RESET':
            return jsonify({'success': False, 'error': 'Gửi {"confirm": "RESET"} để xác nhận xóa toàn bộ lịch sử'}), 400
        ensure_tables(engine)
        return jsonify({'success': True, **reset_portfolio(Session, float(data.get('capital') or MP_CAPITAL))})

    print("✅ Model Portfolio routes registered:")
    print("   GET  /api/vip/model-portfolio          [VIP]")
    print("   POST /api/admin/model-portfolio/run    [ADMIN]")
    print("   POST /api/admin/model-portfolio/reset  [ADMIN]")
