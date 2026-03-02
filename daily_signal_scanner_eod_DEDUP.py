#!/usr/bin/env python3
"""
Daily Signal Scanner - End of Day (With Deduplication)
Prevents duplicate signals for the same ticker on same day.
Only keeps the BEST signal per ticker (highest score).
"""

import sqlite3
from datetime import datetime
import json

DB_PATH = 'signals.db'

def deduplicate_signals(signals):
    """
    Dedup signals by ticker - keep only BEST signal per ticker
    
    Priority:
    1. Highest score
    2. If score same → newest date
    3. If date same → first in list
    
    Args:
        signals: List of signal dicts
    
    Returns:
        Deduplicated list (1 signal per ticker max)
    """
    ticker_signals = {}
    
    for signal in signals:
        ticker = signal['ticker']
        
        if ticker not in ticker_signals:
            # First signal for this ticker
            ticker_signals[ticker] = signal
        else:
            # Compare with existing signal
            existing = ticker_signals[ticker]
            
            # Priority 1: Higher score wins
            if signal['score'] > existing['score']:
                ticker_signals[ticker] = signal
                print(f"  ↪️ {ticker}: Replaced score {existing['score']}% → {signal['score']}%")
            
            elif signal['score'] == existing['score']:
                # Priority 2: Newer date wins
                signal_date = signal.get('date', '')
                existing_date = existing.get('date', '')
                
                if signal_date > existing_date:
                    ticker_signals[ticker] = signal
                    print(f"  ↪️ {ticker}: Replaced (same score, newer date)")
                else:
                    print(f"  ⏭️ {ticker}: Skipped (duplicate, score {signal['score']}%)")
            else:
                print(f"  ⏭️ {ticker}: Skipped (lower score: {signal['score']}% vs {existing['score']}%)")
    
    deduplicated = list(ticker_signals.values())
    
    print(f"\n📊 Deduplication Summary:")
    print(f"  Input signals: {len(signals)}")
    print(f"  Output signals: {len(deduplicated)}")
    print(f"  Removed duplicates: {len(signals) - len(deduplicated)}")
    
    return deduplicated


def save_signals_to_db(signals):
    """
    Save deduplicated signals to database
    
    Args:
        signals: List of signal dicts (already deduplicated)
    """
    if not signals:
        print("⚠️ No signals to save")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        skipped_count = 0
        
        for signal in signals:
            ticker = signal['ticker']
            
            # Check if signal already exists today
            cursor.execute("""
                SELECT COUNT(*) FROM signals 
                WHERE ticker = ? 
                  AND action = 'BUY' 
                  AND date = ?
            """, (ticker, signal['date']))
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"  ⏭️ {ticker}: Already in DB for {signal['date']}")
                skipped_count += 1
                continue
            
            # Insert new signal
            cursor.execute("""
                INSERT INTO signals (
                    ticker, action, entry_price, stop_loss, take_profit,
                    strategy, strength, date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                'BUY',
                signal.get('entry_price'),
                signal.get('stop_loss'),
                signal.get('take_profit'),
                signal.get('strategy'),
                signal.get('score'),
                signal.get('date'),
                datetime.now()
            ))
            
            saved_count += 1
            print(f"  ✅ {ticker}: Saved (score: {signal['score']}%)")
        
        conn.commit()
        conn.close()
        
        print(f"\n💾 Database Save Summary:")
        print(f"  Saved: {saved_count}")
        print(f"  Skipped (already exists): {skipped_count}")
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")


def main():
    """
    Main scanner workflow with deduplication
    """
    print("="*70)
    print("🔍 DAILY SIGNAL SCANNER - END OF DAY (WITH DEDUP)")
    print("="*70)
    
    # STEP 1: Run your scanner logic (existing code)
    # This returns list of signals (may have duplicates)
    print("\n📡 Step 1: Scanning tickers...")
    
    # Example: Load from your scanner output
    # In real implementation, this would be your scanner results
    raw_signals = load_scanner_results()  # Replace with your scanner
    
    print(f"  Found: {len(raw_signals)} raw signals")
    
    # STEP 2: Deduplicate - 1 signal per ticker
    print("\n🔄 Step 2: Deduplicating signals...")
    deduplicated_signals = deduplicate_signals(raw_signals)
    
    # STEP 3: Save to database
    print("\n💾 Step 3: Saving to database...")
    save_signals_to_db(deduplicated_signals)
    
    print("\n" + "="*70)
    print("✅ SCAN COMPLETED")
    print("="*70)


def load_scanner_results():
    """
    Load scanner results from file or return from scanner
    
    Replace this with your actual scanner logic!
    """
    # Example: Load from signals_latest.json
    try:
        with open('scripts/signals/signals_latest.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('signals', [])
    except Exception as e:
        print(f"⚠️ Could not load signals: {e}")
        return []


if __name__ == '__main__':
    main()
