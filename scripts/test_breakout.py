#!/usr/bin/env python3
"""
TEST BREAKOUT SCANNER với mock data

Test cases:
1. Volume spike (3x)
2. MACD crossover (âm → dương)
3. RSI > 70
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the scanner
try:
    # Import BreakoutDetector từ breakout_scanner.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "breakout_scanner",
        os.path.join(os.path.dirname(__file__), "breakout_scanner.py")
    )
    breakout_scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(breakout_scanner)
    
    BreakoutDetector = breakout_scanner.BreakoutDetector
except Exception as e:
    print(f"Error importing: {e}")
    sys.exit(1)


def generate_mock_breakout_data():
    """
    Generate mock data với breakout pattern
    
    Pattern:
    - Bars 1-30: Consolidation (low volume, sideways)
    - Bar 31: BREAKOUT! (3x volume, MACD cross, RSI > 70)
    """
    np.random.seed(42)
    
    # Generate time series (50 hours)
    dates = pd.date_range(
        end=datetime.now(),
        periods=50,
        freq='H'
    )
    
    data = []
    base_price = 50000
    base_volume = 1000000
    
    for i, date in enumerate(dates):
        if i < 30:
            # Consolidation phase
            price = base_price + np.random.uniform(-500, 500)
            volume = base_volume * np.random.uniform(0.8, 1.2)
            
        elif i == 30:
            # BREAKOUT BAR!
            price = base_price + 2000  # Breakout up
            volume = base_volume * 3.5  # 250% increase (3.5x)
            
        else:
            # Follow through
            price = base_price + 2000 + np.random.uniform(-200, 500)
            volume = base_volume * np.random.uniform(1.5, 2.5)
        
        data.append({
            'time': date,
            'open': price - np.random.uniform(0, 100),
            'high': price + np.random.uniform(0, 200),
            'low': price - np.random.uniform(0, 200),
            'close': price,
            'volume': int(volume)
        })
    
    return pd.DataFrame(data)


def generate_mock_no_signal_data():
    """
    Generate mock data WITHOUT signal (để test false positives)
    """
    np.random.seed(123)
    
    dates = pd.date_range(
        end=datetime.now(),
        periods=50,
        freq='H'
    )
    
    data = []
    base_price = 45000
    base_volume = 800000
    
    for i, date in enumerate(dates):
        # Random walk, no clear pattern
        price = base_price + np.random.uniform(-1000, 1000)
        volume = base_volume * np.random.uniform(0.5, 1.8)  # Not enough spike
        
        data.append({
            'time': date,
            'open': price - np.random.uniform(0, 100),
            'high': price + np.random.uniform(0, 200),
            'low': price - np.random.uniform(0, 200),
            'close': price,
            'volume': int(volume)
        })
    
    return pd.DataFrame(data)


def test_breakout_detection():
    """
    Test breakout detection logic
    """
    print("=" * 60)
    print("TEST 1: BREAKOUT PATTERN (should detect signal)")
    print("=" * 60)
    
    # Generate mock data với breakout
    df = generate_mock_breakout_data()
    
    print(f"Data points: {len(df)}")
    print(f"Time range: {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
    print()
    
    # Create detector
    detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
    
    # Detect signal
    df_with_indicators = detector.detect_signal(df)
    
    # Show last 5 bars
    print("Last 5 bars:")
    print(df_with_indicators[['time', 'close', 'volume', 'rsi', 'macd_histogram', 'buy_signal']].tail())
    print()
    
    # Get latest signal
    signal = detector.get_latest_signal(df_with_indicators)
    
    if signal:
        print("✅ SIGNAL DETECTED!")
        print(f"  Time: {signal['time']}")
        print(f"  Price: {signal['close']:,.0f}")
        print(f"  Volume ratio: {signal['volume_ratio']:.2f}x")
        print(f"  RSI: {signal['rsi']:.2f}")
        print(f"  MACD: {signal['macd']:.4f}")
        print(f"  Confidence: {signal['confidence']}/100")
    else:
        print("❌ NO SIGNAL (this is unexpected!)")
    
    print()
    print("=" * 60)
    print("TEST 2: NO SIGNAL PATTERN (should NOT detect)")
    print("=" * 60)
    
    # Generate data without signal
    df2 = generate_mock_no_signal_data()
    
    print(f"Data points: {len(df2)}")
    print()
    
    # Detect
    df2_with_indicators = detector.detect_signal(df2)
    signal2 = detector.get_latest_signal(df2_with_indicators)
    
    if signal2:
        print("❌ FALSE POSITIVE! Signal detected when it shouldn't be")
        print(f"  Volume ratio: {signal2['volume_ratio']:.2f}x")
        print(f"  RSI: {signal2['rsi']:.2f}")
    else:
        print("✅ CORRECT! No signal detected (as expected)")
    
    print()
    print("=" * 60)
    print("TEST 3: INDICATOR CALCULATIONS")
    print("=" * 60)
    
    # Check indicator values at breakout bar
    breakout_bar = df_with_indicators.iloc[30]  # Bar 31 (index 30)
    
    print(f"Breakout bar (index 30):")
    print(f"  Volume: {breakout_bar['volume']:,.0f}")
    print(f"  Volume ratio: {breakout_bar['volume_ratio']:.2f}x")
    print(f"  RSI: {breakout_bar['rsi']:.2f}")
    print(f"  MACD: {breakout_bar['macd']:.4f}")
    print(f"  MACD Histogram: {breakout_bar['macd_histogram']:.4f}")
    print(f"  Volume spike: {breakout_bar['volume_spike']}")
    print(f"  MACD crossover: {breakout_bar['macd_crossover']}")
    print(f"  RSI breakout: {breakout_bar['rsi_breakout']}")
    print(f"  BUY signal: {breakout_bar['buy_signal']}")
    
    print()
    print("=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    test_breakout_detection()
