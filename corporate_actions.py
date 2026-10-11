"""
AI ADVISOR - CORPORATE ACTIONS (điều chỉnh giá theo quyền: cổ tức tiền / cổ phiếu, thưởng, phát hành thêm)
==========================================================================================================
File: corporate_actions.py
Version: 1.1 (2026-10-11) — mốc giá tay / mốc đã báo chỉ chỉnh nếu tạo trước ngày GDKHQ
Version: 1.0 (2026-10-09) — sự cố HDB 09/10: ngày GDKHQ giá giảm ~21%, hệ thống đọc thành "chạm cắt lỗ" và bán.

NGUYÊN LÝ
---------
1. PHÁT HIỆN (update_eod_prices.py, mỗi lần lấy bảng giá):
   Sàn HOSE/HNX: giá tham chiếu hôm nay = giá đóng cửa phiên trước. Ngày GDKHQ, Sở hạ giá tham chiếu
   -> hệ số = tham chiếu hôm nay / đóng cửa phiên trước (lấy từ price_history). Lệch > 1% => có quyền.
   UPCoM: tham chiếu = giá bình quân phiên trước (không phải đóng cửa) -> chỉ ghi 'review' khi lệch > 3%,
   admin xác nhận (POST /api/admin/corporate-actions/apply).
2. ÁP DỤNG (backend, đầu mỗi lần chạy danh mục mẫu / giám sát danh mục — apply_pending), 1 lần / sự kiện:
   price_history (nến trước ngày GDKHQ: giá × hệ số, KL ÷ hệ số) · signals MUA đang mở (giá vào / cắt lỗ /
   mục tiêu × hệ số) · mp_positions (SL cổ phiếu ÷ hệ số, giá × hệ số, tổng vốn giữ nguyên) · watch_levels,
   watch_alert_state, rescue_watch_state (× hệ số). Danh mục khách VIP: KHÔNG tự sửa (cổ phiếu mới về sau
   vài tuần) — báo admin danh sách khách đang giữ mã.
3. CHỐT AN TOÀN (suspicious_move): giá rơi quá biên độ sàn so với phiên trước => không tự bán theo cắt lỗ.

Endpoints (đăng ký trong init_rescue_watch_routes):
  GET  /api/corporate-actions?days=60                      (công khai: mã, ngày, hệ số — cho sell scanner)
  GET  /api/admin/corporate-actions                        [ADMIN] toàn bộ, mọi trạng thái
  POST /api/admin/corporate-actions  {ticker, ex_date, factor | ref_price+prev_close, note}   [ADMIN] thêm tay + áp dụng
  POST /api/admin/corporate-actions/apply  {id}            [ADMIN] xác nhận bản ghi 'review' rồi áp dụng
  POST /api/admin/corporate-actions/ignore {id}            [ADMIN] bỏ qua (phát hiện nhầm)
"""

import os
import json
import html
import logging
from datetime import datetime, date, timedelta

from sqlalchemy import text

logger = logging.getLogger(__name__)

CA_MIN_GAP = float(os.getenv('CA_MIN_GAP', '1.0'))          # % lệch tham chiếu/đóng cửa để coi là có quyền (HOSE/HNX)
CA_UPCOM_GAP = float(os.getenv('CA_UPCOM_GAP', '3.0'))      # UPCoM: ngưỡng cao hơn + cần admin xác nhận
BAND = {'HOSE': 7.0, 'HSX': 7.0, 'HNX': 10.0, 'UPCOM': 15.0}
GUARD_DEFAULT_BAND = 7.0                                    # chưa rõ sàn -> dùng biên HOSE (đa số mã)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_CHAT_ID = os.getenv('ADMIN_TELEGRAM_CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID', '')


# ------------------------------------------------------------------ lịch giao dịch
_HOL = None


