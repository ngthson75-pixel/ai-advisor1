#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO-DISCOVER LIQUID STOCKS FROM VNSTOCK

Step 1: Get all Vietnamese stock codes
Step 2: Check liquidity (average volume > 100k/day)
Step 3: Download only liquid stocks
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


def get_all_vietnamese_stocks():
    """
    Get complete list of all Vietnamese stocks from VNStock
    
    Returns:
        List of stock codes
    """
    
    print("\n" + "=" * 70)
    print("📊 DISCOVERING ALL VIETNAMESE STOCKS")
    print("=" * 70)
    
    try:
        # Method 1: Try using Vnstock().stock().listing.all_symbols()
        print("\n🔍 Method 1: Using Vnstock API...")
        
        all_stocks = []
        
        # Try different exchanges
        for exchange in ['HOSE', 'HNX', 'UPCOM']:
            print(f"\n   Fetching {exchange} stocks...", end=' ')
            try:
                stock = Vnstock().stock(symbol='ACB', source='VCI')
                
                # Try to get listing
                if hasattr(stock, 'listing'):
                    if hasattr(stock.listing, 'all_symbols'):
                        df = stock.listing.all_symbols(exchange=exchange)
                    elif hasattr(stock.listing, 'symbols_by_exchange'):
                        df = stock.listing.symbols_by_exchange(exchange=exchange)
                    elif hasattr(stock.listing, 'all_symbols'):
                        df = stock.listing.all_symbols()
                    else:
                        df = None
                    
                    if df is not None and not df.empty:
                        # Try different column names
                        if 'ticker' in df.columns:
                            codes = df['ticker'].tolist()
                        elif 'symbol' in df.columns:
                            codes = df['symbol'].tolist()
                        elif 'code' in df.columns:
                            codes = df['code'].tolist()
                        else:
                            codes = df.iloc[:, 0].tolist()  # First column
                        
                        all_stocks.extend(codes)
                        print(f"✅ Found {len(codes)} stocks")
                    else:
                        print("⚠️  Empty result")
                else:
                    print("⚠️  No listing method")
                    
            except Exception as e:
                print(f"⚠️  Error: {str(e)[:50]}")
        
        if all_stocks:
            all_stocks = list(set(all_stocks))  # Remove duplicates
            all_stocks = [s.upper() for s in all_stocks if s]  # Clean
            print(f"\n✅ Total unique stocks found: {len(all_stocks)}")
            return sorted(all_stocks)
        
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)[:100]}")
    
    # Method 2: Fallback to comprehensive list
    print("\n⚠️  Fallback to comprehensive list...")
    
    # Comprehensive list of known stocks
    comprehensive_list = [
        # HOSE - Large caps
        'VIC', 'VHM', 'VNM', 'HPG', 'MSN', 'VCB', 'MBB', 'TCB', 'BID', 'CTG',
        'VPB', 'ACB', 'HDB', 'TPB', 'STB', 'SHB', 'MWG', 'FPT', 'GAS', 'PLX',
        'VJC', 'SSI', 'VRE', 'VCI', 'POW', 'GVR', 'NVL', 'REE', 'DGC', 'PHR',
        
        # HOSE - Mid/Small caps
        'VIB', 'SSB', 'BCM', 'BVH', 'PDR', 'VGC', 'KDH', 'NLG', 'DIG', 'CII',
        'TCH', 'CTD', 'HDG', 'LGC', 'HBC', 'DVP', 'PC1', 'DHG', 'DMC', 'DRC',
        'FTS', 'VND', 'HCM', 'SZL', 'HDC', 'HT1', 'IDC', 'PAN', 'GEG', 'TDM',
        'BWE', 'EVF', 'ORS', 'AGR', 'VOS', 'HAH', 'VNA', 'PVG', 'VSH', 'GEX',
        'HAG', 'BMP', 'TRA', 'IMP', 'ANV', 'NKG', 'HSG', 'DBC', 'GEE', 'CMG',
        'FRT', 'DGW', 'PET', 'CTR', 'SCS', 'VCG', 'PVT', 'BSI', 'CTS', 'VIX',
        'DPM', 'DCM', 'GMD', 'SAB', 'NT2', 'PVD', 'PVS', 'VHC', 'DXG',
        
        # Add more HOSE stocks
        'BCC', 'CHP', 'CSV', 'DHA', 'DTL', 'FLC', 'HNG', 'HQC', 'HTN', 'KBC',
        'KDC', 'L10', 'MCH', 'MCP', 'NHA', 'NSC', 'PPC', 'QCG', 'SAM', 'SBT',
        'SCR', 'SJS', 'THG', 'TIP', 'TLG', 'TMP', 'TNH', 'TVB', 'VCS', 'VHG',
        'VIE', 'VPI', 'VTO', 'YEG', 'AAA', 'AAM', 'AAT', 'ABS', 'ABT', 'ACC',
        'ACL', 'ADG', 'ADP', 'ADS', 'AGF', 'AGG', 'AGM', 'AGP', 'AIC', 'ALT',
        'AMD', 'AMP', 'APC', 'APG', 'APH', 'API', 'APS', 'ARM', 'ASG', 'ASM',
        'ASP', 'AST', 'ATA', 'ATB', 'ATC', 'ATG', 'B82', 'BAB', 'BAF', 'BBC',
        'BBM', 'BBS', 'BBT', 'BCE', 'BCG', 'BCI', 'BCN', 'BFC', 'BGW', 'BHC',
        'BIC', 'BID', 'BKC', 'BLF', 'BLT', 'BMC', 'BMD', 'BMF', 'BMG', 'BMI',
        'BMJ', 'BMP', 'BMS', 'BMV', 'BPC', 'BRC', 'BSC', 'BSG', 'BSL', 'BST',
        'BTC', 'BTD', 'BTG', 'BTH', 'BTN', 'BTP', 'BTT', 'BTW', 'BVG', 'BVL',
        'BWA', 'BWS', 'C12', 'C21', 'C22', 'C32', 'C47', 'C69', 'C71', 'C92',
        'CAD', 'CAG', 'CAN', 'CAP', 'CAT', 'CAV', 'CBC', 'CC1', 'CC4', 'CCA',
        'CCI', 'CCL', 'CCM', 'CCP', 'CCR', 'CCV', 'CDC', 'CE1', 'CEC', 'CEN',
        'CEO', 'CET', 'CFC', 'CFM', 'CFV', 'CGL', 'CGP', 'CGV', 'CHC', 'CIA',
        'CIC', 'CID', 'CIG', 'CIP', 'CKA', 'CKD', 'CKG', 'CKV', 'CLC', 'CLG',
        'CLL', 'CLM', 'CLP', 'CLW', 'CMC', 'CMD', 'CMF', 'CMG', 'CMI', 'CMK',
        'CMN', 'CMP', 'CMT', 'CMV', 'CMW', 'CMX', 'CNC', 'CNG', 'CNN', 'COM',
        'CP1', 'CPA', 'CPC', 'CPH', 'CPI', 'CQN', 'CQT', 'CRC', 'CRE', 'CSC',
        'CSG', 'CSM', 'CSV', 'CT3', 'CT6', 'CTA', 'CTB', 'CTC', 'CTD', 'CTF',
        'CTG', 'CTI', 'CTN', 'CTP', 'CTR', 'CTS', 'CTT', 'CTV', 'CTW', 'CTX',
        'CVN', 'CVT', 'CX8', 'D11', 'D2D', 'DAC', 'DAD', 'DAE', 'DAG', 'DAH',
        'DAN', 'DAT', 'DBD', 'DBM', 'DBT', 'DC1', 'DC2', 'DC4', 'DCC', 'DCF',
        'DCG', 'DCH', 'DCL', 'DCM', 'DCR', 'DCS', 'DCT', 'DDG', 'DDH', 'DDM',
        'DDN', 'DDV', 'DFC', 'DFF', 'DGC', 'DGL', 'DGT', 'DGW', 'DHA', 'DHB',
        'DHC', 'DHG', 'DHI', 'DHM', 'DHN', 'DHP', 'DHT', 'DIC', 'DID', 'DIG',
        'DL1', 'DLG', 'DLR', 'DLT', 'DMC', 'DMS', 'DNA', 'DNC', 'DNE', 'DNH',
        'DNL', 'DNM', 'DNN', 'DNP', 'DNR', 'DNS', 'DNT', 'DNW', 'DOP', 'DPC',
        'DPG', 'DPH', 'DPM', 'DPP', 'DPR', 'DPS', 'DQC', 'DRC', 'DRG', 'DRH',
        'DRI', 'DS3', 'DSG', 'DSN', 'DSP', 'DST', 'DSV', 'DTA', 'DTB', 'DTC',
        'DTD', 'DTE', 'DTG', 'DTH', 'DTI', 'DTK', 'DTL', 'DTN', 'DTP', 'DTT',
        'DTV', 'DVC', 'DVG', 'DVM', 'DVN', 'DVP', 'DVW', 'DWC', 'DWS', 'DXG',
        'DXL', 'DXP', 'DXS', 'DXV', 'DZM', 'E12', 'E29', 'EBA', 'EBS', 'ECI',
        'EFI', 'EIB', 'EIC', 'EID', 'EIN', 'ELC', 'EMC', 'EME', 'EMG', 'EMS',
        
        # HNX stocks
        'PVS', 'NVB', 'CEO', 'SHN', 'PVI', 'DTD', 'VCS', 'TNG', 'NHH', 'TIG',
        'VGS', 'VC3', 'PVX', 'PVB', 'THD', 'TV3', 'NDN', 'SRA', 'MBS', 'HUT',
        'TDG', 'LAS', 'DST', 'PLC', 'NET', 'DP3', 'IDV', 'NGC', 'VMC', 'TDN',
        'HTP', 'API', 'TS4', 'DNP', 'PGS', 'VE8', 'PTB', 'PSW', 'L14', 'L18',
        'L35', 'L40', 'L43', 'L44', 'L45', 'L61', 'L62', 'L63', 'MAC', 'MAS',
        'MBG', 'MBS', 'MCC', 'MCF', 'MCG', 'MCP', 'MDC', 'MEC', 'MED', 'MEL',
        
        # UPCOM stocks
        'BSI', 'BVB', 'WIN', 'SFI', 'INN', 'CNC', 'NKG', 'VCC', 'AAM', 'BFC',
        'CTW', 'DL1', 'HGW', 'IBC', 'KSH', 'LTG', 'PTC', 'RCL', 'SEB', 'SFG',
        'TCO', 'VE1', 'VE2', 'VE3', 'VE4', 'VE9',
    ]
    
    comprehensive_list = list(set(comprehensive_list))
    print(f"✅ Using comprehensive list: {len(comprehensive_list)} stocks")
    
    return sorted(comprehensive_list)


