#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST ADD SELL SIGNAL MANUAL
============================

Test thêm SELL signal trực tiếp vào database

Cách chạy:
  cd C:\\ai-advisor1
  python test_add_sell_manual.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')

print("\n" + "=" * 60)
print("🧪 TEST ADD SELL SIGNAL MANUAL")
print("=" * 60)

# Check DB
if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit()

print(f"✅ Database: {DB_PATH}")

# Test data
ticker = "TEST"
entry = 100000
exit_price = 110000
pl_pct = ((exit_price - entry) / entry) * 100
exit_reason = "TAKE_PROFIT"
exit_qty = 100
position_pct = 0
stock_type = "Mid Cap"
today = datetime.now().strftime('%Y-%m-%d')

print(f"\n📋 Test signal:")
print(f"   Ticker: {ticker}")
print(f"   Entry: {entry:,.0f}")
print(f"   Exit: {exit_price:,.0f}")
print(f"   P/L: {pl_pct:+.2f}%")
print(f"   Date: {today}")

# Connect
conn = sqlite3.connect(DB_PATH)

# Try INSERT with exit_price
print(f"\n1️⃣ Trying INSERT with exit_price column...")
try:
    conn.execute(
        """INSERT INTO signals (ticker, action, entry_price, exit_price, stop_loss, take_profit, 
           strategy, strength, stock_type, date, rsi, is_priority, 
           position_pct, status)
           VALUES (?, 'SELL', ?, ?, 0, 0, ?, 80, ?, ?, 50, 0, ?, ?)""",
        (ticker, entry, exit_price, exit_reason, stock_type, today, position_pct, 'closed')
    )
    conn.commit()
    print("   ✅ SUCCESS with exit_price column!")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print(f"\n2️⃣ Trying INSERT WITHOUT exit_price column...")
    
    try:
        conn.execute(
            """INSERT INTO signals (ticker, action, entry_price, stop_loss, take_profit, 
               strategy, strength, stock_type, date, rsi, is_priority, 
               position_pct, status)
               VALUES (?, 'SELL', ?, 0, 0, ?, 80, ?, ?, 50, 0, ?, ?)""",
            (ticker, entry, exit_reason, stock_type, today, position_pct, 'closed')
        )
        conn.commit()
        print("   ✅ SUCCESS without exit_price column!")
    except Exception as e2:
        print(f"   ❌ FAILED: {e2}")
        conn.close()
        exit()

# Verify
print(f"\n3️⃣ Verifying signal in database...")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT * FROM signals WHERE action='SELL' AND ticker=?",
    (ticker,)
).fetchall()

if rows:
    print(f"   ✅ Found {len(rows)} TEST signal(s)")
    for r in rows:
        print(f"      ID: {r['id']}")
        print(f"      Ticker: {r['ticker']}")
        print(f"      Strategy: {r.get('strategy', 'N/A')}")
        print(f"      Entry: {r['entry_price']}")
        print(f"      Exit: {r.get('exit_price', 'N/A')}")
        print(f"      Date: {r['date']}")
else:
    print(f"   ❌ Signal not found in database!")

# Check today's SELL signals
print(f"\n4️⃣ Checking all SELL signals for {today}...")
rows_today = conn.execute(
    "SELECT * FROM signals WHERE action='SELL' AND date=?",
    (today,)
).fetchall()

print(f"   Total SELL signals for today: {len(rows_today)}")
if rows_today:
    for r in rows_today:
        print(f"      {r['ticker']} — {r.get('strategy', 'N/A')}")

# Cleanup
print(f"\n5️⃣ Cleanup test signal...")
confirm = input("   Delete TEST signal? (y/n): ").strip().lower()
if confirm == 'y':
    conn.execute("DELETE FROM signals WHERE ticker=?", (ticker,))
    conn.commit()
    print("   ✅ Deleted TEST signal")

conn.close()

print("\n" + "=" * 60)
print("🎯 DIAGNOSIS:")
print("=" * 60)

if len(rows) > 0:
    print("✅ ADD function works! Signal CAN be saved to database")
    print("\nIf Option 16 not working, check:")
    print("  1. File đã replace đúng chưa?")
    print("  2. Python cache: del __pycache__")
    print("  3. Import lại: Ctrl+C → python signal_reviewer.py")
else:
    print("❌ ADD function has issues")
    print("\nPossible causes:")
    print("  1. Database locked")
    print("  2. Permissions issue")
    print("  3. Disk full")

print("\n" + "=" * 60)
