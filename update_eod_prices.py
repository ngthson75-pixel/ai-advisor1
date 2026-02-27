#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - EOD PRICE UPDATER
================================
Download giá đóng cửa từ vnstock → lưu vào PostgreSQL.
Chạy tự động lúc 4PM Vietnam qua GitHub Actions.

Không dùng file JSON. Giá lưu trong DB → không mất khi Render redeploy.
"""

import os
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class EodPrice(Base):
    __tablename__ = 'eod_prices'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    trade_date = Column(String(20))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def load_ticker_list():
    """Đọc danh sách mã từ daily_signal_scanner_eod.py - tự động sync"""
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


def update_eod_prices():
    """Download giá từ vnstock và upsert vào PostgreSQL"""
    try:
        from vnstock import Quote
    except ImportError:
        logger.error("vnstock not installed")
        return {'success': False, 'error': 'vnstock not installed'}

    tickers = load_ticker_list()
    if not tickers:
        return {'success': False, 'error': 'No tickers loaded'}

    total = len(tickers)
    trade_date = get_last_trading_day()
    end_date = trade_date
    start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')

    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 EOD Price Update → PostgreSQL")
    logger.info(f"   Tickers: {total} | Date: {trade_date}")
    logger.info(f"   ~{total * 2 / 60:.0f} phút")
    logger.info(f"{'='*60}\n")

    session = Session()
    updated = 0
    failed = []
    start_time = datetime.now()

    for i, ticker in enumerate(tickers):
        success = False

        for source in ['VCI', 'TCBS']:
            try:
                df = Quote(symbol=ticker, source=source).history(start=start_date, end=end_date)
                if df is not None and len(df) > 0:
                    # vnstock returns price in thousands VND → multiply by 1000
                    price = float(df['close'].iloc[-1]) * 1000
                    # Upsert
                    record = session.query(EodPrice).filter_by(ticker=ticker).first()
                    if record:
                        record.price = price
                        record.trade_date = trade_date
                        record.updated_at = datetime.now()
                    else:
                        session.add(EodPrice(ticker=ticker, price=price, trade_date=trade_date))
                    updated += 1
                    logger.info(f"[{i+1:3d}/{total}] ✅ {ticker}: {price:>10,.0f} ({source})")
                    success = True
                    break
            except Exception as e:
                if 'rate limit' in str(e).lower() or 'quá nhiều' in str(e).lower():
                    logger.warning(f"[{i+1:3d}/{total}] ⏳ Rate limit. Saving & waiting 60s...")
                    session.commit()
                    time.sleep(60)

        if not success:
            failed.append(ticker)
            logger.warning(f"[{i+1:3d}/{total}] ❌ {ticker}: all sources failed")

        time.sleep(2.0)

        if (i + 1) % 20 == 0:
            session.commit()
            logger.info(f"--- 💾 {updated} saved. Pausing 10s ---")
            time.sleep(10)

    session.commit()
    session.close()

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n✅ Done! Updated {updated}/{total} | Failed {len(failed)} | {elapsed/60:.1f} min")

    return {
        'success': True,
        'updated': updated,
        'failed': len(failed),
        'trade_date': trade_date,
        'elapsed_minutes': round(elapsed / 60, 1)
    }


if __name__ == '__main__':
    result = update_eod_prices()
    print(f"\n📊 Result: {result}")
