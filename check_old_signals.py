import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

response = requests.get(f'{API_BASE}/signals')
signals = response.json()['signals']

print(f'Total: {len(signals)} signals\n')

# Group by date
from collections import defaultdict
by_date = defaultdict(list)
for sig in signals:
    by_date[sig['date']].append(f"{sig['ticker']} (ID:{sig['id']})")

print('📊 Signals by date:')
for date in sorted(by_date.keys(), reverse=True):
    tickers = ', '.join(by_date[date])
    print(f"  {date}: {len(by_date[date])} signals")
    print(f"    → {tickers}")

# Find old signals (before 2026-01-20)
old = [s for s in signals if s['date'] < '2026-01-20']
if old:
    print(f'\n❌ OLD SIGNALS (before 2026-01-20):')
    for s in old:
        print(f"  ID {s['id']}: {s['ticker']} - {s['date']}")
    print(f'\n💡 To delete: Use clear-old endpoint with days parameter')
else:
    print(f'\n✅ No old signals!')