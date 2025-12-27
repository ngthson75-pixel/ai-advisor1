#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOWNLOAD DỮ LIỆU 2025 - FINAL WORKING VERSION
Based on vnstock diagnostics - Method 2 confirmed working
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

OUTPUT_FOLDER = "data_2025"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

START_DATE = "2025-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

CHECKPOINT_INTERVAL = 50

print("="*70)
print("DOWNLOAD DỮ LIỆU 2025 - WORKING VERSION")
print("="*70)
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Output: {OUTPUT_FOLDER}/")
print(f"Method: Vnstock().stock(symbol, source='VCI').quote.history()")
print("="*70)

# ============================================================================
# DOWNLOAD FUNCTION
# ============================================================================

def download_stock_2025(ticker, retries=3):
    """
    Download 2025 data using working Method 2
    """
    for attempt in range(retries):
        try:
            # Method 2: Confirmed working
            stock = Vnstock().stock(symbol=ticker, source='VCI')
            
            # Try different parameter formats
            # Format 1: start, end
            try:
                df = stock.quote.history(start=START_DATE, end=END_DATE)
            except:
                # Format 2: start_date, end_date
                try:
                    df = stock.quote.history(start_date=START_DATE, end_date=END_DATE)
                except:
                    # Format 3: No params (get all available)
                    df = stock.quote.history()
                    if df is not None and len(df) > 0:
                        # Filter by date
                        df['time'] = pd.to_datetime(df['time'])
                        df = df[(df['time'] >= START_DATE) & (df['time'] <= END_DATE)]
            
            if df is None or len(df) == 0:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None
            
            # Standardize
            df = df.copy()
            df.columns = [col.lower() for col in df.columns]
            
            # Add ticker
            if 'ticker' not in df.columns and 'symbol' not in df.columns:
                df.insert(0, 'ticker', ticker)
            
            # Ensure time column
            if 'date' in df.columns and 'time' not in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            
            # Convert time
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
            
            # Required columns
            required = ['time', 'open', 'high', 'low', 'close', 'volume']
            for col in required:
                if col not in df.columns:
                    return None
            
            # Select columns
            cols = ['ticker'] if 'ticker' in df.columns else []
            cols += required
            df = df[cols]
            
            # Sort and reset
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
        
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            else:
                return None
    
    return None


# ============================================================================
# LOAD STOCK LIST
# ============================================================================

def load_stock_list():
    """Load stock list from PKL files"""
    print("\n📂 Loading stock list from existing data...")
    
    data_folder = "data"
    if not os.path.exists(data_folder):
        print(f"⚠️ Folder not found: {data_folder}")
        data_folder = input("Enter path to data folder (or press Enter to use default list): ").strip()
        if not data_folder or not os.path.exists(data_folder):
            return get_default_stock_list()
    
    # Load from PKL
    pkl_files = [f for f in os.listdir(data_folder) if f.endswith('.pkl')]
    
    if len(pkl_files) == 0:
        print("⚠️ No PKL files found")
        return get_default_stock_list()
    
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
            print(f"   ⚠️ {pkl_file}: {e}")
    
    if len(all_tickers) == 0:
        return get_default_stock_list()
    
    tickers = sorted(list(all_tickers))
    print(f"\n✅ Total stocks loaded: {len(tickers)}")
    
    # Save list
    list_file = f"{OUTPUT_FOLDER}/stock_list.txt"
    with open(list_file, 'w') as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    print(f"✅ List saved: {list_file}")
    
    return tickers


def get_default_stock_list():
    """Get default stock list using vnstock listing API"""
    print("\n📋 Getting stock list from vnstock API...")
    
    try:
        listing = Vnstock().stock(symbol='VNM', source='VCI').listing.all_symbols()
        
        if listing is not None and len(listing) > 0:
            tickers = listing['symbol'].tolist()
            print(f"✅ Got {len(tickers)} stocks from API")
            
            # Save
            list_file = f"{OUTPUT_FOLDER}/stock_list_all.txt"
            with open(list_file, 'w') as f:
                for ticker in tickers:
                    f.write(f"{ticker}\n")
            
            return tickers
    except Exception as e:
        print(f"⚠️ Could not get from API: {e}")
    
    # Fallback: Manual top stocks
    print("⚠️ Using fallback list (top 100 liquid stocks)")
    
    top_stocks = [
        # Blue chips
        'VNM', 'VIC', 'VHM', 'HPG', 'TCB', 'VCB', 'BID', 'CTG', 'MBB', 'VPB',
        'MSN', 'VJC', 'GAS', 'PLX', 'SSI', 'HDB', 'VRE', 'NVL', 'POW', 'FPT',
        'SAB', 'MWG', 'ACB', 'TPB', 'STB', 'SHB', 'VCI', 'BCM', 'VND', 'PNJ',
        # Mid caps
        'DIG', 'DXG', 'HCM', 'VPI', 'PDR', 'PVD', 'PVT', 'PVS', 'DCM', 'DPM',
        'NT2', 'GMD', 'KDH', 'PC1', 'REE', 'SBT', 'VGC', 'VHC', 'VIB', 'VSH',
        'PVG', 'PVI', 'EVE', 'ITA', 'BWE', 'CMG', 'DRC', 'GEX', 'HAG', 'HNG',
        # More liquid stocks
        'CSV', 'TCO', 'NDN', 'TIG', 'TC6', 'DL1', 'SCR', 'BMP', 'ITC', 'AGR',
        'YEG', 'VTP', 'SGR', 'ASM', 'HQC', 'MCH', 'JVC', 'EVG', 'CSM', 'VGT',
        'PC1', 'IDI', 'PSD', 'SZC', 'VCS', 'HVN', 'SCS', 'VGS', 'DBC', 'DHC',
        'CEO', 'SVC', 'FIT', 'KBC', 'VNE', 'HAX', 'BSI', 'DGW', 'TLG', 'HDG'
    ]
    
    return top_stocks


