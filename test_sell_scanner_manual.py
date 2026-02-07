#!/usr/bin/env python3
"""
SELL SIGNAL SCANNER - PRODUCTION VERSION
Fixed: VNStock price x1000, removed is_priority column
"""

import os
import sys
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from vnstock import Quote
import pandas as pd

# ==============================================================================
# CONFIGURATION
# ==============================================================================

VERBOSE = True
DRY_RUN = False  # Set False to save to database

# Rate limit protection
DELAY_BETWEEN_REQUESTS = 1.0
RETRY_DELAY = 35

# Hardcoded DATABASE_URL - PASTE YOUR URL HERE:
DEFAULT_DATABASE_URL = "postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5"

# ==============================================================================
# GET DATABASE URL
# ==============================================================================

def get_database_url():
    """Lấy DATABASE_URL"""
    
    # Try environment variable
    db_url = os.getenv('DATABASE_URL')
    if db_url and 'postgresql://' in db_url:
        print(f"✅ Using DATABASE_URL from environment")
        return db_url
    
    # Use hardcoded default
    if DEFAULT_DATABASE_URL:
        print(f"✅ Using hardcoded DATABASE_URL")
        return DEFAULT_DATABASE_URL
    
    # Ask user
    print("\n" + "="*70)
    print("📝 DATABASE CONFIGURATION")
    print("="*70)
    db_url = input("\n📌 Paste DATABASE_URL: ").strip()
    return db_url if db_url and 'postgresql://' in db_url else None

# ==============================================================================
# DATABASE CONNECTION
# ==============================================================================

def test_database_connection(db_url):
    """Test kết nối database"""
    print("\n" + "="*70)
    print("🔌 TEST DATABASE CONNECTION")
    print("="*70)
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version[:50]}...")
            return engine
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

# ==============================================================================
# GET UNIQUE BUY SIGNALS
# ==============================================================================

