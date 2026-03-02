#!/usr/bin/env python3
"""
Cleanup Duplicate Signals in Database
Removes duplicate BUY signals, keeping only the BEST one per ticker per day
"""

import sqlite3
from datetime import datetime
import shutil

DB_PATH = 'signals.db'

def backup_database():
    """Create backup before cleanup"""
    backup_name = f"signals.db.BACKUP_DEDUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Creating backup: {backup_name}")
    shutil.copy2(DB_PATH, backup_name)
    print(f"✅ Backup created")
    return backup_name


def find_duplicates():
    """
    Find duplicate BUY signals (same ticker, same date)
    Returns dict: {(ticker, date): [list of signal IDs]}
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Find all BUY signals grouped by ticker and date
        cursor.execute("""
            SELECT ticker, date, GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM signals
            WHERE action = 'BUY'
            GROUP BY ticker, date
            HAVING count > 1
            ORDER BY ticker, date
        """)
        
        duplicates = {}
        for row in cursor.fetchall():
            ticker, date, ids_str, count = row
            ids = [int(id) for id in ids_str.split(',')]
            duplicates[(ticker, date)] = ids
        
        conn.close()
        
        return duplicates
        
    except Exception as e:
        print(f"❌ Error finding duplicates: {e}")
        return {}


def get_signal_details(signal_id):
    """Get full signal details by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, ticker, entry_price, stop_loss, take_profit, 
                   strategy, strength, date, created_at
            FROM signals
            WHERE id = ?
        """, (signal_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'ticker': row[1],
                'entry_price': row[2],
                'stop_loss': row[3],
                'take_profit': row[4],
                'strategy': row[5],
                'score': row[6],
                'date': row[7],
                'created_at': row[8]
            }
        return None
        
    except Exception as e:
        print(f"❌ Error getting signal details: {e}")
        return None


def select_best_signal(signal_ids):
    """
    From a list of duplicate signal IDs, select the BEST one
    
    Priority:
    1. Highest score (strength)
    2. If same score → most recent created_at
    3. If same time → lowest ID (first created)
    """
    signals = [get_signal_details(sid) for sid in signal_ids]
    signals = [s for s in signals if s]  # Remove None
    
    if not signals:
        return None
    
    # Sort by: score DESC, created_at DESC, id ASC
    best = sorted(signals, 
                  key=lambda s: (-s.get('score', 0), 
                                -datetime.fromisoformat(s.get('created_at', '1970-01-01')).timestamp() if s.get('created_at') else 0,
                                s['id']))[0]
    
    return best


def cleanup_duplicates(dry_run=True):
    """
    Remove duplicate signals, keep only best one per ticker per date
    
    Args:
        dry_run: If True, only show what would be deleted (don't actually delete)
    """
    print("\n🔍 Finding duplicates...")
    duplicates = find_duplicates()
    
    if not duplicates:
        print("✅ No duplicates found! Database is clean.")
        return
    
    print(f"⚠️  Found {len(duplicates)} ticker-date pairs with duplicates")
    print()
    
    total_to_delete = 0
    deletion_plan = []
    
    for (ticker, date), signal_ids in duplicates.items():
        print(f"📊 {ticker} on {date}: {len(signal_ids)} signals")
        
        # Get best signal
        best = select_best_signal(signal_ids)
        
        if not best:
            print(f"  ❌ Error selecting best signal")
            continue
        
        # IDs to delete (all except best)
        ids_to_delete = [sid for sid in signal_ids if sid != best['id']]
        
        print(f"  ✅ Keep: ID={best['id']} (score={best['score']}%, strategy={best['strategy']})")
        print(f"  🗑️  Delete: {len(ids_to_delete)} signals (IDs: {ids_to_delete})")
        
        deletion_plan.append({
            'ticker': ticker,
            'date': date,
            'keep': best['id'],
            'delete': ids_to_delete
        })
        
        total_to_delete += len(ids_to_delete)
    
    print(f"\n📋 Summary:")
    print(f"  Total signals to delete: {total_to_delete}")
    print(f"  Ticker-date pairs affected: {len(duplicates)}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - No changes made")
        print(f"  Run with dry_run=False to actually delete")
        return deletion_plan
    
    # Actually delete
    print(f"\n🗑️  Deleting duplicate signals...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        deleted_count = 0
        
        for plan in deletion_plan:
            for signal_id in plan['delete']:
                cursor.execute("DELETE FROM signals WHERE id = ?", (signal_id,))
                deleted_count += 1
                print(f"  🗑️  Deleted signal ID={signal_id} ({plan['ticker']})")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Cleanup completed!")
        print(f"  Deleted: {deleted_count} duplicate signals")
        
    except Exception as e:
        print(f"❌ Error during deletion: {e}")


def main():
    """Main cleanup workflow"""
    print("="*70)
    print("🧹 CLEANUP DUPLICATE SIGNALS")
    print("="*70)
    
    # Create backup first
    backup_file = backup_database()
    
    # DRY RUN first - show what will be deleted
    print("\n" + "="*70)
    print("🔍 DRY RUN - Analyzing duplicates...")
    print("="*70)
    
    deletion_plan = cleanup_duplicates(dry_run=True)
    
    if not deletion_plan:
        print("\n✅ No cleanup needed!")
        return
    
    # Ask for confirmation
    print("\n" + "="*70)
    print("⚠️  CONFIRMATION REQUIRED")
    print("="*70)
    print(f"Backup saved: {backup_file}")
    print(f"Ready to delete {sum(len(p['delete']) for p in deletion_plan)} duplicate signals")
    
    response = input("\nProceed with deletion? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n🗑️  Proceeding with cleanup...")
        cleanup_duplicates(dry_run=False)
    else:
        print("\n❌ Cleanup cancelled")
    
    print("\n" + "="*70)
    print("✅ DONE")
    print("="*70)


if __name__ == '__main__':
    main()
