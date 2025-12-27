#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD HISTORICAL DATA FOR ALL STOCKS

Download 5 years of data for 700+ stocks with liquidity > 300k/day
Save to local files for offline backtesting
"""

import sys
import os
import io
import time
from datetime import datetime, timedelta
import pandas as pd
import pickle

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Suppress VNStock ads
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

original_stdout = sys.stdout
sys.stdout = NullWriter()

from vnstock import Vnstock

sys.stdout = original_stdout


def get_all_stock_codes():
    """
    Get list of all stocks from HOSE, HNX, UPCOM
    Filter by liquidity > 300k shares/day average
    """
    
    print("📊 Getting list of all Vietnamese stocks...")
    
    try:
        # Get stock list from vnstock
        stock = Vnstock().stock(symbol='ACB', source='VCI')
        
        # Get all symbols (this is a placeholder - vnstock may have different method)
        # You might need to manually provide a list of symbols
        # For now, let's use comprehensive list
        
        all_codes = []
        
        # HOSE stocks (biggest exchange)
        hose_codes = [
            # Large caps
            'VIC', 'VHM', 'VNM', 'HPG', 'MSN', 'VCB', 'MBB', 'TCB', 'BID', 'CTG',
            'VPB', 'ACB', 'HDB', 'TPB', 'STB', 'SHB', 'MWG', 'FPT', 'GAS', 'PLX',
            'VJC', 'SSI', 'VRE', 'VCI', 'POW', 'GVR', 'NVL', 'REE', 'DGC', 'PHR',
            'DPM', 'DXG', 'NT2', 'PVD', 'PVS', 'PVT', 'VHC', 'DCM', 'GMD', 'SAB',
            
            # Mid caps  
            'VIB', 'SSB', 'BCM', 'BVH', 'PDR', 'VGC', 'KDH', 'NLG', 'DIG', 'CII',
            'TCH', 'CTD', 'HDG', 'LGC', 'HBC', 'DVP', 'PC1', 'DHG', 'DMC', 'DRC',
            'FTS', 'VND', 'HCM', 'SZL', 'HDC', 'HT1', 'IDC', 'PAN', 'GEG', 'TDM',
            'BWE', 'EVF', 'ORS', 'AGR', 'VOS', 'HAH', 'VNA', 'PVG', 'VSH', 'GEX',
            'HAG', 'BMP', 'TRA', 'IMP', 'ANV', 'NKG', 'HSG', 'DBC', 'GEE', 'CMG',
            'FRT', 'DGW', 'PET', 'CTR', 'SCS', 'VCG', 'PVT', 'BSI', 'CTS', 'VIX',
            
            # Additional
            'BCC', 'CHP', 'CSV', 'DHA', 'DTL', 'FLC', 'HNG', 'HQC', 'HTN', 'KBC',
            'KDC', 'L10', 'MCH', 'MCP', 'NHA', 'NSC', 'PPC', 'QCG', 'SAM', 'SBT',
            'SCR', 'SJS', 'THG', 'TIP', 'TLG', 'TMP', 'TNH', 'TVB', 'VCS', 'VHG',
            'VIE', 'VPI', 'VTO', 'YEG'
        ]
        
        # HNX stocks (second largest)
        hnx_codes = [
            'PVS', 'NVB', 'CEO', 'SHN', 'PVI', 'DTD', 'VCS', 'TNG', 'NHH', 'TIG',
            'VGS', 'VC3', 'PVX', 'PVB', 'THD', 'TV3', 'NDN', 'SRA', 'MBS', 'HUT',
            'PAN', 'TDG', 'VCG', 'LAS', 'DST', 'PLC', 'NET', 'DP3', 'IDV', 'NGC',
            'VMC', 'TDN', 'HTP', 'API', 'TS4', 'DNP', 'PGS', 'VE8', 'PTB', 'PSW'
        ]
        
        # UPCOM stocks (smaller companies)
        upcom_codes = [
            'BSI', 'ACB', 'FTS', 'BVB', 'WIN', 'SFI', 'INN', 'CNC', 'NKG', 'VCC',
            'AAM', 'BFC', 'CTW', 'DL1', 'HGW', 'IBC', 'KSH', 'LTG', 'PTC', 'RCL',
            'SEB', 'SFG', 'TCO', 'VE1', 'VE2', 'VE3', 'VE4', 'VE9'
        ]
        
        all_codes = list(set(hose_codes + hnx_codes + upcom_codes))
        
        print(f"✅ Found {len(all_codes)} stock codes")
        return all_codes
        
    except Exception as e:
        print(f"❌ Error getting stock list: {e}")
        # Fallback: use VN100 + common stocks
        return [
            'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
            'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'REE', 'SAB', 'SHB', 'SSB', 'SSI',
            'STB', 'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB'
        ]


def download_stock_data(code, start_date, end_date, timeframe='1D', delay=2):
    """
    Download historical data for a single stock
    
    Args:
        code: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: '1D' for daily, '1H' for hourly
        delay: Delay between requests (seconds)
    
    Returns:
        DataFrame with OHLCV data
    """
    
    try:
        time.sleep(delay)  # Rate limiting
        
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        if timeframe == '1D':
            # Daily data
            df = stock.quote.history(
                symbol=code,
                start=start_date,
                end=end_date
            )
        elif timeframe == '1H':
            # Hourly/intraday data
            # Note: VCI typically provides last 30-90 days of intraday data
            df = stock.quote.intraday(
                symbol=code,
                page_size=5000  # Get maximum data
            )
            
            if not df.empty:
                # Filter by date range
                df = df[(df.index >= start_date) & (df.index <= end_date)]
        else:
            print(f"❌ Invalid timeframe: {timeframe}", file=sys.stderr)
            return None
        
        if df.empty:
            return None
        
        # Calculate average volume
        df['avg_volume'] = df['volume'].rolling(window=20).mean()
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading {code}: {e}", file=sys.stderr)
        return None


def filter_by_liquidity(df, min_volume=300000):
    """
    Check if stock meets liquidity requirement
    
    Args:
        df: Stock data
        min_volume: Minimum average daily volume (shares)
    
    Returns:
        bool: True if meets requirement
    """
    if df is None or df.empty:
        return False
    
    # Calculate average volume over entire period
    avg_vol = df['volume'].mean()
    
    return avg_vol >= min_volume


def save_data(data_dict, filename='stock_data_5y.pkl'):
    """Save downloaded data to pickle file"""
    
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data_dict, f)
    
    print(f"\n✅ Data saved to: {filepath}")
    print(f"   Total stocks: {len(data_dict)}")
    print(f"   File size: {os.path.getsize(filepath) / 1024 / 1024:.2f} MB")


def main():
    """Main download function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Download stock data')
    parser.add_argument('--timeframe', type=str, default='1D', 
                       choices=['1D', '1H', 'both'],
                       help='Timeframe: 1D (daily), 1H (hourly), or both')
    parser.add_argument('--years', type=int, default=5,
                       help='Number of years to download (default: 5)')
    
    args = parser.parse_args()
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.years*365)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print("=" * 70)
    print("📥 DOWNLOADING STOCK DATA")
    print("=" * 70)
    print(f"Timeframe: {args.timeframe}")
    print(f"Period: {start_str} to {end_str} ({args.years} years)")
    print(f"Filter: Average volume > 300,000 shares/day")
    print("=" * 70)
    print()
    
    # Get stock list
    all_codes = get_all_stock_codes()
    
    if args.timeframe == 'both':
        timeframes = ['1D', '1H']
    else:
        timeframes = [args.timeframe]
    
    for tf in timeframes:
        print(f"\n{'='*70}")
        print(f"📊 Downloading {tf} data for {len(all_codes)} stocks...")
        
        if tf == '1H':
            print("⚠️  Note: Intraday data typically limited to last 30-90 days")
            # Adjust date range for intraday
            start_str_intraday = (end_date - timedelta(days=90)).strftime('%Y-%m-%d')
        else:
            start_str_intraday = start_str
        
        print("⏰ Estimated time: {:.0f} minutes".format(len(all_codes) * 2 / 60))
        print("=" * 70)
        print()
        
        # Download data
        stock_data = {}
        liquid_stocks = []
        failed_stocks = []
        low_liquidity = []
        
        for i, code in enumerate(all_codes, 1):
            print(f"\n[{i}/{len(all_codes)}] Downloading {code} ({tf})...", end=' ')
            
            df = download_stock_data(
                code, 
                start_str_intraday if tf == '1H' else start_str, 
                end_str, 
                timeframe=tf,
                delay=2
            )
            
            if df is None:
                print("❌ Failed")
                failed_stocks.append(code)
                continue
            
            # Check liquidity
            if filter_by_liquidity(df, min_volume=300000):
                stock_data[code] = df
                liquid_stocks.append(code)
                avg_vol = df['volume'].mean()
                print(f"✅ OK (Avg vol: {avg_vol:,.0f}, Bars: {len(df)})")
            else:
                avg_vol = df['volume'].mean()
                print(f"⚠️  Low liquidity (Avg vol: {avg_vol:,.0f})")
                low_liquidity.append(code)
            
            # Save checkpoint every 50 stocks
            if i % 50 == 0:
                filename = f'stock_data_{tf}_checkpoint_{i}.pkl'
                save_data(stock_data, filename)
                print(f"\n💾 Checkpoint saved: {len(stock_data)} stocks so far")
        
        # Final save
        filename = f'stock_data_{args.years}y_{tf}.pkl'
        save_data(stock_data, filename)
        
        # Summary
        print("\n" + "=" * 70)
        print(f"✅ {tf} DOWNLOAD COMPLETE!")
        print("=" * 70)
        print(f"Total attempted: {len(all_codes)}")
        print(f"✅ Success (liquid): {len(liquid_stocks)}")
        print(f"⚠️  Low liquidity: {len(low_liquidity)}")
        print(f"❌ Failed: {len(failed_stocks)}")
        print()
        
        if liquid_stocks:
            print(f"📊 Liquid stocks saved ({len(liquid_stocks)}):")
            for code in sorted(liquid_stocks)[:20]:  # Show first 20
                vol = stock_data[code]['volume'].mean()
                bars = len(stock_data[code])
                print(f"   {code}: {vol:,.0f} shares/day, {bars} bars")
            if len(liquid_stocks) > 20:
                print(f"   ... and {len(liquid_stocks)-20} more")
        
        print()
    
    print("=" * 70)
    print("🎊 ALL DOWNLOADS COMPLETE!")
    print("=" * 70)
    
    if args.timeframe == 'both':
        print("📁 Daily data: data/stock_data_{}_y_1D.pkl".format(args.years))
        print("📁 Hourly data: data/stock_data_{}_y_1H.pkl".format(args.years))
    else:
        print("📁 Data saved to: data/stock_data_{}_y_{}.pkl".format(args.years, args.timeframe))
    
    print("🚀 Ready for offline backtesting!")
    print("=" * 70)


if __name__ == '__main__':
    main()
