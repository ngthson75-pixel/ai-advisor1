#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER V2 - FINAL VERSION

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLOW ĐÚNG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Lấy DANH SÁCH TICKERS từ BUY signals (2 ngày gần nhất)
        → ['VCB', 'HPG', 'TCB', 'MBB', ...] = 15-20 tickers

STEP 2: Loop qua TỪNG TICKER:
        → Quét VCI 1 lần để lấy: current_price, EMA20, volume
        → Delay 2s giữa mỗi request (tránh rate limit)

STEP 3: Với data từ VCI, check 4 điều kiện SELL:
        1. SL: Price <= Stop Loss → SELL 100%
        2. TP: Price >= Take Profit → SELL 50%
        3. MA20_CONSECUTIVE: 2 ngày < MA20 → SELL 100%
        4. MA20_HIGH_VOLUME: < MA20 + Volume spike → SELL 100%

STEP 4: Lưu SELL SIGNALS vào database
        → Website hiển thị cho nhà đầu tư

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPTIMIZATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OLD: 121 BUY signals → 121 API calls VCI → RATE LIMIT!
NEW: 15 tickers → 15 API calls VCI → NO RATE LIMIT ✓

Giảm: 87% API calls
"""

import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd

try:
    from vnstock import Vnstock
except ImportError:
    from vnstock3 import Vnstock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SellSignalScannerV2:
    """
    SELL Signal Scanner V2
    
    Optimized flow:
      Tickers → VCI data → Check conditions → Save SELL signals
    """
    
    def __init__(self, db_path='signals.db'):
        self.db_path = db_path
        self.stock_api = Vnstock()
    
    
    def auto_migrate_database(self):
        """Auto-add new columns to database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(signals)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = {
            'exit_reason': 'TEXT',
            'exit_date': 'TEXT',
            'profit_loss_pct': 'REAL',
            'exit_quantity_pct': 'REAL DEFAULT 100',
            'buy_signal_id': 'INTEGER',
            'volume_ratio': 'REAL'
        }
        
        added_columns = []
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE signals ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                except Exception as e:
                    pass
        
        if added_columns:
            conn.commit()
            print(f"⚙️ Auto-migration: Added {len(added_columns)} column(s)")
        
        conn.close()
    
    
    def get_unique_tickers_from_buy_signals(self, days=2):
        """
        STEP 1: Lấy DANH SÁCH TICKERS từ BUY signals
        
        Args:
            days: Lấy signals từ N ngày gần nhất
        
        Returns:
            list of ticker strings: ['VCB', 'HPG', 'TCB', ...]
        """
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = """
        SELECT DISTINCT ticker
        FROM signals
        WHERE action = 'BUY'
            AND date >= ?
        ORDER BY ticker
        """
        
        cursor.execute(query, (cutoff_date,))
        tickers = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return tickers
    
    
    def get_buy_signals_for_ticker(self, ticker):
        """
        STEP 3: Lấy TẤT CẢ BUY signals chưa bán hết của 1 ticker
        
        Args:
            ticker: Stock code (e.g., 'VCB')
        
        Returns:
            list of BUY signal dicts
        """
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            b.id,
            b.ticker,
            b.strategy,
            b.entry_price,
            b.stop_loss,
            b.take_profit,
            b.date as entry_date,
            b.strength,
            b.stock_type,
            COALESCE(SUM(s.exit_quantity_pct), 0) as total_sold_pct
        FROM signals b
        LEFT JOIN signals s 
            ON s.buy_signal_id = b.id
            AND s.action = 'SELL'
        WHERE b.ticker = ?
            AND b.action = 'BUY'
        GROUP BY b.id
        HAVING total_sold_pct < 100
        ORDER BY b.date DESC
        """
        
        cursor.execute(query, (ticker,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    
    def get_current_data_from_vci(self, ticker):
        """
        STEP 2: Quét VCI để lấy data hiện tại
        
        Returns:
            dict: {
                current_price, prev_close,
                ema20, prev_ema20,
                volume, avg_volume_20
            }
            
        Note:
            vnstock returns prices in THOUSANDS (nghìn đồng)
            VD: vnstock trả về 71 = 71,000 VND
            Database lưu 70,800 = 70,800 VND
            → Cần nhân 1000
        """
        try:
            stock = self.stock_api.stock(symbol=ticker, source='VCI')
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=80)).strftime('%Y-%m-%d')
            
            history = stock.quote.history(start=start_date, end=end_date)
            
            if history is None or len(history) < 20:
                return None
            
            # Price multiplier: vnstock trả về theo nghìn
            multiplier = 1000
            
            # Calculate EMA20
            history['EMA20'] = history['close'].ewm(span=20, adjust=False).mean()
            
            # Calculate average volume
            history['AvgVolume20'] = history['volume'].rolling(window=20).mean()
            
            # Get latest values
            latest = history.iloc[-1]
            prev = history.iloc[-2] if len(history) > 1 else latest
            
            return {
                'current_price': float(latest['close']) * multiplier,
                'prev_close': float(prev['close']) * multiplier,
                'ema20': float(latest['EMA20']) * multiplier,
                'prev_ema20': float(prev['EMA20']) * multiplier,
                'volume': float(latest['volume']),
                'avg_volume_20': float(latest['AvgVolume20'])
            }
            
        except Exception as e:
            print(f"  ⚠ Error: {e}")
            return None
    
    
    def check_sell_conditions(self, buy_signal, vci_data):
        """
        STEP 3: Check điều kiện SELL
        
        4 Rules (priority order):
          1. SL: Price <= Stop Loss → SELL 100%
          2. TP: Price >= Take Profit → SELL 50% (partial)
          3. MA20_CONSECUTIVE: Close < MA20 AND PrevClose < MA20 → SELL 100%
          4. MA20_HIGH_VOLUME: Close < MA20 AND Volume > 1.5x AvgVol → SELL 100%
        
        Returns:
            list of SELL signal dicts (0 or 1 signal)
        """
        signals = []
        
        ticker = buy_signal['ticker']
        entry_price = buy_signal['entry_price']
        stop_loss = buy_signal['stop_loss']
        take_profit = buy_signal['take_profit']
        available_pct = 100 - buy_signal['total_sold_pct']
        
        current_price = vci_data['current_price']
        prev_close = vci_data['prev_close']
        ema20 = vci_data['ema20']
        prev_ema20 = vci_data['prev_ema20']
        volume = vci_data['volume']
        avg_volume_20 = vci_data['avg_volume_20']
        
        # Calculate volume ratio
        volume_ratio = volume / avg_volume_20 if avg_volume_20 > 0 else 0
        
        # RULE 1: STOP LOSS (highest priority)
        if current_price <= stop_loss:
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            
            signals.append({
                'buy_signal_id': buy_signal['id'],
                'ticker': ticker,
                'strategy': buy_signal['strategy'],
                'action': 'SELL',
                'exit_reason': 'SL',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'exit_price': current_price,
                'exit_date': datetime.now().strftime('%Y-%m-%d'),
                'profit_loss_pct': profit_loss_pct,
                'exit_quantity_pct': available_pct,
                'volume_ratio': volume_ratio,
                'stock_type': buy_signal['stock_type'],
                'strength': buy_signal['strength'],
                'rsi': 0
            })
            return signals
        
        # RULE 2: TAKE PROFIT PARTIAL (50% only)
        if current_price >= take_profit and available_pct >= 50:
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            
            signals.append({
                'buy_signal_id': buy_signal['id'],
                'ticker': ticker,
                'strategy': buy_signal['strategy'],
                'action': 'SELL',
                'exit_reason': 'TP_PARTIAL',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'exit_price': current_price,
                'exit_date': datetime.now().strftime('%Y-%m-%d'),
                'profit_loss_pct': profit_loss_pct,
                'exit_quantity_pct': 50,
                'volume_ratio': volume_ratio,
                'stock_type': buy_signal['stock_type'],
                'strength': buy_signal['strength'],
                'rsi': 0
            })
            return signals
        
        # RULE 3: MA20 CONSECUTIVE (2 days below MA20)
        if current_price < ema20 and prev_close < prev_ema20:
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            
            signals.append({
                'buy_signal_id': buy_signal['id'],
                'ticker': ticker,
                'strategy': buy_signal['strategy'],
                'action': 'SELL',
                'exit_reason': 'MA20_CONSECUTIVE',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'exit_price': current_price,
                'exit_date': datetime.now().strftime('%Y-%m-%d'),
                'profit_loss_pct': profit_loss_pct,
                'exit_quantity_pct': available_pct,
                'volume_ratio': volume_ratio,
                'stock_type': buy_signal['stock_type'],
                'strength': buy_signal['strength'],
                'rsi': 0
            })
            return signals
        
        # RULE 4: MA20 HIGH VOLUME
        if current_price < ema20 and volume_ratio > 1.5:
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            
            signals.append({
                'buy_signal_id': buy_signal['id'],
                'ticker': ticker,
                'strategy': buy_signal['strategy'],
                'action': 'SELL',
                'exit_reason': 'MA20_HIGH_VOLUME',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'exit_price': current_price,
                'exit_date': datetime.now().strftime('%Y-%m-%d'),
                'profit_loss_pct': profit_loss_pct,
                'exit_quantity_pct': available_pct,
                'volume_ratio': volume_ratio,
                'stock_type': buy_signal['stock_type'],
                'strength': buy_signal['strength'],
                'rsi': 0
            })
            return signals
        
        return signals
    
    
    def save_sell_signal(self, sell_signal):
        """STEP 4: Save SELL signal to database"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO signals (
                ticker, strategy, entry_price, stop_loss, take_profit,
                action, exit_reason, exit_date, profit_loss_pct,
                exit_quantity_pct, buy_signal_id, volume_ratio,
                stock_type, strength, rsi, date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sell_signal['ticker'],
                sell_signal['strategy'],
                sell_signal['entry_price'],
                sell_signal['stop_loss'],
                sell_signal['take_profit'],
                sell_signal['action'],
                sell_signal['exit_reason'],
                sell_signal['exit_date'],
                sell_signal['profit_loss_pct'],
                sell_signal['exit_quantity_pct'],
                sell_signal['buy_signal_id'],
                sell_signal.get('volume_ratio'),
                sell_signal['stock_type'],
                sell_signal['strength'],
                sell_signal['rsi'],
                sell_signal['exit_date'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"  ⚠ Error saving: {e}")
            return False
    
    
    def scan(self, days=2, delay=2.0):
        """
        MAIN SCAN FUNCTION
        
        Flow:
          1. Lấy danh sách TICKERS từ BUY signals
          2. Loop TICKERS → Quét VCI (delay 2s)
          3. Check điều kiện SELL
          4. Lưu SELL signals
        
        Args:
            days: Lấy signals từ N ngày gần nhất (default: 2)
            delay: Delay giữa VCI requests (seconds, default: 2.0)
        
        Returns:
            list of SELL signals generated
        """
        
        print("=" * 70)
        print("🔍 SELL SIGNAL SCANNER V2 - FINAL")
        print("=" * 70)
        print("\n🎯 SELL RULES:")
        print("  1. SL: Price <= Stop Loss → SELL 100%")
        print("  2. TP: Price >= Take Profit → SELL 50% (partial)")
        print("  3. MA20 Consecutive: 2 days below MA20 → SELL 100%")
        print("  4. MA20 High Volume: Below MA20 + Volume spike → SELL 100%")
        print(f"\n⚙️ SETTINGS:")
        print(f"  - Scan period: Last {days} days")
        print(f"  - Delay: {delay}s between VCI requests")
        print(f"  - Flow: Tickers → VCI → Check → Save")
        print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Auto-migrate
        self.auto_migrate_database()
        
        # STEP 1: Lấy TICKERS
        print("━" * 70)
        print("STEP 1: Getting unique tickers from BUY signals...")
        print("━" * 70)
        
        tickers = self.get_unique_tickers_from_buy_signals(days)
        
        if not tickers:
            print("⚠ No tickers found")
            return []
        
        print(f"✓ Found {len(tickers)} unique tickers")
        if len(tickers) <= 20:
            print(f"  Tickers: {', '.join(tickers)}")
        else:
            print(f"  First 20: {', '.join(tickers[:20])} + {len(tickers)-20} more...")
        
        # STEP 2-4: Loop TICKERS
        print("\n" + "━" * 70)
        print("STEP 2-4: Scanning tickers...")
        print("━" * 70 + "\n")
        
        all_sell_signals = []
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}")
            
            # Delay
            if i > 1:
                print(f"  ⏳ Waiting {delay}s...")
                time.sleep(delay)
            
            # Get VCI data
            vci_data = None
            for retry in range(3):
                try:
                    vci_data = self.get_current_data_from_vci(ticker)
                    if vci_data:
                        break
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'rate limit' in error_msg or 'quá nhiều' in error_msg:
                        wait = 15 * (retry + 1)
                        print(f"  ⚠ Rate limit! Retry {retry+1}/3, wait {wait}s...")
                        time.sleep(wait)
                    else:
                        break
            
            if not vci_data:
                print(f"  ✗ Cannot get VCI data (skipped)\n")
                continue
            
            print(f"  ✓ Price: {vci_data['current_price']:,.0f}, EMA20: {vci_data['ema20']:,.0f}")
            
            # Get BUY signals
            buy_signals = self.get_buy_signals_for_ticker(ticker)
            
            if not buy_signals:
                print(f"  → No active BUY signals\n")
                continue
            
            print(f"  → Checking {len(buy_signals)} BUY signal(s)")
            
            # Check each BUY signal
            for j, buy_signal in enumerate(buy_signals, 1):
                sold = buy_signal['total_sold_pct']
                entry = buy_signal['entry_price']
                print(f"    [{j}] Entry: {entry:,.0f}, Sold: {sold:.0f}%")
                
                # Check SELL conditions
                sell_signals = self.check_sell_conditions(buy_signal, vci_data)
                
                if sell_signals:
                    for sell_signal in sell_signals:
                        reason = sell_signal['exit_reason']
                        qty = sell_signal['exit_quantity_pct']
                        exit_price = sell_signal['exit_price']
                        pl = sell_signal['profit_loss_pct']
                        
                        emoji = "🟢" if pl > 0 else "🔴"
                        
                        print(f"    {emoji} SELL {reason}: {qty:.0f}% at {exit_price:,.0f} ({pl:+.2f}%)")
                        
                        if self.save_sell_signal(sell_signal):
                            all_sell_signals.append(sell_signal)
                            print(f"    ✓ Saved")
                else:
                    print(f"    ✓ No SELL condition met")
            
            print()
        
        # Summary
        print("=" * 70)
        print("📊 SCAN COMPLETE")
        print("=" * 70)
        print(f"\n✓ Tickers scanned: {len(tickers)}")
        print(f"✓ SELL signals generated: {len(all_sell_signals)}")
        
        if all_sell_signals:
            print("\n📋 By Reason:")
            
            sl = len([s for s in all_sell_signals if s['exit_reason'] == 'SL'])
            tp = len([s for s in all_sell_signals if s['exit_reason'] == 'TP_PARTIAL'])
            ma_con = len([s for s in all_sell_signals if s['exit_reason'] == 'MA20_CONSECUTIVE'])
            ma_vol = len([s for s in all_sell_signals if s['exit_reason'] == 'MA20_HIGH_VOLUME'])
            
            print(f"  SL: {sl}")
            print(f"  TP_PARTIAL (50%): {tp}")
            print(f"  MA20_CONSECUTIVE: {ma_con}")
            print(f"  MA20_HIGH_VOLUME: {ma_vol}")
            
            print("\n🔝 Top 5:")
            sorted_sigs = sorted(all_sell_signals, 
                                key=lambda x: abs(x['profit_loss_pct']), 
                                reverse=True)
            
            for i, s in enumerate(sorted_sigs[:5], 1):
                emoji = "🟢" if s['profit_loss_pct'] > 0 else "🔴"
                print(f"{i}. {emoji} {s['ticker']} - {s['exit_reason']} - "
                      f"{s['exit_quantity_pct']:.0f}% - {s['profit_loss_pct']:+.2f}%")
        
        print("\n" + "=" * 70)
        
        return all_sell_signals


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sell Signal Scanner V2 - Final')
    parser.add_argument('--days', type=int, default=2,
                       help='Days to look back (default: 2)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between VCI requests (default: 2.0s)')
    parser.add_argument('--db', type=str, default='signals.db',
                       help='Database path (default: signals.db)')
    
    args = parser.parse_args()
    
    print("\n🚀 Starting SELL Signal Scanner V2...")
    print(f"⚙️ Settings: days={args.days}, delay={args.delay}s, db={args.db}\n")
    
    scanner = SellSignalScannerV2(db_path=args.db)
    sell_signals = scanner.scan(days=args.days, delay=args.delay)
    
    sys.exit(0 if sell_signals else 1)
