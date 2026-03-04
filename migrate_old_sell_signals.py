#!/usr/bin/env python3
"""
MIGRATE OLD SELL SIGNALS
Fill exit_price, exit_reason, exit_date for signals created by old scanner
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
print("🔧 MIGRATE OLD SELL SIGNALS")
print("="*70)
print(f"Database: {db_url[:50]}...")
print()

# Connect to database
engine = create_engine(db_url)

with engine.begin() as conn:
    # 1. Check how many SELL signals need migration
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM signals 
        WHERE action='SELL' 
          AND exit_reason IS NULL
    """))
    
    count = result.fetchone()[0]
    
    print(f"📊 Found {count} SELL signals needing migration")
    
    if count == 0:
        print("✅ No migration needed!")
        exit(0)
    
    # 2. Show sample before migration
    print("\n📋 Sample BEFORE migration:")
    result = conn.execute(text("""
        SELECT ticker, strategy, stop_loss, take_profit, exit_price, exit_reason
        FROM signals 
        WHERE action='SELL' 
          AND exit_reason IS NULL
        ORDER BY created_at DESC
        LIMIT 3
    """))
    
    print("Ticker | Strategy      | SL      | TP      | exit_price | exit_reason")
    print("-------|---------------|---------|---------|------------|-------------")
    for row in result:
        print(f"{row[0]:<6} | {row[1]:<13} | {row[2]:<7} | {row[3]:<7} | {str(row[4]):<10} | {str(row[5])}")
    
    # 3. Confirm migration
    print(f"\n⚠️  About to migrate {count} SELL signals")
    print("This will set:")
    print("  - exit_reason = strategy")
    print("  - exit_price = stop_loss (if STOP_LOSS) or take_profit (if TAKE_PROFIT)")
    print("  - exit_date = date (entry date)")
    
    confirm = input("\nContinue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Migration cancelled")
        exit(0)
    
    # 4. Run migration
    print("\n🚀 Running migration...")
    
    result = conn.execute(text("""
        UPDATE signals 
        SET 
          exit_reason = strategy,
          exit_price = CASE
            WHEN strategy = 'STOP_LOSS' THEN stop_loss
            WHEN strategy = 'TAKE_PROFIT' THEN take_profit
            WHEN strategy = 'MA20_BREAK' THEN stop_loss
            ELSE stop_loss
          END,
          exit_date = date
        WHERE action = 'SELL' 
          AND exit_reason IS NULL
    """))
    
    print(f"✅ Updated {count} signals")
    
    # 5. Show sample after migration
    print("\n📋 Sample AFTER migration:")
    result = conn.execute(text("""
        SELECT ticker, strategy, exit_price, exit_reason, exit_date, entry_price
        FROM signals 
        WHERE action='SELL'
        ORDER BY created_at DESC
        LIMIT 5
    """))
    
    print("Ticker | Strategy      | exit_price | exit_reason   | exit_date  | entry_price")
    print("-------|---------------|------------|---------------|------------|-------------")
    for row in result:
        entry = row[5] or 0
        exit_p = row[2] or 0
        pl = ((exit_p - entry) / entry * 100) if entry > 0 and exit_p > 0 else 0
        print(f"{row[0]:<6} | {row[1]:<13} | {row[2]:<10} | {row[3]:<13} | {row[4]:<10} | {entry:<7} (P/L: {pl:+.1f}%)")
    
    # 6. Summary
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETE!")
    print("="*70)
    print(f"Total signals migrated: {count}")
    print("\nNext steps:")
    print("1. Deploy updated frontend (SignalsModule.jsx)")
    print("2. Refresh ai-advisor.vn")
    print("3. Click 'Tín hiệu BÁN' tab")
    print("4. Verify exit_price and P/L display correctly")
    print("="*70)
