#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD ALL EOD PRICES
Manual weekly update - downloads ~150 major tickers
Saves to: latest_prices_all.json
"""

import json
import os
from datetime import datetime, timedelta
from vnstock import Vnstock
import time

# Config
OUTPUT_FILE = 'latest_prices_all.json'


def get_all_tickers():
    """
    Get ALL major tickers from Vietnamese stock market
    Returns ~150 major tickers (VN30 + Banks + others)
    """
    
    print("📋 Using major ticker list...")
    
    major_tickers = [
        # VN30 (Top 30 HOSE)
        'VCB', 'VHM', 'VIC', 'VNM', 'GAS', 'MSN', 'SAB', 'BID', 'CTG',
        'HPG', 'MWG', 'PLX', 'POW', 'TCB', 'VPB', 'VRE', 'MBB', 'VJC',
        'FPT', 'HDB', 'BVH', 'NVL', 'TPB', 'STB', 'GVR', 'PDR', 'VCI',
        'SSI', 'HVN', 'TCM',
        
        # Other major HOSE (Banks)
        'ACB', 'EIB', 'LPB', 'SHB', 'VIB', 'OCB', 'MSB', 'VAB', 'BAB',
        'VBB', 'PGB', 'SEA', 'NAB', 'ABB', 'SGB', 'BVB', 'KLB',
        
        # HOSE - Other sectors
        'GMD', 'DIG', 'PNJ', 'DBC', 'REE', 'GEX', 'DHG', 'HSG', 'KBC',
        'DGC', 'NT2', 'PVD', 'HAG', 'DCM', 'DPM', 'HT1', 'VGC',
        'PVT', 'PVS', 'PVG', 'PVB', 'PVC', 'PVX', 'PC1', 'PAN',
        
        # HOSE - Real Estate
        'DXG', 'KDH', 'HDG', 'NLG', 'HDC', 'DXS', 'SZC', 'IDC', 'SCR', 'CEO',
        
        # HOSE - Industrial
        'NKG', 'POM', 'DTL', 'VCS',
        
        # HNX (Major)
        'PVI', 'TNG', 'VC3', 'TDH', 'HUT', 'L10', 'VIG',
        'DTT', 'HTP', 'MBS', 'SD2', 'SD5', 'SD9', 'SDN', 'HHS',
        
        # UPCOM (Major)
        'BSR', 'EVE', 'THD', 'AAA', 'KSB', 'BST', 'CSC', 'VTO',
        'LHC', 'TTB', 'KHP', 'PLP', 'QBS', 'SJD'
    ]
    
    # Remove duplicates
    major_tickers = list(set(major_tickers))
    print(f"✅ Using {len(major_tickers)} major tickers")
    
    return major_tickers


def download_eod_prices():
    """
    Download EOD prices for all tickers
    Returns: filepath of created JSON file
    """
    print("\n" + "="*70)
    print("📥 DOWNLOAD EOD PRICES")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    stock_api = Vnstock()
    
    # Get tickers
    all_tickers = get_all_tickers()
    
    if not all_tickers:
        print("❌ No tickers found!")
        return None
    
    print(f"\n🎯 Downloading prices for {len(all_tickers)} tickers")
    print("⏰ Estimated time: {:.1f} minutes\n".format(len(all_tickers) * 1.5 / 60))
    
    # Download prices
    prices_data = {}
    success_count = 0
    fail_count = 0
    
    for i, ticker in enumerate(all_tickers, 1):
        try:
            print(f"[{i}/{len(all_tickers)}] {ticker}...", end=' ')
            
            stock = stock_api.stock(symbol=ticker, source='VCI')
            
            price = None
            change_pct = None
            volume = None
            
            # Try intraday first
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
                # CRITICAL FIX: VNStock returns price in thousands (27.3 = 27,300 VND)
                # Multiply by 1000 to get actual price in VND
                actual_price = price * 1000
                
                prices_data[ticker] = {
                    'price': actual_price,
                    'change_percent': change_pct if change_pct else 0.0,
                    'volume': volume if volume else 0
                }
                success_count += 1
                print(f"✅ {actual_price:,.0f} VND" + (f" ({change_pct:+.1f}%)" if change_pct else ""))
            else:
                fail_count += 1
                print("❌")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            fail_count += 1
            print(f"❌ {e}")
            continue
    
    # Save to file
    output_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'total_tickers': len(all_tickers),
        'success_count': success_count,
        'fail_count': fail_count,
        'prices': prices_data
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total tickers: {len(all_tickers)}")
    print(f"Success: {success_count} ✅")
    print(f"Failed: {fail_count} ❌")
    print(f"Success rate: {success_count/len(all_tickers)*100:.1f}%")
    print(f"\n📁 Saved to: {OUTPUT_FILE}")
    print(f"📊 File size: {os.path.getsize(OUTPUT_FILE)/1024:.1f} KB")
    print("="*70 + "\n")
    
    return OUTPUT_FILE


if __name__ == '__main__':
    download_eod_prices()
