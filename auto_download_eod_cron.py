#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO DOWNLOAD EOD PRICES - CRON JOB
Runs daily at 6PM (weekdays only)
Auto-deletes files older than 5 days
"""

import json
import os
import glob
from datetime import datetime, timedelta
from vnstock import Vnstock
import time

# Config
EOD_FILE_PREFIX = 'eod_prices_'  # Will be: eod_prices_2026-01-11.json
EOD_FILE_TTL_DAYS = 5
OUTPUT_DIR = '.'


def is_trading_day():
    """Check if today is a trading day (Monday-Friday)"""
    today = datetime.now()
    weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # Monday-Friday only (0-4)
    if weekday >= 5:  # Saturday or Sunday
        print(f"⏸️ Today is {today.strftime('%A')} - Not a trading day. Skipping.")
        return False
    
    print(f"✅ Today is {today.strftime('%A')} - Trading day!")
    return True


def get_all_tickers():
    """
    Get ALL tickers from Vietnamese stock market
    Returns ~100-200 major tickers (fallback mode)
    """
    stock_api = Vnstock()
    
    try:
        print("📊 Fetching ticker list...")
        
        # Try listing API first
        try:
            listing = stock_api.listing.all_symbols()
            if listing is not None and not listing.empty:
                all_tickers = listing['ticker'].unique().tolist()
                print(f"✅ Found {len(all_tickers)} tickers from API")
                return all_tickers
        except Exception as e:
            print(f"⚠️ Listing API failed: {e}")
        
        # Fallback: Major tickers from all exchanges
        print("📋 Using fallback ticker list...")
        
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
            'DGC', 'NT2', 'PVD', 'HAG', 'DCM', 'DPM', 'HT1', 'VGC', 'GAS',
            'PVT', 'PVS', 'PVG', 'PVB', 'PVC', 'PVX', 'POW', 'PC1', 'PAN',
            
            # HOSE - Real Estate
            'VRE', 'NVL', 'DXG', 'PDR', 'DIG', 'KDH', 'HDG', 'NLG', 'HDC',
            'VHM', 'DXS', 'SZC', 'IDC', 'SCR', 'CEO',
            
            # HOSE - Industrial
            'HPG', 'HSG', 'NKG', 'POM', 'DGC', 'DTL', 'VCS', 'HT1', 'HVN',
            
            # HNX (Major)
            'PVS', 'CEO', 'SHS', 'VCS', 'PVI', 'VGC', 'PVX', 'NRC', 'TNG',
            'PVC', 'VC3', 'TDH', 'HUT', 'PVB', 'PVG', 'PVT', 'L10', 'VIG',
            'DBC', 'DTT', 'HTP', 'MBS', 'SD2', 'SD5', 'SD9', 'SDN', 'HHS',
            
            # UPCOM (Major)
            'BSR', 'EVE', 'PAN', 'THD', 'AAA', 'KSB', 'BST', 'CSC', 'VTO',
            'LHC', 'TTB', 'KHP', 'PLP', 'QBS', 'SJD'
        ]
        
        # Remove duplicates
        major_tickers = list(set(major_tickers))
        print(f"✅ Using {len(major_tickers)} major tickers")
        
        return major_tickers
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def download_eod_prices():
    """
    Download EOD prices for all tickers
    Returns: filepath of created JSON file
    """
    print("\n" + "="*70)
    print("📥 AUTO-DOWNLOAD EOD PRICES")
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
                prices_data[ticker] = {
                    'price': price,
                    'change_percent': change_pct if change_pct else 0.0,
                    'volume': volume if volume else 0
                }
                success_count += 1
                print(f"✅ {price:,.0f}")
            else:
                fail_count += 1
                print("❌")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            fail_count += 1
            print(f"❌ {e}")
            continue
    
    # Generate filename with date
    today_str = datetime.now().strftime('%Y-%m-%d')
    output_file = f"{EOD_FILE_PREFIX}{today_str}.json"
    
    output_data = {
        'date': today_str,
        'timestamp': datetime.now().isoformat(),
        'total_tickers': len(all_tickers),
        'success_count': success_count,
        'fail_count': fail_count,
        'prices': prices_data
    }
    
    # Save to file
    filepath = os.path.join(OUTPUT_DIR, output_file)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*70)
    print(f"Date: {today_str}")
    print(f"Total tickers: {len(all_tickers)}")
    print(f"Success: {success_count} ✅")
    print(f"Failed: {fail_count} ❌")
    print(f"Success rate: {success_count/len(all_tickers)*100:.1f}%")
    print(f"\n📁 Saved to: {filepath}")
    print(f"📊 File size: {os.path.getsize(filepath)/1024:.1f} KB")
    print("="*70 + "\n")
    
    return filepath


def delete_old_eod_files():
    """
    Delete EOD files older than TTL
    Keeps only recent 5 days
    """
    print("\n" + "="*70)
    print("🗑️ CLEANING OLD EOD FILES")
    print("="*70)
    
    # Find all EOD files
    pattern = os.path.join(OUTPUT_DIR, f"{EOD_FILE_PREFIX}*.json")
    eod_files = glob.glob(pattern)
    
    if not eod_files:
        print("✅ No old files to delete")
        return
    
    print(f"📁 Found {len(eod_files)} EOD files")
    
    cutoff_date = datetime.now() - timedelta(days=EOD_FILE_TTL_DAYS)
    deleted_count = 0
    
    for filepath in eod_files:
        try:
            # Get file date from filename: eod_prices_2026-01-11.json
            filename = os.path.basename(filepath)
            date_str = filename.replace(EOD_FILE_PREFIX, '').replace('.json', '')
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            age_days = (datetime.now() - file_date).days
            
            if file_date < cutoff_date:
                os.remove(filepath)
                print(f"🗑️ Deleted: {filename} (age: {age_days} days)")
                deleted_count += 1
            else:
                print(f"✅ Kept: {filename} (age: {age_days} days)")
                
        except Exception as e:
            print(f"⚠️ Error processing {filepath}: {e}")
    
    print(f"\n✅ Cleanup complete: Deleted {deleted_count} old files")
    print("="*70 + "\n")


def create_symlink_to_latest():
    """
    Create symlink: latest_prices_all.json → eod_prices_YYYY-MM-DD.json
    Backend always reads from latest_prices_all.json
    """
    try:
        # Find latest EOD file
        pattern = os.path.join(OUTPUT_DIR, f"{EOD_FILE_PREFIX}*.json")
        eod_files = glob.glob(pattern)
        
        if not eod_files:
            print("⚠️ No EOD files found for symlink")
            return
        
        # Get most recent file
        latest_file = max(eod_files, key=os.path.getmtime)
        latest_filename = os.path.basename(latest_file)
        
        symlink_name = 'latest_prices_all.json'
        symlink_path = os.path.join(OUTPUT_DIR, symlink_name)
        
        # Remove old symlink if exists
        if os.path.exists(symlink_path) or os.path.islink(symlink_path):
            os.remove(symlink_path)
        
        # Create new symlink (or copy on Windows)
        try:
            os.symlink(latest_filename, symlink_path)
            print(f"🔗 Created symlink: {symlink_name} → {latest_filename}")
        except OSError:
            # Windows may not support symlinks, copy instead
            import shutil
            shutil.copy2(latest_file, symlink_path)
            print(f"📋 Copied: {latest_filename} → {symlink_name}")
        
    except Exception as e:
        print(f"⚠️ Error creating symlink: {e}")


def main():
    """Main cron job function"""
    print("\n" + "="*70)
    print("🤖 AUTO EOD DOWNLOAD CRON JOB")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Check if trading day
    if not is_trading_day():
        print("\n✅ Job skipped (non-trading day)")
        return
    
    # Download EOD prices
    filepath = download_eod_prices()
    
    if not filepath:
        print("\n❌ Download failed!")
        return
    
    # Create symlink to latest file
    create_symlink_to_latest()
    
    # Delete old files
    delete_old_eod_files()
    
    print("\n" + "="*70)
    print("✅ CRON JOB COMPLETE")
    print("="*70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