def get_unique_buy_signals(engine):
    """Lấy BUY signals và deduplicate theo ticker"""
    print("\n" + "="*70)
    print("📊 GET BUY SIGNALS (DEDUPLICATED)")
    print("="*70)
    
    query = text("""
        WITH RankedSignals AS (
            SELECT 
                ticker,
                entry_price,
                stop_loss,
                take_profit,
                date,
                strategy,
                strength,
                ROW_NUMBER() OVER (
                    PARTITION BY ticker 
                    ORDER BY date DESC, created_at DESC
                ) as rn
            FROM signals
            WHERE action = 'BUY'
        )
        SELECT 
            ticker,
            entry_price,
            stop_loss,
            take_profit,
            date,
            strategy,
            strength
        FROM RankedSignals
        WHERE rn = 1
        ORDER BY date DESC
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
            
            print(f"✅ Found {len(rows)} unique tickers")
            
            if len(rows) > 0:
                print("\nSample signals:")
                for i, row in enumerate(rows[:5]):
                    print(f"  {i+1}. {row[0]} @ {row[1]:,.0f} VND (Date: {row[4]})")
                
                if len(rows) > 5:
                    print(f"\n  ... and {len(rows) - 5} more")
                    
            return rows
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return []

# ==============================================================================
# CHECK SELL CONDITIONS
# ==============================================================================

def check_sell_condition(ticker, entry_price, stop_loss, take_profit, retry=True):
    """Kiểm tra điều kiện SELL - FIXED: VNStock price x1000"""
    
    if VERBOSE:
        print(f"\n  Checking {ticker}...")
    
    try:
        data = Quote(symbol=ticker, source='VCI')
        today = datetime.now()
        yesterday = today - timedelta(days=3)
        
        df = data.history(
            start=yesterday.strftime('%Y-%m-%d'),
            end=today.strftime('%Y-%m-%d')
        )
        
        if df.empty:
            if VERBOSE:
                print(f"    ⚠️  No data")
            return None
        
        # FIX: VNStock returns price in thousands
        raw_price = float(df['close'].iloc[-1])
        current_price = raw_price * 1000
        
        if VERBOSE:
            print(f"    Current: {current_price:,.0f} VND")
            print(f"    Entry:   {entry_price:,.0f} VND")
            print(f"    SL:      {stop_loss:,.0f} VND")
            print(f"    TP:      {take_profit:,.0f} VND")
        
        # Check conditions
        sell_reason = None
        
        if current_price <= stop_loss:
            sell_reason = "STOP_LOSS"
            if VERBOSE:
                print(f"    🔴 STOP LOSS HIT!")
                
        elif current_price >= take_profit:
            sell_reason = "TAKE_PROFIT"
            if VERBOSE:
                print(f"    🟢 TAKE PROFIT HIT!")
        
        if sell_reason:
            profit_loss = current_price - entry_price
            profit_loss_pct = (profit_loss / entry_price) * 100
            
            return {
                'ticker': ticker,
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct,
                'sell_reason': sell_reason,
                'date': today.strftime('%Y-%m-%d')
            }
        else:
            if VERBOSE:
                print(f"    ⏸️  No SELL signal")
            return None
            
    except Exception as e:
        error_msg = str(e)
        
        if 'rate limit' in error_msg.lower() or 'quá nhiều request' in error_msg.lower():
            if VERBOSE:
                print(f"    ⚠️  Rate limit hit!")
            
            if retry:
                print(f"    ⏳ Waiting {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                print(f"    🔄 Retrying {ticker}...")
                return check_sell_condition(ticker, entry_price, stop_loss, take_profit, retry=False)
            else:
                print(f"    ❌ Rate limit - skipping")
                return None
        else:
            if VERBOSE:
                print(f"    ❌ Error: {e}")
            return None

# ==============================================================================
# SCAN ALL TICKERS
# ==============================================================================

def scan_sell_signals(buy_signals, max_tickers=None):
    """Scan tất cả BUY signals"""
    print("\n" + "="*70)
    print("🔍 SCANNING FOR SELL SIGNALS")
    print("="*70)
    
    sell_signals = []
    
    if max_tickers:
        buy_signals = buy_signals[:max_tickers]
        print(f"\n⚠️  Testing mode: Only checking first {max_tickers} tickers")
    
    total = len(buy_signals)
    print(f"\nProcessing {total} unique tickers...")
    print(f"⏱️  Delay: {DELAY_BETWEEN_REQUESTS}s between requests")
    print(f"⏱️  ETA: ~{total * DELAY_BETWEEN_REQUESTS / 60:.1f} minutes")
    
    start_time = time.time()
    
    for i, signal in enumerate(buy_signals):
        ticker = signal[0]
        entry_price = float(signal[1])
        stop_loss = float(signal[2])
        take_profit = float(signal[3])
        
        if i % 10 == 0:
            elapsed = time.time() - start_time
            if i > 0:
                avg_time = elapsed / i
                remaining = (total - i) * avg_time
                print(f"\nProgress: {i}/{total} ({i*100//total}%) - ETA: {remaining/60:.1f} min")
        
        sell_signal = check_sell_condition(ticker, entry_price, stop_loss, take_profit)
        
        if sell_signal:
            sell_signals.append(sell_signal)
            print(f"\n  ✅ SELL: {ticker} ({sell_signal['sell_reason']}) P/L: {sell_signal['profit_loss_pct']:+.2f}%")
        
        if i < total - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    elapsed = time.time() - start_time
    print(f"\n" + "="*70)
    print(f"📊 RESULTS: {len(sell_signals)} SELL signals found")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print("="*70)
    
    return sell_signals

# ==============================================================================
# DISPLAY RESULTS
# ==============================================================================

def display_results(sell_signals):
    """Hiển thị kết quả"""
    print("\n" + "="*70)
    print("📋 SELL SIGNALS SUMMARY")
    print("="*70)
    
    if not sell_signals:
        print("\n⚠️  No SELL signals found")
        return
    
    sl_count = sum(1 for s in sell_signals if s['sell_reason'] == 'STOP_LOSS')
    tp_count = sum(1 for s in sell_signals if s['sell_reason'] == 'TAKE_PROFIT')
    
    print(f"\nTotal: {len(sell_signals)}")
    print(f"  🔴 Stop Loss:   {sl_count}")
    print(f"  🟢 Take Profit: {tp_count}")
    
    print("\nDetails:")
    print("-" * 70)
    for i, signal in enumerate(sell_signals):
        print(f"\n{i+1}. {signal['ticker']}")
        print(f"   Entry:  {signal['entry_price']:,.0f} VND")
        print(f"   Exit:   {signal['exit_price']:,.0f} VND")
        print(f"   P/L:    {signal['profit_loss']:+,.0f} VND ({signal['profit_loss_pct']:+.2f}%)")
        print(f"   Reason: {signal['sell_reason']}")

# ==============================================================================
# SAVE SELL SIGNALS - FIXED: Removed is_priority
# ==============================================================================

def save_sell_signals(engine, sell_signals):
    """Lưu SELL signals - FIXED: No is_priority column"""
    print("\n" + "="*70)
    print("💾 SAVING TO DATABASE")
    print("="*70)
    
    if not sell_signals:
        print("⚠️  No signals to save")
        return 0
    
    if DRY_RUN:
        print("⚠️  DRY RUN MODE")
        return 0
    
    # FIXED: Removed is_priority column
    insert_query = text("""
        INSERT INTO signals (
            ticker,
            strategy,
            entry_price,
            stop_loss,
            take_profit,
            risk_reward,
            strength,
            stock_type,
            date,
            action,
            created_at
        ) VALUES (
            :ticker,
            :strategy,
            :entry_price,
            :stop_loss,
            :take_profit,
            :risk_reward,
            :strength,
            :stock_type,
            :date,
            'SELL',
            NOW()
        )
        ON CONFLICT DO NOTHING
    """)
    
    saved = 0
    
    try:
        with engine.begin() as conn:
            for signal in sell_signals:
                conn.execute(insert_query, {
                    'ticker': signal['ticker'],
                    'strategy': signal['sell_reason'],
                    'entry_price': signal['entry_price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'risk_reward': abs(signal['profit_loss_pct'] / 5.0) if signal['profit_loss_pct'] != 0 else 0,
                    'strength': 100 if signal['sell_reason'] == 'STOP_LOSS' else 80,
                    'stock_type': 'Unknown',
                    'date': signal['date']
                })
                saved += 1
                print(f"  ✅ {signal['ticker']} ({signal['sell_reason']})")
            
        print(f"\n🎉 Saved {saved} signals!")
        return saved
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 0

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main"""
    print("\n" + "="*70)
    print("🧪 SELL SIGNAL SCANNER - PRODUCTION")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'SAVE TO DB'}")
    
    db_url = get_database_url()
    if not db_url:
        return
    
    engine = test_database_connection(db_url)
    if not engine:
        return
    
    buy_signals = get_unique_buy_signals(engine)
    if not buy_signals:
        return
    
    print("\n" + "="*70)
    print("Choose:")
    print(f"  1. Test 10 tickers (~10 sec)")
    print(f"  2. Test 50 tickers (~1 min)")
    print(f"  3. ALL {len(buy_signals)} tickers (~{len(buy_signals)/60:.0f} min)")
    
    choice = input("\nChoice (1/2/3): ").strip()
    
    max_tickers = None
    if choice == '1':
        max_tickers = 10
    elif choice == '2':
        max_tickers = 50
    elif choice == '3':
        confirm = input(f"\nScan ALL? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    sell_signals = scan_sell_signals(buy_signals, max_tickers)
    display_results(sell_signals)
    
    if sell_signals and not DRY_RUN:
        saved = save_sell_signals(engine, sell_signals)
        if saved > 0:
            print(f"\n🎉 SUCCESS! Check: https://ai-advisor.vn")
    
    print("\n" + "="*70)
    print("✅ COMPLETE")
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()