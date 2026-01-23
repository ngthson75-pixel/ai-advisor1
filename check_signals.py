import sqlite3

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM signals WHERE date="2026-01-20"')
count = cursor.fetchone()[0]
print(f'Signals on 2026-01-20: {count}')

if count > 0:
    cursor.execute('SELECT ticker, strategy, strength FROM signals WHERE date="2026-01-20" ORDER BY strength DESC LIMIT 5')
    print('\nTop 5:')
    for row in cursor.fetchall():
        print(f'  {row[0]} - {row[1]} - {row[2]}%')

conn.close()