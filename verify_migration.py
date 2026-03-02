import sqlite3

conn = sqlite3.connect('signals.db')
cur = conn.cursor()

# Check signal codes
cur.execute('SELECT signal_code, ticker FROM signals WHERE action="BUY" LIMIT 5')
print("Signal codes:")
for row in cur.fetchall():
    print(f"  {row[0]} - {row[1]}")

# Count
cur.execute('SELECT COUNT(*), COUNT(signal_code) FROM signals WHERE action="BUY"')
total, with_code = cur.fetchone()
print(f"\nTotal BUY signals: {total}")
print(f"With signal_code: {with_code}")
print(f"Success: {with_code == total}")

conn.close()