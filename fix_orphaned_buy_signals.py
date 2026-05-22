#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX ORPHANED BUY SIGNALS
========================
Update BUY signals that have exit_date/exit_reason but status still 'open'

PROBLEM:
  Scanner creates SELL signal → writes exit_date, exit_reason
  BUT forgets to update status='closed'!

FIX:
  Find all BUY signals with:
    - status='open'
    - exit_date IS NOT NULL
  → Update status='closed'
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Add SSL mode if not present
if 'sslmode' not in DATABASE_URL:
    separator = '&' if '?' in DATABASE_URL else '?'
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

print(f"Connecting to: {DATABASE_URL[:50]}...")

# SQLAlchemy setup
Base = declarative_base()

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10))
    action = Column(String(10))
    entry_date = Column(String(20))
    entry_price = Column(Float)
    status = Column(String(20))
    exit_date = Column(String(20))
    exit_reason = Column(String(50))

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def main():
    session = Session()
    
    try:
        # Find orphaned BUY signals
        orphaned = session.query(Signal).filter(
            Signal.action == 'buy',
            Signal.status == 'open',
            Signal.exit_date.isnot(None),
            Signal.exit_date != ''
        ).all()
        
        if not orphaned:
            print("✅ No orphaned signals found!")
            return
        
        print(f"\n🔍 Found {len(orphaned)} orphaned BUY signals:\n")
        
        for sig in orphaned:
            print(f"  ID {sig.id}: {sig.ticker}")
            print(f"    Status: {sig.status} (should be 'closed')")
            print(f"    Exit Date: {sig.exit_date}")
            print(f"    Exit Reason: {sig.exit_reason}")
            print()
        
        # Confirm
        confirm = input(f"\nUpdate {len(orphaned)} signals to status='closed'? (y/n): ").lower()
        
        if confirm != 'y':
            print("❌ Cancelled")
            return
        
        # Update
        updated = 0
        for sig in orphaned:
            sig.status = 'closed'
            updated += 1
        
        session.commit()
        
        print(f"\n✅ Updated {updated} signals to status='closed'")
        print("\nFixed signals:")
        for sig in orphaned:
            print(f"  ✅ {sig.ticker} (ID {sig.id}) - {sig.exit_reason}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    main()
