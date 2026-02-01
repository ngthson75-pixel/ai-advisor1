#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: Check vnstock price data format

Purpose: Verify if vnstock returns prices in VND or thousands VND
"""

from vnstock import Quote
from datetime import datetime, timedelta

def check_price_format():
    """Check actual price format from vnstock"""
    
    print("="*70)
    print("🔍 VNSTOCK PRICE FORMAT DEBUG")
    print("="*70)
    
    # Test with well-known stocks
    test_stocks = ['VCB', 'TCB', 'HPG', 'VHM']
    
    for ticker in test_stocks:
        print(f"\n{'─'*70}")
        print(f"Testing: {ticker}")
        print(f"{'─'*70}")
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            
            quote = Quote(symbol=ticker, source='VCI')
            df = quote.history(start=start_date, end=end_date)
            
            if df is not None and len(df) > 0:
                print(f"\n✅ Got {len(df)} bars")
                print(f"\nColumn names: {df.columns.tolist()}")
                print(f"\nLast 3 rows:")
                print(df.tail(3))
                
                # Get latest close
                latest = df.iloc[-1]
                
                print(f"\n📊 Latest bar:")
                for col in ['time', 'open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        print(f"   {col}: {latest[col]}")
                
                # Check if prices look correct
                close_val = latest['close'] if 'close' in latest else None
                
                if close_val:
                    print(f"\n🔍 Analysis:")
                    print(f"   Raw close value: {close_val}")
                    print(f"   In VND: {close_val:,.0f} VND")
                    print(f"   In thousands VND: {close_val*1000:,.0f} VND")
                    
                    # Expected prices for reference
                    expected = {
                        'VCB': 85000,   # ~85k
                        'TCB': 36000,   # ~36k
                        'HPG': 26000,   # ~26k
                        'VHM': 140000   # ~140k
                    }
                    
                    if ticker in expected:
                        exp = expected[ticker]
                        print(f"\n   Expected price: ~{exp:,.0f} VND")
                        
                        # Check which interpretation is closer
                        diff_raw = abs(close_val - exp)
                        diff_1000x = abs(close_val * 1000 - exp)
                        
                        print(f"\n   If raw = VND:")
                        print(f"      Difference: {diff_raw:,.0f} VND")
                        print(f"   If raw = thousands VND:")
                        print(f"      Difference: {diff_1000x:,.0f} VND")
                        
                        if diff_raw < diff_1000x:
                            print(f"\n   ✅ Likely: Raw value IS in VND (no conversion needed)")
                        else:
                            print(f"\n   ⚠️  Likely: Raw value is in THOUSANDS VND (need × 1000)")
            else:
                print(f"❌ No data")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("DEBUG COMPLETE")
    print(f"{'='*70}")


if __name__ == '__main__':
    check_price_format()
