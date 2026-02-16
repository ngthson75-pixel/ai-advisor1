#!/usr/bin/env python3
"""
Add Position Tracking Columns - status, position_pct
Completes the full signal code tracking feature
"""

import sqlite3
import os
from datetime import datetime
import shutil

DB_PATH = 'signals.db'

print("="*70)
print("🔧 POSITION TRACKING MIGRATION - ADD STATUS & POSITION")
print("="*70)

# Check database exists
if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit(1)

print(f"✅ Found database: {DB_PATH}")

# Backup database
backup_name = f"signals.db.BACKUP_POSITION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
print(f"\n📦 Creating backup: {backup_name}")
shutil.copy2(DB_PATH, backup_name)
print(f"✅ Backup created")

# Connect to database
print(f"\n🔌 Connecting to database...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
print(f"✅ Connected")

# Check if columns already exist
cursor.execute("PRAGMA table_info(signals)")
columns = [col[1] for col in cursor.fetchall()]
has_status = 'status' in columns
has_position = 'position_pct' in columns

print(f"\n🔍 Current schema:")
print(f"  Total columns: {len(columns)}")
print(f"  Has status: {has_status}")
print(f"  Has position_pct: {has_position}")

# Migration steps
migrations = []

if not has_status:
    migrations.append({
        "name": "Add status column",
        "sql": "ALTER TABLE signals ADD COLUMN status VARCHAR(20) DEFAULT 'open';"
    })

if not has_position:
    migrations.append({
        "name": "Add position_pct column",
        "sql": "ALTER TABLE signals ADD COLUMN position_pct INTEGER DEFAULT 100;"
    })

if not migrations:
    print(f"\n✅ Columns already exist! No migration needed.")
else:
    print(f"\n🚀 Running {len(migrations)} migration(s)...\n")
    
    for i, migration in enumerate(migrations, 1):
        try:
            print(f"Step {i}/{len(migrations)}: {migration['name']}")
            cursor.execute(migration['sql'])
            conn.commit()
            print(f"  ✅ Success")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  ⚠️  Column already exists, skipping")
            else:
                print(f"  ❌ Error: {e}")
                conn.rollback()
                raise
        except Exception as e:
            print(f"  ❌ Error: {e}")
            conn.rollback()
            raise

# Update existing BUY signals to have status='open' and position_pct=100
print(f"\n🔄 Updating existing BUY signals...")
cursor.execute("""
    UPDATE signals 
    SET status = 'open', position_pct = 100
    WHERE action = 'BUY' 
      AND (status IS NULL OR position_pct IS NULL)
""")
updated = cursor.rowcount
conn.commit()
print(f"  ✅ Updated {updated} BUY signals")

# Update existing SELL signals to have status='closed' and position_pct=0
print(f"\n🔄 Updating existing SELL signals...")
cursor.execute("""
    UPDATE signals 
    SET status = 'closed', position_pct = 0
    WHERE action = 'SELL'
      AND (status IS NULL OR position_pct IS NULL)
""")
updated = cursor.rowcount
conn.commit()
print(f"  ✅ Updated {updated} SELL signals")

# Verification
print(f"\n🔍 VERIFICATION")
print("="*70)

cursor.execute("PRAGMA table_info(signals)")
columns = [col[1] for col in cursor.fetchall()]

has_signal_code = 'signal_code' in columns
has_buy_signal_code = 'buy_signal_code' in columns
has_status = 'status' in columns
has_position = 'position_pct' in columns

print(f"\nColumn check:")
print(f"  signal_code: {has_signal_code} ✅" if has_signal_code else "  signal_code: False ❌")
print(f"  buy_signal_code: {has_buy_signal_code} ✅" if has_buy_signal_code else "  buy_signal_code: False ❌")
print(f"  status: {has_status} ✅" if has_status else "  status: False ❌")
print(f"  position_pct: {has_position} ✅" if has_position else "  position_pct: False ❌")

# Sample data
cursor.execute("""
    SELECT id, signal_code, ticker, action, status, position_pct
    FROM signals
    WHERE action = 'BUY'
    ORDER BY id DESC
    LIMIT 5
""")

print(f"\nSample BUY signals:")
print(f"{'ID':<6} {'Code':<15} {'Ticker':<8} {'Action':<6} {'Status':<10} {'Position':<8}")
print("-"*70)
for row in cursor.fetchall():
    signal_id, code, ticker, action, status, position = row
    code_str = code or f"#{signal_id}"
    status_str = status or "NULL"
    position_str = f"{position}%" if position is not None else "NULL"
    print(f"{signal_id:<6} {code_str:<15} {ticker:<8} {action:<6} {status_str:<10} {position_str:<8}")

# Summary
cursor.execute("SELECT COUNT(*) FROM signals WHERE action='BUY'")
total_buy = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM signals WHERE action='BUY' AND status='open'")
open_buy = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM signals WHERE action='SELL'")
total_sell = cursor.fetchone()[0]

print(f"\nSummary:")
print(f"  Total BUY signals: {total_buy}")
print(f"  Open BUY signals: {open_buy}")
print(f"  Total SELL signals: {total_sell}")

# Close connection
conn.close()

print(f"\n" + "="*70)
print(f"🎉 MIGRATION COMPLETED SUCCESSFULLY!")
print(f"="*70)
print(f"\nBackup saved: {backup_name}")
print(f"Database: {DB_PATH}")

if has_signal_code and has_buy_signal_code and has_status and has_position:
    print(f"\n✅ All columns present:")
    print(f"  1. signal_code ✅")
    print(f"  2. buy_signal_code ✅")
    print(f"  3. status ✅")
    print(f"  4. position_pct ✅")
    print(f"\n✅ Ready for full position tracking!")
else:
    print(f"\n⚠️  Warning: Some columns missing, manual check needed")

print(f"\nNext steps:")
print(f"1. Restart backend: python backend_api.py")
print(f"2. Update frontend with status & position columns")
print(f"3. Test position tracking features")
