#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Database Locations - Find where signals are stored
"""

import os
import sqlite3

def check_db_location(db_path, name):
    """Check a database file"""
    print(f"\n{'='*70}")
    print(f"🔍 {name}")
    print(f"Path: {db_path}")
    print(f"{'='*70}")
    
    if not os.path.exists(db_path):
        print("❌ File does not exist")
        return
    
    abs_path = os.path.abspath(db_path)
    size = os.path.getsize(db_path)
    modified = os.path.getmtime(db_path)
    
    print(f"✅ File exists")
    print(f"   Absolute path: {abs_path}")
    print(f"   Size: {size:,} bytes")
    print(f"   Modified: {os.path.basename(db_path)} @ {os.path.getctime(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count signals
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        
        print(f"   Signals: {count}")
        
        if count > 0:
            # Get date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM signals")
            min_date, max_date = cursor.fetchone()
            print(f"   Date range: {min_date} to {max_date}")
            
            # Get sample
            cursor.execute("SELECT ticker, entry_price, date FROM signals LIMIT 3")
            samples = cursor.fetchall()
            
            print(f"\n   Sample signals:")
            for ticker, entry, date in samples:
                status = "✅ CORRECT" if entry >= 1000 else "❌ WRONG"
                print(f"   - {ticker}: {entry:,.2f} VND ({date}) {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")


def main():
    """Check all possible database locations"""
    
    print("="*70)
    print("🔍 DATABASE LOCATION FINDER")
    print("="*70)
    print(f"\nCurrent directory: {os.getcwd()}")
    
    # Check all possible locations
    locations = [
        ('signals.db', 'Root directory (C:\\ai-advisor1\\signals.db)'),
        ('scripts/signals.db', 'Scripts directory (C:\\ai-advisor1\\scripts\\signals.db)'),
        ('../signals.db', 'Parent directory (from scripts)'),
    ]
    
    for path, name in locations:
        check_db_location(path, name)
    
    print("\n" + "="*70)
    print("📊 RECOMMENDATION")
    print("="*70)
    
    # Find which one has correct data
    root_exists = os.path.exists('signals.db')
    scripts_exists = os.path.exists('scripts/signals.db')
    
    if scripts_exists:
        try:
            conn = sqlite3.connect('scripts/signals.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals")
            scripts_count = cursor.fetchone()[0]
            
            if scripts_count > 0:
                cursor.execute("SELECT entry_price FROM signals LIMIT 1")
                sample_price = cursor.fetchone()[0]
                conn.close()
                
                if sample_price >= 1000:
                    print("\n✅ FOUND CORRECT DATABASE: scripts/signals.db")
                    print("\nAction required:")
                    print("  cd C:\\ai-advisor1")
                    print("  copy scripts\\signals.db signals.db")
                    print("  python check_database.py")
        except:
            pass
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
