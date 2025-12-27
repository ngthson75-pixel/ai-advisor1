#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOMATED DAILY SCANNER
Run daily after market close to generate signals
Can be scheduled with Windows Task Scheduler or cron
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner
from daily_signal_scanner import scan_all_stocks, save_signals, classify_stock
from vnstock import Vnstock
import pandas as pd
from datetime import datetime
import json

print("="*70)
print("AUTOMATED DAILY SCANNER")
print("="*70)
print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Auto-run settings
AUTO_RUN = True  # Set to True for automated mode
SCAN_ALL = False  # True = all stocks, False = priority only
MAX_STOCKS = None  # None = no limit, or set number for testing

# Priority stocks (top performers + blue chips)
PRIORITY_STOCKS = [
    # Top 2025 performers
    'TCH', 'PWA', 'GEE', 'QCG', 'LGL', 'HID', 'VHE', 'HHV', 'HTN', 'GIL',
    # Top 2023-2024 performers
    'NDN', 'TCO', 'CSV', 'TIG', 'TC6', 'DL1', 'SCR', 'BMP', 'ITC',
    # Blue chips
    'VNM', 'VIC', 'VHM', 'HPG', 'TCB', 'VCB', 'BID', 'CTG', 'MBB', 'VPB',
    'MSN', 'VJC', 'GAS', 'PLX', 'SSI', 'HDB', 'VRE', 'NVL', 'POW', 'FPT',
    # Mid caps
    'HCM', 'DXG', 'PDR', 'KDH'
]

# ============================================================================
# LOAD STOCK LIST
# ============================================================================

def get_stock_list():
    """Get stock list based on configuration"""
    
    if SCAN_ALL:
        print("Loading ALL stocks from vnstock...")
        
        # Try cached list first
        if os.path.exists('vnstock_symbols.csv'):
            df = pd.read_csv('vnstock_symbols.csv')
            stocks = df['symbol'].tolist()
            print(f"✅ Loaded {len(stocks)} stocks from cache")
        else:
            # Fetch from API
            try:
                stock = Vnstock().stock(symbol='VNM', source='VCI')
                listing = stock.listing.all_symbols()
                stocks = listing['symbol'].tolist()
                
                # Cache for future
                listing.to_csv('vnstock_symbols.csv', index=False)
                print(f"✅ Fetched {len(stocks)} stocks from API")
            except Exception as e:
                print(f"❌ Error fetching stocks: {e}")
                print("Falling back to priority stocks...")
                stocks = PRIORITY_STOCKS
    else:
        print("Using PRIORITY stocks only...")
        stocks = PRIORITY_STOCKS
        print(f"✅ {len(stocks)} priority stocks")
    
    if MAX_STOCKS:
        stocks = stocks[:MAX_STOCKS]
        print(f"⚠️ Limited to {MAX_STOCKS} stocks for testing")
    
    return stocks

# ============================================================================
# POST-PROCESS SIGNALS
# ============================================================================

def post_process_signals(signals):
    """
    Post-process signals for frontend
    Add additional info, sort, filter
    """
    
    # Sort by priority and strength
    for strategy in ['pullback', 'ema_cross']:
        signals[strategy].sort(
            key=lambda x: (x['is_priority'], x['strength']), 
            reverse=True
        )
    
    # Add metadata
    metadata = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_signals': len(signals['pullback']) + len(signals['ema_cross']),
        'market_status': 'CLOSED' if datetime.now().hour >= 15 else 'OPEN',
        'next_scan': 'Tomorrow 3:45 PM'
    }
    
    signals['metadata'] = metadata
    
    return signals

# ============================================================================
# COPY TO FRONTEND
# ============================================================================

def copy_to_frontend(signals_file):
    """
    Copy signals to frontend data folder
    """
    
    # Find frontend folder
    frontend_paths = [
        '../frontend/public/data/',
        '../../frontend/public/data/',
        '../ai-advisor1-frontend/public/data/'
    ]
    
    for path in frontend_paths:
        if os.path.exists(path):
            try:
                import shutil
                dest = os.path.join(path, 'signals.json')
                shutil.copy(signals_file, dest)
                print(f"✅ Copied to frontend: {dest}")
                return True
            except Exception as e:
                print(f"⚠️ Error copying to {path}: {e}")
    
    print("⚠️ Frontend folder not found")
    print("   Manual copy required:")
    print(f"   Copy: {signals_file}")
    print("   To:   frontend/public/data/signals.json")
    
    return False

# ============================================================================
# SEND NOTIFICATION (Optional)
# ============================================================================

def send_telegram_notification(signals):
    """
    Send notification via Telegram
    """
    try:
        import requests
        
        BOT_TOKEN = "8447350659:AAGyvRMGvXRs3VloDo0wk_zbXYhlPAsxaXs"
        CHAT_ID = "6421252178"
        
        pullback_count = len(signals['pullback'])
        ema_count = len(signals['ema_cross'])
        
        message = f"""
🤖 AI ADVISOR - Daily Scan Complete

📊 Signals Generated:
• PULLBACK: {pullback_count} signals
• EMA_CROSS: {ema_count} signals
• Total: {pullback_count + ema_count} signals

⏰ Scan Time: {datetime.now().strftime('%H:%M:%S')}

🔝 Top PULLBACK:
"""
        
        # Add top 3 pullback
        for i, sig in enumerate(signals['pullback'][:3], 1):
            priority = "⭐" if sig['is_priority'] else ""
            message += f"{i}. {priority}{sig['ticker']}: {sig['strength']:.0f}% strength\n"
        
        message += f"\n🔝 Top EMA_CROSS:\n"
        
        # Add top 3 ema_cross
        for i, sig in enumerate(signals['ema_cross'][:3], 1):
            priority = "⭐" if sig['is_priority'] else ""
            message += f"{i}. {priority}{sig['ticker']}: {sig['strength']:.0f}% strength\n"
        
        message += "\n✅ Ready to trade!"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram notification sent")
        else:
            print(f"⚠️ Telegram error: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main automated scanner"""
    
    try:
        # Get stocks
        stocks = get_stock_list()
        
        print(f"\nScanning {len(stocks)} stocks...")
        print("This may take 10-30 minutes depending on stock count\n")
        
        # Scan
        signals = scan_all_stocks(stocks)
        
        # Post-process
        signals = post_process_signals(signals)
        
        # Save
        output_file = save_signals(signals)
        
        # Copy to frontend
        copy_to_frontend(output_file)
        
        # Send notification
        if len(signals['pullback']) + len(signals['ema_cross']) > 0:
            send_telegram_notification(signals)
        
        print("\n" + "="*70)
        print("AUTOMATED SCAN COMPLETE!")
        print("="*70)
        print(f"Total signals: {len(signals['pullback']) + len(signals['ema_cross'])}")
        print(f"Output: {output_file}")
        print(f"Status: Ready for trading")
        print("="*70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
