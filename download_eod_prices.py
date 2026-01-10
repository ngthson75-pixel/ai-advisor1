#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY EOD PRICE DOWNLOADER
Download latest prices for all VN30 + common stocks
Run daily at 5:30 PM (after market close)
"""

import json
from datetime import datetime, timedelta
from vnstock import Vnstock

# VN30 stocks + popular stocks
TICKERS = [
    # VN30
    'VCB', 'VHM', 'VIC', 'VNM', 'GAS', 'MSN', 'VPB', 'HPG', 'TCB', 'MWG',
    'BID', 'CTG', 'FPT', 'PLX', 'POW', 'SSI', 'STB', 'VRE', 'NVL', 'PDR',
    'MBB', 'HDB', 'ACB', 'VJC', 'GVR', 'SAB', 'VHC', 'TPB', 'KDH', 'BCM',
    
    # Other popular
    'DGC', 'DIG', 'DPM', 'FRT', 'GMD', 'HCM', 'HNG', 'HPX', 'KBC', 'LPB',
    'OCB', 'PNJ', 'REE', 'SHB', 'SSB', 'TCH', 'VCG', 'VCI', 'VIB', 'VND'
]

OUTPUT_FILE = 'latest_prices.json'


def download_latest_prices():
    """Download latest closing prices for all tickers"""
    
    print("🔄 Starting EOD price download...")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Tickers: {len(TICKERS)}")
    
    stock_api = Vnstock()
    prices = {}
    errors = []
    
    # Get today and yesterday
    today = datetime.now()
    yesterday = today - timedelta(days=7)  # Get last 7 days to ensure data
    
    for i, ticker in enumerate(TICKERS, 1):
        try:
            print(f"[{i}/{len(TICKERS)}] Fetching {ticker}...", end=' ')
            
            stock = stock_api.stock(symbol=ticker, source='VCI')
            
            # Get historical data (last 7 days)
            df = stock.quote.history(
                symbol=ticker,
                start=yesterday.strftime('%Y-%m-%d'),
                end=today.strftime('%Y-%m-%d')
            )
            
            if df.empty:
                print("❌ No data")
                errors.append(ticker)
                continue
            
            # Get latest price
            latest = df.iloc[-1]
            
            prices[ticker] = {
                'price': float(latest['close']),
                'date': latest['time'].strftime('%Y-%m-%d') if hasattr(latest['time'], 'strftime') else str(latest['time']),
                'change': float(latest.get('change', 0)),
                'change_percent': float(latest.get('pct_change', 0)),
                'volume': int(latest.get('volume', 0))
            }
            
            print(f"✅ {prices[ticker]['price']:,.0f} VND")
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            errors.append(ticker)
    
    # Save to JSON
    data = {
        'updated_at': datetime.now().isoformat(),
        'total_tickers': len(TICKERS),
        'success_count': len(prices),
        'error_count': len(errors),
        'errors': errors,
        'prices': prices
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "="*70)
    print("📊 DOWNLOAD SUMMARY")
    print("="*70)
    print(f"✅ Success: {len(prices)}/{len(TICKERS)}")
    print(f"❌ Errors: {len(errors)}")
    if errors:
        print(f"Failed tickers: {', '.join(errors)}")
    print(f"💾 Saved to: {OUTPUT_FILE}")
    print("="*70)
    
    return data


def test_load_prices():
    """Test loading prices from file"""
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n📂 LOADED DATA:")
        print(f"Updated: {data['updated_at']}")
        print(f"Tickers: {data['success_count']}")
        
        # Sample prices
        print("\nSample prices:")
        for ticker in ['VCB', 'VHM', 'VIC', 'FPT', 'HPG']:
            if ticker in data['prices']:
                p = data['prices'][ticker]
                print(f"  {ticker}: {p['price']:,.0f} VND ({p['change_percent']:+.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return False


if __name__ == '__main__':
    import sys
    
    print("\n" + "="*70)
    print("💰 EOD PRICE DOWNLOADER")
    print("="*70)
    
    # Download
    data = download_latest_prices()
    
    # Test load
    print("\n🧪 Testing file load...")
    if test_load_prices():
        print("\n✅ ALL DONE!")
        sys.exit(0)
    else:
        print("\n❌ FAILED!")
        sys.exit(1)
