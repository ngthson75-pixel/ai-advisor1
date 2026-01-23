import sqlite3
import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT ticker, strategy, entry_price, stop_loss, take_profit, 
           risk_reward, strength, stock_type, rsi, date
    FROM signals 
    WHERE date="2026-01-20"
''')

print(f'Pushing signals to production...\n')

success = 0
failed = 0

for row in cursor.fetchall():
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
        # REMOVED: is_priority
    }
    
    try:
        response = requests.post(
            f'{API_BASE}/signals/import',
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            success += 1
            print(f'  ✅ {signal_data["ticker"]} - {signal_data["strategy"]} - {signal_data["strength"]}%')
        elif response.status_code == 409:
            print(f'  ⚠️  {signal_data["ticker"]} - Already exists')
            success += 1
        else:
            failed += 1
            print(f'  ❌ {signal_data["ticker"]}: {response.status_code} - {response.text}')
            
    except Exception as e:
        failed += 1
        print(f'  ❌ {signal_data["ticker"]}: {str(e)}')

conn.close()

print(f'\n{"="*50}')
print(f'✅ Success: {success}')
print(f'❌ Failed: {failed}')
print(f'{"="*50}')

if success > 0:
    print('\n🎉 Signals pushed successfully!')
    print('Refresh website: https://ai-advisor.vn')