def quick_liquidity_check(code, lookback_days=30):
    """
    Quick check of recent liquidity (last 30 days)
    Faster than downloading full 5 years
    
    Returns:
        (average_volume, is_liquid) tuple
    """
    
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        df = stock.quote.history(
            symbol=code,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        if df.empty or len(df) < 10:  # Need at least 10 days
            return 0, False
        
        avg_volume = df['volume'].mean()
        is_liquid = avg_volume >= 100000
        
        return avg_volume, is_liquid
        
    except Exception as e:
        return 0, False


def filter_liquid_stocks(all_stocks, min_volume=100000, batch_size=10, delay=1):
    """
    Filter stocks by liquidity in batches
    
    Args:
        all_stocks: List of stock codes
        min_volume: Minimum average volume
        batch_size: Process N stocks at a time
        delay: Delay between stocks (rate limiting)
    
    Returns:
        List of liquid stocks with volumes
    """
    
    print("\n" + "=" * 70)
    print("🔍 FILTERING BY LIQUIDITY")
    print("=" * 70)
    print(f"Checking: {len(all_stocks)} stocks")
    print(f"Criteria: Average volume > {min_volume:,} shares/day")
    print(f"Method: Last 30 days average")
    print("=" * 70)
    print()
    
    liquid_stocks = []
    failed_stocks = []
    low_liquidity = []
    
    for i, code in enumerate(all_stocks, 1):
        print(f"[{i}/{len(all_stocks)}] Checking {code}...", end=' ')
        
        time.sleep(delay)
        
        avg_vol, is_liquid = quick_liquidity_check(code, lookback_days=30)
        
        if avg_vol == 0:
            print("❌ Failed")
            failed_stocks.append(code)
        elif is_liquid:
            print(f"✅ Liquid ({avg_vol:,.0f} shares/day)")
            liquid_stocks.append({
                'code': code,
                'avg_volume': avg_vol
            })
        else:
            print(f"⚠️  Low ({avg_vol:,.0f} shares/day)")
            low_liquidity.append(code)
        
        # Progress report every 50 stocks
        if i % 50 == 0:
            print(f"\n📊 Progress: {i}/{len(all_stocks)} checked")
            print(f"   ✅ Liquid: {len(liquid_stocks)}")
            print(f"   ⚠️  Low: {len(low_liquidity)}")
            print(f"   ❌ Failed: {len(failed_stocks)}\n")
    
    # Sort by volume (highest first)
    liquid_stocks.sort(key=lambda x: x['avg_volume'], reverse=True)
    
    print("\n" + "=" * 70)
    print("✅ LIQUIDITY FILTER COMPLETE")
    print("=" * 70)
    print(f"Total checked: {len(all_stocks)}")
    print(f"✅ Liquid stocks: {len(liquid_stocks)} ({len(liquid_stocks)/len(all_stocks)*100:.1f}%)")
    print(f"⚠️  Low liquidity: {len(low_liquidity)} ({len(low_liquidity)/len(all_stocks)*100:.1f}%)")
    print(f"❌ Failed: {len(failed_stocks)} ({len(failed_stocks)/len(all_stocks)*100:.1f}%)")
    print()
    
    if liquid_stocks:
        print("📊 Top 20 most liquid stocks:")
        for i, stock in enumerate(liquid_stocks[:20], 1):
            print(f"   {i:2}. {stock['code']}: {stock['avg_volume']:>12,.0f} shares/day")
    
    return liquid_stocks, low_liquidity, failed_stocks


def download_full_history(liquid_stocks, years=5, timeframe='1D', delay=2):
    """
    Download full historical data for liquid stocks only
    """
    
    print("\n" + "=" * 70)
    print("📥 DOWNLOADING FULL HISTORY FOR LIQUID STOCKS")
    print("=" * 70)
    print(f"Stocks: {len(liquid_stocks)}")
    print(f"Period: {years} years")
    print(f"Timeframe: {timeframe}")
    print("=" * 70)
    print()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    stock_data = {}
    success = []
    failed = []
    
    codes = [s['code'] for s in liquid_stocks]
    
    for i, code in enumerate(codes, 1):
        print(f"\n[{i}/{len(codes)}] Downloading {code}...", end=' ')
        
        try:
            time.sleep(delay)
            
            stock = Vnstock().stock(symbol=code, source='VCI')
            
            if timeframe == '1D':
                df = stock.quote.history(
                    symbol=code,
                    start=start_str,
                    end=end_str
                )
            elif timeframe == '1H':
                df = stock.quote.intraday(symbol=code, page_size=5000)
                if not df.empty:
                    df = df[(df.index >= start_str) & (df.index <= end_str)]
            
            if df.empty or len(df) < 100:
                print(f"❌ Insufficient data ({len(df)} bars)")
                failed.append(code)
                continue
            
            # Add indicators
            df['avg_volume'] = df['volume'].rolling(window=20).mean()
            df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            stock_data[code] = df
            success.append(code)
            
            print(f"✅ OK ({len(df)} bars)")
            
            # Checkpoint every 50 stocks
            if i % 50 == 0:
                filename = f'liquid_stocks_{timeframe}_checkpoint_{i}.pkl'
                save_data(stock_data, filename)
                print(f"\n💾 Checkpoint: {len(stock_data)} stocks saved\n")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            failed.append(code)
    
    print("\n" + "=" * 70)
    print("✅ DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Success: {len(success)}/{len(codes)}")
    print(f"Failed: {len(failed)}/{len(codes)}")
    print("=" * 70)
    
    return stock_data


def save_data(data_dict, filename):
    """Save data to pickle file"""
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data_dict, f)
    
    size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"💾 Saved: {filepath} ({size_mb:.1f} MB)")


