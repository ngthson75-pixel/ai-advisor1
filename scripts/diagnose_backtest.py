#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTIC SCRIPT

Check why no trades are being generated
"""

import sys
import os
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Suppress VNStock ads
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

original_stdout = sys.stdout
sys.stdout = NullWriter()

from vnstock import Vnstock

sys.stdout = original_stdout

from breakout_scanner import BreakoutDetector
import pandas as pd


def diagnose_stock(code, start_date, end_date):
    """Diagnose why stock is not generating signals"""
    
    print(f"\n{'='*60}")
    print(f"DIAGNOSING: {code}")
    print(f"{'='*60}")
    
    try:
        # Fetch data
        print(f"\n1. Fetching data...")
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(
            symbol=code,
            start=start_date,
            end=end_date
        )
        
        if df.empty:
            print(f"   ❌ No data returned")
            return
        
        print(f"   ✅ Got {len(df)} rows")
        print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
        
        # Check data quality
        print(f"\n2. Data quality check...")
        print(f"   Close price range: {df['close'].min():.0f} - {df['close'].max():.0f}")
        print(f"   Volume range: {df['volume'].min():,.0f} - {df['volume'].max():,.0f}")
        print(f"   Avg daily volume: {df['volume'].mean():,.0f}")
        
        # Calculate indicators
        print(f"\n3. Running strategy detection...")
        detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
        df_signals = detector.detect_signal(df)
        
        print(f"   ✅ Indicators calculated")
        
        # Check conditions separately
        print(f"\n4. Checking conditions...")
        
        volume_spikes = df_signals[df_signals['volume_spike'] == True]
        print(f"   Volume spikes (≥3x): {len(volume_spikes)} bars")
        
        if len(volume_spikes) > 0:
            print(f"   Sample volume spikes:")
            for idx, row in volume_spikes.head(3).iterrows():
                print(f"      {row['time']}: {row['volume_ratio']:.2f}x, RSI={row['rsi']:.1f}")
        
        macd_crosses = df_signals[df_signals['macd_positive'] == True]
        print(f"   MACD positive: {len(macd_crosses)} bars")
        
        rsi_high = df_signals[df_signals['rsi'] > 70]
        print(f"   RSI > 70: {len(rsi_high)} bars")
        
        # Check combined signal
        buy_signals = df_signals[df_signals['buy_signal'] == True]
        print(f"\n5. BUY signals (all 3 conditions): {len(buy_signals)}")
        
        if len(buy_signals) > 0:
            print(f"   ✅ Found {len(buy_signals)} signals!")
            for idx, row in buy_signals.iterrows():
                print(f"      Date: {row['time']}")
                print(f"      Price: {row['close']:,.0f}")
                print(f"      Volume: {row['volume_ratio']:.2f}x")
                print(f"      RSI: {row['rsi']:.1f}")
                print(f"      MACD: {row['macd']:.4f}")
                print()
        else:
            print(f"   ❌ No signals found")
            print(f"\n   Analysis:")
            
            if len(volume_spikes) == 0:
                print(f"      • No volume spikes ≥3x detected")
                print(f"      • Suggestion: Lower volume_multiplier to 2.5x")
            
            if len(rsi_high) == 0:
                print(f"      • RSI never exceeded 70")
                print(f"      • Max RSI: {df_signals['rsi'].max():.1f}")
                print(f"      • Suggestion: Lower rsi_threshold to 65")
            
            if len(macd_crosses) == 0:
                print(f"      • MACD never positive")
                print(f"      • Suggestion: Check if stock in downtrend")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run diagnostics"""
    
    print("="*60)
    print("BACKTEST DIAGNOSTIC TOOL")
    print("="*60)
    print()
    print("Checking why no trades are generated...")
    print()
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    STOCK_CODES = ['VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC']
    
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Stocks: {', '.join(STOCK_CODES)}")
    print()
    print(f"Current parameters:")
    print(f"  Volume multiplier: 3.0x (200% increase)")
    print(f"  RSI threshold: 70 (overbought)")
    print()
    
    # Diagnose each stock
    for code in STOCK_CODES:
        diagnose_stock(code, START_DATE, END_DATE)
    
    # Summary
    print()
    print("="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print()
    print("If no signals found, try relaxing parameters:")
    print()
    print("Option 1: Lower volume requirement")
    print("  volume_multiplier: 3.0 → 2.5")
    print()
    print("Option 2: Lower RSI threshold")
    print("  rsi_threshold: 70 → 65")
    print()
    print("Option 3: Both")
    print("  volume_multiplier: 2.5")
    print("  rsi_threshold: 65")
    print()
    print("Edit run_backtest_improved.py and change PARAMS")
    print()


if __name__ == '__main__':
    main()
