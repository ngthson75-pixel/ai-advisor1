#!/usr/bin/env python3
"""
VERIFY DATABASE COLUMNS - Check if SELL signal columns exist
"""

import os
from sqlalchemy import create_engine, text

def verify_columns():
    """
    Verify that all required SELL signal columns exist
    """
    
    # Get database URL - PRIORITIZE environment variable
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("\n⚠️  WARNING: DATABASE_URL not found in environment!")
        print("⚠️  Using SQLite fallback (LOCAL ONLY)")
        db_url = 'sqlite:///signals.db'
    
    # Fix PostgreSQL URL
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    print("\n" + "="*70)
    print("🔍 DATABASE COLUMN VERIFICATION")
    print("="*70)
    
    if 'sqlite' in db_url.lower():
        print(f"⚠️  LOCAL SQLite: {db_url}")
    else:
        print(f"✅ PRODUCTION PostgreSQL: {db_url[:50]}...")
    
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            
            # Get all columns
            if 'postgresql' in db_url:
                query = text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'signals'
                    ORDER BY ordinal_position
                """)
                result = conn.execute(query)
                columns = [(row[0], row[1]) for row in result]
            else:  # SQLite
                query = text("PRAGMA table_info(signals)")
                result = conn.execute(query)
                # SQLite PRAGMA returns: (cid, name, type, notnull, dflt_value, pk)
                columns = [(row[1], row[2]) for row in result]
            
            print(f"\n📊 Total columns: {len(columns)}")
            print("\n" + "-"*70)
            print(f"{'Column Name':<30} {'Type':<20}")
            print("-"*70)
            
            for col_name, col_type in columns:
                print(f"{col_name:<30} {col_type:<20}")
            
            print("-"*70)
            
            # Check required columns
            print("\n🔍 Checking SELL signal columns:")
            
            required_columns = ['exit_price', 'exit_reason', 'exit_date']
            column_names = [col[0] for col in columns]
            
            all_present = True
            for req_col in required_columns:
                if req_col in column_names:
                    # Get type
                    col_type = next((c[1] for c in columns if c[0] == req_col), 'UNKNOWN')
                    print(f"   ✅ {req_col:<20} ({col_type})")
                else:
                    print(f"   ❌ {req_col:<20} MISSING!")
                    all_present = False
            
            print("\n" + "="*70)
            
            if all_present:
                print("✅ ALL REQUIRED COLUMNS PRESENT!")
                print("="*70)
                print("\n🎉 Database ready for SELL signals!")
                return True
            else:
                print("❌ MISSING REQUIRED COLUMNS!")
                print("="*70)
                print("\n⚠️  Run migration: python migration_add_sell_columns.py")
                return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    """
    Run verification
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    
    success = verify_columns()
    
    exit(0 if success else 1)
