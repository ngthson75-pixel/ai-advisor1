#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATABASE SCHEMA UPDATE FOR SELL SIGNALS

Adds tracking columns:
- signal_status: ACTIVE, PARTIAL_SOLD, FULLY_SOLD
- quantity_sold: Percentage sold (0-100)
"""

import sqlite3
import os

def update_database():
    """Add new columns for sell signal tracking"""
    
    # Path to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'signals.db')
    
    print("=" * 70)
    print("📊 DATABASE SCHEMA UPDATE - SELL SIGNALS")
    print("=" * 70)
    print(f"\n📁 Database: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"\n❌ Database not found: {db_path}")
        print("Please run backend first to create database")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(signals)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📋 Current columns: {len(columns)}")
        
        # Add signal_status if not exists
        if 'signal_status' not in columns:
            print("\n➕ Adding column: signal_status")
            cursor.execute("""
                ALTER TABLE signals 
                ADD COLUMN signal_status TEXT DEFAULT 'ACTIVE'
            """)
            print("   ✅ Done")
        else:
            print("\n✅ Column 'signal_status' already exists")
        
        # Add quantity_sold if not exists
        if 'quantity_sold' not in columns:
            print("\n➕ Adding column: quantity_sold")
            cursor.execute("""
                ALTER TABLE signals 
                ADD COLUMN quantity_sold REAL DEFAULT 0
            """)
            print("   ✅ Done")
        else:
            print("\n✅ Column 'quantity_sold' already exists")
        
        # Update existing BUY signals to ACTIVE
        print("\n🔄 Updating existing signals...")
        cursor.execute("""
            UPDATE signals 
            SET signal_status = 'ACTIVE', 
                quantity_sold = 0
            WHERE action = 'BUY' 
            AND (signal_status IS NULL OR signal_status = '')
        """)
        updated = cursor.rowcount
        print(f"   ✅ Updated {updated} BUY signals to ACTIVE")
        
        # Commit changes
        conn.commit()
        
        # Verify - Check updated schema
        cursor.execute("PRAGMA table_info(signals)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n✅ Schema updated! Now has {len(new_columns)} columns")
        
        # Show sample data
        cursor.execute("""
            SELECT ticker, action, signal_status, quantity_sold, date
            FROM signals 
            WHERE action = 'BUY'
            ORDER BY date DESC
            LIMIT 5
        """)
        results = cursor.fetchall()
        
        if results:
            print("\n" + "=" * 70)
            print("📋 SAMPLE DATA (Latest 5 BUY signals):")
            print("=" * 70)
            print(f"{'Ticker':<8} {'Action':<8} {'Status':<15} {'Sold %':<10} {'Date':<12}")
            print("-" * 70)
            for row in results:
                print(f"{row[0]:<8} {row[1]:<8} {row[2]:<15} {row[3]:<10.1f} {row[4]:<12}")
        
        # Count active signals
        cursor.execute("""
            SELECT COUNT(*) 
            FROM signals 
            WHERE action = 'BUY' AND signal_status = 'ACTIVE'
        """)
        active_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 70)
        print(f"✅ DATABASE READY!")
        print("=" * 70)
        print(f"📊 Active BUY signals: {active_count}")
        print("🎯 Ready to generate SELL signals!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating database: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    success = update_database()
    exit(0 if success else 1)