def _holidays():
    global _HOL
    if _HOL is None:
        days = {'2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20',
                '2026-04-30', '2026-05-01', '2026-09-02'}
        for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vietnam_holidays.json'), 'vietnam_holidays.json'):
            try:
                with open(p, encoding='utf-8') as f:
                    for lst in json.load(f).get('holidays', {}).values():
                        days.update(str(d)[:10] for d in lst)
                break
            except Exception:
                continue
        _HOL = days
    return _HOL


def prev_trading_day(d):
    d = datetime.strptime(str(d)[:10], '%Y-%m-%d').date() if not isinstance(d, date) else d
    d -= timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in _holidays():
        d -= timedelta(days=1)
    return d.isoformat()


# ------------------------------------------------------------------ DB
def ensure_table(engine):
    pk = 'INTEGER PRIMARY KEY AUTOINCREMENT' if engine.dialect.name == 'sqlite' else 'SERIAL PRIMARY KEY'
    with engine.begin() as c:
        c.execute(text(f"""
            CREATE TABLE IF NOT EXISTS corporate_actions (
                id {pk}, ticker VARCHAR(10) NOT NULL, ex_date VARCHAR(10) NOT NULL,
                factor DOUBLE PRECISION NOT NULL, prev_close DOUBLE PRECISION, ref_price DOUBLE PRECISION,
                exchange VARCHAR(10), source VARCHAR(20), note TEXT,
                status VARCHAR(12) DEFAULT 'detected',      -- detected | review | applying | applied | ignored
                summary TEXT, created_at TIMESTAMP, applied_at TIMESTAMP)"""))


def _rows(conn, sql, **p):
    return [dict(r) for r in conn.execute(text(sql), p).mappings().all()]


def band_pct(exchange=None):
    ex = (exchange or '').upper().replace(' ', '')
    for k, v in BAND.items():
        if k in ex:
            return v
    return GUARD_DEFAULT_BAND


def suspicious_move(prev_close, price, exchange=None):
    """True nếu giá thay đổi vượt biên độ sàn so với phiên trước (+0,5% dung sai làm tròn bước giá):
    không thể là biến động thường — gần như chắc chắn là ngày điều chỉnh quyền (hoặc dữ liệu lỗi)."""
    try:
        prev_close, price = float(prev_close), float(price)
    except (TypeError, ValueError):
        return False
    if prev_close <= 0 or price <= 0:
        return False
    return abs(price / prev_close - 1) * 100 > band_pct(exchange) + 0.5


def last_close_before(conn, ticker, day):
    r = _rows(conn, """SELECT trade_date, close FROM price_history WHERE ticker = :t AND trade_date < :d
                       ORDER BY trade_date DESC LIMIT 1""", t=ticker, d=str(day)[:10])
    return (r[0]['trade_date'], float(r[0]['close'])) if r and r[0]['close'] else (None, None)


# ------------------------------------------------------------------ 1) PHÁT HIỆN
def detect_and_record(engine, board, trade_date):
    """
    board: {ticker: {'ref': giá tham chiếu VND, 'exchange': 'HOSE'|...}} từ bảng giá của phiên trade_date.
    Ghi bản ghi mới vào corporate_actions (status detected / review). Trả list bản ghi mới.
    """
    ensure_table(engine)
    prev_day = prev_trading_day(trade_date)
    new = []
    with engine.begin() as c:
        try:
            known = {(r['ticker'], r['ex_date']) for r in _rows(
                c, "SELECT ticker, ex_date FROM corporate_actions WHERE ex_date >= :d", d=prev_day)}
        except Exception:
            known = set()
        for t, info in board.items():
            ref = info.get('ref')
            if not ref or (t, trade_date) in known:
                continue
            try:
                pdate, pclose = last_close_before(c, t, trade_date)
            except Exception:
                return new                                   # chưa có bảng price_history
            if not pclose or pdate != prev_day:              # thiếu nến phiên trước -> không so được (chốt an toàn lo)
                continue
            f = float(ref) / pclose
            gap = (1 - f) * 100
            exch = (info.get('exchange') or '').upper()
            is_upcom = 'UPCOM' in exch
            if gap <= (CA_UPCOM_GAP if is_upcom else CA_MIN_GAP):   # quyền luôn làm GIẢM giá tham chiếu
                continue
            status = 'review' if is_upcom else 'detected'
            c.execute(text("""INSERT INTO corporate_actions (ticker, ex_date, factor, prev_close, ref_price, exchange, source,
                                                              note, status, created_at)
                              VALUES (:t, :d, :f, :pc, :r, :e, 'ref_price', :n, :s, :now)"""),
                      dict(t=t, d=trade_date, f=f, pc=pclose, r=float(ref), e=exch or None,
                           n=f"Tham chiếu {ref:,.0f} vs đóng cửa {pdate} {pclose:,.0f} (-{gap:.1f}%)", s=status,
                           now=datetime.now()))
            new.append({'ticker': t, 'ex_date': trade_date, 'factor': round(f, 5), 'status': status, 'gap_pct': round(gap, 2)})
    if new:
        logger.info(f"🏷️ Phát hiện điều chỉnh quyền: {new}")
    return new


