#!/usr/bin/env python3
"""
Copy Signals Data from Production to Staging - SSL FIX
"""

import psycopg
from psycopg.rows import dict_row

# =============================================================================
# DATABASE CONNECTIONS - WITH EXPLICIT SSL PARAMETERS
# =============================================================================

# Production (Render PostgreSQL)
PRODUCTION_PARAMS = {
    'host': 'dpg-ctg0nllds78s73a9h880-a.oregon-postgres.render.com',
    'port': 5432,
    'dbname': 'ai_advisor_db',
    'user': 'ai_advisor_user',
    'password': 'OPmx1O1UTpXkn1XvlFKZPDPbAZlCx1TJ',
    'sslmode': 'prefer',
    'connect_timeout': 10
}

# Staging (Supabase PostgreSQL)
STAGING_PARAMS = {
    'host': 'aws-1-ap-southeast-2.pooler.supabase.com',
    'port': 5432,
    'dbname': 'postgres',
    'user': 'postgres.xyzxaxajshlowpkiouon',
    'password': '3NfbmvjGThaS2l2L',
    'sslmode': 'prefer',
    'connect_timeout': 10
}

# =============================================================================
# COPY FUNCTIONS
# =============================================================================

def copy_signals():
    """Copy all signals from production to staging"""
    
    print("🔄 Connecting to databases...")
    
    # Connect to both databases
    with psycopg.connect(**PRODUCTION_PARAMS) as prod_conn, \
         psycopg.connect(**STAGING_PARAMS) as staging_conn:
        
        # Get production data
        print("📊 Fetching signals from production...")
        with prod_conn.cursor(row_factory=dict_row) as prod_cur:
            prod_cur.execute("SELECT * FROM signals ORDER BY id")
            signals = prod_cur.fetchall()
        
        print(f"✅ Found {len(signals)} signals in production")
        
        # Clear staging data first
        print("🗑️  Clearing staging signals...")
        with staging_conn.cursor() as staging_cur:
            staging_cur.execute("TRUNCATE TABLE signals RESTART IDENTITY CASCADE")
            staging_conn.commit()
        
        # Insert into staging
        print("📥 Inserting signals into staging...")
        with staging_conn.cursor() as staging_cur:
            for signal in signals:
                staging_cur.execute("""
                    INSERT INTO signals (
                        ticker, strategy, entry_price, stop_loss, take_profit,
                        risk_reward, strength, stock_type, rsi, date, action, created_at
                    ) VALUES (
                        %(ticker)s, %(strategy)s, %(entry_price)s, %(stop_loss)s, %(take_profit)s,
                        %(risk_reward)s, %(strength)s, %(stock_type)s, %(rsi)s, %(date)s, %(action)s, %(created_at)s
                    )
                """, signal)
            
            staging_conn.commit()
        
        print(f"✅ Copied {len(signals)} signals to staging!")


def copy_blacklist():
    """Copy ticker blacklist from production to staging"""
    
    print("\n🔄 Copying blacklist...")
    
    with psycopg.connect(**PRODUCTION_PARAMS) as prod_conn, \
         psycopg.connect(**STAGING_PARAMS) as staging_conn:
        
        # Get production blacklist
        print("📊 Fetching blacklist from production...")
        with prod_conn.cursor(row_factory=dict_row) as prod_cur:
            prod_cur.execute("SELECT * FROM ticker_blacklist ORDER BY id")
            blacklist = prod_cur.fetchall()
        
        print(f"✅ Found {len(blacklist)} blacklisted tickers in production")
        
        # Clear staging blacklist
        print("🗑️  Clearing staging blacklist...")
        with staging_conn.cursor() as staging_cur:
            staging_cur.execute("TRUNCATE TABLE ticker_blacklist RESTART IDENTITY CASCADE")
            staging_conn.commit()
        
        # Insert into staging
        print("📥 Inserting blacklist into staging...")
        with staging_conn.cursor() as staging_cur:
            for item in blacklist:
                staging_cur.execute("""
                    INSERT INTO ticker_blacklist (ticker, reason, created_at)
                    VALUES (%(ticker)s, %(reason)s, %(created_at)s)
                """, item)
            
            staging_conn.commit()
        
        print(f"✅ Copied {len(blacklist)} blacklist entries to staging!")


def verify_copy():
    """Verify data was copied correctly"""
    
    print("\n🔍 Verifying copy...")
    
    with psycopg.connect(**PRODUCTION_PARAMS) as prod_conn, \
         psycopg.connect(**STAGING_PARAMS) as staging_conn:
        
        # Count signals
        with prod_conn.cursor() as prod_cur:
            prod_cur.execute("SELECT COUNT(*) FROM signals")
            prod_count = prod_cur.fetchone()[0]
        
        with staging_conn.cursor() as staging_cur:
            staging_cur.execute("SELECT COUNT(*) FROM signals")
            staging_count = staging_cur.fetchone()[0]
        
        print(f"Production signals: {prod_count}")
        print(f"Staging signals: {staging_count}")
        
        if prod_count == staging_count:
            print("✅ Signal counts match!")
        else:
            print("❌ Signal counts DO NOT match!")
        
        # Count blacklist
        with prod_conn.cursor() as prod_cur:
            prod_cur.execute("SELECT COUNT(*) FROM ticker_blacklist")
            prod_bl_count = prod_cur.fetchone()[0]
        
        with staging_conn.cursor() as staging_cur:
            staging_cur.execute("SELECT COUNT(*) FROM ticker_blacklist")
            staging_bl_count = staging_cur.fetchone()[0]
        
        print(f"Production blacklist: {prod_bl_count}")
        print(f"Staging blacklist: {staging_bl_count}")
        
        if prod_bl_count == staging_bl_count:
            print("✅ Blacklist counts match!")
        else:
            print("❌ Blacklist counts DO NOT match!")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("="*70)
    print("📦 COPY PRODUCTION DATA TO STAGING")
    print("="*70)
    
    try:
        # Test connections first
        print("\n🔌 Testing connections...")
        
        try:
            with psycopg.connect(**PRODUCTION_PARAMS) as conn:
                print("  ✅ Production database connected!")
        except Exception as e:
            print(f"  ❌ Production connection failed: {e}")
            raise
        
        try:
            with psycopg.connect(**STAGING_PARAMS) as conn:
                print("  ✅ Staging database connected!")
        except Exception as e:
            print(f"  ❌ Staging connection failed: {e}")
            raise
        
        print()
        
        # Copy signals
        copy_signals()
        
        # Copy blacklist
        copy_blacklist()
        
        # Verify
        verify_copy()
        
        print("\n" + "="*70)
        print("🎉 DATA COPY COMPLETED SUCCESSFULLY!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
