import sqlite3
import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

# Step 1: Delete signals from 2026-01-20
print('Step 1: Deleting signals from 2026-01-20...')

response = requests.get(f'{API_BASE}/signals')
all_signals = response.json()['signals']

# Get IDs of signals from 2026-01-20
today_ids = [s['id'] for s in all_signals if s['date'] == '2026-01-20' and s['action'] == 'BUY']

print(f'Found {len(today_ids)} signals to delete: {today_ids}\n')

# Delete via clear-old endpoint (delete last 0 days = today only)
response = requests.post(
    f'{API_BASE}/signals/clear-old',
    json={'days': 5},  # Delete last 5 days
    timeout=10
)

print(f'Deleted: {response.json()}\n')

# Step 2: Re-push with strength
print('Step 2: Re-pushing with correct strength values...\n')

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT ticker, strategy, entry_price, stop_loss, take_profit, 
           risk_reward, strength, stock_type, rsi, date
    FROM signals 
    WHERE date="2026-01-20"
    ORDER BY strength DESC
''')

rows = cursor.fetchall()
conn.close()

success = 0

for row in rows:
    signal_data = {
        'ticker': row[0],
        'strategy': row[1],
        'entry_price': float(row[2]),
        'stop_loss': float(row[3]),
        'take_profit': float(row[4]),
        'risk_reward': float(row[5]) if row[5] else 0.0,
        'strength': int(row[6]) if row[6] else 0,
        'stock_type': row[7] if row[7] else 'Penny',
        'rsi': float(row[8]) if row[8] else 50.0,
        'date': row[9],
        'action': 'BUY'
    }
    
    try:
        response = requests.post(
            f'{API_BASE}/signals/import',
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            success += 1
            print(f'  ✅ {signal_data["ticker"]:6} - Strength: {signal_data["strength"]}%')
        else:
            print(f'  ❌ {signal_data["ticker"]}: {response.status_code}')
            
    except Exception as e:
        print(f'  ❌ {signal_data["ticker"]}: {str(e)}')

print(f'\n✅ Re-pushed {success} signals with strength!')