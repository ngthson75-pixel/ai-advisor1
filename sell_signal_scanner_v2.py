#!/usr/bin/env python3
"""
SELL SIGNAL SCANNER V2 - PRODUCTION MODULE
Reusable scanner for automated execution
"""

import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from vnstock import Quote

class SellSignalScannerV2:
    """
    Production-ready SELL signal scanner
    """
    
    def __init__(self, db_url=None):
        """
        Initialize scanner
        
        Args:
            db_url: Database URL (if None, use environment variable)
        """
        if db_url is None:
            import os
            db_url = os.getenv('DATABASE_URL')
            
            if not db_url:
                print("⚠️  WARNING: DATABASE_URL not found in environment!")
                print("⚠️  Using SQLite fallback (LOCAL ONLY - will NOT persist on Render)")
                db_url = 'sqlite:///signals.db'
        
        # Fix PostgreSQL URL
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Warn if using SQLite
        if 'sqlite' in db_url.lower():
            print(f"⚠️  Scanner using LOCAL SQLite: {db_url}")
            print("⚠️  This will NOT work in production!")
            print("⚠️  Set DATABASE_URL in .env to use PostgreSQL")
        else:
            print(f"✅ Scanner using PRODUCTION database: {db_url[:50]}...")
        
    
    def get_unique_buy_signals(self, days=7):
        """
        Get unique BUY signals from last N days
        
        Args:
            days: Look back N days for BUY signals
            
        Returns:
            List of (ticker, entry_price, stop_loss, take_profit, date, strategy, strength)
        """
        query = text(f"""
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
                  AND date >= CURRENT_DATE - INTERVAL '{days} days'
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
            with self.engine.connect() as conn:
                result = conn.execute(query)
                rows = result.fetchall()
                
                print(f"✅ Found {len(rows)} unique BUY signals (last {days} days)")
                return rows
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def check_sell_condition(self, ticker, entry_price, stop_loss, take_profit, retry=True):
        """
        Check if ticker meets SELL conditions
        
        Args:
            ticker: Stock code
            entry_price: Entry price from BUY signal
            stop_loss: Stop loss price
            take_profit: Take profit price
            retry: Retry on rate limit (default True)
            
        Returns:
            dict with SELL signal data or None
        """
        try:
            data = Quote(symbol=ticker, source='VCI')
            today = datetime.now()
            yesterday = today - timedelta(days=3)
            
            df = data.history(
                start=yesterday.strftime('%Y-%m-%d'),
                end=today.strftime('%Y-%m-%d')
            )
            
            if df.empty:
                return None
            
            # FIX: VNStock price x1000
            raw_price = float(df['close'].iloc[-1])
            current_price = raw_price * 1000
            
            # Check SELL conditions
            sell_reason = None
            
            if current_price <= stop_loss:
                sell_reason = "STOP_LOSS"
            elif current_price >= take_profit:
                sell_reason = "TAKE_PROFIT"
            
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
                    'exit_reason': sell_reason,  # NEW FIELD!
                    'exit_date': today.strftime('%Y-%m-%d')
                }
            
            return None
            
        except Exception as e:
            error_msg = str(e)
            
            if 'rate limit' in error_msg.lower() and retry:
                print(f"  ⚠️  Rate limit - retrying in 35s...")
                time.sleep(35)
                return self.check_sell_condition(
                    ticker, entry_price, stop_loss, take_profit, retry=False
                )
            
            return None
    
    def scan(self, days=7, delay=1.0):
        """
        Scan all BUY signals for SELL conditions
        
        Args:
            days: Look back N days
            delay: Delay between requests (seconds)
            
        Returns:
            List of SELL signals
        """
        print("\n" + "="*70)
        print("🔍 SCANNING FOR SELL SIGNALS")
        print("="*70)
        
        buy_signals = self.get_unique_buy_signals(days=days)
        
        if not buy_signals:
            print("⚠️  No BUY signals found")
            return []
        
        print(f"\nProcessing {len(buy_signals)} tickers...")
        print(f"⏱️  Delay: {delay}s between requests")
        print(f"⏱️  ETA: ~{len(buy_signals) * delay / 60:.1f} minutes")
        
        sell_signals = []
        start_time = time.time()
        
        for i, signal in enumerate(buy_signals):
            ticker = signal[0]
            entry_price = float(signal[1])
            stop_loss = float(signal[2])
            take_profit = float(signal[3])
            
            if i % 10 == 0 and i > 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(buy_signals) - i) * avg_time
                print(f"\nProgress: {i}/{len(buy_signals)} ({i*100//len(buy_signals)}%) - ETA: {remaining/60:.1f} min")
            
            sell_signal = self.check_sell_condition(
                ticker, entry_price, stop_loss, take_profit
            )
            
            if sell_signal:
                sell_signals.append(sell_signal)
                print(f"  ✅ SELL: {ticker} ({sell_signal['exit_reason']}) P/L: {sell_signal['profit_loss_pct']:+.2f}%")
            
            if i < len(buy_signals) - 1:
                time.sleep(delay)
        
        elapsed = time.time() - start_time
        print(f"\n" + "="*70)
        print(f"📊 RESULTS: {len(sell_signals)} SELL signals found")
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print("="*70)
        
        # Save to database
        if sell_signals:
            saved = self.save_sell_signals(sell_signals)
            print(f"\n✅ Saved {saved}/{len(sell_signals)} signals to database")
        
        return sell_signals
    
    def save_sell_signals(self, sell_signals):
        """
        Save SELL signals to database with proper exit fields
        
        Args:
            sell_signals: List of SELL signal dicts
            
        Returns:
            Number of signals saved
        """
        if not sell_signals:
            return 0
        
        # NEW: Use dedicated exit fields
        insert_query = text("""
            INSERT INTO signals (
                ticker,
                strategy,
                entry_price,
                exit_price,
                exit_reason,
                exit_date,
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
                :exit_price,
                :exit_reason,
                :exit_date,
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
            with self.engine.begin() as conn:
                for signal in sell_signals:
                    conn.execute(insert_query, {
                        'ticker': signal['ticker'],
                        'strategy': 'SELL_SIGNAL',  # Strategy for SELL
                        'entry_price': signal['entry_price'],
                        'exit_price': signal['exit_price'],  # NEW!
                        'exit_reason': signal['exit_reason'],  # NEW!
                        'exit_date': signal['exit_date'],  # NEW!
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'risk_reward': abs(signal['profit_loss_pct'] / 5.0) if signal['profit_loss_pct'] != 0 else 0,
                        'strength': 100 if signal['exit_reason'] == 'STOP_LOSS' else 80,
                        'stock_type': 'Unknown',
                        'date': signal['exit_date']
                    })
                    saved += 1
                
            return saved
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return 0


if __name__ == '__main__':
    """
    Test scanner locally
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("\n" + "="*70)
    print("🧪 SELL SCANNER V2 - TEST")
    print("="*70)
    
    # Use environment database or default
    db_url = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    
    scanner = SellSignalScannerV2(db_url=db_url)
    
    # Scan last 7 days
    sell_signals = scanner.scan(days=7, delay=2.0)
    
    if sell_signals:
        print("\n✅ Test complete!")
        print(f"Found {len(sell_signals)} SELL signals")
    else:
        print("\n⚠️  No SELL signals found")
    
    print("\n" + "="*70)
