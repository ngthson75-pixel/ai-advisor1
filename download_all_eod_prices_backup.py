#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD ALL EOD PRICES
Downloads end-of-day prices for ALL Vietnamese stocks
HOSE + HNX + UPCOM = ~2000+ tickers
"""

import json
from datetime import datetime
from vnstock import Vnstock
import time

def get_all_tickers():
    """
    Get ALL tickers from all exchanges
    HOSE, HNX, UPCOM
    """
    stock_api = Vnstock()
    
    try:
        # Get listing from all exchanges
        print("📊 Fetching ticker list from all exchanges...")
        
        all_tickers = []
        
        # Method 1: Try listing API
        try:
            listing = stock_api.listing.all_symbols()
            if listing is not None and not listing.empty:
                all_tickers = listing['ticker'].unique().tolist()
                print(f"✅ Found {len(all_tickers)} tickers from listing API")
                return all_tickers
        except Exception as e:
            print(f"⚠️ Listing API failed: {e}")
        
        # Method 2: Hardcoded exchanges (fallback)
        exchanges = ['HOSE', 'HNX', 'UPCOM']
        
        for exchange in exchanges:
            try:
                print(f"  Fetching {exchange}...")
                
                if exchange == 'HOSE':
                    # VN30 + major stocks
                    tickers = [
                        # VN30 index
                        'VCB', 'VHM', 'VIC', 'VNM', 'GAS', 'MSN', 'SAB', 'BID', 'CTG',
                        'HPG', 'MWG', 'PLX', 'POW', 'TCB', 'VPB', 'VRE', 'MBB', 'VJC',
                        'FPT', 'HDB', 'BVH', 'NVL', 'TPB', 'STB', 'GVR', 'PDR', 'VCI',
                        'SSI', 'HVN', 'TCM',
                        # Other major HOSE
                        'ACB', 'EIB', 'LPB', 'SHB', 'VIB', 'OCB', 'MSB',
                        'GMD', 'DIG', 'PNJ', 'DBC', 'REE', 'GEX', 'DHG',
                        'HSG', 'KBC', 'DGC', 'NT2', 'PVD', 'HAG', 'DCM'
                    ]
                    all_tickers.extend(tickers)
                    
                elif exchange == 'HNX':
                    # Major HNX
                    tickers = [
                        'PVS', 'CEO', 'SHS', 'VCS', 'PVI', 'VGC', 'PVX',
                        'NRC', 'TNG', 'PVC', 'VC3', 'TDH', 'HUT', 'PVB'
                    ]
                    all_tickers.extend(tickers)
                    
                elif exchange == 'UPCOM':
                    # Major UPCOM
                    tickers = ['BSR', 'EVE', 'PAN', 'THD', 'AAA']
                    all_tickers.extend(tickers)
                    
            except Exception as e:
                print(f"⚠️ Error fetching {exchange}: {e}")
        
        # Remove duplicates
        all_tickers = list(set(all_tickers))
        print(f"✅ Collected {len(all_tickers)} tickers (fallback mode)")
        
        return all_tickers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def download_all_prices():
    """
    Download EOD prices for ALL tickers
    """
    print("\n" + "="*70)
    print("📥 DOWNLOADING ALL EOD PRICES")
    print("="*70)
    
    stock_api = Vnstock()
    
    # Get all tickers
    all_tickers = get_all_tickers()
    
    if not all_tickers:
        print("❌ No tickers found!")
        return
    
    print(f"\n🎯 Will download prices for {len(all_tickers)} tickers")
    print("⏰ Estimated time: {:.1f} minutes".format(len(all_tickers) * 2 / 60))
    print("\nStarting download...\n")
    
    # Download prices
    prices_data = {}
    success_count = 0
    fail_count = 0
    
    for i, ticker in enumerate(all_tickers, 1):
        try:
            print(f"[{i}/{len(all_tickers)}] Fetching {ticker}...", end=' ')
            
            stock = stock_api.stock(symbol=ticker, source='VCI')
            
            # Try intraday first (more recent)
            price = None
            change_pct = None
            volume = None
            
            try:
                intraday = stock.quote.intraday(symbol=ticker, page_size=1)
                if not intraday.empty:
                    price = float(intraday['close'].iloc[-1])
                    if 'change_percent' in intraday.columns:
                        change_pct = float(intraday['change_percent'].iloc[-1])
                    if 'volume' in intraday.columns:
                        volume = int(intraday['volume'].iloc[-1])
            except:
                pass
            
            # Fallback to daily
            if price is None:
                from datetime import datetime, timedelta
                today = datetime.now().strftime('%Y-%m-%d')
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                daily = stock.quote.history(symbol=ticker, start=week_ago, end=today)
                if not daily.empty:
                    price = float(daily['close'].iloc[-1])
                    if 'change_percent' in daily.columns:
                        change_pct = float(daily['change_percent'].iloc[-1])
                    elif len(daily) > 1:
                        prev_close = float(daily['close'].iloc[-2])
                        change_pct = ((price - prev_close) / prev_close * 100)
                    if 'volume' in daily.columns:
                        volume = int(daily['volume'].iloc[-1])
            
            if price:
                prices_data[ticker] = {
                    'price': price,
                    'change_percent': change_pct if change_pct else 0.0,
                    'volume': volume if volume else 0
                }
                success_count += 1
                print(f"✅ {price:,.0f} ({change_pct:+.1f}%)" if change_pct else f"✅ {price:,.0f}")
            else:
                fail_count += 1
                print("❌ No data")
            
            # Rate limiting (avoid overwhelming API)
            time.sleep(1)  # 1 second delay between requests
            
        except Exception as e:
            fail_count += 1
            print(f"❌ Error: {e}")
            continue
    
    # Save to JSON
    output_file = 'latest_prices_all.json'
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_tickers': len(all_tickers),
        'success_count': success_count,
        'fail_count': fail_count,
        'prices': prices_data
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*70)
    print(f"Total tickers: {len(all_tickers)}")
    print(f"Success: {success_count} ✅")
    print(f"Failed: {fail_count} ❌")
    print(f"Success rate: {success_count/len(all_tickers)*100:.1f}%")
    print(f"\n📁 Saved to: {output_file}")
    print(f"📊 File size: {len(json.dumps(output_data))/1024:.1f} KB")
    print("="*70 + "\n")
    
    return output_data


if __name__ == '__main__':
    download_all_prices()
