#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - EOD PRICE UPDATER v2 (2026-09-27)
==============================================
Ghi giá mới nhất của các mã trong danh sách scanner vào bảng eod_prices (PostgreSQL).

v2 — NHANH HƠN ~10 LẦN:
  - Lấy giá theo BẢNG GIÁ (price board), ~50 mã / 1 request, thay vì tải lịch sử 7 ngày
    cho từng mã + nghỉ 2s/mã + 10s mỗi 20 mã (bản cũ mất 11-60 phút/lần).
  - Mã nào bảng giá không trả về -> tự quay lại cách cũ (tải lịch sử từng mã) cho riêng mã đó.
  - Nếu bảng giá hỏng hoàn toàn (vd vnstock đổi API) -> tự chạy lại toàn bộ bằng cách cũ.
    => Không bao giờ tệ hơn bản cũ.
  - Ghi DB 1 lần (đọc sẵn toàn bộ bản ghi cũ), không query từng mã.
  - --dry-run: chỉ lấy giá và in kết quả, KHÔNG ghi DB (để test trên máy local).

Chạy:
  python update_eod_prices.py            # cập nhật thật
  python update_eod_prices.py --dry-run  # thử, không ghi DB
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DRY_RUN = '--dry-run' in sys.argv
BATCH_SIZE = int(os.getenv('EOD_BATCH_SIZE', '50'))

# ============================================================
# DATABASE
# ============================================================
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class EodPrice(Base):
    __tablename__ = 'eod_prices'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    trade_date = Column(String(20))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


engine = None
Session = None
if not DRY_RUN:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)


# ============================================================
# TICKERS / DATES (giữ nguyên như bản cũ)
# ============================================================

def load_ticker_list():
    """Đọc danh sách mã từ daily_signal_scanner_eod.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for path in [
        os.path.join(script_dir, 'scripts', 'daily_signal_scanner_eod.py'),
        os.path.join(script_dir, 'daily_signal_scanner_eod.py'),
    ]:
        if os.path.exists(path):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("scanner", path)
                scanner = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(scanner)
                tickers = list(dict.fromkeys(scanner.TOP_343_STOCKS))
                logger.info(f"✅ Loaded {len(tickers)} tickers from scanner")
                return tickers
            except Exception as e:
                logger.warning(f"Could not load from {path}: {e}")
    logger.error("❌ Scanner file not found!")
    return []


def get_last_trading_day():
    today = datetime.now()
    if today.weekday() == 5:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif today.weekday() == 6:
        return (today - timedelta(days=2)).strftime('%Y-%m-%d')
    return today.strftime('%Y-%m-%d')


def _to_vnd(v):
    """Chuẩn hóa về VND. Bảng giá thường trả VND (27400), lịch sử trả nghìn đồng (27.4)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v <= 0 or v != v:   # <=0 hoặc NaN
        return None
    return v * 1000 if v < 500 else v


def _is_rate_limit(e):
    s = str(e).lower()
    return 'rate limit' in s or 'quá nhiều' in s or 'too many' in s or '429' in s


# ============================================================
# CÁCH 1 — BẢNG GIÁ (nhanh, nhiều mã / 1 request)
# ============================================================

def _make_trading():
    from vnstock import Trading
    errors = []
    for kwargs in ({'source': 'VCI'}, {'source': 'vci'}, {'symbol': 'VN30F1M', 'source': 'VCI'}):
        try:
            return Trading(**kwargs)
        except Exception as e:
            errors.append(f"{kwargs}: {e}")
    raise RuntimeError('Không khởi tạo được Trading: ' + ' | '.join(errors))


def _parse_board(df):
    """DataFrame bảng giá -> {ticker: price_vnd}. Chịu được cột phẳng hoặc MultiIndex."""
    if df is None or len(df) == 0:
        return {}
    df = df.copy()
    if hasattr(df.columns, 'levels'):  # MultiIndex -> 'match_match_price'
        df.columns = ['_'.join(str(x) for x in c if str(x)) for c in df.columns]
    cols = [str(c) for c in df.columns]
    low = {c.lower(): c for c in cols}

    sym_col = next((low[c] for c in low if c == 'symbol' or c.endswith('_symbol') or c in ('ticker', 'code')), None)
    # Ưu tiên giá khớp gần nhất, rồi giá đóng cửa, cuối cùng giá tham chiếu (trước giờ mở cửa)
    price_col = None
    for key in ('match_price', 'last_price', 'close_price', 'close', 'price', 'ref_price', 'reference_price'):
        price_col = next((low[c] for c in low if c == key or c.endswith('_' + key)), None)
        if price_col:
            break
    ref_col = next((low[c] for c in low if c.endswith('ref_price') or c.endswith('reference_price')), None)
    if not sym_col or not price_col:
        raise RuntimeError(f"Không nhận ra cột symbol/giá trong bảng giá: {cols[:25]}")

    out = {}
    for _, row in df.iterrows():
        t = str(row[sym_col]).upper().strip()
        p = _to_vnd(row[price_col])
        if p is None and ref_col:           # chưa khớp lệnh nào trong phiên -> dùng giá tham chiếu
            p = _to_vnd(row[ref_col])
        if t and p:
            out[t] = p
    return out


