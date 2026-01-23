import sqlite3

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

cursor.execute('SELECT date, COUNT(*) FROM signals WHERE action="BUY" GROUP BY date ORDER BY date DESC LIMIT 3')
print('Recent BUY signals by date:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} signals')

cursor.execute('SELECT stock_type, COUNT(*) FROM signals WHERE date="2026-01-20" GROUP BY stock_type')
print('\nStock types for 2026-01-20:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

cursor.execute('SELECT COUNT(*) FROM signals')
total = cursor.fetchone()[0]
print(f'\nTotal signals in database: {total}')

conn.close()