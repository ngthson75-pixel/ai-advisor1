#!/usr/bin/env python3
"""
PUSH LOCAL SIGNALS TO PRODUCTION/STAGING

Reads signals from local SQLite (signals.db)
Posts them to production/staging backend via API
"""

import sqlite3
import requests
import json
from datetime import datetime
import sys

# Configuration
LOCAL_DB = "signals.db"
PRODUCTION_API = "https://ai-advisor1-backend.onrender.com/api"
STAGING_API = "https://ai-advisor1-staging.onrender.com/api"

def get_available_dates():
    """Get list of dates that have signals in database"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT date, COUNT(*) as count
        FROM signals 
        GROUP BY date 
        ORDER BY date DESC
        LIMIT 10
    """)
    
    dates = cursor.fetchall()
    conn.close()
    
    return dates

def get_local_signals(date=None):
    """Read signals from local SQLite"""
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # If no date specified, get latest date
    if not date:
        cursor.execute("""
            SELECT DISTINCT date 
            FROM signals 
            ORDER BY date DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            date = result[0]
        else:
            conn.close()
            return [], None
    
    cursor.execute("""
        SELECT * FROM signals 
        WHERE date = ?
        ORDER BY strength DESC
    """, (date,))
    
    signals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return signals, date

def push_signal_to_backend(signal, backend_url):
    """Push single signal to backend API"""
    
    # Format signal data for API
    data = {
        'ticker': signal['ticker'],
        'strategy': signal['strategy'],
        'entry_price': signal['entry_price'],
        'stop_loss': signal['stop_loss'],
        'take_profit': signal['take_profit'],
        'risk_reward': signal.get('risk_reward', 0),
        'strength': signal.get('strength', 0),
        'is_priority': signal.get('is_priority', 0),
        'stock_type': signal.get('stock_type', ''),
        'rsi': signal.get('rsi', 0),
        'date': signal['date'],
        'action': signal.get('action', 'BUY')
    }
    
    try:
        response = requests.post(
            f"{backend_url}/signals",
            json=data,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            return True, "Success"
        else:
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)

def verify_backend(backend_url):
    """Verify signals count on backend"""
    try:
        response = requests.get(f"{backend_url}/signals", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('count', 0)
        else:
            return None
    except:
        return None

def main():
    print("=" * 80)
    print("🚀 PUSH LOCAL SIGNALS TO BACKEND")
    print("=" * 80)
    print()
    
    # Check available dates
    print("📅 Step 1: Checking available dates...")
    dates = get_available_dates()
    
    if not dates:
        print("❌ No signals found in database!")
        print()
        print("Try running scanner first:")
        print("  cd C:\\ai-advisor1\\scripts")
        print("  python daily_signal_scanner_eod.py")
        return
    
    print(f"✓ Found signals for {len(dates)} date(s)")
    print()
    
    # Show available dates
    print("Available dates:")
    for i, (date, count) in enumerate(dates, 1):
        print(f"  {i}. {date} - {count} signals")
    print()
    
    # Select date
    if len(dates) == 1:
        selected_date = dates[0][0]
        print(f"Auto-selected: {selected_date}")
    else:
        print("Choose date:")
        choice = input(f"Enter choice (1-{len(dates)}) or press Enter for latest: ").strip()
        
        if choice == '':
            selected_date = dates[0][0]
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(dates):
                    selected_date = dates[idx][0]
                else:
                    print("❌ Invalid choice!")
                    return
            except:
                print("❌ Invalid input!")
                return
    
    print()
    print(f"Selected date: {selected_date}")
    print()
    
    # Get signals for selected date
    print("📊 Step 2: Reading signals...")
    signals, date = get_local_signals(selected_date)
    
    if not signals:
        print(f"❌ No signals found for {selected_date}")
        return
    
    # Show summary
    pullback = len([s for s in signals if s['strategy'] == 'PULLBACK'])
    ema_cross = len([s for s in signals if s['strategy'] == 'EMA_CROSS'])
    priority = len([s for s in signals if s['is_priority'] == 1])
    
    print(f"✓ Found {len(signals)} signals for {date}")
    print(f"  PULLBACK: {pullback}")
    print(f"  EMA_CROSS: {ema_cross}")
    print(f"  Priority: {priority}")
    print()
    
    # Show top 5
    print("Top 5 signals:")
    for i, sig in enumerate(signals[:5], 1):
        print(f"  {i}. {sig['ticker']} - {sig['strategy']} - {sig['strength']}%")
    print()
    
    # Choose environment
    print("📤 Step 2: Choose destination")
    print("  1. Production (https://ai-advisor.vn)")
    print("  2. Staging (https://staging.ai-advisor.vn)")
    print("  3. Both")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    print()
    
    # Determine backends
    backends = []
    if choice == '1':
        backends = [("Production", PRODUCTION_API)]
    elif choice == '2':
        backends = [("Staging", STAGING_API)]
    elif choice == '3':
        backends = [("Production", PRODUCTION_API), ("Staging", STAGING_API)]
    else:
        print("❌ Invalid choice!")
        return
    
    # Confirm
    print(f"⚠️  About to push {len(signals)} signals to:")
    for name, _ in backends:
        print(f"  - {name}")
    print()
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    print()
    
    # Push signals
    for env_name, api_url in backends:
        print(f"🔄 Pushing to {env_name}...")
        print("-" * 80)

        # ── Lấy danh sách tickers đang open trên server ──────────────
        open_tickers = set()
        try:
            r = requests.get(f"{api_url}/signals", timeout=30)
            if r.status_code == 200:
                all_sigs = r.json().get('signals', r.json().get('data', []))
                open_tickers = {
                    s['ticker'] for s in all_sigs
                    if s.get('action') == 'BUY'
                    and s.get('status') in ('open', 'partial', None, '')
                }
                print(f"  ℹ️  {len(open_tickers)} tickers đang open trên {env_name} → sẽ bỏ qua nếu trùng")
        except Exception as e:
            print(f"  ⚠️  Không lấy được danh sách open signals: {e}")

        success_count = 0
        fail_count = 0
        skip_dup_count = 0

        for i, signal in enumerate(signals, 1):
            # Skip nếu ticker đã có open BUY signal trên server
            if signal['ticker'] in open_tickers:
                print(f"  {i:3d}/{len(signals)} ⏭ {signal['ticker']:<6} — đã có open signal, bỏ qua")
                skip_dup_count += 1
                continue

            ticker = signal['ticker']
            strategy = signal['strategy']
            strength = signal['strength']
            
            success, message = push_signal_to_backend(signal, api_url)
            
            if success:
                print(f"  {i:3d}/{len(signals)} ✓ {ticker:6s} {strategy:12s} {strength:3.0f}%")
                success_count += 1
            else:
                print(f"  {i:3d}/{len(signals)} ✗ {ticker:6s} - {message}")
                fail_count += 1
        
        print()
        print(f"Results for {env_name}:")
        print(f"  ✓ Success: {success_count}")
        print(f"  ⏭ Skipped: {skip_dup_count} (đã open)")
        print(f"  ✗ Failed: {fail_count}")
        print()
        
        # Verify
        print(f"🔍 Verifying {env_name}...")
        count = verify_backend(api_url)
        if count is not None:
            print(f"  ✓ Backend has {count} total signals")
        else:
            print(f"  ⚠️  Cannot verify (check manually)")
        print()
    
    print("=" * 80)
    print("✅ PUSH COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Clear browser cache (Ctrl + Shift + R)")
    print("  2. Visit website:")
    for name, _ in backends:
        if name == "Production":
            print("     https://ai-advisor.vn")
        else:
            print("     https://staging.ai-advisor.vn")
    print("  3. Check 'Tín hiệu mua' tab")
    print("  4. Should see new signals dated", date)
    print()

if __name__ == '__main__':
    main()
