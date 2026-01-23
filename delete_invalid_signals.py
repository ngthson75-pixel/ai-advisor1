#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DELETE INVALID SIGNALS & FIX DATA
"""

import sqlite3
from datetime import datetime

print("=" * 70)
print("🔧 DELETE INVALID SIGNALS")
print("=" * 70)

db_path = 'signals.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count invalid signals BEFORE deletion
cursor.execute("""
    SELECT COUNT(*) FROM signals 
    WHERE action = 'BUY' 
    AND (take_profit < entry_price OR stop_loss > entry_price)
""")
invalid_count = cursor.fetchone()[0]

print(f"\n📊 Found {invalid_count} invalid BUY signals")

if invalid_count == 0:
    print("✅ No invalid signals to delete!")
    conn.close()
    exit(0)

# Show examples
cursor.execute("""
    SELECT id, ticker, entry_price, stop_loss, take_profit, date
    FROM signals 
    WHERE action = 'BUY' 
    AND (take_profit < entry_price OR stop_loss > entry_price)
    LIMIT 5
""")

print("\n📋 Examples of invalid signals:")
for row in cursor.fetchall():
    print(f"   ID {row[0]}: {row[1]} | Entry: {row[2]:.1f} | SL: {row[3]:.1f} | TP: {row[4]:.1f} | {row[5]}")

# Confirm deletion
response = input(f"\n❓ Delete {invalid_count} invalid signals? (yes/no): ")

if response.lower() not in ['yes', 'y']:
    print("❌ Cancelled")
    conn.close()
    exit(0)

# Delete invalid signals
cursor.execute("""
    DELETE FROM signals 
    WHERE action = 'BUY' 
    AND (take_profit < entry_price OR stop_loss > entry_price)
""")

deleted = cursor.rowcount
conn.commit()

print(f"\n✅ Deleted {deleted} invalid signals")

# Check remaining
cursor.execute("SELECT COUNT(*) FROM signals WHERE action = 'BUY'")
remaining = cursor.fetchone()[0]

print(f"📊 Remaining BUY signals: {remaining}")

# Show date distribution
cursor.execute("""
    SELECT date, COUNT(*) as count
    FROM signals
    WHERE action = 'BUY'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 5
""")

print("\n📅 Signals by date:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]} signals")

print("\n" + "=" * 70)
print("✅ CLEANUP COMPLETE")
print("=" * 70)

conn.close()
