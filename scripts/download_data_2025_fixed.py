#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD DỮ LIỆU 2025 - FIXED VERSION
Hỗ trợ nhiều phương thức download (fallback)
"""

from datetime import datetime
import pandas as pd
import pickle
import time
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_FOLDER = "data_2025"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

START_DATE = "2025-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

CHECKPOINT_INTERVAL = 50

print("="*70)
print("DOWNLOAD DỮ LIỆU 2025 - FIXED VERSION")
print("="*70)
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Output: {OUTPUT_FOLDER}/")
print("="*70)

# ============================================================================
# DETECT WORKING DOWNLOAD METHOD
# ============================================================================

def detect_working_method():
    """
    Tự động detect method nào hoạt động
    """
    print("\n🔍 Detecting working download method...")
    
    test_symbol = 'VNM'
    
    # Method 1: Classic Vnstock
    try:
        print("\n[1/5] Testing: Vnstock().quote.history()...")
        from vnstock import Vnstock
        stock = Vnstock(test_symbol)
        df = stock.quote.history(start=START_DATE, end=END_DATE, interval='1D')
        if df is not None and len(df) > 0:
            print(f"✅ Method 1 works! Got {len(df)} rows")
            return 1, lambda ticker: download_method1(ticker)
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: New Vnstock API
    try:
        print("\n[2/5] Testing: Vnstock().stock().quote.history()...")
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=test_symbol, source='VCI')
        df = stock.quote.history(start=START_DATE, end=END_DATE)
        if df is not None and len(df) > 0:
            print(f"✅ Method 2 works! Got {len(df)} rows")
            return 2, lambda ticker: download_method2(ticker)
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: stock_historical_data function
    try:
        print("\n[3/5] Testing: stock_historical_data()...")
        from vnstock import stock_historical_data
        df = stock_historical_data(symbol=test_symbol, start_date=START_DATE, end_date=END_DATE)
        if df is not None and len(df) > 0:
            print(f"✅ Method 3 works! Got {len(df)} rows")
            return 3, lambda ticker: download_method3(ticker)
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    # Method 4: Vnstock3
    try:
        print("\n[4/5] Testing: Vnstock3()...")
        from vnstock3 import Vnstock as Vnstock3
        stock = Vnstock3(symbol=test_symbol, source='VCI')
        df = stock.quote.history(start=START_DATE, end=END_DATE)
        if df is not None and len(df) > 0:
            print(f"✅ Method 4 works! Got {len(df)} rows")
            return 4, lambda ticker: download_method4(ticker)
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
    
    # Method 5: Alternative API (ssi-fc)
    try:
        print("\n[5/5] Testing: SSI Fast Connect...")
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=test_symbol, source='TCBS')  # Try different source
        df = stock.quote.history(start=START_DATE, end=END_DATE)
        if df is not None and len(df) > 0:
            print(f"✅ Method 5 works! Got {len(df)} rows")
            return 5, lambda ticker: download_method5(ticker)
    except Exception as e:
        print(f"❌ Method 5 failed: {e}")
    
    return None, None


# ============================================================================
# DOWNLOAD METHODS
# ============================================================================

def download_method1(ticker):
    """Method 1: Classic Vnstock"""
    from vnstock import Vnstock
    stock = Vnstock(ticker)
    df = stock.quote.history(start=START_DATE, end=END_DATE, interval='1D')
    return df


def download_method2(ticker):
    """Method 2: New Vnstock API with source"""
    from vnstock import Vnstock
    stock = Vnstock().stock(symbol=ticker, source='VCI')
    df = stock.quote.history(start=START_DATE, end=END_DATE)
    return df


def download_method3(ticker):
    """Method 3: stock_historical_data function"""
    from vnstock import stock_historical_data
    df = stock_historical_data(symbol=ticker, start_date=START_DATE, end_date=END_DATE)
    return df


def download_method4(ticker):
    """Method 4: Vnstock3"""
    from vnstock3 import Vnstock as Vnstock3
    stock = Vnstock3(symbol=ticker, source='VCI')
    df = stock.quote.history(start=START_DATE, end=END_DATE)
    return df


def download_method5(ticker):
    """Method 5: Alternative source TCBS"""
    from vnstock import Vnstock
    stock = Vnstock().stock(symbol=ticker, source='TCBS')
    df = stock.quote.history(start=START_DATE, end=END_DATE)
    return df


def standardize_dataframe(df, ticker):
    """
    Chuẩn hóa DataFrame về format thống nhất
    """
    if df is None or len(df) == 0:
        return None
    
    df = df.copy()
    
    # Standardize column names (lowercase)
    df.columns = [col.lower() for col in df.columns]
    
    # Map common variations
    column_map = {
        'date': 'time',
        'datetime': 'time',
        'ticker': 'ticker',
        'symbol': 'ticker',
        'code': 'ticker'
    }
    
    for old, new in column_map.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    
    # Add ticker if not present
    if 'ticker' not in df.columns:
        df['ticker'] = ticker
    
    # Ensure required columns
    required = ['time', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            print(f"   ⚠️ Missing column: {col}")
            return None
    
    # Select and reorder
    df = df[['ticker'] + required]
    
    # Convert time to datetime
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])
    
    # Sort by time
    df = df.sort_values('time').reset_index(drop=True)
    
    return df


# ============================================================================
# LOAD STOCK LIST
# ============================================================================

def load_stock_list():
    """Load stock list from existing data"""
    print("\n📂 Loading stock list...")
    
    # Try to load from existing PKL
    data_folder = "data"
    if os.path.exists(data_folder):
        pkl_files = [f for f in os.listdir(data_folder) if f.endswith('.pkl')]
        
        if len(pkl_files) > 0:
            all_tickers = set()
            for pkl_file in pkl_files[:3]:  # Check first 3 files
                try:
                    with open(os.path.join(data_folder, pkl_file), 'rb') as f:
                        data = pickle.load(f)
                    if isinstance(data, dict):
                        all_tickers.update(data.keys())
                except:
                    pass
            
            if len(all_tickers) > 0:
                tickers = sorted(list(all_tickers))
                print(f"✅ Loaded {len(tickers)} stocks from PKL files")
                return tickers
    
    # Fallback: Manual list of top liquid stocks
    print("⚠️ Could not load from PKL, using default list...")
    
    default_tickers = [
        'VNM', 'VIC', 'VHM', 'HPG', 'TCB', 'VCB', 'BID', 'CTG', 'MBB', 'VPB',
        'MSN', 'VJC', 'GAS', 'PLX', 'SSI', 'HDB', 'VRE', 'NVL', 'POW', 'FPT',
        'SAB', 'MWG', 'ACB', 'TPB', 'STB', 'SHB', 'DIG', 'DXG', 'HCM', 'VPI',
        # Add more as needed
    ]
    
    print(f"✅ Using default list: {len(default_tickers)} stocks")
    return default_tickers


# ============================================================================
# MAIN DOWNLOAD
# ============================================================================

def main():
    """Main download function"""
    
    # Detect working method
    method_num, download_func = detect_working_method()
    
    if download_func is None:
        print("\n❌ CRITICAL: No working download method found!")
        print("\nPossible solutions:")
        print("1. Update vnstock: pip install --upgrade vnstock")
        print("2. Try vnstock3: pip install vnstock3")
        print("3. Check internet connection")
        print("4. Check https://vnstocks.com for latest version")
        return
    
    print(f"\n✅ Using Method {method_num} for download")
    
    # Load stock list
    tickers = load_stock_list()
    
    # Confirm
    print(f"\n{'='*70}")
    print(f"READY TO DOWNLOAD")
    print(f"{'='*70}")
    print(f"Stocks: {len(tickers)}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Method: {method_num}")
    print(f"Est. time: {len(tickers) * 1.5 / 60:.0f} minutes")
    print(f"{'='*70}")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Cancelled")
        return
    
    # Download
    print(f"\n📥 Starting download...\n")
    
    all_data = {}
    success_count = 0
    failed_stocks = []
    
    start_time = time.time()
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        try:
            df = download_func(ticker)
            df = standardize_dataframe(df, ticker)
            
            if df is not None and len(df) > 0:
                all_data[ticker] = df
                success_count += 1
                print(f"✅ {len(df)} rows")
            else:
                failed_stocks.append(ticker)
                print("❌ No data")
        
        except Exception as e:
            failed_stocks.append(ticker)
            print(f"❌ Error: {e}")
        
        # Checkpoint
        if i % CHECKPOINT_INTERVAL == 0:
            checkpoint_file = f"{OUTPUT_FOLDER}/checkpoint_2025_{i}.pkl"
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(all_data, f)
            print(f"   💾 Checkpoint saved: {i} stocks")
        
        # Rate limit
        time.sleep(1.5)
    
    # Save final
    print(f"\n{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*70}")
    
    final_file = f"{OUTPUT_FOLDER}/data_2025_complete.pkl"
    with open(final_file, 'wb') as f:
        pickle.dump(all_data, f)
    
    print(f"✅ Saved: {final_file}")
    print(f"   Stocks: {success_count}/{len(tickers)} ({success_count/len(tickers)*100:.1f}%)")
    
    if len(failed_stocks) > 0:
        print(f"\n⚠️ Failed: {len(failed_stocks)} stocks")
        print(", ".join(failed_stocks[:20]))
        
        failed_file = f"{OUTPUT_FOLDER}/failed_stocks.txt"
        with open(failed_file, 'w') as f:
            for ticker in failed_stocks:
                f.write(f"{ticker}\n")
    
    total_time = time.time() - start_time
    print(f"\nTotal time: {total_time/60:.1f} minutes")
    print(f"File size: {os.path.getsize(final_file)/1024/1024:.1f} MB")
    
    print("\n✅ Ready to backtest!")


if __name__ == "__main__":
    main()
