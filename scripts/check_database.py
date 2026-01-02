"""
Check signals in database
"""

import sqlite3
import sys

DB_PATH = 'signals.db'

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count total signals
    cursor.execute('SELECT COUNT(*) FROM signals')
    count = cursor.fetchone()[0]
    
    print(f"\n{'='*60}")
    print(f"SIGNALS IN DATABASE")
    print(f"{'='*60}")
    print(f"Total signals: {count}")
    
    if count > 0:
        # Get all signals
        cursor.execute('''
            SELECT ticker, strategy, strength, entry_price, take_profit, stop_loss, rsi, is_priority
            FROM signals
            ORDER BY strength DESC
        ''')
        
        signals = cursor.fetchall()
        
        print(f"\n{'='*60}")
        print("ALL SIGNALS:")
        print(f"{'='*60}")
        print(f"{'#':<4} {'Ticker':<6} {'Strategy':<12} {'Strength':<10} {'Entry':<12} {'Target':<12} {'Stop':<12} {'RSI':<8} {'Priority'}")
        print("-" * 100)
        
        for i, sig in enumerate(signals, 1):
            ticker, strategy, strength, entry, target, stop, rsi, priority = sig
            profit = ((target / entry) - 1) * 100
            pri_mark = "⭐" if priority == 1 else ""
            print(f"{i:<4} {ticker:<6} {strategy:<12} {strength:<10} {entry:>10,.0f}  {target:>10,.0f}  {stop:>10,.0f}  {rsi:>6.1f}  {pri_mark}")
        
        # Summary by strategy
        cursor.execute("SELECT strategy, COUNT(*) FROM signals GROUP BY strategy")
        by_strategy = cursor.fetchall()
        
        print(f"\n{'='*60}")
        print("BY STRATEGY:")
        print(f"{'='*60}")
        for strategy, cnt in by_strategy:
            print(f"{strategy}: {cnt}")
        
        # Priority signals
        cursor.execute("SELECT COUNT(*) FROM signals WHERE is_priority = 1")
        priority_count = cursor.fetchone()[0]
        print(f"\nPriority signals: {priority_count}")
        
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Database check complete")
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
