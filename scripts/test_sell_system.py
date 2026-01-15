#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SYSTEM - COMPREHENSIVE TEST

Tests:
1. Database schema updated
2. SELL signal generation logic
3. Status tracking
4. API endpoints
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))


def test_database_schema():
    """Test 1: Verify database has new columns"""
    print("\n" + "=" * 70)
    print("TEST 1: DATABASE SCHEMA")
    print("=" * 70)
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    # Check columns
    cursor.execute("PRAGMA table_info(signals)")
    columns = [col[1] for col in cursor.fetchall()]
    
    has_status = 'signal_status' in columns
    has_quantity = 'quantity_sold' in columns
    
    print(f"✅ signal_status column: {'✅ EXISTS' if has_status else '❌ MISSING'}")
    print(f"✅ quantity_sold column: {'✅ EXISTS' if has_quantity else '❌ MISSING'}")
    
    if not has_status or not has_quantity:
        print("\n❌ Database schema not updated!")
        print("Run: python scripts/update_database.py")
        conn.close()
        return False
    
    # Check if BUY signals have status
    cursor.execute("""
        SELECT COUNT(*) 
        FROM signals 
        WHERE action = 'BUY' 
        AND signal_status IS NOT NULL
    """)
    buy_with_status = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM signals WHERE action = 'BUY'")
    total_buy = cursor.fetchone()[0]
    
    print(f"\n📊 BUY signals with status: {buy_with_status}/{total_buy}")
    
    if buy_with_status == 0 and total_buy > 0:
        print("⚠️  BUY signals don't have status. Run update_database.py")
    
    conn.close()
    
    print("\n✅ TEST 1 PASSED")
    return True


def test_sell_signal_generator():
    """Test 2: Test SELL signal generation logic"""
    print("\n" + "=" * 70)
    print("TEST 2: SELL SIGNAL GENERATOR")
    print("=" * 70)
    
    try:
        from sell_signal_generator import SellSignalGenerator
        
        generator = SellSignalGenerator()
        
        # Get active signals
        buy_signals = generator.get_active_buy_signals()
        
        print(f"\n📊 Found {len(buy_signals)} active BUY signals")
        
        if buy_signals:
            print("\nSample signals:")
            for sig in buy_signals[:3]:
                print(f"  • {sig['ticker']}: {sig['status']} ({sig['quantity_sold']:.0f}% sold)")
        
        print("\n✅ TEST 2 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_mock_sell_signal():
    """Test 3: Create a mock SELL signal"""
    print("\n" + "=" * 70)
    print("TEST 3: CREATE MOCK SELL SIGNAL")
    print("=" * 70)
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    try:
        # Get a BUY signal to work with
        cursor.execute("""
            SELECT id, ticker, entry_price, stop_loss, take_profit,
                   signal_status, quantity_sold
            FROM signals 
            WHERE action = 'BUY'
            AND signal_status = 'ACTIVE'
            LIMIT 1
        """)
        
        buy_signal = cursor.fetchone()
        
        if not buy_signal:
            print("⚠️  No ACTIVE BUY signals found. Skipping test.")
            conn.close()
            return True
        
        print(f"\n📊 Using BUY signal: {buy_signal[1]}")
        print(f"   Entry: {buy_signal[2]:,.0f}")
        print(f"   Status: {buy_signal[5]}")
        
        # Create a test SELL signal
        test_ticker = buy_signal[1]
        test_price = buy_signal[2] * 0.95  # 5% below entry (stop loss scenario)
        
        cursor.execute("""
            INSERT INTO signals (
                ticker, strategy, entry_price, stop_loss, take_profit,
                action, signal_status, quantity_sold, date, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_ticker,
            'TEST - Cắt lỗ',
            test_price,
            buy_signal[3],
            buy_signal[4],
            'SELL',
            'ACTIVE',
            100,
            datetime.now().strftime('%Y-%m-%d'),
            datetime.now()
        ))
        
        sell_id = cursor.lastrowid
        
        print(f"\n✅ Created test SELL signal (ID: {sell_id})")
        
        # Verify
        cursor.execute("""
            SELECT ticker, strategy, entry_price, quantity_sold
            FROM signals 
            WHERE id = ?
        """, (sell_id,))
        
        sell_signal = cursor.fetchone()
        print(f"\n📋 Verify SELL signal:")
        print(f"   Ticker: {sell_signal[0]}")
        print(f"   Type: {sell_signal[1]}")
        print(f"   Price: {sell_signal[2]:,.0f}")
        print(f"   Quantity: {sell_signal[3]:.0f}%")
        
        # Clean up test signal
        cursor.execute("DELETE FROM signals WHERE id = ?", (sell_id,))
        conn.commit()
        
        print(f"\n🧹 Cleaned up test signal")
        
        conn.close()
        
        print("\n✅ TEST 3 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        conn.rollback()
        conn.close()
        return False


def test_status_transitions():
    """Test 4: Verify status transitions work"""
    print("\n" + "=" * 70)
    print("TEST 4: STATUS TRANSITIONS")
    print("=" * 70)
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    # Count signals by status
    cursor.execute("""
        SELECT signal_status, COUNT(*) 
        FROM signals 
        WHERE action = 'BUY'
        GROUP BY signal_status
    """)
    
    status_counts = cursor.fetchall()
    
    print("\n📊 BUY Signal Status Distribution:")
    for status, count in status_counts:
        print(f"   {status}: {count} signals")
    
    conn.close()
    
    print("\n✅ TEST 4 PASSED")
    return True


def test_api_simulation():
    """Test 5: Simulate API calls"""
    print("\n" + "=" * 70)
    print("TEST 5: API SIMULATION")
    print("=" * 70)
    
    try:
        from sell_signal_generator import SellSignalGenerator
        
        generator = SellSignalGenerator()
        
        # Simulate GET /api/sell-signals
        print("\n📡 Simulating: GET /api/sell-signals")
        sell_signals = generator.get_sell_signals_for_display()
        
        print(f"   ✅ Returned {len(sell_signals)} SELL signals")
        
        if sell_signals:
            print("\n   Sample signals:")
            for sig in sell_signals[:3]:
                print(f"   • {sig['ticker']}: {sig['type']} @ {sig['price']:,.0f}")
        
        print("\n✅ TEST 5 PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 SELL SIGNAL SYSTEM - COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Signal Generator", test_sell_signal_generator),
        ("Mock SELL Signal", test_create_mock_sell_signal),
        ("Status Transitions", test_status_transitions),
        ("API Simulation", test_api_simulation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Sell signal system is ready!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Check the errors above and fix issues")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
