#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUICK DATABASE INSPECTOR

Shows your exact database schema and sample data
"""

import sqlite3
import sys

def inspect_database(db_path='signals.db'):
    """Inspect database and show schema"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 70)
        print("🔍 DATABASE INSPECTOR")
        print("=" * 70)
        print(f"\nDatabase: {db_path}\n")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Tables found: {len(tables)}")
        for table in tables:
            print(f"   → {table[0]}")
        
        if not any(t[0] == 'signals' for t in tables):
            print("\n❌ ERROR: 'signals' table not found!")
            conn.close()
            return
        
        # Get signals table schema
        print("\n" + "=" * 70)
        print("📋 SIGNALS TABLE SCHEMA")
        print("=" * 70)
        
        cursor.execute("PRAGMA table_info(signals)")
        columns = cursor.fetchall()
        
        print(f"\n{'Column Name':<25} {'Type':<15} {'Nullable'}")
        print("-" * 70)
        for col in columns:
            nullable = "NOT NULL" if col[3] else "NULL"
            print(f"{col[1]:<25} {col[2]:<15} {nullable}")
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM signals")
        total = cursor.fetchone()[0]
        
        print("\n" + "=" * 70)
        print("📈 DATA STATISTICS")
        print("=" * 70)
        print(f"\nTotal signals: {total}")
        
        if total == 0:
            print("⚠️  Database is empty!")
            conn.close()
            return
        
        # Try to find date column
        date_cols = ['date', 'detected_at', 'created_at', 'timestamp']
        date_col = None
        for col in columns:
            if col[1] in date_cols:
                date_col = col[1]
                break
        
        if date_col:
            cursor.execute(f"""
                SELECT {date_col}, COUNT(*) 
                FROM signals 
                GROUP BY {date_col} 
                ORDER BY {date_col} DESC
            """)
            by_date = cursor.fetchall()
            
            print(f"\nBy {date_col}:")
            for date, count in by_date[:10]:
                print(f"  {date}: {count} signals")
            
            if len(by_date) > 10:
                print(f"  ... and {len(by_date) - 10} more dates")
        
        # Show sample row
        print("\n" + "=" * 70)
        print("📝 SAMPLE SIGNAL (first row)")
        print("=" * 70)
        
        cursor.execute("SELECT * FROM signals LIMIT 1")
        sample = cursor.fetchone()
        
        if sample:
            for i, col in enumerate(columns):
                value = sample[i]
                if isinstance(value, str) and len(str(value)) > 50:
                    value = str(value)[:50] + "..."
                print(f"{col[1]:<25} = {value}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ INSPECTION COMPLETE")
        print("=" * 70)
        
    except FileNotFoundError:
        print(f"❌ ERROR: Database file '{db_path}' not found!")
        print(f"\nCurrent directory: {os.getcwd()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description='Inspect database schema')
    parser.add_argument('--db', default='signals.db', help='Database file path')
    args = parser.parse_args()
    
    inspect_database(args.db)
