import sqlite3

conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

blue_chips = ['VNM', 'MBB', 'BID', 'CTG', 'VPB', 'HPG', 'VRE', 'SAB', 'BVH', 'VGC']
for ticker in blue_chips:
    cursor.execute('UPDATE signals SET stock_type="Blue Chip" WHERE ticker=?', (ticker,))

mid_caps = ['PLX', 'POW', 'HPX']
for ticker in mid_caps:
    cursor.execute('UPDATE signals SET stock_type="Mid Cap" WHERE ticker=?', (ticker,))

cursor.execute('UPDATE signals SET stock_type="Penny" WHERE stock_type IS NULL OR stock_type=""')

conn.commit()
print('✅ Stock types updated')
conn.close()