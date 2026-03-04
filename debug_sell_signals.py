#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG SELL SIGNALS DATABASE
============================

Kiểm tra SELL signals trong database

Cách chạy:
  cd C:\\ai-advisor1
  python debug_sell_signals.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')

print("\n" + "=" * 60)
print("🔍 DEBUG SELL SIGNALS DATABASE")
print("=" * 60)

# Check DB exists
if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit()

print(f"✅ Database: {DB_PATH}")

# Connect
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("\n" + "-" * 60)
print("📊 ALL SELL SIGNALS (NO DATE FILTER)")
print("-" * 60)

# Get ALL SELL signals (no date filter)
rows = conn.execute(
    "SELECT * FROM signals WHERE action='SELL' ORDER BY date DESC"
).fetchall()

print(f"Total SELL signals: {len(rows)}")

if rows:
    print(f"\n{'ID':<6} {'Ticker':<8} {'Strategy':<15} {'Entry':<10} {'Date':<12}")
    print("-" * 60)
    for r in rows:
        print(f"{r['id']:<6} {r['ticker']:<8} {r.get('strategy', 'N/A'):<15} {r['entry_price']:<10,.0f} {r.get('date', 'N/A'):<12}")

print("\n" + "-" * 60)
print("📅 SELL SIGNALS FOR TODAY")
print("-" * 60)

today = datetime.now().strftime('%Y-%m-%d')
print(f"Today: {today}")

rows_today = conn.execute(
    "SELECT * FROM signals WHERE action='SELL' AND date=? ORDER BY ticker",
    (today,)
).fetchall()

print(f"Total for today: {len(rows_today)}")

if rows_today:
    print(f"\n{'ID':<6} {'Ticker':<8} {'Strategy':<15} {'Entry':<10} {'Date':<12}")
    print("-" * 60)
    for r in rows_today:
        print(f"{r['id']:<6} {r['ticker']:<8} {r.get('strategy', 'N/A'):<15} {r['entry_price']:<10,.0f} {r.get('date', 'N/A'):<12}")

print("\n" + "-" * 60)
print("📋 DATABASE SCHEMA")
print("-" * 60)

# Get table schema
cursor = conn.execute("PRAGMA table_info(signals)")
columns = cursor.fetchall()

print("\nColumns in 'signals' table:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n" + "-" * 60)
print("💡 DIAGNOSTIC")
print("-" * 60)

if len(rows) == 0:
    print("❌ NO SELL signals in database at all!")
    print("   → Option 16 may not be working")
    print("   → Check if commit() is called")
elif len(rows_today) == 0:
    print("⚠️ SELL signals exist but NOT for today!")
    print(f"   Database dates: {[r['date'] for r in rows[:5]]}")
    print(f"   Today: {today}")
    print("   → Date mismatch!")
    print("   → Add signal with correct date")
else:
    print(f"✅ Found {len(rows_today)} SELL signals for today")

conn.close()

print("\n" + "=" * 60)
