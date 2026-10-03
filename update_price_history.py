#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - PRICE HISTORY (nến ngày) cho Giám sát danh mục VIP
================================================================
File: update_price_history.py
Version: 1.1 (2026-10-03) — nghỉ 3,5s/mã, bắt sys.exit khi bị giới hạn, thử lại mã lỗi, báo đỏ khi còn mã thiếu
Version: 1.0 (2026-10-01)

Chạy trên GitHub Actions lúc 16:00 (sau update_eod_prices.py). Ghi bảng price_history
(ticker, trade_date, open, high, low, close, volume — giá VND) cho:
  - mọi mã trong danh mục của khách VIP (bảng portfolios, chỉ user tier 'vip' đang active)
  - mọi mã có mốc theo dõi admin nhập tay (watch_levels)
  - (tùy chọn) mã thêm qua biến môi trường EXTRA_TICKERS="HDG,BSR"

Lần đầu mỗi mã: tải ~1 năm (HISTORY_DAYS). Các lần sau: chỉ tải từ phiên cuối đã có (lùi 5 ngày
để ghi đè phiên chưa chốt). ~7 khách × ~10 mã ≈ 70 mã → khoảng 2 phút.

Cũng bổ sung eod_prices cho mã trong danh mục khách mà danh sách quét chưa có (để Rescue Watch
không báo "không có giá").

Chạy:
  python update_price_history.py             # ghi DB
  python update_price_history.py --dry-run   # chỉ tải và in, không ghi
  python update_price_history.py HDG BSR     # chỉ các mã này
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRY_RUN = '--dry-run' in sys.argv
ONLY = [a.upper() for a in sys.argv[1:] if not a.startswith('--')]
HISTORY_DAYS = int(os.getenv('HISTORY_DAYS', '400'))
PAUSE = float(os.getenv('HISTORY_PAUSE', '3.5'))   # ~17 lượt/phút: dưới giới hạn ~20/phút của vnstock gói miễn phí

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

from sqlalchemy import create_engine, text


