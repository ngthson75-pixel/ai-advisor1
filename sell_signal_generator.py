#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL GENERATOR

Tự động tạo SELL signals dựa trên BUY signals:
1. STOP_LOSS: Price <= Stop Loss → Sell 100%
2. TAKE_PROFIT: Price >= Take Profit → Sell 50%
3. MA20_EXIT: Price < MA20 → Sell 50% (remaining)

Chạy mỗi ngày 6:00 PM sau khi download data
"""

import sqlite3
import os
from datetime import datetime, timedelta
from vnstock import Vnstock
import pandas as pd

class SellSignalGenerator:
    """Generate SELL signals based on active BUY signals"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Try to find database in multiple locations
            possible_paths = [
                'signals.db',  # Root directory (when running from root)
                os.path.join(os.path.dirname(__file__), '..', 'signals.db'),  # scripts/../signals.db
                os.path.join(os.getcwd(), 'signals.db'),  # Current working directory
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'signals.db'),  # Absolute path
            ]
            
            # Find first existing database
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = os.path.abspath(path)
                    break
            else:
                # Default to root
                self.db_path = 'signals.db'
        else:
            self.db_path = db_path
        
        self.stock_api = Vnstock()
    
    def get_active_buy_signals(self):
        """Get all ACTIVE and PARTIAL_SOLD BUY signals"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, ticker, entry_price, stop_loss, take_profit, 
                   signal_status, quantity_sold, date
            FROM signals 
            WHERE action = 'BUY' 
            AND signal_status IN ('ACTIVE', 'PARTIAL_SOLD')
            ORDER BY date DESC
        """)
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'ticker': row[1],
                'entry_price': row[2],
                'stop_loss': row[3],
                'take_profit': row[4],
                'status': row[5],
                'quantity_sold': row[6],
                'buy_date': row[7]
            })
        
        conn.close()
        return signals
    
    def get_current_price(self, ticker):
        """Get current price from VNStock"""
        try:
            stock = self.stock_api.stock(symbol=ticker, source='VCI')
            
            # Try to get latest price
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            df = stock.quote.history(symbol=ticker, start=yesterday, end=today)
            
            if not df.empty:
                return float(df['close'].iloc[-1])
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error getting price for {ticker}: {e}")
            return None
    
    def calculate_ma20(self, ticker):
        """Calculate 20-day moving average"""
        try:
            stock = self.stock_api.stock(symbol=ticker, source='VCI')
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            df = stock.quote.history(symbol=ticker, start=start_date, end=end_date)
            
            if len(df) >= 20:
                ma20 = df['close'].rolling(window=20).mean().iloc[-1]
                return float(ma20)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error calculating MA20 for {ticker}: {e}")
            return None
    
    def create_sell_signal(self, buy_signal, sell_type, quantity_pct, current_price):
        """Create a SELL signal in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Determine sell type label
            sell_labels = {
                'STOP_LOSS': 'Cắt lỗ',
                'TAKE_PROFIT': 'Chốt lời',
                'MA20_EXIT': 'Thoát MA20'
            }
            
            # Create SELL signal
            cursor.execute("""
                INSERT INTO signals (
                    ticker, strategy, entry_price, stop_loss, take_profit,
                    action, signal_status, quantity_sold, date, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                buy_signal['ticker'],
                sell_labels[sell_type],
                current_price,
                buy_signal['stop_loss'],
                buy_signal['take_profit'],
                'SELL',
                'ACTIVE',
                quantity_pct,
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now()
            ))
            
            # Update BUY signal status
            new_quantity_sold = buy_signal['quantity_sold'] + quantity_pct
            
            if new_quantity_sold >= 100:
                new_status = 'FULLY_SOLD'
            else:
                new_status = 'PARTIAL_SOLD'
            
            cursor.execute("""
                UPDATE signals 
                SET signal_status = ?,
                    quantity_sold = ?
                WHERE id = ?
            """, (new_status, new_quantity_sold, buy_signal['id']))
            
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating SELL signal: {e}")
            conn.rollback()
            return False
        
        finally:
            conn.close()
    
    def generate_sell_signals(self):
        """
        Main function: Generate SELL signals for all active BUY signals
        
        Returns:
            Number of SELL signals created
        """
        print("\n" + "=" * 70)
        print("🎯 SELL SIGNAL GENERATOR")
        print("=" * 70)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get active BUY signals
        buy_signals = self.get_active_buy_signals()
        
        if not buy_signals:
            print("\n📭 No active BUY signals found")
            return 0
        
        print(f"\n📊 Found {len(buy_signals)} active BUY signals to check")
        
        sell_count = 0
        
        for signal in buy_signals:
            ticker = signal['ticker']
            print(f"\n🔍 Checking {ticker}...")
            
            # Get current price
            current_price = self.get_current_price(ticker)
            
            if not current_price:
                print(f"   ⚠️  Could not get current price, skipping")
                continue
            
            print(f"   💰 Current: {current_price:,.0f}")
            print(f"   📉 Stop Loss: {signal['stop_loss']:,.0f}")
            print(f"   📈 Take Profit: {signal['take_profit']:,.0f}")
            print(f"   📊 Status: {signal['status']} ({signal['quantity_sold']:.0f}% sold)")
            
            # Check STOP LOSS (Priority 1)
            if current_price <= signal['stop_loss']:
                remaining_pct = 100 - signal['quantity_sold']
                
                if remaining_pct > 0:
                    print(f"   🚨 STOP LOSS triggered! Selling {remaining_pct:.0f}%")
                    
                    if self.create_sell_signal(
                        signal, 'STOP_LOSS', remaining_pct, current_price
                    ):
                        print(f"   ✅ Created STOP_LOSS signal")
                        sell_count += 1
                    continue
            
            # Check TAKE PROFIT (Priority 2)
            if current_price >= signal['take_profit']:
                # Only if haven't taken profit yet
                if signal['status'] == 'ACTIVE':
                    print(f"   🎯 TAKE PROFIT triggered! Selling 50%")
                    
                    if self.create_sell_signal(
                        signal, 'TAKE_PROFIT', 50, current_price
                    ):
                        print(f"   ✅ Created TAKE_PROFIT signal")
                        sell_count += 1
                    continue
            
            # Check MA20 EXIT (Priority 3)
            # Only if partially sold (already took profit)
            if signal['status'] == 'PARTIAL_SOLD':
                ma20 = self.calculate_ma20(ticker)
                
                if ma20:
                    print(f"   📊 MA20: {ma20:,.0f}")
                    
                    if current_price < ma20:
                        remaining_pct = 100 - signal['quantity_sold']
                        
                        if remaining_pct > 0:
                            print(f"   📉 MA20 EXIT triggered! Selling {remaining_pct:.0f}%")
                            
                            if self.create_sell_signal(
                                signal, 'MA20_EXIT', remaining_pct, current_price
                            ):
                                print(f"   ✅ Created MA20_EXIT signal")
                                sell_count += 1
                                continue
                    else:
                        print(f"   ✅ Price above MA20, holding")
        
        print("\n" + "=" * 70)
        print(f"✅ COMPLETED")
        print("=" * 70)
        print(f"📊 Checked: {len(buy_signals)} BUY signals")
        print(f"🎯 Created: {sell_count} SELL signals")
        print("=" * 70)
        
        return sell_count
    
    def get_sell_signals_for_display(self):
        """Get SELL signals for frontend display"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ticker, strategy, entry_price, date, quantity_sold
            FROM signals 
            WHERE action = 'SELL'
            ORDER BY date DESC
            LIMIT 50
        """)
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'ticker': row[0],
                'type': row[1],
                'price': row[2],
                'date': row[3],
                'quantity': row[4]
            })
        
        conn.close()
        return signals


def main():
    """Test the generator"""
    generator = SellSignalGenerator()
    sell_count = generator.generate_sell_signals()
    
    if sell_count > 0:
        print(f"\n🎉 Successfully created {sell_count} SELL signals!")
    else:
        print(f"\n📭 No SELL signals needed at this time")


if __name__ == '__main__':
    main()
