#!/usr/bin/env python3
"""
SQLite Migration Script - Signal Code
Run database migration using Python sqlite3 module
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = 'signals.db'

print("="*70)
print("🔧 SIGNAL CODE MIGRATION - SQLITE")
print("="*70)

# Check database exists
if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit(1)

print(f"✅ Found database: {DB_PATH}")

# Backup database
backup_name = f"signals.db.BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
print(f"\n📦 Creating backup: {backup_name}")
import shutil
shutil.copy2(DB_PATH, backup_name)
print(f"✅ Backup created")

# Connect to database
print(f"\n🔌 Connecting to database...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print(f"✅ Connected")

# Migration SQL
migrations = [
    # STEP 1: Add signal_code column
    {
        "name": "Add signal_code column",
        "sql": "ALTER TABLE signals ADD COLUMN signal_code VARCHAR(50);"
    },
    
    # STEP 2: Add buy_signal_code column
    {
        "name": "Add buy_signal_code column",
        "sql": "ALTER TABLE signals ADD COLUMN buy_signal_code VARCHAR(50);"
    },
    
    # STEP 3: Generate codes for existing BUY signals
    {
        "name": "Generate signal codes",
        "sql": """
            UPDATE signals 
            SET signal_code = ticker || '-' || id
            WHERE action = 'BUY' AND signal_code IS NULL;
        """
    },
    
    # STEP 4: Create index
    {
        "name": "Create index on signal_code",
        "sql": "CREATE INDEX IF NOT EXISTS idx_signals_code ON signals(signal_code);"
    },
    
    # STEP 5: Create index on buy_signal_code
    {
        "name": "Create index on buy_signal_code",
        "sql": "CREATE INDEX IF NOT EXISTS idx_signals_buy_code ON signals(buy_signal_code);"
    },
    
    # STEP 6: Link existing SELL signals to BUY signals (if linked_signal_id exists)
    {
        "name": "Link SELL signals to BUY signals (optional)",
        "sql": """
            UPDATE signals AS sell
            SET buy_signal_code = (
                SELECT buy.signal_code
                FROM signals AS buy
                WHERE buy.id = sell.linked_signal_id
                  AND buy.action = 'BUY'
            )
            WHERE sell.action = 'SELL'
              AND sell.linked_signal_id IS NOT NULL
              AND sell.buy_signal_code IS NULL;
        """,
        "optional": True  # Skip if column doesn't exist
    }
]

# Run migrations
print(f"\n🚀 Running migrations...\n")
for i, migration in enumerate(migrations, 1):
    try:
        print(f"Step {i}/{len(migrations)}: {migration['name']}")
        cursor.execute(migration['sql'])
        conn.commit()
        print(f"  ✅ Success")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"  ⚠️  Column already exists, skipping")
        elif "already exists" in str(e).lower():
            print(f"  ⚠️  Index already exists, skipping")
        elif "no such column" in str(e).lower() and migration.get('optional', False):
            print(f"  ⚠️  Optional step skipped (column not found)")
            conn.rollback()
        else:
            print(f"  ❌ Error: {e}")
            conn.rollback()
            raise
    except Exception as e:
        print(f"  ❌ Error: {e}")
        conn.rollback()
        raise

# Verification
print(f"\n🔍 VERIFICATION")
print("="*70)

# Check BUY signals with codes
cursor.execute("""
    SELECT 
        COUNT(*) as total_buy_signals,
        COUNT(signal_code) as signals_with_code
    FROM signals
    WHERE action = 'BUY'
""")
result = cursor.fetchone()
total_buy = result[0]
with_code = result[1]

print(f"\nBUY Signals:")
print(f"  Total: {total_buy}")
print(f"  With code: {with_code}")
print(f"  Percentage: {(with_code/total_buy*100) if total_buy > 0 else 0:.1f}%")

if total_buy > 0 and with_code == total_buy:
    print(f"  ✅ All BUY signals have codes!")
else:
    print(f"  ⚠️  Some BUY signals missing codes")

# Sample signals - check if status/position_pct columns exist
cursor.execute("PRAGMA table_info(signals)")
columns = [col[1] for col in cursor.fetchall()]
has_status = 'status' in columns
has_position = 'position_pct' in columns

if has_status and has_position:
    cursor.execute("""
        SELECT id, signal_code, ticker, entry_price, status, position_pct
        FROM signals
        WHERE action = 'BUY'
        ORDER BY id DESC
        LIMIT 5
    """)
    print(f"\nSample BUY signals:")
    print(f"{'ID':<6} {'Code':<15} {'Ticker':<8} {'Entry':<12} {'Status':<10} {'Position':<8}")
    print("-"*70)
    for row in cursor.fetchall():
        signal_id, code, ticker, entry, status, position = row
        code_str = code or "NULL"
        status_str = status or "NULL"
        position_str = f"{position}%" if position is not None else "NULL"
        print(f"{signal_id:<6} {code_str:<15} {ticker:<8} {entry:<12,.0f} {status_str:<10} {position_str:<8}")
else:
    cursor.execute("""
        SELECT id, signal_code, ticker, entry_price
        FROM signals
        WHERE action = 'BUY'
        ORDER BY id DESC
        LIMIT 5
    """)
    print(f"\nSample BUY signals:")
    print(f"{'ID':<6} {'Code':<15} {'Ticker':<8} {'Entry':<12}")
    print("-"*70)
    for row in cursor.fetchall():
        signal_id, code, ticker, entry = row
        code_str = code or "NULL"
        print(f"{signal_id:<6} {code_str:<15} {ticker:<8} {entry:<12,.0f}")
    if not has_status:
        print(f"\n  ⓘ  Note: status/position_pct columns not present (position tracking not deployed yet)")

# Check SELL signals linking (if applicable)
try:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM signals 
        WHERE action = 'SELL' 
          AND buy_signal_code IS NOT NULL
    """)
    linked_sells = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) 
        FROM signals 
        WHERE action = 'SELL'
    """)
    total_sells = cursor.fetchone()[0]

    print(f"\nSELL Signals:")
    print(f"  Total: {total_sells}")
    print(f"  Linked to BUY: {linked_sells}")
    if total_sells > 0:
        print(f"  Percentage: {(linked_sells/total_sells*100):.1f}%")
    if linked_sells == 0 and total_sells > 0:
        print(f"  ⓘ  Note: SELL signals not linked (linked_signal_id column not present)")
except Exception as e:
    print(f"\nSELL Signals:")
    print(f"  ⚠️  Could not verify SELL signal linking: {e}")

# Close connection
conn.close()

print(f"\n" + "="*70)
print(f"🎉 MIGRATION COMPLETED SUCCESSFULLY!")
print(f"="*70)
print(f"\nBackup saved: {backup_name}")
print(f"Database: {DB_PATH}")
print(f"\n✅ Ready to update backend code!")
