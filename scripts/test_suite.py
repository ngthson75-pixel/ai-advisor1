#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE

Test all components before running full backtest
"""

import sys
from datetime import datetime, timedelta

def test_imports():
    """Test 1: Check all required imports"""
    print("=" * 60)
    print("TEST 1: IMPORTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test vnstock
    try:
        from vnstock import Vnstock
        print("✅ vnstock")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ vnstock: {e}")
        tests_failed += 1
    
    # Test pandas
    try:
        import pandas as pd
        print("✅ pandas")
        tests_passed += 1
    except ImportError:
        print("❌ pandas")
        tests_failed += 1
    
    # Test numpy
    try:
        import numpy as np
        print("✅ numpy")
        tests_passed += 1
    except ImportError:
        print("❌ numpy")
        tests_failed += 1
    
    # Test scipy
    try:
        from scipy.signal import argrelextrema
        print("✅ scipy")
        tests_passed += 1
    except ImportError:
        print("❌ scipy - Install: pip install scipy --break-system-packages")
        tests_failed += 1
    
    # Test openpyxl
    try:
        from openpyxl import Workbook
        print("✅ openpyxl")
        tests_passed += 1
    except ImportError:
        print("❌ openpyxl - Install: pip install openpyxl --break-system-packages")
        tests_failed += 1
    
    print(f"\nResult: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


def test_vnstock_connection():
    """Test 2: VNStock connection and data fetch"""
    print("\n" + "=" * 60)
    print("TEST 2: VNSTOCK CONNECTION")
    print("=" * 60)
    
    try:
        from vnstock import Vnstock
        
        print("\nFetching VNM data (last 30 days)...")
        
        stock = Vnstock().stock(symbol='VNM', source='VCI')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = stock.quote.history(
            symbol='VNM',
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        if df.empty:
            print("❌ No data returned")
            return False
        
        print(f"✅ Success! Got {len(df)} rows")
        print(f"Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Check required columns
        required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ Missing columns: {missing_cols}")
            return False
        
        print("✅ All required columns present")
        
        # Show sample
        print("\nSample data (last 3 rows):")
        print(df[['time', 'close', 'volume']].tail(3))
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_detectors():
    """Test 3: Strategy detection modules"""
    print("\n" + "=" * 60)
    print("TEST 3: STRATEGY DETECTORS")
    print("=" * 60)
    
    try:
        # Import detectors
        print("\nImporting detector modules...")
        
        try:
            from breakout_scanner import BreakoutDetector
            print("✅ BreakoutDetector imported")
        except ImportError as e:
            print(f"❌ BreakoutDetector: {e}")
            return False
        
        try:
            from divergence_scanner import BearishDivergenceDetector
            print("✅ BearishDivergenceDetector imported")
        except ImportError as e:
            print(f"❌ BearishDivergenceDetector: {e}")
            return False
        
        # Create detector instances
        print("\nCreating detector instances...")
        
        breakout_detector = BreakoutDetector(
            volume_multiplier=3.0,
            rsi_threshold=70
        )
        print("✅ Breakout detector created")
        
        divergence_detector = BearishDivergenceDetector(
            volume_multiplier=3.0,
            rsi_threshold=70
        )
        print("✅ Divergence detector created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtest_engine():
    """Test 4: Backtest engine module"""
    print("\n" + "=" * 60)
    print("TEST 4: BACKTEST ENGINE")
    print("=" * 60)
    
    try:
        print("\nImporting backtest engine...")
        
        try:
            from backtest_system import BacktestEngine, StrategyBacktester
            print("✅ Backtest modules imported")
        except ImportError as e:
            print(f"❌ Backtest engine: {e}")
            return False
        
        # Create engine instance
        print("\nCreating backtest engine...")
        
        engine = BacktestEngine(initial_capital=100_000_000)
        print("✅ Backtest engine created")
        print(f"   Initial capital: {engine.initial_capital:,.0f} VND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end():
    """Test 5: End-to-end mini backtest"""
    print("\n" + "=" * 60)
    print("TEST 5: END-TO-END MINI BACKTEST")
    print("=" * 60)
    
    try:
        from vnstock import Vnstock
        from breakout_scanner import BreakoutDetector
        
        print("\nRunning mini backtest on VNM (last 30 days)...")
        
        # Fetch data
        stock = Vnstock().stock(symbol='VNM', source='VCI')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df = stock.quote.history(
            symbol='VNM',
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        print(f"✅ Fetched {len(df)} rows")
        
        # Detect signals
        detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
        df_signals = detector.detect_signal(df)
        
        print("✅ Strategy detection completed")
        
        # Count signals
        buy_signals = df_signals[df_signals['buy_signal'] == True]
        
        print(f"✅ Found {len(buy_signals)} BUY signals")
        
        if len(buy_signals) > 0:
            print("\nSignal summary:")
            for idx, row in buy_signals.iterrows():
                print(f"  Date: {row['time']}, Price: {row['close']:,.0f}, RSI: {row['rsi']:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "BACKTEST SYSTEM TEST SUITE" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("VNStock Connection", test_vnstock_connection()))
    results.append(("Strategy Detectors", test_strategy_detectors()))
    results.append(("Backtest Engine", test_backtest_engine()))
    results.append(("End-to-End", test_end_to_end()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30s} {status}")
    
    print("=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System ready to run full backtest")
        print("\nNext step:")
        print("  python backtest_system.py > backtest_results.json")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Fix issues above before running full backtest")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
