"""
AI ADVISOR - LƯỚT SÓNG AI MODEL PORTFOLIO (danh mục mẫu VIP)
=============================================================
File: model_portfolio.py
Version: 1.4 (2026-10-06) — đếm số phiên nắm giữ theo lịch giao dịch (không phụ thuộc bảng NAV)
Version: 1.3 (2026-09-27) — nhãn [Thủ công] chỉ hiện cho admin, API khách chỉ trả lý do
Version: 1.2 (2026-09-27) — can thiệp thủ công, bật/tắt tự động, hủy giao dịch, loại mã (quản lý qua signal_reviewer.py mục 23)

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
    POST /api/admin/model-portfolio/trade    [ADMIN]  mua/bán THỦ CÔNG (nhãn [Thủ công] chỉ admin thấy)
    POST /api/admin/model-portfolio/position [ADMIN]  sửa cắt lỗ / mục tiêu của 1 mã
    POST /api/admin/model-portfolio/auto     [ADMIN]  {"enabled": false} tạm dừng tự động (chỉ định giá)
"""

import os
import hmac
import html
import logging
import json
from datetime import datetime, date, timedelta
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
    # v1.1: cờ bật/tắt chế độ tự động (admin can thiệp thủ công)
    try:
        with engine.begin() as c:
            if sqlite:
                cols = [r[1] for r in c.execute(text("PRAGMA table_info(mp_state)")).fetchall()]
                if 'auto_enabled' not in cols:
                    c.execute(text("ALTER TABLE mp_state ADD COLUMN auto_enabled BOOLEAN DEFAULT 1"))
            else:
                c.execute(text("ALTER TABLE mp_state ADD COLUMN IF NOT EXISTS auto_enabled BOOLEAN DEFAULT TRUE"))
    except Exception as e:
        logger.warning(f'[ModelPortfolio] auto_enabled column: {e}')
    with engine.begin() as c:
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
                reason      TEXT,
                position_id INTEGER,
                cost_basis  DOUBLE PRECISION
            )"""))
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS mp_exclude (
                ticker      VARCHAR(10) PRIMARY KEY,
                reason      TEXT,
                created_at  TIMESTAMP
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

    # v1.2: liên kết giao dịch <-> vị thế để HỦY được giao dịch; bảng mã bị loại khỏi tự mua
    for col, typ in (('position_id', 'INTEGER'), ('cost_basis', 'DOUBLE PRECISION')):
        try:
            with engine.begin() as c:
                if sqlite:
                    cols = [r[1] for r in c.execute(text("PRAGMA table_info(mp_trades)")).fetchall()]
                    if cols and col not in cols:
                        c.execute(text(f"ALTER TABLE mp_trades ADD COLUMN {col} {typ}"))
                else:
                    c.execute(text(f"ALTER TABLE mp_trades ADD COLUMN IF NOT EXISTS {col} {typ}"))
        except Exception as e:
            logger.warning(f'[ModelPortfolio] mp_trades.{col}: {e}')

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


_HOLIDAYS = None


def _holidays():
    """Ngày nghỉ lễ HOSE từ vietnam_holidays.json (cùng thư mục / thư mục chạy); thiếu file -> danh sách 2026 dựng sẵn."""
    global _HOLIDAYS
    if _HOLIDAYS is None:
        days = {'2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20',
                '2026-04-30', '2026-05-01', '2026-09-02'}
        for path in (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vietnam_holidays.json'), 'vietnam_holidays.json'):
            try:
                with open(path, encoding='utf-8') as f:
                    for lst in json.load(f).get('holidays', {}).values():
                        days.update(str(d)[:10] for d in lst)
                break
            except Exception:
                continue
        _HOLIDAYS = days
    return _HOLIDAYS


def _sessions_held(s, entry_date, trade_date):
    """
    Số phiên đã giữ = số NGÀY GIAO DỊCH (thứ 2–6, trừ lễ) sau ngày mua, tính đến hết trade_date.
    v1.4: trước đây đếm theo bảng mp_nav -> ngày job lỗi không ghi NAV bị bỏ sót (HDB giữ 7 phiên chỉ hiện 4),
    làm lệch quy tắc T+2 và bán sau 15 phiên.
    """
    try:
        d0 = datetime.strptime(str(entry_date)[:10], '%Y-%m-%d').date()
        d1 = datetime.strptime(str(trade_date)[:10], '%Y-%m-%d').date()
    except Exception:
        return 0
    hol, n, d = _holidays(), 0, d0 + timedelta(days=1)
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in hol:
            n += 1
        d += timedelta(days=1)
    return n


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
    try:
        excluded = {r['ticker'] for r in _rows(s, "SELECT ticker FROM mp_exclude")}
    except Exception:
        s.rollback()
        excluded = set()
    out = []
    for r in rows:
        t = (r['ticker'] or '').upper().strip()
        if t in excluded:
            continue
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

def _record_trade(s, trade_date, action, ticker, qty, price, fee, reason, pnl=None, pnl_pct=None,
                  position_id=None, cost_basis=None):
    s.execute(text("""
        INSERT INTO mp_trades (trade_date, created_at, action, ticker, qty, price, value, fee, pnl, pnl_pct, reason,
                               position_id, cost_basis)
        VALUES (:d, :now, :a, :t, :q, :p, :v, :f, :pnl, :pp, :r, :pid, :cb)
    """), dict(d=trade_date, now=datetime.now(), a=action, t=ticker, q=int(qty), p=price, v=qty * price,
               f=fee, pnl=pnl, pp=pnl_pct, r=reason, pid=position_id, cb=cost_basis))


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
    _record_trade(s, trade_date, 'SELL', pos['ticker'], qty, price, fee, reason, pnl, pnl_pct,
                  position_id=pos['id'], cost_basis=cost_part)
    log.append(f"{label} {pos['ticker']} {qty:,} cp @ {_fmt(price)} — {reason} ({pnl_pct:+.1f}%)")
    pos['qty'], pos['cost'] = remaining, pos['cost'] - cost_part
    return gross - fee


def _buy(s, st, cand, budget, trade_date, log, reason=None):
    price = cand['price']
    qty = int(budget / (price * (1 + FEE_BUY)) // 100 * 100)
    if qty <= 0 or qty * price * (1 + FEE_BUY) > st['cash']:
        return False
    fee = qty * price * FEE_BUY
    cost = qty * price + fee
    pid = s.execute(text("""
        INSERT INTO mp_positions (ticker, signal_code, qty, init_qty, entry_price, entry_date, cost,
                                  stop_loss, take_profit, confidence, status)
        VALUES (:t, :sc, :q, :q, :p, :d, :c, :sl, :tp, :cf, 'open')
        RETURNING id
    """), dict(t=cand['ticker'], sc=cand.get('signal_code'), q=qty, p=price, d=trade_date, c=cost,
               sl=float(cand['stop_loss'] or 0), tp=float(cand['take_profit'] or 0), cf=cand['confidence'])).scalar()
    st['cash'] -= cost
    reason = reason or (f"Tín hiệu VIP {cand['confidence']:.0f}% · cắt lỗ {_fmt(float(cand['stop_loss'] or 0))}"
                        f" · mục tiêu {_fmt(float(cand['take_profit'] or 0))}")
    _record_trade(s, trade_date, 'BUY', cand['ticker'], qty, price, fee, reason, position_id=pid, cost_basis=cost)
    log.append(f"MUA {cand['ticker']} {qty:,} cp @ {_fmt(price)} — {reason}")
    return True


# ============================================================
# ENGINE
# ============================================================

def _save_nav(s, st, prices, trade_date, market, alloc, commit=True):
    positions = _open_positions(s)
    stock_val = sum(p['qty'] * prices.get(p['ticker'], p['entry_price']) for p in positions)
    nav = st['cash'] + stock_val
    if commit:
        s.execute(text("""UPDATE mp_state SET cash = :c, last_rebalance_date = :d, updated_at = :now WHERE id = 1"""),
                  dict(c=st['cash'], d=st.get('last_rebalance_date'), now=datetime.now()))
        s.execute(text("""
            INSERT INTO mp_nav (trade_date, nav, cash, stock_value, allocation, market_mode, updated_at)
            VALUES (:d, :n, :c, :sv, :a, :m, :now)
            ON CONFLICT (trade_date) DO UPDATE SET nav = EXCLUDED.nav, cash = EXCLUDED.cash,
                stock_value = EXCLUDED.stock_value, allocation = EXCLUDED.allocation,
                market_mode = EXCLUDED.market_mode, updated_at = EXCLUDED.updated_at
        """), dict(d=trade_date, n=nav, c=st['cash'], sv=stock_val, a=alloc, m=(market or {}).get('market_mode'),
                   now=datetime.now()))
        s.commit()
    return nav, stock_val


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
        auto = st.get('auto_enabled')
        auto = True if auto is None else bool(auto)
        rebalance = auto and (force_rebalance or (st.get('last_rebalance_date') or '') < trade_date)

        positions = _open_positions(s) if auto else []   # tự động TẮT -> không giao dịch, chỉ định giá

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
        nav, stock_val = _save_nav(s, st, prices, trade_date, market, alloc, commit=not dry_run)
        if dry_run:
            s.rollback()
        elif log:
            _notify(log, nav, st['capital'], trade_date)

        return {'success': True, 'dry_run': dry_run, 'trade_date': trade_date, 'rebalanced': rebalance, 'auto_enabled': auto,
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


# ============================================================
# CAN THIỆP THỦ CÔNG (admin)
# ============================================================

def _load_ctx(s):
    st = _state(s)
    if not st:
        raise ValueError('Danh mục mẫu chưa khởi tạo — gọi /run hoặc /reset trước')
    prices, trade_date = _prices(s)
    market = _market(s) or {}
    return dict(st), prices, trade_date, market, float(market.get('allocation') or MP_DEFAULT_ALLOC)


def manual_trade(Session, action, ticker, reason, qty=None, pct=None, amount=None, price=None,
                 stop_loss=None, take_profit=None):
    """
    Lệnh thủ công của admin. Lưu với nhãn nội bộ [Thủ công] (chỉ admin thấy); khách chỉ thấy lý do.
      BUY : amount (VND) hoặc qty; giá mặc định = giá quét gần nhất; nên kèm stop_loss / take_profit.
      SELL: qty hoặc pct (% vị thế, mặc định 100); bán các lô cũ trước (FIFO); vẫn tôn trọng T+2.
    """
    action = (action or '').upper()
    ticker = (ticker or '').upper().strip()
    if action not in ('BUY', 'SELL') or not ticker:
        raise ValueError('action phải là BUY hoặc SELL và phải có ticker')
    if not reason or len(reason.strip()) < 5:
        raise ValueError('Cần ghi lý do (khách sẽ thấy lý do này trong lịch sử giao dịch)')
    s = Session()
    log = []
    try:
        st, prices, trade_date, market, alloc = _load_ctx(s)
        px = float(price) if price else prices.get(ticker)
        if not px:
            raise ValueError(f'Không có giá cho {ticker} — truyền price hoặc thêm mã vào danh sách cập nhật giá')
        label = f"{MANUAL_TAG} {reason.strip()}"

        if action == 'BUY':
            nav = st['cash'] + sum(p['qty'] * prices.get(p['ticker'], p['entry_price']) for p in _open_positions(s))
            budget = float(amount) if amount else (float(qty) * px * (1 + FEE_BUY) if qty else nav * alloc / 100 / MP_MAX_POSITIONS)
            if budget > st['cash']:
                raise ValueError(f'Không đủ tiền: cần {_fmt(budget)}, còn {_fmt(st["cash"])}')
            cand = {'ticker': ticker, 'price': px, 'stop_loss': stop_loss or 0, 'take_profit': take_profit or 0,
                    'confidence': None, 'signal_code': None}
            extra = []
            if stop_loss: extra.append(f"cắt lỗ {_fmt(float(stop_loss))}")
            if take_profit: extra.append(f"mục tiêu {_fmt(float(take_profit))}")
            if not _buy(s, st, cand, budget, trade_date, log, reason=label + (' · ' + ' · '.join(extra) if extra else '')):
                raise ValueError('Số tiền quá nhỏ để mua 1 lô 100 cp')
        else:
            rows = [p for p in _open_positions(s) if p['ticker'] == ticker and p['qty'] > 0]
            if not rows:
                raise ValueError(f'Danh mục mẫu không có {ticker}')
            sellable = [p for p in rows if _sessions_held(s, p['entry_date'], trade_date) >= MP_MIN_HOLD]
            if not sellable:
                raise ValueError(f'{ticker} chưa đủ T+2, chưa bán được')
            total = sum(p['qty'] for p in sellable)
            want = int(qty) if qty else int(total * float(pct or 100) / 100)
            want = total if want >= total else want // 100 * 100
            if want <= 0:
                raise ValueError('Khối lượng bán phải ≥ 100 cp')
            for p in sellable:
                if want <= 0:
                    break
                q = min(p['qty'], want)
                _sell(s, st, p, q, px, trade_date, label, log)
                want -= q

        _save_nav(s, st, prices, trade_date, market, alloc)
        _notify(log, st['cash'] + sum(p['qty'] * prices.get(p['ticker'], p['entry_price']) for p in _open_positions(s)),
                st['capital'], trade_date)
        return {'success': True, 'trade_date': trade_date, 'actions': log}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def update_position(Session, ticker, stop_loss=None, take_profit=None):
    """Sửa cắt lỗ / mục tiêu cho mọi lô đang mở của 1 mã."""
    ticker = (ticker or '').upper().strip()
    s = Session()
    try:
        rows = [p for p in _open_positions(s) if p['ticker'] == ticker]
        if not rows:
            raise ValueError(f'Danh mục mẫu không có {ticker}')
        sets, params = [], {'t': ticker}
        if stop_loss is not None:
            sets.append('stop_loss = :sl'); params['sl'] = float(stop_loss)
        if take_profit is not None:
            sets.append('take_profit = :tp'); params['tp'] = float(take_profit)
        if not sets:
            raise ValueError('Truyền stop_loss và/hoặc take_profit')
        s.execute(text(f"UPDATE mp_positions SET {', '.join(sets)} WHERE ticker = :t AND status = 'open'"), params)
        s.commit()
        return {'success': True, 'ticker': ticker, 'stop_loss': stop_loss, 'take_profit': take_profit}
    finally:
        s.close()


def set_auto(Session, enabled):
    s = Session()
    try:
        if not _state(s):
            raise ValueError('Danh mục mẫu chưa khởi tạo')
        s.execute(text("UPDATE mp_state SET auto_enabled = :e, updated_at = :now WHERE id = 1"),
                  dict(e=bool(enabled), now=datetime.now()))
        s.commit()
        return {'success': True, 'auto_enabled': bool(enabled)}
    finally:
        s.close()


def void_trade(Session, trade_id):
    """
    HỦY 1 giao dịch như chưa từng xảy ra (hoàn tiền / hoàn cổ phiếu, xóa khỏi lịch sử).
    Chỉ hủy được giao dịch MỚI NHẤT của vị thế đó (hủy dần từ mới đến cũ) để số liệu luôn khớp.
    """
    s = Session()
    try:
        st, prices, trade_date, market, alloc = _load_ctx(s)
        t = _one(s, "SELECT * FROM mp_trades WHERE id = :i", i=int(trade_id))
        if not t:
            raise ValueError(f'Không có giao dịch #{trade_id}')
        if not t.get('position_id'):
            raise ValueError('Giao dịch cũ (trước v1.2) không có liên kết vị thế — không hủy tự động được')
        later = _one(s, "SELECT id FROM mp_trades WHERE position_id = :p AND id > :i ORDER BY id LIMIT 1",
                     p=t['position_id'], i=t['id'])
        if later:
            raise ValueError(f"Phải hủy giao dịch mới hơn của {t['ticker']} trước (#{later['id']})")
        pos = _one(s, "SELECT * FROM mp_positions WHERE id = :p", p=t['position_id'])
        if not pos:
            raise ValueError('Không tìm thấy vị thế gốc')
        if t['action'] == 'BUY':
            if int(pos['qty']) != int(pos['init_qty']):
                raise ValueError('Vị thế đã bán một phần — hủy các lệnh bán trước')
            s.execute(text("DELETE FROM mp_positions WHERE id = :p"), dict(p=pos['id']))
            st['cash'] += float(t['cost_basis'] or (t['value'] + t['fee']))
            # tránh lần quét sau tự mua lại đúng mã vừa hủy -> tự đưa vào danh sách loại (admin mở lại khi muốn)
            s.execute(text("DELETE FROM mp_exclude WHERE ticker = :t"), dict(t=t['ticker']))
            s.execute(text("INSERT INTO mp_exclude (ticker, reason, created_at) VALUES (:t, :r, :now)"),
                      dict(t=t['ticker'], r=f"Admin hủy lệnh mua #{t['id']}", now=datetime.now()))
            note = f"{t['ticker']} đã được đưa vào danh sách LOẠI khỏi tự mua (mở lại trong mục loại mã nếu muốn)"
        else:
            s.execute(text("""UPDATE mp_positions SET qty = qty + :q, cost = cost + :c, status = 'open', closed_at = NULL
                              WHERE id = :p"""), dict(q=int(t['qty']), c=float(t['cost_basis'] or 0), p=pos['id']))
            st['cash'] -= float(t['value']) - float(t['fee'])
            note = (f"Vị thế {t['ticker']} đã được khôi phục. Nếu giá vẫn dưới cắt lỗ {_fmt(float(pos['stop_loss'] or 0))}, "
                    "lần quét sau sẽ tự bán lại — hãy sửa cắt lỗ hoặc tạm dừng tự động nếu không muốn")
        s.execute(text("DELETE FROM mp_trades WHERE id = :i"), dict(i=t['id']))
        msg = f"HỦY giao dịch #{t['id']}: {t['action']} {t['ticker']} {int(t['qty']):,} cp @ {_fmt(t['price'])} ({t['trade_date']})"
        nav, _ = _save_nav(s, st, prices, trade_date, market, alloc)
        _notify([msg], nav, st['capital'], trade_date)
        return {'success': True, 'voided': msg, 'note': note, 'nav': round(nav), 'cash': round(st['cash'])}
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def set_exclude(Session, ticker, exclude=True, reason=''):
    """Loại (hoặc cho phép lại) 1 mã khỏi danh sách TỰ ĐỘNG mua. Không ảnh hưởng vị thế đang giữ."""
    ticker = (ticker or '').upper().strip()
    if not ticker:
        raise ValueError('Thiếu mã')
    s = Session()
    try:
        s.execute(text("DELETE FROM mp_exclude WHERE ticker = :t"), dict(t=ticker))
        if exclude:
            s.execute(text("INSERT INTO mp_exclude (ticker, reason, created_at) VALUES (:t, :r, :now)"),
                      dict(t=ticker, r=reason or '', now=datetime.now()))
        s.commit()
        return {'success': True, 'ticker': ticker, 'excluded': bool(exclude)}
    finally:
        s.close()


def admin_status(Session):
    """Toàn bộ chi tiết cho admin: vị thế (có id), giao dịch (có id), mã bị loại, ứng viên hiện tại."""
    s = Session()
    try:
        st = _state(s)
        if not st:
            return {'success': True, 'initialized': False}
        prices, trade_date = _prices(s)
        pos = _open_positions(s)
        for p in pos:
            p['price'] = prices.get(p['ticker'])
            p['pl_pct'] = round((p['qty'] * p['price'] / p['cost'] - 1) * 100, 2) if p['price'] and p['cost'] else None
            p['sessions'] = _sessions_held(s, p['entry_date'], trade_date)
        trades = _rows(s, """SELECT id, trade_date, action, ticker, qty, price, pnl_pct, reason, position_id
                             FROM mp_trades ORDER BY id DESC LIMIT 40""")
        cands = [{'ticker': c['ticker'], 'score': c['score'], 'confidence': c['confidence'], 'price': c['price'],
                  'entry_price': c['entry_price'], 'date': str(c['date'])[:10],
                  'held': c['ticker'] in {p['ticker'] for p in pos}}
                 for c in _vip_candidates(s, prices, trade_date)][:15]
        return {'success': True, 'initialized': True, 'as_of': trade_date,
                'auto_enabled': True if st.get('auto_enabled') is None else bool(st.get('auto_enabled')),
                'cash': round(st['cash']), 'positions': pos, 'trades': trades,
                'excluded': _rows(s, "SELECT ticker, reason, created_at FROM mp_exclude ORDER BY ticker"),
                'candidates': cands}
    finally:
        s.close()


MANUAL_TAG = '[Thủ công]'


def _public_reason(reason):
    r = (reason or '').strip()
    return r[len(MANUAL_TAG):].strip() if r.startswith(MANUAL_TAG) else r


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
        # v1.3: nhãn [Thủ công] chỉ dùng nội bộ (admin / signal_reviewer) — không trả ra API cho khách
        for t in trades:
            t['reason'] = _public_reason(t.get('reason'))
        closed = _rows(s, "SELECT pnl FROM mp_trades WHERE action = 'SELL' AND pnl IS NOT NULL")
        wins = sum(1 for c in closed if c['pnl'] > 0)
        alloc = float(market.get('allocation') or MP_DEFAULT_ALLOC)
        return {
            'initialized': True,
            'auto_enabled': True if st.get('auto_enabled') is None else bool(st.get('auto_enabled')),
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

    def _admin_call(fn):
        data = request.get_json(silent=True) or {}
        try:
            ensure_tables(engine)
            return jsonify(fn(data))
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            logger.exception('[ModelPortfolio] admin error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/model-portfolio/trade', methods=['POST'])
    @_require_admin
    def mp_trade():
        return _admin_call(lambda d: manual_trade(
            Session, d.get('action'), d.get('ticker'), d.get('reason'), qty=d.get('qty'), pct=d.get('pct'),
            amount=d.get('amount'), price=d.get('price'), stop_loss=d.get('stop_loss'), take_profit=d.get('take_profit')))

    @app.route('/api/admin/model-portfolio/position', methods=['POST'])
    @_require_admin
    def mp_position():
        return _admin_call(lambda d: update_position(Session, d.get('ticker'), d.get('stop_loss'), d.get('take_profit')))

    @app.route('/api/admin/model-portfolio/void', methods=['POST'])
    @_require_admin
    def mp_void():
        return _admin_call(lambda d: void_trade(Session, d.get('trade_id')))

    @app.route('/api/admin/model-portfolio/exclude', methods=['POST'])
    @_require_admin
    def mp_exclude():
        return _admin_call(lambda d: set_exclude(Session, d.get('ticker'), d.get('exclude', True), d.get('reason', '')))

    @app.route('/api/admin/model-portfolio/admin', methods=['GET'])
    @_require_admin
    def mp_admin_status():
        try:
            ensure_tables(engine)
            return jsonify(admin_status(Session))
        except Exception as e:
            logger.exception('[ModelPortfolio] admin status error')
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/model-portfolio/auto', methods=['POST'])
    @_require_admin
    def mp_auto():
        return _admin_call(lambda d: set_auto(Session, d.get('enabled', True)))

    print("✅ Model Portfolio routes registered:")
    print("   GET  /api/vip/model-portfolio          [VIP]")
    print("   POST /api/admin/model-portfolio/run    [ADMIN]")
    print("   POST /api/admin/model-portfolio/reset  [ADMIN]")
    print("   POST /api/admin/model-portfolio/trade  [ADMIN] mua/bán thủ công")
    print("   POST /api/admin/model-portfolio/position [ADMIN] sửa cắt lỗ/mục tiêu")
    print("   POST /api/admin/model-portfolio/auto   [ADMIN] bật/tắt tự động")
    print("   POST /api/admin/model-portfolio/void   [ADMIN] hủy 1 giao dịch")
    print("   POST /api/admin/model-portfolio/exclude [ADMIN] loại/cho phép mã khỏi tự mua")
    print("   GET  /api/admin/model-portfolio/admin  [ADMIN] chi tiết cho signal_reviewer")