# ------------------------------------------------------------------ 2) ÁP DỤNG
def _upd(engine, sql, label, out, **p):
    """Mỗi bảng 1 giao dịch riêng: bảng chưa tồn tại / thiếu cột không làm hỏng các bước khác."""
    try:
        with engine.begin() as c:
            n = c.execute(text(sql), p).rowcount
        if n:
            out.append(f"{label}: {n}")
        return n
    except Exception as e:
        logger.warning(f'[CA] {label}: {str(e)[:150]}')
        return 0


def _adjust_positions(engine, ticker, ex_date, f, out, only_ids=None):
    """mp_positions đang mở mua TRƯỚC ngày GDKHQ: SL cp ÷ f (làm tròn), giá × f, tổng vốn giữ nguyên."""
    try:
        with engine.begin() as c:
            rows = _rows(c, """SELECT id, qty, init_qty FROM mp_positions WHERE ticker = :t AND status = 'open'
                               AND entry_date < :d""", t=ticker, d=ex_date)
            if only_ids is not None:
                rows = [r for r in rows if r['id'] in only_ids]
            for r in rows:
                c.execute(text("""UPDATE mp_positions SET qty = :q, init_qty = :iq, entry_price = entry_price * :f,
                                  stop_loss = stop_loss * :f, take_profit = take_profit * :f WHERE id = :i"""),
                          dict(q=int(round(int(r['qty']) / f)), iq=int(round(int(r['init_qty'] or r['qty']) / f)), f=f, i=r['id']))
        if rows:
            out.append(f"danh mục mẫu: {len(rows)} vị thế")
        return len(rows)
    except Exception as e:
        logger.warning(f'[CA] mp_positions: {str(e)[:150]}')
        return 0


