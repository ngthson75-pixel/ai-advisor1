from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(db_url)

print('='*70)
print('CHECKING PRODUCTION DATABASE')
print('='*70)
print(f'URL: {db_url[:60]}...\n')

with engine.connect() as conn:
    # Check SELL signals
    result = conn.execute(text('''
        SELECT 
            ticker,
            exit_price,
            exit_reason,
            exit_date,
            strategy,
            entry_price
        FROM signals 
        WHERE action='SELL'
        ORDER BY created_at DESC
        LIMIT 5
    '''))
    
    print('📊 Sample SELL signals in PRODUCTION:')
    print('Ticker | exit_price | exit_reason | exit_date  | strategy')
    print('-------|------------|-------------|------------|----------')
    
    rows = list(result)
    for row in rows:
        ep = str(row[1]) if row[1] else 'None'
        er = str(row[2]) if row[2] else 'None'
        ed = str(row[3]) if row[3] else 'None'
        print(f'{row[0]:<6} | {ep:<10} | {er:<11} | {ed:<10} | {row[4]}')
    
    print('\n' + '='*70)
    
    # Count NULL values
    result = conn.execute(text('''
        SELECT 
            COUNT(*) as total,
            COUNT(exit_price) as has_exit_price,
            COUNT(exit_reason) as has_exit_reason,
            COUNT(exit_date) as has_exit_date
        FROM signals 
        WHERE action='SELL'
    '''))
    
    row = result.fetchone()
    total = row[0]
    with_ep = row[1]
    with_er = row[2]
    with_ed = row[3]
    
    print(f'Total SELL signals: {total}')
    print(f'  With exit_price:  {with_ep}/{total}')
    print(f'  With exit_reason: {with_er}/{total}')
    print(f'  With exit_date:   {with_ed}/{total}')
    
    missing = total - with_ep
    
    if missing > 0:
        print(f'\n❌ {missing} signals MISSING exit_price!')
        print('   → Need to run migration!')
    else:
        print(f'\n✅ All {total} signals have exit_price!')
    
    print('='*70)
