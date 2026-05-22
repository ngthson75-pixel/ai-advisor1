#!/usr/bin/env python3
"""
Get CTI exit price for 10/3/2026
Run: python get_cti_price.py
"""

try:
    from vnstock3 import Vnstock
    import pandas as pd
    
    print("🔍 Getting CTI price on 10/3/2026...")
    print()
    
    stock = Vnstock().stock(symbol='CTI', source='VCI')
    df = stock.quote.history(start='2026-03-10', end='2026-03-10')
    
    if df.empty:
        print("❌ No data for 10/3/2026")
        print("   → Market might be closed or data not available yet")
        print()
        print("FALLBACK: Estimate from MA20_STRICT logic:")
        print("   Entry: 23,800")
        print("   If P/L = -1%: exit ≈ 23,562")
        print("   If P/L = -2%: exit ≈ 23,324")
        print("   If P/L = -3%: exit ≈ 23,086")
    else:
        raw_price = df['close'].iloc[-1]
        
        # vnstock returns prices in thousands VND
        exit_price = raw_price * 1000
        
        entry_price = 23800
        pnl_pct = ((exit_price - entry_price) / entry_price * 100)
        
        print(f"✅ CTI on 10/3/2026:")
        print(f"   Raw price: {raw_price:,.3f} (from vnstock)")
        print(f"   Exit price: {exit_price:,.0f} VND")
        print(f"   Entry price: {entry_price:,.0f} VND")
        print(f"   P/L: {pnl_pct:+.2f}%")
        print()
        print("📋 SQL to run in pgAdmin4:")
        print()
        print(f"UPDATE signals")
        print(f"SET exit_price = {exit_price:.0f},")
        print(f"    exit_date = '2026-03-10'")
        print(f"WHERE ticker = 'CTI'")
        print(f"  AND action = 'SELL'")
        print(f"  AND date = '2026-03-10'")
        print(f"  AND exit_price IS NULL;")
        print()
        print("-- Verify:")
        print("SELECT ticker, entry_price, exit_price,")
        print("       ROUND(((exit_price - entry_price)::numeric / entry_price * 100), 2) as pnl_pct")
        print("FROM signals")
        print("WHERE ticker = 'CTI' AND action = 'SELL' AND date = '2026-03-10';")
        
except ImportError:
    print("❌ vnstock not installed")
    print()
    print("Install: pip install vnstock3 --break-system-packages")
    print()
    print("Or check price manually:")
    print("1. Go to https://finance.vietstock.vn/CTI")
    print("2. Find close price on 10/3/2026")
    print("3. Use that in SQL UPDATE")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("FALLBACK: Use estimated price")
    print("   Entry: 23,800")
    print("   Exit (estimated): 23,000 - 23,500")