def apply_action(engine, ca):
    t, d, f = ca['ticker'], ca['ex_date'], float(ca['factor'])
    out = []
    _upd(engine, """UPDATE price_history SET open = open * :f, high = high * :f, low = low * :f, close = close * :f,
                    volume = volume / :f WHERE ticker = :t AND trade_date < :d""", 'nến lịch sử', out, f=f, t=t, d=d)
    _upd(engine, """UPDATE signals SET entry_price = entry_price * :f, stop_loss = stop_loss * :f,
                    take_profit = take_profit * :f
                    WHERE ticker = :t AND action = 'BUY' AND (status IS NULL OR status IN ('open', 'partial'))
                    AND date < :d""", 'tín hiệu MUA đang mở', out, f=f, t=t, d=d)
    _adjust_positions(engine, t, d, f, out)
    # v1.1: chỉ chỉnh mốc được tạo/báo TRƯỚC ngày GDKHQ (mốc admin nhập sau đó đã theo giá mới)
    _upd(engine, """UPDATE watch_levels SET price = price * :f
                    WHERE ticker = :t AND (created_at IS NULL OR created_at < :d)""",
         'mốc giá tay', out, f=f, t=t, d=d)
    _upd(engine, """UPDATE watch_alert_state SET value = value * :f
                    WHERE ticker = :t AND value IS NOT NULL AND (last_date IS NULL OR last_date < :d)""",
         'mốc đã báo', out, f=f, t=t, d=d)
    _upd(engine, """UPDATE rescue_watch_state SET peak_price = peak_price * :f, last_price = last_price * :f
                    WHERE ticker = :t AND (last_trade_date IS NULL OR last_trade_date < :d)""",
         'đỉnh theo dõi', out, f=f, t=t, d=d)
    holders = []
    try:
        with engine.connect() as c:
            holders = [r['user_id'] for r in _rows(c, """SELECT DISTINCT user_id FROM portfolios
                                                       WHERE UPPER(TRIM(ticker)) = :t AND quantity > 0""", t=t)]
    except Exception:
        pass
    summary = '; '.join(out) or 'không có dữ liệu cần chỉnh'
    with engine.begin() as c:
        c.execute(text("UPDATE corporate_actions SET status = 'applied', applied_at = :now, summary = :s WHERE id = :i"),
                  dict(now=datetime.now(), s=summary, i=ca['id']))
    _notify(f"🏷️ <b>Điều chỉnh quyền {html.escape(t)}</b> — GDKHQ {d}, hệ số {f:.4f} (giá cũ × {f:.4f})\n"
            f"{html.escape(ca.get('note') or '')}\nĐã chỉnh: {html.escape(summary)}"
            + (f"\n👥 Khách đang giữ {html.escape(t)} (giá vốn/số lượng KHÔNG tự sửa — nhắc khách cập nhật khi cổ phiếu về): "
               + html.escape(', '.join(holders)) if holders else ''))
    return {'ticker': t, 'ex_date': d, 'factor': f, 'summary': summary, 'holders': holders}


def apply_pending(engine):
    """Áp dụng mọi bản ghi 'detected' (gọi đầu mỗi lần chạy danh mục mẫu / giám sát). An toàn khi gọi song song."""
    try:
        ensure_table(engine)
        with engine.connect() as c:
            pend = _rows(c, "SELECT * FROM corporate_actions WHERE status = 'detected' ORDER BY ex_date, id")
    except Exception as e:
        logger.warning(f'[CA] apply_pending: {e}')
        return []
    done = []
    for ca in pend:
        with engine.begin() as c:                      # giữ chỗ: chỉ 1 tiến trình áp dụng 1 sự kiện
            claimed = c.execute(text("UPDATE corporate_actions SET status = 'applying' WHERE id = :i AND status = 'detected'"),
                                dict(i=ca['id'])).rowcount
        if claimed:
            try:
                done.append(apply_action(engine, ca))
            except Exception as e:
                logger.exception('[CA] apply error')
                with engine.begin() as c:
                    c.execute(text("UPDATE corporate_actions SET status = 'detected' WHERE id = :i"), dict(i=ca['id']))
    return done


def applied_since(engine, ticker, after_dt):
    """Các sự kiện đã áp dụng SAU thời điểm after_dt (dùng khi khôi phục vị thế đã đóng — void_trade)."""
    try:
        with engine.connect() as c:
            return _rows(c, """SELECT * FROM corporate_actions WHERE ticker = :t AND status = 'applied'
                               AND applied_at > :a ORDER BY ex_date""", t=ticker, a=after_dt)
    except Exception:
        return []


def latest_applied_ex_dates(engine):
    try:
        with engine.connect() as c:
            return {r['ticker']: r['d'] for r in _rows(
                c, "SELECT ticker, MAX(ex_date) AS d FROM corporate_actions WHERE status = 'applied' GROUP BY ticker")}
    except Exception:
        return {}


def _notify(msg):
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        import requests
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                      json={'chat_id': ADMIN_CHAT_ID, 'text': msg, 'parse_mode': 'HTML',
                            'disable_web_page_preview': True}, timeout=15)
    except Exception as e:
        logger.error(f'[CA] notify: {e}')


