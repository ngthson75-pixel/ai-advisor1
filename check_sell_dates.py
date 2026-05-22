from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
db_url = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(db_url)

with engine.connect() as conn:
    # Count by exit_date
    result = conn.execute(text('''
        SELECT exit_date, COUNT(*) as count
        FROM signals 
        WHERE action='SELL'
        GROUP BY exit_date
        ORDER BY exit_date DESC
    '''))
    
    print('\n📅 SELL signals by exit_date:')
    print('Date       | Count')
    print('-----------|------')
    total = 0
    for row in result:
        date_str = row[0] if row[0] else 'None'
        print(f'{date_str:<10} | {row[1]}')
        total += row[1]
    
    print(f'-----------|------')
    print(f'TOTAL      | {total}')
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f'\n📆 Today: {today}')
    
    # Count created today
    result = conn.execute(text(f'''
        SELECT COUNT(*) 
        FROM signals 
        WHERE action='SELL' 
          AND exit_date = '{today}'
    '''))
    
    today_count = result.fetchone()[0]
    print(f'✅ SELL signals created TODAY: {today_count}')
    
    # Last 3 days breakdown
    print(f'\n📊 Last 3 days:')
    for i in range(3):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        result = conn.execute(text(f'''
            SELECT COUNT(*) 
            FROM signals 
            WHERE action='SELL' AND exit_date='{date}'
        '''))
        count = result.fetchone()[0]
        emoji = '✅' if count > 0 else '⏳'
        print(f'{emoji} {date}: {count} signals')
