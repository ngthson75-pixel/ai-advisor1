#!/usr/bin/env python3
"""
Test user isolation với fake data
"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

print("=" * 70)
print("🧪 TESTING USER ISOLATION")
print("=" * 70)

# Clean old test data
print("\n1️⃣  Cleaning old test data...")
cursor.execute("DELETE FROM portfolios WHERE user_id IN (1, 2, 3)")
cursor.execute("DELETE FROM chat_history WHERE user_id IN (1, 2, 3)")
conn.commit()
print("✅ Cleaned")

# Insert fake data for 3 different users
print("\n2️⃣  Inserting fake data for 3 users...")

# User 1
cursor.execute("""
    INSERT INTO portfolios (user_id, ticker, quantity, avg_price, created_at)
    VALUES (1, 'VCB', 100, 85000, ?)
""", (datetime.now(),))

cursor.execute("""
    INSERT INTO portfolios (user_id, ticker, quantity, avg_price, created_at)
    VALUES (1, 'VNM', 50, 95000, ?)
""", (datetime.now(),))

cursor.execute("""
    INSERT INTO chat_history (user_id, message, response, created_at)
    VALUES (1, 'Tôi nên mua VCB?', 'VCB là cổ phiếu blue-chip tốt...', ?)
""", (datetime.now(),))

# User 2
cursor.execute("""
    INSERT INTO portfolios (user_id, ticker, quantity, avg_price, created_at)
    VALUES (2, 'HPG', 200, 25000, ?)
""", (datetime.now(),))

cursor.execute("""
    INSERT INTO chat_history (user_id, message, response, created_at)
    VALUES (2, 'Phân tích HPG cho tôi', 'HPG là cổ phiếu thép...', ?)
""", (datetime.now(),))

# User 3
cursor.execute("""
    INSERT INTO portfolios (user_id, ticker, quantity, avg_price, created_at)
    VALUES (3, 'MBB', 150, 28000, ?)
""", (datetime.now(),))

cursor.execute("""
    INSERT INTO portfolios (user_id, ticker, quantity, avg_price, created_at)
    VALUES (3, 'TCB', 80, 30000, ?)
""", (datetime.now(),))

conn.commit()
print("✅ Inserted fake data")

# Check isolation
print("\n3️⃣  Checking data isolation...")

cursor.execute("SELECT user_id, COUNT(*) FROM portfolios GROUP BY user_id")
portfolio_stats = cursor.fetchall()

print("\n📊 PORTFOLIOS BY USER:")
for user_id, count in portfolio_stats:
    print(f"   user_id={user_id}: {count} stocks")
    
    cursor.execute("SELECT ticker FROM portfolios WHERE user_id = ?", (user_id,))
    stocks = [row[0] for row in cursor.fetchall()]
    print(f"      → Stocks: {', '.join(stocks)}")

cursor.execute("SELECT user_id, COUNT(*) FROM chat_history GROUP BY user_id")
chat_stats = cursor.fetchall()

print("\n💬 CHAT BY USER:")
for user_id, count in chat_stats:
    print(f"   user_id={user_id}: {count} messages")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

print("\n📝 NEXT STEPS:")
print("1. Visit website in Browser 1")
print("2. Portfolio Manager should show:")
print("   - If website uses user_id=1: Shows VCB + VNM ❌ WRONG!")
print("   - If website uses unique ID: Shows EMPTY ✅ CORRECT!")
print("\n3. Visit website in Browser 2 (different)")
print("   - Should see DIFFERENT data than Browser 1")
print("\n4. Clean test data:")
print("   python -c \"import sqlite3; c=sqlite3.connect('signals.db'); c.execute('DELETE FROM portfolios WHERE user_id IN (1,2,3)'); c.execute('DELETE FROM chat_history WHERE user_id IN (1,2,3)'); c.commit()\"")

conn.close()
