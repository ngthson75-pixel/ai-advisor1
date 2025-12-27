#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST VNSTOCK REAL-TIME CAPABILITIES
Check if vnstock provides intraday data (1m, 5m, 15m, 1H)
Measure latency and update frequency
"""

from vnstock import Vnstock
import pandas as pd
from datetime import datetime, timedelta
import time

print("="*70)
print("VNSTOCK REAL-TIME DATA TEST")
print("="*70)
print(f"Test Time: {datetime.now()}")
print()

# Test stock
TEST_SYMBOL = 'VNM'

# ============================================================================
# TEST 1: Check Available Intervals
# ============================================================================

print("TEST 1: AVAILABLE INTERVALS")
print("-"*70)

intervals_to_test = ['1m', '5m', '15m', '30m', '1H', '1D']
available_intervals = []

stock = Vnstock().stock(symbol=TEST_SYMBOL, source='VCI')

for interval in intervals_to_test:
    print(f"\nTesting interval: {interval}")
    try:
        # Try to get last 2 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        df = stock.quote.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=interval
        )
        
        if df is not None and len(df) > 0:
            latest_time = df['time'].max()
            rows = len(df)
            
            print(f"  ✅ {interval}: {rows} rows")
            print(f"     Latest: {latest_time}")
            print(f"     Sample:\n{df.tail(2)}")
            
            available_intervals.append(interval)
        else:
            print(f"  ❌ {interval}: No data")
    
    except Exception as e:
        print(f"  ❌ {interval}: Error - {e}")
    
    time.sleep(1)  # Rate limit

print(f"\n{'='*70}")
print(f"Available intervals: {available_intervals}")

# ============================================================================
# TEST 2: Intraday Data Check
# ============================================================================

print(f"\n{'='*70}")
print("TEST 2: INTRADAY DATA (TODAY)")
print("-"*70)

today = datetime.now().strftime('%Y-%m-%d')

for interval in ['1m', '5m', '15m', '1H']:
    if interval not in available_intervals:
        continue
        
    print(f"\nInterval: {interval}")
    try:
        df = stock.quote.history(
            start=today,
            end=today,
            interval=interval
        )
        
        if df is not None and len(df) > 0:
            print(f"  ✅ Rows today: {len(df)}")
            print(f"  Latest: {df['time'].max()}")
            print(f"  Data:\n{df.tail(3)}")
        else:
            print(f"  ❌ No intraday data for {interval}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    time.sleep(1)

# ============================================================================
# TEST 3: Latency Test
# ============================================================================

print(f"\n{'='*70}")
print("TEST 3: LATENCY TEST (5 consecutive calls)")
print("-"*70)

latencies = []

for i in range(5):
    print(f"\nCall {i+1}/5...")
    
    start_time = time.time()
    
    try:
        df = stock.quote.history(
            start=today,
            end=today,
            interval='1D'
        )
        
        end_time = time.time()
        latency = end_time - start_time
        latencies.append(latency)
        
        if df is not None and len(df) > 0:
            latest = df['time'].max()
            close = df['close'].iloc[-1]
            
            print(f"  ✅ Latency: {latency:.2f}s")
            print(f"     Latest: {latest}")
            print(f"     Close: {close:,.0f}")
        else:
            print(f"  ⚠️  No data, latency: {latency:.2f}s")
    
    except Exception as e:
        end_time = time.time()
        latency = end_time - start_time
        print(f"  ❌ Error after {latency:.2f}s: {e}")
    
    time.sleep(2)  # Rate limit

if latencies:
    print(f"\nLatency Statistics:")
    print(f"  Average: {sum(latencies)/len(latencies):.2f}s")
    print(f"  Min: {min(latencies):.2f}s")
    print(f"  Max: {max(latencies):.2f}s")

# ============================================================================
# TEST 4: Price Board (Real-time alternative?)
# ============================================================================

print(f"\n{'='*70}")
print("TEST 4: PRICE BOARD (POTENTIAL REAL-TIME)")
print("-"*70)

try:
    # Check if trading.price_board exists
    if hasattr(stock, 'trading'):
        print("\nTesting trading.price_board()...")
        
        start_time = time.time()
        price_data = stock.trading.price_board(TEST_SYMBOL)
        end_time = time.time()
        
        if price_data is not None:
            print(f"✅ Price Board available!")
            print(f"   Latency: {end_time - start_time:.2f}s")
            print(f"   Data type: {type(price_data)}")
            print(f"   Data:\n{price_data}")
        else:
            print("⚠️  Price Board returned None")
    else:
        print("❌ No trading.price_board method")

except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# TEST 5: Listing (Get all symbols for scanning)
# ============================================================================

print(f"\n{'='*70}")
print("TEST 5: LISTING (FOR SCANNING)")
print("-"*70)

try:
    print("\nGetting all symbols...")
    
    start_time = time.time()
    listing = stock.listing.all_symbols()
    end_time = time.time()
    
    if listing is not None and len(listing) > 0:
        print(f"✅ Listing available!")
        print(f"   Total symbols: {len(listing)}")
        print(f"   Latency: {end_time - start_time:.2f}s")
        print(f"   Sample:\n{listing.head()}")
        
        # Save for later use
        listing.to_csv('vnstock_symbols.csv', index=False)
        print(f"\n   Saved to: vnstock_symbols.csv")
    else:
        print("⚠️  No listing data")

except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================

print(f"\n{'='*70}")
print("SUMMARY & RECOMMENDATIONS")
print("="*70)

print("\n1. AVAILABLE FEATURES:")
if available_intervals:
    print(f"   ✅ Intervals: {', '.join(available_intervals)}")
else:
    print("   ❌ No intraday data available")

print("\n2. REAL-TIME CAPABILITY:")
if '1m' in available_intervals or '5m' in available_intervals:
    print("   ✅ Intraday data available")
    print("   → Can potentially use for near real-time signals")
    print("   → Check update frequency during market hours")
else:
    print("   ❌ Only daily data available")
    print("   → End-of-day signals only")
    print("   → Consider vnstock premium or other data sources")

print("\n3. LATENCY:")
if latencies:
    avg_latency = sum(latencies) / len(latencies)
    if avg_latency < 2:
        print(f"   ✅ Low latency ({avg_latency:.2f}s avg)")
        print("   → Suitable for automated trading")
    elif avg_latency < 5:
        print(f"   ⚠️  Medium latency ({avg_latency:.2f}s avg)")
        print("   → Acceptable for swing trading")
    else:
        print(f"   ❌ High latency ({avg_latency:.2f}s avg)")
        print("   → May need faster data source")

print("\n4. RECOMMENDATIONS:")
print("   For PULLBACK + EMA_CROSS strategies:")
print("   → These are DAILY strategies (not intraday)")
print("   → Daily data is sufficient ✅")
print("   → No need for real-time data")
print("   → Scan end-of-day (after market close)")
print()
print("   Suggested workflow:")
print("   1. Run scanner daily after 3:30 PM")
print("   2. Generate signals for next day")
print("   3. Update frontend with signals")
print("   4. Traders execute during trading hours")

print("\n5. NEXT STEPS:")
print("   ✅ Build daily scanner (end-of-day)")
print("   ✅ No need for real-time subscription")
print("   ✅ Focus on signal quality over speed")
print("   ⚠️  If need real-time: Consider vnstock Insiders")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
