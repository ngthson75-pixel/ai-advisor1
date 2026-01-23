#!/usr/bin/env python3
"""Check if user data is properly isolated"""

import sqlite3

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

print("=" * 70)
print("🔍 USER DATA ISOLATION CHECK")
print("=" * 70)

# Check portfolios
cursor.execute("SELECT DISTINCT user_id, COUNT(*) FROM portfolios GROUP BY user_id")
portfolio_users = cursor.fetchall()

print(f"\n📊 PORTFOLIOS:")
print(f"   Unique user_ids: {len(portfolio_users)}")
for user_id, count in portfolio_users:
    print(f"   user_id={user_id}: {count} stocks")

# Check chat history
cursor.execute("SELECT DISTINCT user_id, COUNT(*) FROM chat_history GROUP BY user_id")
chat_users = cursor.fetchall()

print(f"\n💬 CHAT HISTORY:")
print(f"   Unique user_ids: {len(chat_users)}")
for user_id, count in chat_users:
    print(f"   user_id={user_id}: {count} messages")

# Sample portfolio data
print(f"\n📝 SAMPLE PORTFOLIO DATA:")
cursor.execute("SELECT user_id, ticker, quantity FROM portfolios LIMIT 5")
for row in cursor.fetchall():
    print(f"   user_id={row[0]}: {row[1]} ({row[2]} shares)")

# Sample chat data
print(f"\n💬 SAMPLE CHAT DATA:")
cursor.execute("SELECT user_id, substr(message, 1, 50) FROM chat_history LIMIT 3")
for row in cursor.fetchall():
    print(f"   user_id={row[0]}: {row[1]}...")

print("\n" + "=" * 70)
print("⚠️  ISSUE: All data likely has user_id=1 (hardcoded)")
print("=" * 70)

conn.close()
