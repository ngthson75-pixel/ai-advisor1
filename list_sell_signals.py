from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT 
            id,
            ticker,
            entry_price,
            exit_price,
            stop_loss,
            take_profit,
            exit_reason,
            date as entry_date,
            exit_date
        FROM signals 
        WHERE action='SELL'
        ORDER BY exit_date DESC, ticker
    '''))
    
    print('\n' + '='*100)
    print('📊 TẤT CẢ SELL SIGNALS CẦN SỬA')
    print('='*100)
    print('ID   | Ticker | Entry   | Exit(hiện) | SL      | TP      | Exit Reason  | Entry Date | Exit Date')
    print('-----|--------|---------|------------|---------|---------|--------------|------------|----------')
    
    for row in result:
        id_str = str(row[0])
        print(f'{id_str:<4} | {row[1]:<6} | {row[2]:<7} | {row[3]:<10} | {row[4]:<7} | {row[5]:<7} | {row[6]:<12} | {row[7]:<10} | {row[8]}')
    
    print('='*100)
    print('\n💡 Copy bảng này để xem từng signal cần sửa gì')
