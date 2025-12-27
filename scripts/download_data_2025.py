#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD DỮ LIỆU 2025 - 343 STOCKS
Owner: Nguyễn Thanh Sơn

Download dữ liệu năm 2025 (YTD) cho 343 mã thanh khoản >100k/ngày
Để backtest offline cho 4 strategies
"""

from vnstock import Vnstock
import pandas as pd
import pickle
import time
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output folder
OUTPUT_FOLDER = "data_2025"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Date range for 2025
START_DATE = "2025-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# Checkpoint settings
CHECKPOINT_INTERVAL = 50  # Save every 50 stocks
RESUME_FROM_CHECKPOINT = True  # Continue from last checkpoint

print("="*70)
print("DOWNLOAD DỮ LIỆU NĂM 2025")
print("="*70)
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Output: {OUTPUT_FOLDER}/")
print("="*70)

# ============================================================================
# LOAD STOCK LIST FROM PREVIOUS DATA
# ============================================================================

def load_stock_list_from_pkl():
    """
    Load list of 343 liquid stocks from existing PKL files
    """
    print("\n📂 Loading stock list from existing data...")
    
    data_folder = "data"
    if not os.path.exists(data_folder):
        print(f"❌ Folder not found: {data_folder}")
        print("Please specify the correct path to your existing data folder.")
        data_folder = input("Enter data folder path (or press Enter for 'data'): ").strip()
        if not data_folder:
            data_folder = "data"
    
    # Find PKL files
    pkl_files = [f for f in os.listdir(data_folder) if f.endswith('.pkl')]
    
    if len(pkl_files) == 0:
        print(f"❌ No PKL files found in {data_folder}/")
        return None
    
    all_tickers = set()
    
    for pkl_file in pkl_files:
        try:
            filepath = os.path.join(data_folder, pkl_file)
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            if isinstance(data, dict):
                all_tickers.update(data.keys())
                print(f"   ✅ {pkl_file}: {len(data)} stocks")
        except Exception as e:
            print(f"   ⚠️ {pkl_file}: Error - {e}")
    
    tickers = sorted(list(all_tickers))
    print(f"\n✅ Total stocks found: {len(tickers)}")
    
    # Save list to file
    list_file = f"{OUTPUT_FOLDER}/stock_list_343.txt"
    with open(list_file, 'w') as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    
    print(f"✅ Stock list saved to: {list_file}")
    
    return tickers


def load_stock_list_manual():
    """
    Manual stock list input if PKL files not available
    """
    print("\n📝 Manual stock list input...")
    print("Enter stock codes (comma-separated or from file)")
    print("Example: VNM,HPG,VCB,TCB,...")
    
    choice = input("\n1. Enter codes manually\n2. Load from file\nChoice (1/2): ").strip()
    
    if choice == "1":
        codes = input("Enter stock codes: ").strip()
        tickers = [c.strip().upper() for c in codes.split(',')]
    else:
        filepath = input("Enter file path: ").strip()
        with open(filepath, 'r') as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
    
    print(f"✅ Loaded {len(tickers)} stocks")
    return tickers


# ============================================================================
# DOWNLOAD FUNCTIONS
# ============================================================================

def download_stock_2025(ticker, retries=3):
    """
    Download 2025 data for one stock
    
    Args:
        ticker: Stock code
        retries: Number of retry attempts
    
    Returns:
        DataFrame or None
    """
    for attempt in range(retries):
        try:
            stock = Vnstock(ticker)
            
            df = stock.quote.history(
                start=START_DATE,
                end=END_DATE,
                interval='1D'
            )
            
            if df is None or len(df) == 0:
                return None
            
            # Standardize columns
            df['ticker'] = ticker
            
            # Reorder
            required_cols = ['ticker', 'time', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in required_cols if col in df.columns]]
            
            return df
        
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            else:
                return None
    
    return None


def find_last_checkpoint():
    """
    Find last checkpoint to resume from
    """
    checkpoints = [f for f in os.listdir(OUTPUT_FOLDER) 
                   if f.startswith('checkpoint_2025_') and f.endswith('.pkl')]
    
    if len(checkpoints) == 0:
        return None, 0
    
    # Get latest checkpoint
    checkpoints.sort()
    latest = checkpoints[-1]
    
    # Extract count
    count = int(latest.split('_')[2].split('.')[0])
    
    return os.path.join(OUTPUT_FOLDER, latest), count


def save_checkpoint(data, count):
    """
    Save checkpoint
    """
    filename = f"{OUTPUT_FOLDER}/checkpoint_2025_{count}.pkl"
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"   💾 Checkpoint saved: {filename}")


def load_checkpoint(filepath):
    """
    Load checkpoint
    """
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data


# ============================================================================
# MAIN DOWNLOAD
# ============================================================================

def main():
    """
    Main download function
    """
    # Load stock list
    tickers = load_stock_list_from_pkl()
    
    if tickers is None:
        print("\n⚠️ Could not load from PKL files.")
        use_manual = input("Load manually? (y/n): ").strip().lower()
        if use_manual == 'y':
            tickers = load_stock_list_manual()
        else:
            print("❌ Cancelled")
            return
    
    # Check for checkpoint
    all_data = {}
    start_index = 0
    
    if RESUME_FROM_CHECKPOINT:
        checkpoint_file, checkpoint_count = find_last_checkpoint()
        if checkpoint_file:
            print(f"\n📂 Found checkpoint: {checkpoint_count} stocks")
            resume = input("Resume from checkpoint? (y/n): ").strip().lower()
            if resume == 'y':
                all_data = load_checkpoint(checkpoint_file)
                start_index = checkpoint_count
                print(f"✅ Resumed from {checkpoint_count} stocks")
    
    # Confirm download
    remaining = len(tickers) - start_index
    print(f"\n{'='*70}")
    print(f"READY TO DOWNLOAD")
    print(f"{'='*70}")
    print(f"Total stocks: {len(tickers)}")
    print(f"Already done: {start_index}")
    print(f"Remaining: {remaining}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Est. time: {remaining * 1.5 / 60:.0f} minutes")
    print(f"{'='*70}")
    
    proceed = input("\nProceed with download? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Cancelled")
        return
    
    # Download
    print(f"\n📥 Starting download...\n")
    
    success_count = 0
    failed_stocks = []
    
    start_time = time.time()
    
    for i, ticker in enumerate(tickers[start_index:], start=start_index+1):
        print(f"[{i}/{len(tickers)}] Downloading {ticker}...", end=" ")
        
        df = download_stock_2025(ticker)
        
        if df is not None and len(df) > 0:
            all_data[ticker] = df
            success_count += 1
            print(f"✅ {len(df)} rows")
        else:
            failed_stocks.append(ticker)
            print(f"❌ No data")
        
        # Save checkpoint
        if i % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(all_data, i)
        
        # Rate limit
        time.sleep(1.5)
        
        # Progress
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60
            remaining_time = (len(tickers) - i) / rate
            print(f"   ⏱️  Progress: {i}/{len(tickers)} ({i/len(tickers)*100:.1f}%), "
                  f"Rate: {rate:.1f} stocks/min, "
                  f"ETA: {remaining_time:.0f} min")
    
    # Save final
    print(f"\n{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*70}")
    
    final_file = f"{OUTPUT_FOLDER}/data_2025_complete.pkl"
    with open(final_file, 'wb') as f:
        pickle.dump(all_data, f)
    
    print(f"✅ Final data saved: {final_file}")
    print(f"   Total stocks: {success_count}/{len(tickers)}")
    print(f"   Success rate: {success_count/len(tickers)*100:.1f}%")
    
    # Failed stocks
    if len(failed_stocks) > 0:
        print(f"\n⚠️ Failed stocks ({len(failed_stocks)}):")
        print(", ".join(failed_stocks))
        
        failed_file = f"{OUTPUT_FOLDER}/failed_stocks.txt"
        with open(failed_file, 'w') as f:
            for ticker in failed_stocks:
                f.write(f"{ticker}\n")
        print(f"✅ Failed list saved: {failed_file}")
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Stocks downloaded: {success_count:,}")
    print(f"Avg rows per stock: {sum(len(df) for df in all_data.values())/len(all_data):.0f}")
    print(f"Total data points: {sum(len(df) for df in all_data.values()):,}")
    print(f"File size: {os.path.getsize(final_file)/1024/1024:.1f} MB")
    print(f"{'='*70}")
    
    print(f"\n✅ Ready to backtest!")
    print(f"Run: python backtest_4strategies_PKL.py")


# ============================================================================
# VERIFY FUNCTION
# ============================================================================

def verify_downloaded_data():
    """
    Verify downloaded data
    """
    print("="*70)
    print("VERIFY DOWNLOADED DATA")
    print("="*70)
    
    final_file = f"{OUTPUT_FOLDER}/data_2025_complete.pkl"
    
    if not os.path.exists(final_file):
        print("❌ No data file found!")
        return
    
    # Load
    with open(final_file, 'rb') as f:
        data = pickle.load(f)
    
    print(f"✅ Loaded {len(data)} stocks")
    
    # Check each stock
    print("\nSample data (first 5 stocks):")
    for i, (ticker, df) in enumerate(list(data.items())[:5]):
        print(f"\n{ticker}:")
        print(f"  Rows: {len(df)}")
        print(f"  Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Sample:\n{df.head(2)}")
    
    # Statistics
    total_rows = sum(len(df) for df in data.values())
    avg_rows = total_rows / len(data)
    
    print(f"\n{'='*70}")
    print("STATISTICS")
    print(f"{'='*70}")
    print(f"Total stocks: {len(data)}")
    print(f"Total rows: {total_rows:,}")
    print(f"Avg rows/stock: {avg_rows:.1f}")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Trading days: ~{avg_rows:.0f} days")
    
    # Check for missing data
    stocks_with_data = []
    stocks_no_data = []
    
    for ticker, df in data.items():
        if len(df) > 10:  # At least 10 days
            stocks_with_data.append(ticker)
        else:
            stocks_no_data.append(ticker)
    
    print(f"\nData quality:")
    print(f"  Good data: {len(stocks_with_data)} stocks")
    print(f"  Insufficient: {len(stocks_no_data)} stocks")
    
    if len(stocks_no_data) > 0:
        print(f"\n⚠️ Stocks with insufficient data:")
        print(", ".join(stocks_no_data))


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_downloaded_data()
    else:
        main()
