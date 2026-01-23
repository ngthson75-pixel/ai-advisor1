import sqlite3
import json

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT ticker, strategy, entry_price, stop_loss, take_profit, 
           risk_reward, strength, is_priority, stock_type, rsi, date
    FROM signals 
    WHERE date="2026-01-20"
    ORDER BY strength DESC
''')

signals = []
for row in cursor.fetchall():
    signals.append({
        'ticker': row[0],
        'strategy': row[1],
        'entry_price': row[2],
        'stop_loss': row[3],
        'take_profit': row[4],
        'risk_reward': row[5],
        'strength': row[6],
        'stock_type': row[8],
        'rsi': row[9],
        'date': row[10]
    })

with open('signals_export.json', 'w', encoding='utf-8') as f:
    json.dump(signals, f, indent=2, ensure_ascii=False)

print(f'✅ Exported {len(signals)} signals to signals_export.json')
conn.close()