def save_stock_list(liquid_stocks, filename='liquid_stocks_list.txt'):
    """Save list of liquid stocks to text file"""
    
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# LIQUID STOCKS (Volume > 100k/day)\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(liquid_stocks)} stocks\n\n")
        
        for stock in liquid_stocks:
            f.write(f"{stock['code']}\t{stock['avg_volume']:,.0f}\n")
    
    print(f"📝 Stock list saved: {filepath}")


def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-discover and download liquid stocks')
    parser.add_argument('--min-volume', type=int, default=100000,
                       help='Minimum average volume (default: 100,000)')
    parser.add_argument('--years', type=int, default=5,
                       help='Years of history (default: 5)')
    parser.add_argument('--timeframe', type=str, default='1D',
                       choices=['1D', '1H'],
                       help='Timeframe (default: 1D)')
    parser.add_argument('--filter-only', action='store_true',
                       help='Only filter, don\'t download full history')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 AUTO-DISCOVER LIQUID STOCKS")
    print("=" * 70)
    print(f"Min volume: {args.min_volume:,} shares/day")
    print(f"History: {args.years} years")
    print(f"Timeframe: {args.timeframe}")
    print("=" * 70)
    
    # Step 1: Get all stocks
    all_stocks = get_all_vietnamese_stocks()
    
    if not all_stocks:
        print("❌ No stocks found!")
        return
    
    # Step 2: Filter by liquidity
    liquid_stocks, low_liquidity, failed = filter_liquid_stocks(
        all_stocks,
        min_volume=args.min_volume,
        delay=1
    )
    
    if not liquid_stocks:
        print("❌ No liquid stocks found!")
        return
    
    # Save list
    save_stock_list(liquid_stocks)
    
    if args.filter_only:
        print("\n✅ Filtering complete! (--filter-only mode)")
        print(f"📝 Stock list saved to: data/liquid_stocks_list.txt")
        return
    
    # Step 3: Download full history
    stock_data = download_full_history(
        liquid_stocks,
        years=args.years,
        timeframe=args.timeframe,
        delay=2
    )
    
    # Final save
    filename = f'liquid_stocks_{args.years}y_{args.timeframe}.pkl'
    save_data(stock_data, filename)
    
    print("\n" + "=" * 70)
    print("🎊 ALL COMPLETE!")
    print("=" * 70)
    print(f"✅ Discovered: {len(all_stocks)} total stocks")
    print(f"✅ Filtered: {len(liquid_stocks)} liquid stocks")
    print(f"✅ Downloaded: {len(stock_data)} stocks with full history")
    print(f"📁 Data file: data/{filename}")
    print(f"📝 Stock list: data/liquid_stocks_list.txt")
    print("🚀 Ready for backtesting!")
    print("=" * 70)


if __name__ == '__main__':
    main()