def _to_vnd(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v <= 0 or v != v:
        return None
    return v * 1000 if v < 500 else v


def _is_rate_limit(e):
    s = str(e).lower()
    return 'rate limit' in s or 'quá nhiều' in s or 'too many' in s or '429' in s


def ensure_table(engine):
    with engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS price_history (
                ticker VARCHAR(10) NOT NULL, trade_date VARCHAR(10) NOT NULL,
                open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION,
                close DOUBLE PRECISION, volume DOUBLE PRECISION,
                PRIMARY KEY (ticker, trade_date))"""))


def watched_tickers(engine):
    out = set(ONLY)
    if ONLY:
        return sorted(out)
    with engine.connect() as c:
        try:
            for r in c.execute(text("""
                    SELECT DISTINCT UPPER(TRIM(p.ticker)) FROM portfolios p
                    JOIN vip_users u ON u.email = p.user_id
                    WHERE u.is_active = TRUE AND LOWER(u.tier) = 'vip' AND p.quantity > 0""")):
                if r[0]:
                    out.add(r[0])
        except Exception as e:
            logger.warning(f"Không đọc được danh mục khách: {e}")
        try:
            for r in c.execute(text("SELECT DISTINCT UPPER(ticker) FROM watch_levels")):
                if r[0]:
                    out.add(r[0])
        except Exception:
            pass
    out.update(t.strip().upper() for t in os.getenv('EXTRA_TICKERS', '').split(',') if t.strip())
    return sorted(t for t in out if t.isalnum() and len(t) <= 10)


def last_dates(engine):
    with engine.connect() as c:
        return {r[0]: r[1] for r in c.execute(text("SELECT ticker, MAX(trade_date) FROM price_history GROUP BY ticker"))}


def fetch(ticker, start, end):
    from vnstock import Quote
    last_err = None
    for source in ('VCI', 'KBS'):
        try:
            try:
                q = Quote(symbol=ticker, source=source)
            except TypeError:
                q = Quote(source=source, symbol=ticker)
            df = q.history(start=start, end=end, interval='1D')
            if df is None or len(df) == 0:
                continue
            cols = {c.lower(): c for c in df.columns}
            tcol = cols.get('time') or cols.get('date') or cols.get('trading_date')
            rows = []
            for _, r in df.iterrows():
                d = str(r[tcol])[:10] if tcol else None
                cl = _to_vnd(r[cols['close']])
                if not d or not cl:
                    continue
                rows.append({'t': ticker, 'd': d,
                             'o': _to_vnd(r[cols['open']]) if 'open' in cols else cl,
                             'h': _to_vnd(r[cols['high']]) if 'high' in cols else cl,
                             'l': _to_vnd(r[cols['low']]) if 'low' in cols else cl,
                             'c': cl,
                             'v': float(r[cols['volume']]) if 'volume' in cols and r[cols['volume']] == r[cols['volume']] else 0.0})
            return rows, source
        except (Exception, SystemExit) as e:          # vnstock có thể gọi sys.exit khi bị giới hạn tần suất
            if _is_rate_limit(e) or isinstance(e, SystemExit):
                raise RuntimeError(f'rate limit: {e}')
            last_err = e
    if last_err:
        logger.warning(f"   {ticker}: {str(last_err)[:120]}")
    return [], None


def upsert(engine, rows):
    """Ghi theo lô: xóa khoảng ngày vừa tải của mã đó rồi chèn 1 lần (executemany) — tránh hàng nghìn lượt
    gửi/nhận giữa GitHub Actions và Postgres trên Render ở lần nạp đầu."""
    if not rows:
        return
    rows = list({r['d']: r for r in rows}.values())          # bỏ trùng ngày (nếu nguồn trả lặp)
    with engine.begin() as c:
        c.execute(text("DELETE FROM price_history WHERE ticker = :t AND trade_date >= :d0 AND trade_date <= :d1"),
                  {'t': rows[0]['t'], 'd0': min(r['d'] for r in rows), 'd1': max(r['d'] for r in rows)})
        c.execute(text("""INSERT INTO price_history (ticker, trade_date, open, high, low, close, volume)
                          VALUES (:t, :d, :o, :h, :l, :c, :v)"""), rows)


def fill_eod(engine, latest):
    """Thêm giá vào eod_prices cho mã danh mục khách chưa nằm trong danh sách quét."""
    with engine.begin() as c:
        have = {r[0]: str(r[1] or '')[:10] for r in c.execute(text("SELECT ticker, trade_date FROM eod_prices"))}
        added = 0
        for t, (d, p) in latest.items():
            if t not in have:
                c.execute(text("INSERT INTO eod_prices (ticker, price, trade_date, updated_at) VALUES (:t, :p, :d, :now)"),
                          {'t': t, 'p': p, 'd': d, 'now': datetime.now()})
                added += 1
            elif have[t] < d:          # mã ngoài danh sách quét: làm mới giá đóng cửa hằng ngày
                c.execute(text("UPDATE eod_prices SET price = :p, trade_date = :d, updated_at = :now WHERE ticker = :t"),
                          {'t': t, 'p': p, 'd': d, 'now': datetime.now()})
    return added


def main():
    t0 = datetime.now()
    engine = create_engine(DATABASE_URL)
    if not DRY_RUN:
        ensure_table(engine)
    tickers = watched_tickers(engine)
    have = {} if DRY_RUN else last_dates(engine)
    end = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"🚀 Price history | {len(tickers)} mã | {'DRY-RUN' if DRY_RUN else 'GHI DB'} | {', '.join(tickers)}")

    ok, failed, total_rows, latest = 0, [], 0, {}

    def one(t):
        start = ((datetime.strptime(have[t], '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')
                 if have.get(t) else (datetime.now() - timedelta(days=HISTORY_DAYS)).strftime('%Y-%m-%d'))
        for attempt in range(2):
            try:
                return fetch(t, start, end)[0]
            except Exception as e:
                logger.warning(f"   ⏳ {t}: {str(e)[:80]} — chờ {30 * (attempt + 1)}s")
                time.sleep(30 * (attempt + 1))
        return []

    queue = list(tickers)
    for rnd in (1, 2):                     # vòng 2: thử lại các mã lỗi sau khi nghỉ 60s
        failed = []
        for i, t in enumerate(queue):
            rows = one(t)
            if rows:
                ok += 1
                total_rows += len(rows)
                latest[t] = (rows[-1]['d'], rows[-1]['c'])
                if DRY_RUN:
                    logger.info(f"   {t}: {len(rows)} nến, cuối {rows[-1]['d']} close {rows[-1]['c']:,.0f} vol {rows[-1]['v']:,.0f}")
                else:
                    upsert(engine, rows)
            else:
                failed.append(t)
            time.sleep(PAUSE)
            if (i + 1) % 20 == 0:
                logger.info(f"   … {i + 1}/{len(queue)}")
        if not failed or rnd == 2:
            break
        logger.warning(f"   🔁 Thử lại {len(failed)} mã lỗi sau 60s: {', '.join(failed)}")
        time.sleep(60)
        queue = failed

    added = 0 if DRY_RUN else fill_eod(engine, latest)
    logger.info(f"✅ Xong {ok}/{len(tickers)} mã, {total_rows} nến, thêm {added} mã vào eod_prices | "
                f"lỗi: {', '.join(failed) or 'không'} | {(datetime.now() - t0).total_seconds():.0f}s")
    if failed:
        sys.exit(1)                        # bước Actions báo đỏ để admin biết còn mã thiếu nến


if __name__ == '__main__':
    main()
