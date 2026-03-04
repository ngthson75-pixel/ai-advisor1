from sqlalchemy import create_engine, text
from vnstock import Quote
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
db_url = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(db_url)

print('='*70)
print('SELL SIGNAL DIAGNOSTIC - FULL CHECK')
print('='*70)

seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

with engine.connect() as conn:
    # 1. Count BUY signals
    result = conn.execute(text(f'''
        SELECT COUNT(*) FROM signals 
        WHERE action='BUY' AND date >= '{seven_days_ago}'
    '''))
    buy_count = result.fetchone()[0]
    
    print(f'\n1. BUY signals (last 7 days): {buy_count}')
    
    if buy_count == 0:
        print('   ❌ NO BUY SIGNALS - This is why no SELL signals!')
        print('   → Need to run BUY signal scanner first')
    else:
        print(f'   ✅ {buy_count} BUY signals found')
        
        # 2. Check for SELL conditions
        result = conn.execute(text(f'''
            SELECT DISTINCT ticker, entry_price, stop_loss, take_profit, date
            FROM signals 
            WHERE action='BUY' AND date >= '{seven_days_ago}'
            LIMIT 5
        '''))
        
        print('\n2. Sample BUY signals:')
        print('   Ticker | Entry  | SL     | TP     | Date')
        for row in result:
            print(f'   {row[0]:<6} | {row[1]:<6} | {row[2]:<6} | {row[3]:<6} | {row[4]}')
        
        # 3. Check current prices
        print('\n3. Checking current prices vs SL/TP...')
        
        result = conn.execute(text(f'''
            SELECT DISTINCT ticker, entry_price, stop_loss, take_profit
            FROM signals 
            WHERE action='BUY' AND date >= '{seven_days_ago}'
            LIMIT 3
        '''))
        
        for row in result:
            ticker, entry, sl, tp = row
            try:
                data = Quote(symbol=ticker, source='VCI')
                df = data.history(
                    start=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    end=datetime.now().strftime('%Y-%m-%d')
                )
                if not df.empty:
                    current = float(df['close'].iloc[-1]) * 1000
                    if current <= sl:
                        print(f'   ✅ {ticker}: SL HIT (Current: {current:.0f} <= SL: {sl})')
                    elif current >= tp:
                        print(f'   ✅ {ticker}: TP HIT (Current: {current:.0f} >= TP: {tp})')
                    else:
                        print(f'   ⏳ {ticker}: No trigger (Current: {current:.0f}, SL: {sl}, TP: {tp})')
            except Exception as e:
                print(f'   ⚠️  {ticker}: {str(e)[:50]}')

print('\n' + '='*70)
