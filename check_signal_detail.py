import requests

response = requests.get('https://ai-advisor1-backend.onrender.com/api/signals')
signals = response.json()['signals']

# Find signal from 2026-01-20
recent = [s for s in signals if s['date'] == '2026-01-20']

if recent:
    print(f'Found {len(recent)} signals from 2026-01-20:\n')
    for sig in recent[:3]:
        print(f"Ticker: {sig['ticker']}")
        print(f"Strategy: {sig['strategy']}")
        print(f"Strength: {sig['strength']}")
        print(f"Stock Type: {sig['stock_type']}")
        print(f"Date: {sig['date']}")
        print('-' * 40)
else:
    print('No signals from 2026-01-20!')

# Check SELL signals
sell_signals = [s for s in signals if s['action'] == 'SELL']
print(f'\nSELL signals: {len(sell_signals)}')
if sell_signals:
    print('Latest SELL:')
    print(f"  {sell_signals[0]['ticker']} - {sell_signals[0]['date']}")