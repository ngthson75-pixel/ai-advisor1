#!/usr/bin/env python3
"""
DATABASE MIGRATION - ADD SELL SIGNAL COLUMNS
Adds: exit_price, exit_reason, exit_date
"""

import os
from sqlalchemy import create_engine, text

def run_migration():
    """
    Add columns for SELL signals:
    - exit_price: Exit price when signal triggers
    - exit_reason: STOP_LOSS or TAKE_PROFIT
    - exit_date: Date when signal triggered
    """
    
    # Get database URL - PRIORITIZE environment variable
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("\n⚠️  WARNING: DATABASE_URL not found in environment!")
        print("⚠️  Using SQLite fallback (LOCAL ONLY)")
        print("⚠️  This migration will NOT affect production database!")
        print("\nTo migrate production database:")
        print("1. Set DATABASE_URL in .env")
        print("2. Run this script again")
        print("\nContinuing with local SQLite in 5 seconds...")
        import time
        time.sleep(5)
        db_url = 'sqlite:///signals.db'
    
    # Fix PostgreSQL URL
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    print("\n" + "="*70)
    print("🔧 DATABASE MIGRATION - ADD SELL COLUMNS")
    print("="*70)
    
    if 'sqlite' in db_url.lower():
        print(f"⚠️  LOCAL SQLite: {db_url}")
        print("⚠️  This will NOT affect production!")
    else:
        print(f"✅ PRODUCTION PostgreSQL: {db_url[:50]}...")
    
    
    engine = create_engine(db_url)
    
    try:
        with engine.begin() as conn:
            
            # Check if columns already exist
            print("\n1. Checking existing columns...")
            
            if 'postgresql' in db_url:
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'signals'
                """)
                result = conn.execute(check_query)
                existing_columns = [row[0] for row in result]
            else:  # SQLite
                check_query = text("PRAGMA table_info(signals)")
                result = conn.execute(check_query)
                # SQLite PRAGMA returns: (cid, name, type, notnull, dflt_value, pk)
                existing_columns = [row[1] for row in result]  # Get name from index 1
            
            print(f"   Existing columns: {len(existing_columns)}")
            print(f"   Columns: {', '.join(existing_columns[:5])}...")
            
            # Add exit_price column
            if 'exit_price' not in existing_columns:
                print("\n2. Adding exit_price column...")
                try:
                    conn.execute(text("""
                        ALTER TABLE signals 
                        ADD COLUMN exit_price REAL
                    """))
                    print("   ✅ exit_price added")
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        print("   ✓ exit_price already exists (duplicate error - safe to ignore)")
                    else:
                        raise
            else:
                print("\n2. exit_price column already exists ✓")
            
            # Add exit_reason column
            if 'exit_reason' not in existing_columns:
                print("\n3. Adding exit_reason column...")
                try:
                    conn.execute(text("""
                        ALTER TABLE signals 
                        ADD COLUMN exit_reason VARCHAR(50)
                    """))
                    print("   ✅ exit_reason added")
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        print("   ✓ exit_reason already exists (duplicate error - safe to ignore)")
                    else:
                        raise
            else:
                print("\n3. exit_reason column already exists ✓")
            
            # Add exit_date column
            if 'exit_date' not in existing_columns:
                print("\n4. Adding exit_date column...")
                try:
                    conn.execute(text("""
                        ALTER TABLE signals 
                        ADD COLUMN exit_date VARCHAR(20)
                    """))
                    print("   ✅ exit_date added")
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        print("   ✓ exit_date already exists (duplicate error - safe to ignore)")
                    else:
                        raise
            else:
                print("\n4. exit_date column already exists ✓")
            
            print("\n" + "="*70)
            print("✅ MIGRATION COMPLETE!")
            print("="*70)
            
            # Verify
            print("\nVerifying columns:")
            result = conn.execute(check_query)
            all_columns = [row[0] for row in result]
            
            for col in ['exit_price', 'exit_reason', 'exit_date']:
                status = "✅" if col in all_columns else "❌"
                print(f"  {status} {col}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    """
    Run migration
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    
    success = run_migration()
    
    if success:
        print("\n🎉 You can now use SELL signal features!")
        print("   - exit_price: Actual exit price")
        print("   - exit_reason: STOP_LOSS or TAKE_PROFIT")
        print("   - exit_date: Exit date")
    else:
        print("\n⚠️  Migration failed. Check errors above.")
