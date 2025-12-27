#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIND EXACT TRADE DATES

Extract precise dates when signals were generated
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


def find_exact_signal_date(code, start_date, end_date):
    """Find exact date when signal was generated"""
    
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(
            symbol=code,
            start=start_date,
            end=end_date
        )
        
        if df.empty:
            return None
        
        # Detect signals
        detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
        df = detector.detect_signal(df)
        
        # Find signals
        signals = df[df['buy_signal'] == True].copy()
        
        if len(signals) == 0:
            return None
        
        # Return all signal dates
        results = []
        for idx, row in signals.iterrows():
            results.append({
                'date': row['time'],
                'price': float(row['close']),
                'volume_ratio': float(row['volume_ratio']),
                'rsi': float(row['rsi']),
                'macd': float(row['macd'])
            })
        
        return results
        
    except Exception as e:
        print(f"Error for {code}: {e}", file=sys.stderr)
        return None


def main():
    """Find exact dates for all 8 trades"""
    
    print("=" * 70)
    print("FINDING EXACT TRADE DATES")
    print("=" * 70)
    print()
    
    # All 15 stocks from VN100 backtest that generated signals
    stocks = [
        # Original 8 (already confirmed)
        'MBB', 'VIC', 'TCB', 'STB', 'SHB', 'POW', 'SAB',
        # New 7 from VN100 test
        'VIB', 'DXG', 'SZL', 'PAN', 'DHG', 'NT2', 'PVS'
    ]
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    all_trades = []
    
    for code in stocks:
        print(f"\n🔍 Searching {code}...", file=sys.stderr)
        
        signals = find_exact_signal_date(code, START_DATE, END_DATE)
        
        if signals:
            print(f"   ✅ Found {len(signals)} signal(s)", file=sys.stderr)
            for i, sig in enumerate(signals, 1):
                print(f"   Signal {i}:", file=sys.stderr)
                print(f"      Date: {sig['date']}", file=sys.stderr)
                print(f"      Price: {sig['price']:,.0f}", file=sys.stderr)
                print(f"      Volume: {sig['volume_ratio']:.2f}x", file=sys.stderr)
                print(f"      RSI: {sig['rsi']:.1f}", file=sys.stderr)
                print(f"      MACD: {sig['macd']:.4f}", file=sys.stderr)
                
                all_trades.append({
                    'stock': code,
                    'date': sig['date'],
                    'price': sig['price'],
                    'volume_ratio': sig['volume_ratio'],
                    'rsi': sig['rsi'],
                    'macd': sig['macd']
                })
        else:
            print(f"   ❌ No signals found", file=sys.stderr)
    
    # Summary table
    print("\n" + "=" * 70)
    print("COMPLETE TRADE LIST WITH EXACT DATES")
    print("=" * 70)
    print()
    print(f"{'#':<4} {'Stock':<8} {'Date':<20} {'Price':<12} {'Vol':<8} {'RSI':<8}")
    print("-" * 70)
    
    for i, trade in enumerate(all_trades, 1):
        print(f"{i:<4} {trade['stock']:<8} {str(trade['date']):<20} "
              f"{trade['price']:>10,.0f}  {trade['volume_ratio']:>6.2f}x  {trade['rsi']:>6.1f}")
    
    print()
    print("=" * 70)
    print(f"Total: {len(all_trades)} trades found")
    print("=" * 70)
    print()
    
    # For copying to dashboard
    print("\n📋 FOR DASHBOARD UPDATE:")
    print("-" * 70)
    for i, trade in enumerate(all_trades, 1):
        # Format date nicely
        date_str = str(trade['date']).split()[0]  # Get just the date part
        print(f"Trade {i}: {trade['stock']} @ {date_str} - Entry: {trade['price']:,.0f} VND")
    print()


if __name__ == '__main__':
    main()
