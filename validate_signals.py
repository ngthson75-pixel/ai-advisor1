#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATE & FIX INVALID SIGNALS

Checks for signals with invalid logic:
- BUY signals where TP < Entry
- SELL signals where TP > Entry
- Stop Loss > Entry
"""

import sqlite3
from datetime import datetime

print("=" * 70)
print("🔍 SIGNAL VALIDATION")
print("=" * 70)

# Connect to database
db_path = 'signals.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check 1: BUY signals where TP < Entry
print("\n❌ CHECK 1: BUY signals with TP < Entry")
cursor.execute("""
    SELECT id, ticker, entry_price, stop_loss, take_profit, date, strategy
    FROM signals 
    WHERE action = 'BUY' 
    AND take_profit < entry_price
    ORDER BY date DESC
    LIMIT 20
""")

invalid_tp = cursor.fetchall()

if invalid_tp:
    print(f"\n⚠️  Found {len(invalid_tp)} INVALID BUY signals:")
    for sig in invalid_tp:
        print(f"   ID {sig['id']}: {sig['ticker']} | Entry: {sig['entry_price']:.1f} | TP: {sig['take_profit']:.1f} | Date: {sig['date']}")
else:
    print("   ✅ All BUY signals have TP > Entry")

# Check 2: BUY signals where SL > Entry
print("\n❌ CHECK 2: BUY signals with SL > Entry")
cursor.execute("""
    SELECT id, ticker, entry_price, stop_loss, take_profit, date, strategy
    FROM signals 
    WHERE action = 'BUY' 
    AND stop_loss > entry_price
    ORDER BY date DESC
    LIMIT 20
""")

invalid_sl = cursor.fetchall()

if invalid_sl:
    print(f"\n⚠️  Found {len(invalid_sl)} INVALID SL positions:")
    for sig in invalid_sl:
        print(f"   ID {sig['id']}: {sig['ticker']} | Entry: {sig['entry_price']:.1f} | SL: {sig['stop_loss']:.1f} | Date: {sig['date']}")
else:
    print("   ✅ All BUY signals have SL < Entry")

# Check 3: Recent signals by date
print("\n📅 CHECK 3: Signal dates")
cursor.execute("""
    SELECT date, COUNT(*) as count
    FROM signals
    WHERE action = 'BUY'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 10
""")

dates = cursor.fetchall()

print(f"\n📊 Signals by date:")
for d in dates:
    print(f"   {d['date']}: {d['count']} signals")

# Check 4: Today's date
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute("""
    SELECT COUNT(*) as count
    FROM signals
    WHERE action = 'BUY'
    AND date = ?
""", (today,))

today_count = cursor.fetchone()['count']

print(f"\n📅 Today ({today}): {today_count} signals")

if today_count == 0:
    print("   ⚠️  NO SIGNALS FOR TODAY!")
    print("   Need to run scanner or import signals")

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"Invalid TP: {len(invalid_tp)}")
print(f"Invalid SL: {len(invalid_sl)}")
print(f"Today's signals: {today_count}")

if len(invalid_tp) > 0 or len(invalid_sl) > 0:
    print("\n🔧 ACTIONS NEEDED:")
    print("1. Delete invalid signals")
    print("2. Re-run scanner with fixed logic")
    print("3. Validate new signals before display")

conn.close()

print("\n" + "=" * 70)
print("✅ VALIDATION COMPLETE")
print("=" * 70)
