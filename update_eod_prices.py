#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - EOD PRICE UPDATER
================================
Script riêng để download giá đóng cửa cho tất cả 343 mã.
Chạy sau 4PM mỗi ngày giao dịch (tách riêng khỏi signal scanner).

Lịch chạy (GitHub Actions): cron '0 10 * * 1-5' = 5PM Vietnam, T2-T6
Output: latest_prices_all.json

Cách dùng:
  python update_eod_prices.py          # Chạy local
  POST /api/prices/update              # Trigger qua API
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# DANH SÁCH 343 MÃ - copy từ daily_signal_scanner_eod.py
# Cập nhật cùng lúc với scanner khi thêm/bớt mã
# ============================================================

ALL_TICKERS = [
    # HOSE - Blue Chips & Large Caps
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'BSR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
    'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'SHB', 'LPB', 'VCI', 'TCX',
    'BVH', 'HVN', 'BMP', 'DXG', 'VPL', 'KBC', 'DIG', 'GEX', 'VIB', 'EIB',

    # HOSE - Mid Caps
    'VPI', 'HSG', 'DCM', 'NT2', 'HNG', 'VND', 'VCG', 'SBT', 'EVF', 'BFC',
    'DBC', 'HCM', 'CTD', 'PC1', 'DGW', 'SZC', 'CTR', 'MCH', 'VIX', 'HDG',
    'VSC', 'BWE', 'VCK', 'VDS', 'VTP', 'SCS', 'CNG', 'PVD', 'HSL', 'OCB',
    'PVT', 'VOS', 'CSV', 'NLG', 'CMG', 'TCH', 'PAN', 'BSI', 'DCL', 'HAH',
    'PHR', 'DPR', 'GEG', 'CII', 'PTB', 'NAF', 'HAG', 'TAL', 'NTL', 'BMI',
    'CMX', 'ORS', 'HDC', 'TNG', 'HRC', 'SVC', 'TCL', 'KSB', 'ELC', 'IJC',
    'VHC', 'HHS', 'MSH', 'HAX', 'VTO', 'VPX', 'PET', 'PVP', 'SIP', 'SMC',
    'QCG', 'FRT', 'SJS', 'FCN', 'GEE', 'DSE', 'TCM', 'VGT', 'TV2', 'BAF',
    'DHA', 'GEL', 'GIL', 'CTI', 'PDR', 'IDC', 'KHG', 'DPG', 'LCG', 'ANV',
    'MSB', 'DXS',

    # HNX - Top Stocks
    'PVS', 'VFS', 'SHS', 'PVB', 'CEO', 'BVS', 'BAB', 'NVB', 'PLC', 'IPA',
    'TIG', 'API', 'PVC', 'BVB', 'HUT', 'MIG', 'EVS', 'PSI', 'APS', 'IDJ',
    'MBS', 'LAS', 'VGS', 'VCS',

    # Additional stocks commonly held in portfolios
    'ASG', 'ASP', 'ABI', 'BAF', 'C69', 'CLC', 'HDB', 'HPG', 'HT1', 'HTI',
    'KDC', 'L18', 'LSS', 'PC1', 'PGC', 'PGD', 'PPC', 'PVP', 'SZL', 'TCO',
    'TIP', 'VHM', 'VSH', 'VTP', 'SZC', 'SZL',
]

# Deduplicate
ALL_TICKERS = list(dict.fromkeys(ALL_TICKERS))

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latest_prices_all.json')


def get_last_trading_day():
    today = datetime.now()
    if today.weekday() == 5:  # Saturday
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif today.weekday() == 6:  # Sunday
        return (today - timedelta(days=2)).strftime('%Y-%m-%d')
    return today.strftime('%Y-%m-%d')


def fetch_price_batch(tickers, batch_size=20):
    """
    Fetch closing prices for a batch of tickers.
    Returns dict: {ticker: {'price': float, 'date': str}}
    """
    try:
        from vnstock import Quote
    except ImportError:
        logger.error("vnstock not installed. Run: pip install vnstock3")
        return {}

    prices = {}
    end_date = get_last_trading_day()
    start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')

    for i, ticker in enumerate(tickers):
        try:
            quote = Quote(symbol=ticker, source='VCI')
            df = quote.history(start=start_date, end=end_date)

            if df is not None and len(df) > 0:
                close_price = float(df['close'].iloc[-1])
                trade_date = str(df.index[-1])[:10] if hasattr(df.index[-1], 'strftime') else end_date

                prices[ticker] = {
                    'price': close_price,
                    'date': trade_date,
                }
                logger.info(f"✅ {ticker}: {close_price:,.0f} ({trade_date})")
            else:
                logger.warning(f"⚠️  {ticker}: No data")

        except Exception as e:
            error_str = str(e).lower()
            if 'rate limit' in error_str or 'quá nhiều' in error_str:
                logger.warning(f"⏳ Rate limit hit at {ticker}. Waiting 30s...")
                time.sleep(30)
                # Retry once
                try:
                    quote = Quote(symbol=ticker, source='VCI')
                    df = quote.history(start=start_date, end=end_date)
                    if df is not None and len(df) > 0:
                        prices[ticker] = {
                            'price': float(df['close'].iloc[-1]),
                            'date': str(df.index[-1])[:10],
                        }
                except Exception:
                    pass
            else:
                logger.warning(f"❌ {ticker}: {e}")

        # Polite delay every 10 tickers
        if (i + 1) % 10 == 0:
            time.sleep(2)

    return prices


def update_eod_prices(tickers=None):
    """
    Main function: Download EOD prices and save to latest_prices_all.json
    Returns: dict with success status and stats
    """
    if tickers is None:
        tickers = ALL_TICKERS

    logger.info(f"🚀 Starting EOD price update for {len(tickers)} tickers...")
    logger.info(f"   Output: {OUTPUT_FILE}")
    start_time = datetime.now()

    # Fetch prices
    prices = fetch_price_batch(tickers)

    # Build output structure
    output = {
        'generated_at': datetime.now().isoformat(),
        'trade_date': get_last_trading_day(),
        'total_tickers': len(prices),
        'prices': prices,
    }

    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"\n✅ Done! {len(prices)}/{len(tickers)} tickers updated in {elapsed:.0f}s")
    logger.info(f"   Saved to: {OUTPUT_FILE}")

    return {
        'success': True,
        'tickers_updated': len(prices),
        'tickers_requested': len(tickers),
        'trade_date': get_last_trading_day(),
        'elapsed_seconds': int(elapsed),
        'output_file': OUTPUT_FILE,
    }


if __name__ == '__main__':
    result = update_eod_prices()
    print(f"\n📊 Result: {result}")
