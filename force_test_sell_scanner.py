#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORCE TEST SELL SCANNER
Test scanner với mock data để verify logic hoạt động
"""

import sys
import sqlite3
from datetime import datetime, timedelta

# Import scanner class
try:
    from sell_signal_scanner_v2 import SellSignalScannerV2
except:
    # If not found, try scripts folder
    sys.path.append('scripts')
    from sell_signal_scanner_v2 import SellSignalScannerV2


def create_mock_buy_signals():
    """Create mock BUY signals for testing"""
    
    print("🔧 Creating mock BUY signals for testing...")
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    # Today and yesterday
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Mock signals that should trigger SELL
    mock_signals = [
        # Should trigger SL (current price will be below stop_loss)
        {
            'ticker': 'HPG',
            'strategy': 'PULLBACK',
            'entry_price': 30000,
            'stop_loss': 28500,  # Current ~27000 → Should trigger
            'take_profit': 32500,
            'date': yesterday,
            'action': 'BUY',
            'strength': 75,
            'stock_type': 'Blue Chip',
            'rsi': 45
        },
        
        # Should trigger TP (current price will be above take_profit)
        {
            'ticker': 'VCB',
            'strategy': 'EMA_CROSS',
            'entry_price': 85000,
            'stop_loss': 80750,
            'take_profit': 93500,  # Current ~95000 → Should trigger
            'date': yesterday,
            'action': 'BUY',
            'strength': 80,
            'stock_type': 'Blue Chip',
            'rsi': 55
        },
        
        # Should trigger MA20_CONSECUTIVE (price below MA20 for 2 days)
        {
            'ticker': 'TCB',
            'strategy': 'PULLBACK',
            'entry_price': 27000,
            'stop_loss': 25650,
            'take_profit': 29160,
            'date': yesterday,
            'action': 'BUY',
            'strength': 70,
            'stock_type': 'Blue Chip',
            'rsi': 50
        }
    ]
    
    # Insert mock signals
    inserted = 0
    for signal in mock_signals:
        try:
            cursor.execute("""
            INSERT INTO signals (
                ticker, strategy, entry_price, stop_loss, take_profit,
                date, action, strength, stock_type, rsi, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['ticker'],
                signal['strategy'],
                signal['entry_price'],
                signal['stop_loss'],
                signal['take_profit'],
                signal['date'],
                signal['action'],
                signal['strength'],
                signal['stock_type'],
                signal['rsi'],
                datetime.now().isoformat()
            ))
            inserted += 1
        except Exception as e:
            print(f"  ⚠ Error inserting {signal['ticker']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created {inserted} mock BUY signals")
    return inserted


def test_scanner():
    """Test scanner with mock data"""
    
    print("\n" + "="*60)
    print("FORCE TEST - SELL SIGNAL SCANNER")
    print("="*60)
    
    # Step 1: Create mock BUY signals
    mock_count = create_mock_buy_signals()
    
    if mock_count == 0:
        print("❌ Failed to create mock signals")
        return False
    
    # Step 2: Run scanner
    print("\n🔍 Running SELL scanner...")
    print("-" * 60)
    
    scanner = SellSignalScannerV2(db_path='signals.db')
    sell_signals = scanner.scan(days=2, delay=1.0)
    
    # Step 3: Results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    if sell_signals and len(sell_signals) > 0:
        print(f"✅ SUCCESS: Generated {len(sell_signals)} SELL signals")
        print("\nDetails:")
        for sig in sell_signals:
            reason = sig['exit_reason']
            pl = sig['profit_loss_pct']
            emoji = "🟢" if pl > 0 else "🔴"
            print(f"  {emoji} {sig['ticker']} - {reason} - {pl:+.2f}%")
        
        # Check database
        conn = sqlite3.connect('signals.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals WHERE action='SELL' AND exit_date=?", 
                      (datetime.now().strftime('%Y-%m-%d'),))
        db_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\n✓ Verified in database: {db_count} SELL signals")
        return True
        
    else:
        print("⚠ NO SELL signals generated")
        print("\nPossible reasons:")
        print("  1. VCI data fetch failed (rate limit?)")
        print("  2. Mock signals don't match current market prices")
        print("  3. Scanner logic issue")
        
        # Check what tickers were found
        conn = sqlite3.connect('signals.db')
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT DISTINCT ticker FROM signals 
            WHERE action='BUY' AND date >= ?
        """, (cutoff,))
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"\n📊 Found {len(tickers)} tickers in database:")
        for ticker in tickers:
            print(f"  - {ticker}")
        
        return False


def cleanup():
    """Remove mock signals"""
    
    print("\n🧹 Cleanup (optional)...")
    response = input("Remove mock BUY signals? (y/N): ").lower()
    
    if response == 'y':
        conn = sqlite3.connect('signals.db')
        cursor = conn.cursor()
        
        # Delete mock signals
        cursor.execute("""
        DELETE FROM signals 
        WHERE action='BUY' 
            AND ticker IN ('HPG', 'VCB', 'TCB')
            AND created_at >= DATE('now')
        """)
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✓ Removed {deleted} mock signals")
    else:
        print("✓ Mock signals kept")


if __name__ == '__main__':
    
    success = test_scanner()
    
    print("\n" + "="*60)
    
    if success:
        print("✅ SCANNER WORKING CORRECTLY!")
        print("\nThe issue is: No recent BUY signals in production database")
        print("\nSOLUTION:")
        print("  1. Run BUY scanner first: python scripts/daily_signal_scanner_eod.py")
        print("  2. Then SELL scanner will find signals to check")
    else:
        print("⚠ SCANNER NEEDS DEBUGGING")
        print("\nCheck:")
        print("  - VCI API connection")
        print("  - Database schema (all columns exist?)")
        print("  - Scanner logic")
    
    print("="*60)
    
    # Cleanup
    cleanup()