def fetch_prices_board(tickers):
    trading = _make_trading()
    prices = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        chunk = tickers[i:i + BATCH_SIZE]
        for attempt in range(1, 4):
            try:
                try:
                    df = trading.price_board(symbols_list=chunk)
                except TypeError:
                    df = trading.price_board(chunk)
                got = _parse_board(df)
                prices.update({t: p for t, p in got.items() if t in set(chunk)})
                logger.info(f"   📋 Bảng giá lô {i // BATCH_SIZE + 1}: {len(got)}/{len(chunk)} mã")
                break
            except Exception as e:
                if _is_rate_limit(e) and attempt < 3:
                    logger.warning(f"   ⏳ Rate limit ở lô {i // BATCH_SIZE + 1}, chờ {30 * attempt}s")
                    time.sleep(30 * attempt)
                    continue
                if i == 0:
                    raise  # lô đầu đã hỏng -> để hàm gọi chuyển sang cách cũ
                logger.warning(f"   ⚠️ Lô {i // BATCH_SIZE + 1} lỗi: {str(e)[:120]}")
                break
        time.sleep(1)
    return prices


# ============================================================
# CÁCH 2 — LỊCH SỬ TỪNG MÃ (cách cũ, chỉ dùng cho mã còn thiếu)
# ============================================================

def fetch_price_history(ticker, start_date, end_date):
    from vnstock import Quote
    for source in ("VCI", "vci", "TCBS", "tcbs", "SSI", "ssi"):
        try:
            try:
                q = Quote(symbol=ticker, source=source)
            except TypeError:
                q = Quote(source=source, symbol=ticker)
            df = q.history(start=start_date, end=end_date)
            if df is not None and len(df) > 0:
                return _to_vnd(df['close'].iloc[-1]), source
        except Exception as e:
            if _is_rate_limit(e):
                raise
            continue
    return None, None


def fetch_prices_history(tickers, start_date, end_date, pause=1.0):
    prices = {}
    for i, t in enumerate(tickers):
        for attempt in range(2):
            try:
                p, src = fetch_price_history(t, start_date, end_date)
                if p:
                    prices[t] = p
                break
            except Exception:
                logger.warning(f"   ⏳ Rate limit ({t}), chờ 60s")
                time.sleep(60)
        time.sleep(pause)
        if (i + 1) % 25 == 0:
            logger.info(f"   … lịch sử từng mã: {i + 1}/{len(tickers)}")
    return prices


# ============================================================
# MAIN
# ============================================================

def update_eod_prices():
    tickers = load_ticker_list()
    if not tickers:
        return {'success': False, 'error': 'No tickers loaded'}

    trade_date = get_last_trading_day()
    start_date = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
    t0 = datetime.now()
    logger.info(f"🚀 EOD Price Update v2 | {len(tickers)} mã | ngày {trade_date} | {'DRY-RUN' if DRY_RUN else 'GHI DB'}")

    method = 'board'
    try:
        prices = fetch_prices_board(tickers)
    except Exception as e:
        logger.warning(f"⚠️ Bảng giá không dùng được ({str(e)[:150]}) → chuyển sang cách cũ cho toàn bộ")
        prices, method = {}, 'history'

    missing = [t for t in tickers if t not in prices]
    if missing:
        logger.info(f"🔁 {len(missing)} mã chưa có giá → lấy bằng lịch sử từng mã")
        prices.update(fetch_prices_history(missing, start_date, trade_date))

    failed = [t for t in tickers if t not in prices]
    logger.info(f"📊 Lấy được {len(prices)}/{len(tickers)} mã ({method}) trong {(datetime.now() - t0).total_seconds():.0f}s")
    if failed:
        logger.info(f"   Không có giá: {', '.join(failed[:40])}{' …' if len(failed) > 40 else ''}")

    if DRY_RUN:
        for t in list(prices)[:10]:
            logger.info(f"   {t}: {prices[t]:,.0f}")
        return {'success': True, 'dry_run': True, 'fetched': len(prices), 'failed': len(failed)}

    session = Session()
    try:
        existing = {r.ticker: r for r in session.query(EodPrice).filter(EodPrice.ticker.in_(list(prices))).all()}
        now = datetime.now()
        for t, p in prices.items():
            rec = existing.get(t)
            if rec:
                rec.price, rec.trade_date, rec.updated_at = p, trade_date, now
            else:
                session.add(EodPrice(ticker=t, price=p, trade_date=trade_date))
        session.commit()
    finally:
        session.close()

    elapsed = (datetime.now() - t0).total_seconds()
    logger.info(f"✅ Done! Updated {len(prices)}/{len(tickers)} | Failed {len(failed)} | {elapsed / 60:.1f} min | method={method}")
    return {'success': True, 'updated': len(prices), 'failed': len(failed), 'trade_date': trade_date,
            'elapsed_minutes': round(elapsed / 60, 1), 'method': method}


if __name__ == '__main__':
    result = update_eod_prices()
    print(f"\n📊 Result: {result}")
    if not result.get('success') or result.get('updated', result.get('fetched', 0)) == 0:
        sys.exit(1)