# ============================================================================
# CHECKPOINT FUNCTIONS
# ============================================================================

def find_last_checkpoint():
    """Find latest checkpoint"""
    checkpoints = [f for f in os.listdir(OUTPUT_FOLDER) 
                   if f.startswith('checkpoint_2025_') and f.endswith('.pkl')]
    
    if len(checkpoints) == 0:
        return None, 0
    
    checkpoints.sort()
    latest = checkpoints[-1]
    count = int(latest.split('_')[2].split('.')[0])
    
    return os.path.join(OUTPUT_FOLDER, latest), count


def save_checkpoint(data, count):
    """Save checkpoint"""
    filename = f"{OUTPUT_FOLDER}/checkpoint_2025_{count}.pkl"
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    return filename


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main download function"""
    
    # Load stocks
    tickers = load_stock_list()
    
    # Check checkpoint
    all_data = {}
    start_index = 0
    
    checkpoint_file, checkpoint_count = find_last_checkpoint()
    if checkpoint_file:
        print(f"\n📂 Found checkpoint: {checkpoint_count} stocks")
        resume = input("Resume from checkpoint? (y/n): ").strip().lower()
        if resume == 'y':
            with open(checkpoint_file, 'rb') as f:
                all_data = pickle.load(f)
            start_index = checkpoint_count
            print(f"✅ Resumed from {checkpoint_count} stocks")
    
    # Confirm
    remaining = len(tickers) - start_index
    print(f"\n{'='*70}")
    print(f"READY TO DOWNLOAD")
    print(f"{'='*70}")
    print(f"Total stocks: {len(tickers)}")
    print(f"Already done: {start_index}")
    print(f"Remaining: {remaining}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Est. time: {remaining * 2 / 60:.0f} minutes")
    print(f"{'='*70}")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Cancelled")
        return
    
    # Download
    print(f"\n📥 Starting download...\n")
    
    success_count = len(all_data)
    failed_stocks = []
    
    start_time = time.time()
    
    for i, ticker in enumerate(tickers[start_index:], start=start_index+1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ", flush=True)
        
        df = download_stock_2025(ticker)
        
        if df is not None and len(df) > 0:
            all_data[ticker] = df
            success_count += 1
            print(f"✅ {len(df)} rows (from {df['time'].min().date()} to {df['time'].max().date()})")
        else:
            failed_stocks.append(ticker)
            print("❌ No data")
        
        # Checkpoint
        if i % CHECKPOINT_INTERVAL == 0:
            cp_file = save_checkpoint(all_data, i)
            elapsed = time.time() - start_time
            rate = i / elapsed * 60
            eta = (len(tickers) - i) / rate
            print(f"   💾 Checkpoint: {cp_file}")
            print(f"   ⏱️  Progress: {i}/{len(tickers)} ({i/len(tickers)*100:.1f}%), "
                  f"Rate: {rate:.1f}/min, ETA: {eta:.0f}min")
        
        # Rate limit (important!)
        time.sleep(2)
    
    # Save final
    print(f"\n{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*70}")
    
    final_file = f"{OUTPUT_FOLDER}/data_2025_complete.pkl"
    with open(final_file, 'wb') as f:
        pickle.dump(all_data, f)
    
    print(f"✅ Final file: {final_file}")
    print(f"   Total stocks: {success_count}/{len(tickers)} ({success_count/len(tickers)*100:.1f}%)")
    
    # Statistics
    if len(all_data) > 0:
        total_rows = sum(len(df) for df in all_data.values())
        avg_rows = total_rows / len(all_data)
        
        print(f"\nStatistics:")
        print(f"   Total rows: {total_rows:,}")
        print(f"   Avg rows/stock: {avg_rows:.1f}")
        print(f"   File size: {os.path.getsize(final_file)/1024/1024:.1f} MB")
    
    # Failed stocks
    if len(failed_stocks) > 0:
        print(f"\n⚠️ Failed stocks ({len(failed_stocks)}):")
        print(", ".join(failed_stocks[:20]))
        if len(failed_stocks) > 20:
            print(f"... and {len(failed_stocks)-20} more")
        
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
    print(f"Success rate: {success_count/len(tickers)*100:.1f}%")
    print(f"Output: {final_file}")
    print(f"{'='*70}")
    
    print(f"\n✅ Ready to backtest!")
    print(f"Next: python backtest_4strategies_PKL.py")


if __name__ == "__main__":
    main()
