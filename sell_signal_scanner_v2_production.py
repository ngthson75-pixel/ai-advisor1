#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER V2 - PRODUCTION VERSION

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
Phone: +84938127666

HOURLY SCAN: Every 1 hour during trading hours (9:00-15:00)
FLOW: Tickers → VCI → Check 4 conditions → Save SELL signals

RULES:
  1. SL: Price <= Stop Loss → SELL 100%
  2. TP: Price >= Take Profit → SELL 50%
  3. MA20_CONSECUTIVE: 2 days < MA20 → SELL 100%
  4. MA20_HIGH_VOLUME: < MA20 + Volume spike → SELL 100%
"""

import os
import sys
import time
from datetime import datetime, timedelta
import sqlite3

try:
    from vnstock import Vnstock
except ImportError:
    from vnstock3 import Vnstock


class SellSignalScannerV2:
    """SELL Signal Scanner for Production"""
    
    def __init__(self, db_path='signals.db'):
        self.db_path = db_path
        self.stock_api = Vnstock()
    
    
    def auto_migrate_database(self):
        """Auto-add required columns"""
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
        
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE signals ADD COLUMN {column_name} {column_type}")
                except:
                    pass
        
        conn.commit()
        conn.close()
    
    
    def get_unique_tickers(self, days=2):
        """Get unique tickers from recent BUY signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = """
        SELECT DISTINCT ticker
        FROM signals
        WHERE action = 'BUY' AND date >= ?
        ORDER BY ticker
        """
        
        cursor.execute(query, (cutoff_date,))
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return tickers
    
    
    def get_buy_signals_for_ticker(self, ticker):
        """Get active BUY signals for a ticker"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT 
            b.id, b.ticker, b.strategy, b.entry_price,
            b.stop_loss, b.take_profit, b.date as entry_date,
            b.strength, b.stock_type,
            COALESCE(SUM(s.exit_quantity_pct), 0) as total_sold_pct
        FROM signals b
        LEFT JOIN signals s 
            ON s.buy_signal_id = b.id AND s.action = 'SELL'
        WHERE b.ticker = ? AND b.action = 'BUY'
        GROUP BY b.id
        HAVING total_sold_pct < 100
        ORDER BY b.date DESC
        """
        
        cursor.execute(query, (ticker,))
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    
    def get_vci_data(self, ticker):
        """Get current data from VCI"""
        try:
            stock = self.stock_api.stock(symbol=ticker, source='VCI')
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=80)).strftime('%Y-%m-%d')
            
            history = stock.quote.history(start=start_date, end=end_date)
            
            if history is None or len(history) < 20:
                return None
            
            # vnstock returns prices in THOUSANDS
            multiplier = 1000
            
            history['EMA20'] = history['close'].ewm(span=20, adjust=False).mean()
            history['AvgVolume20'] = history['volume'].rolling(window=20).mean()
            
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
            print(f"  ⚠ VCI error: {e}")
            return None
    
    
    def check_sell_conditions(self, buy_signal, vci_data):
        """Check SELL conditions"""
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
        
        volume_ratio = volume / avg_volume_20 if avg_volume_20 > 0 else 0
        
        # RULE 1: STOP LOSS
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
        
        # RULE 2: TAKE PROFIT PARTIAL
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
        
        # RULE 3: MA20 CONSECUTIVE
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
        """Save SELL signal to database"""
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
            print(f"  ⚠ Save error: {e}")
            return False
    
    
    def scan(self, days=2, delay=2.0):
        """Main scan function"""
        
        print(f"🔍 SELL SCANNER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Migrate database
        self.auto_migrate_database()
        
        # Get tickers
        tickers = self.get_unique_tickers(days)
        
        if not tickers:
            print("⚠ No tickers")
            return []
        
        print(f"✓ Scanning {len(tickers)} tickers...")
        
        # Scan
        all_sell_signals = []
        
        for i, ticker in enumerate(tickers, 1):
            
            # Delay
            if i > 1:
                time.sleep(delay)
            
            # Get VCI data
            vci_data = None
            for retry in range(3):
                try:
                    vci_data = self.get_vci_data(ticker)
                    if vci_data:
                        break
                except Exception as e:
                    if 'rate limit' in str(e).lower() or 'quá nhiều' in str(e).lower():
                        time.sleep(15 * (retry + 1))
                    else:
                        break
            
            if not vci_data:
                continue
            
            # Get BUY signals
            buy_signals = self.get_buy_signals_for_ticker(ticker)
            
            if not buy_signals:
                continue
            
            # Check each BUY signal
            for buy_signal in buy_signals:
                sell_signals = self.check_sell_conditions(buy_signal, vci_data)
                
                for sell_signal in sell_signals:
                    if self.save_sell_signal(sell_signal):
                        all_sell_signals.append(sell_signal)
                        
                        reason = sell_signal['exit_reason']
                        pl = sell_signal['profit_loss_pct']
                        emoji = "🟢" if pl > 0 else "🔴"
                        
                        print(f"{emoji} {ticker} - {reason} - {pl:+.2f}%")
        
        # Summary
        print(f"\n✓ Generated {len(all_sell_signals)} SELL signals")
        
        return all_sell_signals


if __name__ == '__main__':
    scanner = SellSignalScannerV2(db_path='signals.db')
    sell_signals = scanner.scan(days=2, delay=2.0)
    
    sys.exit(0 if sell_signals is not None else 1)
