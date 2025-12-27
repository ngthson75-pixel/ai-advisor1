#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIND EXACT DATES FOR STRATEGY 3 SIGNALS

Extract precise entry dates and details for all 30 trades
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

from trend_pullback_scanner import TrendPullbackDetector


def find_signal_dates(code, start_date, end_date, detector):
    """Find all signal dates for a stock"""
    
    try:
        # Get data
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(
            symbol=code,
            start=start_date,
            end=end_date
        )
        
        if df.empty or len(df) < 60:
            return []
        
        # Detect signals
        df = detector.detect_signal(df)
        
        # Find buy signals
        signals = df[df['buy_signal'] == True].copy()
        
        if len(signals) == 0:
            return []
        
        # Extract signal details
        results = []
        
        for idx, row in signals.iterrows():
            signal_details = {
                'code': code,
                'date': str(row.name).split()[0],  # Just date part
                'price': float(row['close']),
                'ema20': float(row['ema20']),
                'ema50': float(row['ema50']),
                'rsi': float(row['rsi']),
                'volume_ratio': float(row['volume'] / row['avg_volume_20']),
                'pullback_pct': float(row['pullback_pct']),
                'stop_loss': float(row['ema50'] * 0.99),
                'risk_pct': float(((row['close'] - row['ema50'] * 0.99) / row['close']) * 100)
            }
            results.append(signal_details)
        
        return results
        
    except Exception as e:
        print(f"Error processing {code}: {e}", file=sys.stderr)
        return []


def main():
    """Find all signal dates for Strategy 3"""
    
    # Stocks that generated signals (from backtest output)
    SIGNAL_STOCKS = [
        'BID', 'REE', 'SSB', 'VCG', 'CTD', 'HDC', 'HDG', 'SZL',
        'VCI', 'FTS', 'ORS', 'EVF', 'DCM', 'BMP', 'PHR', 'DHG',
        'TDM', 'GEX', 'FRT', 'HAH', 'VOS', 'PVT', 'HAG'
    ]
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    print("=" * 80)
    print("STRATEGY 3: FINDING EXACT SIGNAL DATES")
    print("=" * 80)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Stocks: {len(SIGNAL_STOCKS)}")
    print("=" * 80)
    print()
    
    # Initialize detector
    detector = TrendPullbackDetector(
        ema_short=20,
        ema_long=50,
        rsi_period=14,
        rsi_lower=40,
        rsi_upper=60,
        volume_multiplier=1.5,
        pullback_min=0.03,
        pullback_max=0.08
    )
    
    # Find all signals
    all_signals = []
    
    for code in SIGNAL_STOCKS:
        print(f"🔍 Searching {code}...", file=sys.stderr)
        
        signals = find_signal_dates(code, START_DATE, END_DATE, detector)
        
        if signals:
            print(f"   ✅ Found {len(signals)} signal(s)", file=sys.stderr)
            for sig in signals:
                print(f"      Date: {sig['date']}", file=sys.stderr)
                print(f"      Entry: {sig['price']:,.0f}", file=sys.stderr)
                print(f"      EMA20: {sig['ema20']:.0f} | EMA50: {sig['ema50']:.0f}", file=sys.stderr)
                print(f"      RSI: {sig['rsi']:.1f} | Volume: {sig['volume_ratio']:.2f}x", file=sys.stderr)
                print(f"      Pullback: {sig['pullback_pct']:.1f}%", file=sys.stderr)
                print(f"      Stop Loss: {sig['stop_loss']:,.0f} (Risk: {sig['risk_pct']:.1f}%)", file=sys.stderr)
                print(file=sys.stderr)
                
                all_signals.append(sig)
        else:
            print(f"   ❌ No signals found", file=sys.stderr)
        
        print(file=sys.stderr)
    
    # Summary table
    print("\n" + "=" * 80)
    print("COMPLETE SIGNAL LIST WITH EXACT DATES")
    print("=" * 80)
    print()
    print(f"{'#':<4} {'Stock':<8} {'Date':<15} {'Entry':<10} {'EMA20':<8} {'EMA50':<8} {'RSI':<6} {'Vol':<7} {'Pull%':<6}")
    print("-" * 80)
    
    for i, sig in enumerate(all_signals, 1):
        print(f"{i:<4} {sig['code']:<8} {sig['date']:<15} "
              f"{sig['price']:>8,.0f}  {sig['ema20']:>6.0f}  {sig['ema50']:>6.0f}  "
              f"{sig['rsi']:>5.1f}  {sig['volume_ratio']:>5.2f}x  {sig['pullback_pct']:>5.1f}")
    
    print()
    print("=" * 80)
    print(f"Total: {len(all_signals)} signals found")
    print("=" * 80)
    print()
    
    # For dashboard update
    print("\n📋 FOR DASHBOARD UPDATE:")
    print("-" * 80)
    
    # Group by result (need to match with backtest output)
    winning_stocks = [
        'REE', 'SSB', 'VCG', 'HDC', 'HDG', 'SZL', 'ORS', 'DCM',
        'BMP', 'DHG', 'TDM', 'GEX', 'FRT', 'HAH', 'VOS', 'PVT'
    ]
    
    losing_stocks = [
        'BID', 'CTD', 'VCI', 'FTS', 'EVF', 'PHR', 'TDM', 'HAG'
    ]
    
    print("\n✅ WINNING TRADES:")
    for sig in all_signals:
        if sig['code'] in winning_stocks:
            print(f"Trade: {sig['code']} @ {sig['date']} - Entry: {sig['price']:,.0f} VND")
    
    print("\n❌ LOSING TRADES:")
    for sig in all_signals:
        if sig['code'] in losing_stocks:
            print(f"Trade: {sig['code']} @ {sig['date']} - Entry: {sig['price']:,.0f} VND")
    
    print()
    
    # Sector analysis
    print("\n📊 BY SECTOR:")
    print("-" * 80)
    
    sectors = {
        'Banking': ['BID', 'SSB'],
        'Construction': ['CTD', 'HDC', 'HDG', 'SZL', 'VCG'],
        'Securities': ['VCI', 'FTS', 'ORS'],
        'Manufacturing': ['EVF', 'DCM', 'BMP', 'PHR'],
        'Energy': ['REE', 'TDM', 'GEX'],
        'Consumer': ['DHG', 'FRT'],
        'Transportation': ['HAH', 'VOS', 'PVT', 'HAG']
    }
    
    for sector, codes in sectors.items():
        sector_signals = [s for s in all_signals if s['code'] in codes]
        if sector_signals:
            print(f"\n{sector} ({len(sector_signals)} signals):")
            for sig in sector_signals:
                print(f"  {sig['code']} @ {sig['date']}: {sig['price']:,.0f}")
    
    print()
    
    # Time distribution
    print("\n📅 BY MONTH:")
    print("-" * 80)
    
    from collections import defaultdict
    by_month = defaultdict(list)
    
    for sig in all_signals:
        month = sig['date'][:7]  # YYYY-MM
        by_month[month].append(sig)
    
    for month in sorted(by_month.keys()):
        signals = by_month[month]
        print(f"\n{month} ({len(signals)} signals):")
        for sig in signals:
            print(f"  {sig['date']}: {sig['code']} @ {sig['price']:,.0f}")
    
    print()


if __name__ == '__main__':
    main()
