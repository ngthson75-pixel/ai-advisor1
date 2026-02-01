#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Database Check - Verify if prices are correct
"""

import sqlite3
import os

def check_database():
    """Check if database has correct prices"""
    
    db_path = 'signals.db'
    
    if not os.path.exists(db_path):
        print("❌ signals.db not found!")
        print(f"   Looking in: {os.path.abspath('.')}")
        return
    
    print("="*70)
    print("🔍 DATABASE PRICE CHECK")
    print("="*70)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get first 5 signals
        cursor.execute("""
            SELECT ticker, entry_price, stop_loss, take_profit, strategy, date
            FROM signals 
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("\n⚠️  Database is EMPTY!")
            print("   No signals found.")
            conn.close()
            return
        
        print(f"\n✅ Found {len(rows)} signals in database\n")
        print("="*70)
        
        correct_count = 0
        wrong_count = 0
        
        for i, row in enumerate(rows, 1):
            ticker, entry, sl, tp, strategy, date = row
            
            print(f"\nSignal #{i}:")
            print(f"  Ticker:   {ticker}")
            print(f"  Strategy: {strategy}")
            print(f"  Date:     {date}")
            print(f"  Entry:    {entry:,.2f} VND")
            print(f"  Stop:     {sl:,.2f} VND")
            print(f"  Target:   {tp:,.2f} VND")
            
            # Check if price looks correct
            if entry >= 1000:  # Should be at least 1,000 VND
                print(f"  Status:   ✅ CORRECT (price in normal range)")
                correct_count += 1
            else:
                print(f"  Status:   ❌ WRONG (price too small - needs × 1000)")
                wrong_count += 1
        
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        print(f"Total signals checked: {len(rows)}")
        print(f"Correct prices (≥1000):  {correct_count} ✅")
        print(f"Wrong prices (<1000):    {wrong_count} ❌")
        
        if wrong_count > 0:
            print("\n" + "="*70)
            print("🚨 CRITICAL ISSUE DETECTED!")
            print("="*70)
            print("Database has WRONG prices (too small by 1000x)!")
            print("\nIMPACT:")
            print("  • All entry prices are wrong")
            print("  • All stop loss values are wrong")
            print("  • All take profit targets are wrong")
            print("  • Users seeing incorrect signals!")
            print("\nACTION REQUIRED:")
            print("  1. Deploy fixed scanner immediately")
            print("  2. Re-run scanner to regenerate signals")
            print("  3. Verify new data is correct")
            print("  4. Notify users if they received wrong signals")
            
        elif correct_count > 0:
            print("\n" + "="*70)
            print("✅ DATABASE IS CORRECT!")
            print("="*70)
            print("Prices are in correct VND units.")
            print("\nMystery: Scanner file lacks conversion × 1000")
            print("But database has correct values!")
            print("\nPossible reasons:")
            print("  • Backend API doing conversion")
            print("  • Deployed version different from uploaded file")
            print("  • Database already had data from earlier version")
            print("\nRECOMMENDATION:")
            print("  • Deploy fixed scanner anyway (safety measure)")
            print("  • Update test scripts (already done)")
            print("  • Monitor next scan to ensure consistency")
        
        conn.close()
        
        print("\n" + "="*70)
        
        # Return status
        return wrong_count == 0
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    check_database()
