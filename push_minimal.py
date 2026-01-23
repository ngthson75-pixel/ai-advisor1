import sqlite3
import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT ticker, strategy, entry_price, stop_loss, take_profit, date
    FROM signals 
    WHERE date="2026-01-20"
''')

print(f'Pushing signals (minimal fields only)...\n')

success = 0
failed = 0

for row in cursor.fetchall():
    # CHỈ GỬI REQUIRED FIELDS
    signal_data = {
        'ticker': row[0],
        'strategy': row[1],
        'entry_price': float(row[2]),
        'stop_loss': float(row[3]),
        'take_profit': float(row[4]),
        'date': row[5]
    }
    
    try:
        response = requests.post(
            f'{API_BASE}/signals/import',
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            success += 1
            print(f'  ✅ {signal_data["ticker"]}')
        else:
            failed += 1
            print(f'  ❌ {signal_data["ticker"]}: {response.text}')
            
    except Exception as e:
        failed += 1
        print(f'  ❌ {signal_data["ticker"]}: {str(e)}')

conn.close()

print(f'\n✅ Success: {success} / ❌ Failed: {failed}')