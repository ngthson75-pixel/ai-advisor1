#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX DUPLICATE SIGNALS
Giữ signal mới nhất, xóa các bản duplicate cũ

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
"""

import sqlite3
from datetime import datetime

def fix_duplicates(dry_run=True):
    """
    Fix duplicate signals
    
    Strategy: Keep signal with highest ID (newest), delete older ones
    """
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    print("=" * 70)
    print("🔧 FIX DUPLICATE SIGNALS")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'ACTUAL DELETE'}")
    print()
    
    # Find duplicates
    cursor.execute("""
        SELECT ticker, date, COUNT(*) as count
        FROM signals
        GROUP BY ticker, date
        HAVING count > 1
    """)
    
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✅ No duplicates found!")
        conn.close()
        return
    
    print(f"Found {len(duplicates)} duplicate groups:\n")
    
    total_deleted = 0
    
    for ticker, date, count in duplicates:
        print(f"📊 {ticker} on {date}: {count} signals")
        
        # Get all signals for this ticker+date
        cursor.execute("""
            SELECT id, strategy, entry_price, strength, created_at
            FROM signals
            WHERE ticker = ? AND date = ?
            ORDER BY id DESC
        """, (ticker, date))
        
        signals = cursor.fetchall()
        
        # Keep the first one (highest ID = newest)
        keep_id = signals[0][0]
        delete_ids = [s[0] for s in signals[1:]]
        
        print(f"   ✅ KEEP: ID={keep_id} (newest)")
        for sig in signals[1:]:
            print(f"   🗑️  DELETE: ID={sig[0]}, Strategy={sig[1]}, Entry={sig[2]:,.0f}")
        
        if not dry_run:
            # Actually delete
            for del_id in delete_ids:
                cursor.execute("DELETE FROM signals WHERE id = ?", (del_id,))
                total_deleted += 1
        else:
            total_deleted += len(delete_ids)
        
        print()
    
    if not dry_run:
        conn.commit()
        print(f"✅ Deleted {total_deleted} duplicate signals")
    else:
        print(f"🔍 Would delete {total_deleted} duplicate signals")
    
    print("\n" + "=" * 70)
    
    if dry_run:
        print("This was a DRY RUN - no changes made")
        print("To actually delete duplicates, run:")
        print("  python fix_duplicate_signals.py --confirm")
    else:
        print("✅ DUPLICATES FIXED!")
        
        # Show final stats
        cursor.execute("SELECT COUNT(*) FROM signals")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM signals")
        unique = cursor.fetchone()[0]
        
        print(f"\nFinal state:")
        print(f"  Total signals: {total}")
        print(f"  Unique tickers: {unique}")
    
    print("=" * 70)
    
    conn.close()


if __name__ == '__main__':
    import sys
    
    # Check if --confirm flag provided
    if '--confirm' in sys.argv:
        print("⚠️  CONFIRMATION REQUIRED!")
        response = input("Are you sure you want to DELETE duplicate signals? (yes/no): ")
        
        if response.lower() == 'yes':
            fix_duplicates(dry_run=False)
        else:
            print("❌ Cancelled")
    else:
        # Dry run by default
        fix_duplicates(dry_run=True)
        print("\n💡 To actually fix, run: python fix_duplicate_signals.py --confirm")