# ------------------------------------------------------------------ ROUTES
def init_routes(app, engine, require_admin):
    from flask import request, jsonify

    try:
        ensure_table(engine)
    except Exception as e:
        print(f"⚠️  corporate_actions: chưa tạo được bảng ({e})")

    @app.route('/api/corporate-actions', methods=['GET'])
    def ca_public():
        days = int(request.args.get('days', 60))
        since = (date.today() - timedelta(days=days)).isoformat()
        with engine.connect() as c:
            rows = _rows(c, """SELECT ticker, ex_date, factor, prev_close, ref_price FROM corporate_actions
                               WHERE status = 'applied' AND ex_date >= :s ORDER BY ex_date""", s=since)
        return jsonify({'success': True, 'actions': rows})

    @app.route('/api/admin/corporate-actions', methods=['GET', 'POST'])
    @require_admin
    def ca_admin():
        ensure_table(engine)
        if request.method == 'GET':
            with engine.connect() as c:
                rows = _rows(c, "SELECT * FROM corporate_actions ORDER BY ex_date DESC, id DESC LIMIT 100")
            for r in rows:
                for k in ('created_at', 'applied_at'):
                    r[k] = str(r[k]) if r.get(k) else None
            return jsonify({'success': True, 'actions': rows})
        d = request.get_json(silent=True) or {}
        t = (d.get('ticker') or '').upper().strip()
        ex = str(d.get('ex_date') or '')[:10]
        try:
            datetime.strptime(ex, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'ex_date dạng YYYY-MM-DD'}), 400
        f = d.get('factor')
        if not f and d.get('ref_price') and d.get('prev_close'):
            f = float(d['ref_price']) / float(d['prev_close'])
        try:
            f = float(f)
        except (TypeError, ValueError):
            f = 0
        if not t or not (0.2 < f < 1.0):
            return jsonify({'success': False, 'error': 'Cần ticker và factor trong (0.2; 1) — hoặc ref_price + prev_close'}), 400
        with engine.begin() as c:
            if _rows(c, "SELECT id FROM corporate_actions WHERE ticker = :t AND ex_date = :d AND status IN ('applied','applying')",
                     t=t, d=ex):
                return jsonify({'success': False, 'error': f'{t} {ex} đã được áp dụng rồi'}), 400
            c.execute(text("DELETE FROM corporate_actions WHERE ticker = :t AND ex_date = :d AND status <> 'applied'"),
                      dict(t=t, d=ex))
            c.execute(text("""INSERT INTO corporate_actions (ticker, ex_date, factor, prev_close, ref_price, source, note,
                                                              status, created_at)
                              VALUES (:t, :d, :f, :pc, :r, 'admin', :n, 'detected', :now)"""),
                      dict(t=t, d=ex, f=f, pc=d.get('prev_close'), r=d.get('ref_price'),
                           n=(d.get('note') or 'Admin nhập tay').strip(), now=datetime.now()))
        return jsonify({'success': True, 'applied': apply_pending(engine)})

    @app.route('/api/admin/corporate-actions/apply', methods=['POST'])
    @require_admin
    def ca_apply():
        i = int((request.get_json(silent=True) or {}).get('id') or 0)
        with engine.begin() as c:
            n = c.execute(text("UPDATE corporate_actions SET status = 'detected' WHERE id = :i AND status = 'review'"),
                          dict(i=i)).rowcount
        if not n:
            return jsonify({'success': False, 'error': 'Không có bản ghi chờ xác nhận với id này'}), 400
        return jsonify({'success': True, 'applied': apply_pending(engine)})

    @app.route('/api/admin/corporate-actions/ignore', methods=['POST'])
    @require_admin
    def ca_ignore():
        i = int((request.get_json(silent=True) or {}).get('id') or 0)
        with engine.begin() as c:
            n = c.execute(text("UPDATE corporate_actions SET status = 'ignored' WHERE id = :i AND status IN ('detected','review')"),
                          dict(i=i)).rowcount
        return jsonify({'success': bool(n), 'ignored': n})

    print("✅ Corporate actions routes: GET /api/corporate-actions · GET/POST /api/admin/corporate-actions · /apply · /ignore")
