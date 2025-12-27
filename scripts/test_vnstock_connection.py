#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST VNSTOCK CONNECTION - DIAGNOSTICS
Kiểm tra xem vnstock còn hoạt động không và cách dùng đúng
"""

print("="*70)
print("VNSTOCK DIAGNOSTICS - KIỂM TRA KẾT NỐI")
print("="*70)

# Test 1: Import
print("\n[1/6] Testing import...")
try:
    import vnstock
    print(f"✅ vnstock version: {vnstock.__version__ if hasattr(vnstock, '__version__') else 'unknown'}")
    from vnstock import Vnstock
    print("✅ Can import Vnstock class")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Check available methods
print("\n[2/6] Checking Vnstock class methods...")
stock = Vnstock('VNM')
methods = [m for m in dir(stock) if not m.startswith('_')]
print(f"✅ Available methods: {', '.join(methods[:10])}...")

# Test 3: Try different download methods
print("\n[3/6] Testing different download methods...")

test_methods = [
    # Method 1: Old way (might be deprecated)
    ("Method 1: stock.quote.history()", 
     lambda: stock.quote.history(start='2025-01-01', end='2025-12-19', interval='1D')),
    
    # Method 2: Direct class
    ("Method 2: Vnstock().stock()", 
     lambda: Vnstock().stock(symbol='VNM', source='VCI').quote.history(start='2025-01-01', end='2025-12-19')),
    
    # Method 3: New API (if exists)
    ("Method 3: stock.trading.price_board()",
     lambda: stock.trading.price_board('VNM')),
]

working_method = None

for name, func in test_methods:
    print(f"\n{name}")
    try:
        result = func()
        if result is not None and len(result) > 0:
            print(f"✅ SUCCESS! Got {len(result)} rows")
            print(f"   Columns: {list(result.columns)}")
            print(f"   Sample:\n{result.head(2)}")
            working_method = (name, func)
            break
        else:
            print("⚠️  Method returned empty data")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 4: Try listing API
print("\n[4/6] Testing listing API...")
try:
    listing = Vnstock().stock(symbol='VNM', source='VCI').listing.all_symbols()
    if listing is not None:
        print(f"✅ Listing works! Got {len(listing)} stocks")
        print(f"   Columns: {list(listing.columns)}")
    else:
        print("⚠️  Listing returned None")
except Exception as e:
    print(f"❌ Listing failed: {e}")

# Test 5: Try alternative download
print("\n[5/6] Testing alternative methods...")
try:
    # Method: Direct stock class
    from vnstock import stock_historical_data
    df = stock_historical_data(symbol='VNM', start_date='2025-01-01', end_date='2025-12-19')
    if df is not None and len(df) > 0:
        print(f"✅ stock_historical_data works! Got {len(df)} rows")
        working_method = ("stock_historical_data", None)
except:
    pass

try:
    # Try new Vnstock 3.x API
    from vnstock3 import Vnstock as Vnstock3
    stock3 = Vnstock3(symbol='VNM', source='VCI')
    df = stock3.quote.history(start='2025-01-01', end='2025-12-19')
    if df is not None and len(df) > 0:
        print(f"✅ Vnstock3 API works! Got {len(df)} rows")
        working_method = ("Vnstock3", None)
except:
    pass

# Test 6: Check documentation
print("\n[6/6] Checking help documentation...")
try:
    print("\nVnstock class signature:")
    import inspect
    print(inspect.signature(Vnstock.__init__))
    print("\nquote.history signature:")
    if hasattr(stock, 'quote') and hasattr(stock.quote, 'history'):
        print(inspect.signature(stock.quote.history))
except Exception as e:
    print(f"⚠️  Could not get signatures: {e}")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if working_method:
    print(f"✅ FOUND WORKING METHOD: {working_method[0]}")
    print("\nRecommended code:")
    
    if "Method 1" in working_method[0]:
        print("""
from vnstock import Vnstock

stock = Vnstock('VNM')
df = stock.quote.history(start='2025-01-01', end='2025-12-19', interval='1D')
""")
    
    elif "Method 2" in working_method[0]:
        print("""
from vnstock import Vnstock

stock = Vnstock().stock(symbol='VNM', source='VCI')
df = stock.quote.history(start='2025-01-01', end='2025-12-19')
""")
    
    elif "stock_historical_data" in working_method[0]:
        print("""
from vnstock import stock_historical_data

df = stock_historical_data(symbol='VNM', start_date='2025-01-01', end_date='2025-12-19')
""")
    
    elif "Vnstock3" in working_method[0]:
        print("""
from vnstock3 import Vnstock

stock = Vnstock(symbol='VNM', source='VCI')
df = stock.quote.history(start='2025-01-01', end='2025-12-19')
""")

else:
    print("❌ NO WORKING METHOD FOUND!")
    print("\nPossible issues:")
    print("1. vnstock package needs update: pip install --upgrade vnstock")
    print("2. API changed - need new version")
    print("3. Internet/firewall blocking")
    print("4. Source server down")
    
    print("\nTry:")
    print("pip uninstall vnstock")
    print("pip install vnstock")
    print("\nOr:")
    print("pip install vnstock3")

print("\n" + "="*70)
print("Check documentation: https://vnstocks.com")
print("="*70)
