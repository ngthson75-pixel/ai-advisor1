#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD DATA FROM LIQUID STOCKS LIST

Reads liquid stocks list and downloads full history
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


def read_stock_list(filepath):
    """Read stock codes from liquid_stocks_list.txt"""
    
    print(f"\n📂 Reading stock list from: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return []
    
    stocks = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse: "CODE\tVOLUME" format
            parts = line.split('\t')
            if parts:
                code = parts[0].strip().upper()
                if code and len(code) <= 5:
                    stocks.append(code)
    
    print(f"✅ Loaded {len(stocks)} stock codes")
    
    if stocks:
        print(f"   First 10: {', '.join(stocks[:10])}")
        print(f"   Last 10: {', '.join(stocks[-10:])}")
    
    return stocks


def download_stock_data(code, start_date, end_date, timeframe='1D', delay=2):
    """Download historical data for a single stock"""
    
    try:
        time.sleep(delay)
        
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        if timeframe == '1D':
            df = stock.quote.history(
                symbol=code,
                start=start_date,
                end=end_date
            )
        elif timeframe == '1H':
            df = stock.quote.intraday(symbol=code, page_size=5000)
            if not df.empty:
                df = df[(df.index >= start_date) & (df.index <= end_date)]
        else:
            return None
        
        if df.empty:
            return None
        
        # Calculate indicators
        df['avg_volume'] = df['volume'].rolling(window=20).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}", file=sys.stderr)
        return None


def save_data(data_dict, filename):
    """Save data to pickle file"""
    
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data_dict, f)
    
    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"\n💾 Saved: {filepath} ({size_mb:.1f} MB)")
    
    return filepath


def main():
    """Main download function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Download liquid stocks data')
    parser.add_argument('--list-file', type=str, 
                       default='data/liquid_stocks_list.txt',
                       help='Path to liquid stocks list file')
    parser.add_argument('--timeframe', type=str, default='1D',
                       choices=['1D', '1H', 'both'],
                       help='Timeframe (default: 1D)')
    parser.add_argument('--years', type=int, default=5,
                       help='Years of history (default: 5)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests (default: 2s)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📥 DOWNLOAD LIQUID STOCKS DATA")
    print("=" * 70)
    
    # Read stock list
    stock_codes = read_stock_list(args.list_file)
    
    if not stock_codes:
        print("❌ No stock codes found!")
        return
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.years*365)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\nPeriod: {start_str} to {end_str} ({args.years} years)")
    print(f"Timeframe: {args.timeframe}")
    print(f"Stocks: {len(stock_codes)}")
    print(f"Delay: {args.delay}s per request")
    print("=" * 70)
    
    # Determine timeframes
    if args.timeframe == 'both':
        timeframes = ['1D', '1H']
    else:
        timeframes = [args.timeframe]
    
    # Download for each timeframe
    for tf in timeframes:
        print(f"\n{'='*70}")
        print(f"📊 DOWNLOADING {tf} DATA")
        print("=" * 70)
        
        if tf == '1H':
            print("⚠️  Note: Intraday data limited to ~90 days")
            start_str_tf = (end_date - timedelta(days=90)).strftime('%Y-%m-%d')
        else:
            start_str_tf = start_str
        
        est_time = len(stock_codes) * args.delay / 60
        print(f"⏰ Estimated time: {est_time:.0f} minutes")
        print("=" * 70)
        print()
        
        stock_data = {}
        success = []
        failed = []
        
        for i, code in enumerate(stock_codes, 1):
            print(f"[{i}/{len(stock_codes)}] {code}...", end=' ')
            
            df = download_stock_data(code, start_str_tf, end_str, tf, args.delay)
            
            if df is None or df.empty:
                print("❌")
                failed.append(code)
            else:
                stock_data[code] = df
                success.append(code)
                print(f"✅ {len(df)} bars")
            
            # Checkpoint every 50
            if i % 50 == 0:
                checkpoint_file = f'liquid_stocks_{tf}_checkpoint_{i}.pkl'
                save_data(stock_data, checkpoint_file)
                print(f"\n💾 Checkpoint: {len(stock_data)} stocks saved\n")
        
        # Final save
        final_file = f'liquid_stocks_{args.years}y_{tf}.pkl'
        filepath = save_data(stock_data, final_file)
        
        # Summary
        print("\n" + "=" * 70)
        print(f"✅ {tf} DOWNLOAD COMPLETE")
        print("=" * 70)
        print(f"Total: {len(stock_codes)}")
        print(f"✅ Success: {len(success)} ({len(success)/len(stock_codes)*100:.1f}%)")
        print(f"❌ Failed: {len(failed)} ({len(failed)/len(stock_codes)*100:.1f}%)")
        print(f"📁 File: {filepath}")
        print("=" * 70)
        
        if success:
            print(f"\n📊 Sample data (first 10 stocks):")
            for code in success[:10]:
                df = stock_data[code]
                print(f"   {code}: {len(df)} bars, "
                      f"{df.index[0]} to {df.index[-1]}")
    
    print("\n" + "=" * 70)
    print("🎊 ALL DOWNLOADS COMPLETE!")
    print("=" * 70)
    print(f"✅ Downloaded {len(success)} stocks")
    print(f"📁 Data ready for backtesting!")
    print("🚀 Next: Run offline_backtest.py")
    print("=" * 70)


if __name__ == '__main__':
    main()
