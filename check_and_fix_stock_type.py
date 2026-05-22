#!/usr/bin/env python3
"""
CHECK & FIX STOCK_TYPE CLASSIFICATION
Current issue: Scanner uses PRICE to classify, should use TICKER LIST
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
load_dotenv()
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not found")
    exit(1)

if db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)

# Blue Chip list (top 50 large caps)
BLUE_CHIP_STOCKS = [
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'POW', 'NVL', 'PDR', 'TPB', 'GVR', 'VCI', 'ACB', 'SAB', 'PVD', 'KDH',
    'BCM', 'PNJ', 'REE', 'VGC', 'HAG', 'SHB', 'DPM', 'GMD', 'BWE', 'LPB',
    'VIB', 'PAN', 'EIB', 'TCH', 'VPI', 'PVS', 'VCS', 'VHC', 'OCB', 'KDC',
]

engine = create_engine(db_url)

print("="*70)
print("📊 CHECK STOCK_TYPE CLASSIFICATION")
print("="*70)

# Check current stock_type values
with engine.connect() as conn:
    print("\n1️⃣ Current stock_type distribution:")
    result = conn.execute(text("""
        SELECT stock_type, COUNT(*) as count
        FROM signals 
        GROUP BY stock_type
        ORDER BY count DESC
    """))
    
    print("Stock Type  | Count")
    print("------------|------")
    for row in result:
        st = row[0] if row[0] else 'NULL'
        print(f"{st:<11} | {row[1]}")

    # Check 4 signals from today
    print("\n2️⃣ Today's 4 SELL signals:")
    result = conn.execute(text("""
        SELECT ticker, stock_type, entry_price
        FROM signals 
        WHERE action='SELL' AND exit_date='2026-03-06'
        ORDER BY ticker
    """))
    
    print("Ticker | Current Type | Entry Price | Should Be")
    print("-------|-------------|-------------|------------")
    for row in result:
        ticker = row[0]
        current = row[1] if row[1] else 'NULL'
        price = row[2]
        
        should_be = 'Blue Chip' if ticker in BLUE_CHIP_STOCKS else 'Mid Cap'
        match = '✅' if current == should_be else '❌'
        
        print(f"{ticker:<6} | {current:<11} | {price:<11} | {should_be:<11} {match}")

    # Check all tickers
    print("\n3️⃣ All signals - Classification check:")
    result = conn.execute(text("""
        SELECT DISTINCT ticker, stock_type
        FROM signals 
        ORDER BY ticker
    """))
    
    wrong_count = 0
    corrections = []
    
    print("Ticker | Current     | Should Be   | Status")
    print("-------|-------------|-------------|--------")
    for row in result:
        ticker = row[0]
        current = row[1] if row[1] else 'NULL'
        should_be = 'Blue Chip' if ticker in BLUE_CHIP_STOCKS else 'Mid Cap'
        
        if current != should_be:
            wrong_count += 1
            corrections.append((ticker, should_be))
            status = '❌ WRONG'
        else:
            status = '✅ OK'
        
        print(f"{ticker:<6} | {current:<11} | {should_be:<11} | {status}")

print("\n" + "="*70)
print(f"📊 SUMMARY: {wrong_count} tickers need correction")
print("="*70)

if wrong_count > 0:
    print(f"\n⚠️  Found {wrong_count} tickers with wrong classification")
    print("\nCorrections needed:")
    for ticker, correct_type in corrections:
        print(f"  {ticker}: → {correct_type}")
    
    print("\n" + "="*70)
    choice = input("Fix database now? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("\n🔧 Updating database...")
        
        with engine.begin() as conn:
            for ticker, correct_type in corrections:
                result = conn.execute(text(f"""
                    UPDATE signals 
                    SET stock_type = '{correct_type}'
                    WHERE ticker = '{ticker}'
                """))
                
                print(f"✅ Updated {ticker} → {correct_type}")
        
        print("\n" + "="*70)
        print("✅ DATABASE UPDATED!")
        print("="*70)
        print("\n💡 Next steps:")
        print("1. Refresh https://ai-advisor.vn (Ctrl+Shift+R)")
        print("2. Fix scanner code to use ticker list (not price)")
        print("3. See FIX_STOCK_TYPE_CLASSIFICATION.md for details")
    else:
        print("\n❌ Update cancelled")
        print("\n💡 To fix manually, run UPDATE commands from")
        print("   FIX_STOCK_TYPE_CLASSIFICATION.md")
else:
    print("\n✅ All classifications are correct!")

print("="*70)
