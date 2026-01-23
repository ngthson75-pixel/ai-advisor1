import sqlite3
import requests
import json

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT ticker, strategy, entry_price, stop_loss, take_profit, 
           risk_reward, strength, is_priority, stock_type, rsi, date, action
    FROM signals 
    WHERE date="2026-01-20"
''')

signals = []
for row in cursor.fetchall():
    signals.append({
        'ticker': row[0],
        'strategy': row[1],
        'entry_price': row[2],
        'stop_loss': row[3],
        'take_profit': row[4],
        'risk_reward': row[5] or 0,
        'strength': row[6] or 0,
        'is_priority': row[7] or 0,
        'stock_type': row[8] or 'Penny',
        'rsi': row[9] or 50,
        'date': row[10],
        'action': row[11] or 'BUY'
    })

conn.close()

print(f'Found {len(signals)} signals to push')
print('\nPushing to production...')

success = 0
failed = 0

for sig in signals:
    try:
        response = requests.post(
            f'{API_BASE}/signals/import',
            json=sig,
            timeout=10
        )
        
        if response.status_code == 200:
            success += 1
            print(f'  ✅ {sig["ticker"]}')
        else:
            failed += 1
            print(f'  ❌ {sig["ticker"]}: {response.status_code}')
    except Exception as e:
        failed += 1
        print(f'  ❌ {sig["ticker"]}: {str(e)}')

print(f'\n✅ Success: {success}')
print(f'❌ Failed: {failed}')