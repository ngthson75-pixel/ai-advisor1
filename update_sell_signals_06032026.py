#!/usr/bin/env python3
"""
UPDATE SELL SIGNALS - 06/03/2026
Sửa giá bán và lý do bán cho 4 signals hôm nay
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not found in .env")
    exit(1)

# Fix PostgreSQL URL
if db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)

print("="*70)
print("🔧 UPDATE SELL SIGNALS - 06/03/2026")
print("="*70)
print(f"Database: {db_url[:50]}...")
print()

# Updates to apply
updates = [
    # (ticker, exit_price, exit_reason, notes)
    ('HPG', 27000, 'STOP_LOSS', '-4% Stoploss'),
    ('CTD', 80600, 'STOP_LOSS', '-5% Stoploss'),
    ('PHR', 61300, 'STOP_LOSS', '-4.5% Stoploss'),
    ('STB', 63800, 'TAKE_PROFIT', '+4% Takeprofit'),
]

# Connect to database
engine = create_engine(db_url)

print("📋 Danh sách updates:")
print("Ticker | Exit Price (cũ) → (mới) | Exit Reason (cũ) → (mới) | Notes")
print("-------|-------------------------|--------------------------|--------")

with engine.connect() as conn:
    # Show current values
    for ticker, new_price, new_reason, notes in updates:
        result = conn.execute(text(f"""
            SELECT exit_price, exit_reason, entry_price
            FROM signals 
            WHERE ticker = '{ticker}' 
              AND action = 'SELL'
              AND exit_date = '2026-03-06'
        """))
        
        row = result.fetchone()
        if row:
            old_price = row[0]
            old_reason = row[1]
            entry = row[2]
            
            # Calculate P/L
            old_pl = ((old_price - entry) / entry * 100) if entry > 0 else 0
            new_pl = ((new_price - entry) / entry * 100) if entry > 0 else 0
            
            print(f"{ticker:<6} | {old_price:<10} → {new_price:<10} | {old_reason:<12} → {new_reason:<12} | {notes}")
            print(f"       | P/L: {old_pl:+.1f}% → {new_pl:+.1f}%")
        else:
            print(f"{ticker:<6} | ❌ NOT FOUND")

print("\n" + "="*70)
confirm = input("Confirm update? (y/n): ").strip().lower()

if confirm != 'y':
    print("❌ Update cancelled")
    exit(0)

print("\n🚀 Running updates...")

with engine.begin() as conn:
    for ticker, new_price, new_reason, notes in updates:
        result = conn.execute(text(f"""
            UPDATE signals 
            SET 
                exit_price = {new_price},
                exit_reason = '{new_reason}'
            WHERE ticker = '{ticker}' 
              AND action = 'SELL'
              AND exit_date = '2026-03-06'
        """))
        
        print(f"✅ Updated {ticker}: exit_price={new_price:,}, exit_reason={new_reason}")

print("\n" + "="*70)
print("✅ UPDATE COMPLETE!")
print("="*70)

# Verify updates
print("\n📊 Verification:")
print("Ticker | Entry   | Exit    | P/L      | Exit Reason")
print("-------|---------|---------|----------|-------------")

with engine.connect() as conn:
    for ticker, _, _, _ in updates:
        result = conn.execute(text(f"""
            SELECT entry_price, exit_price, exit_reason
            FROM signals 
            WHERE ticker = '{ticker}' 
              AND action = 'SELL'
              AND exit_date = '2026-03-06'
        """))
        
        row = result.fetchone()
        if row:
            entry = row[0]
            exit_p = row[1]
            reason = row[2]
            pl = ((exit_p - entry) / entry * 100) if entry > 0 else 0
            
            icon = '🔴' if reason == 'STOP_LOSS' else '🟢'
            print(f"{ticker:<6} | {entry:<7} | {exit_p:<7} | {pl:+6.1f}% | {icon} {reason}")

print("\n💡 Next step: Refresh https://ai-advisor.vn")
print("   Press Ctrl+Shift+R to see updates")
print("="*70)
