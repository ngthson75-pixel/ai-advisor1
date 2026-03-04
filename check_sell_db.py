from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check SELL signals from March 3 onwards
    result = conn.execute(text('''
        SELECT COUNT(*) as count
        FROM signals 
        WHERE action='SELL' 
          AND exit_date >= '2026-03-03'
    '''))
    
    count = result.fetchone()[0]
    print(f'\n📊 SELL signals since March 3: {count}')
    
    if count == 0:
        print('❌ NO SELL SIGNALS IN DATABASE!')
        print('   Scanner found signals but failed to save!')
    else:
        print(f'✅ Database has {count} SELL signals')
        
        # Show them
        result = conn.execute(text('''
            SELECT ticker, exit_reason, exit_price, exit_date, created_at
            FROM signals 
            WHERE action='SELL' 
              AND exit_date >= '2026-03-03'
            ORDER BY created_at DESC
        '''))
        
        print('\nRecent SELL signals:')
        print('Ticker | Reason       | Price  | Exit Date  | Created')
        print('-------|--------------|--------|------------|----------')
        for row in result:
            print(f'{row[0]:<6} | {row[1]:<12} | {row[2]:<6} | {row[3]} | {str(row[4])[:19]}')
