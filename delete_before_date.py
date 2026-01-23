import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

# Get all signals
response = requests.get(f'{API_BASE}/signals')
signals = response.json()['signals']

# Find signals before 2026-01-20
old_signals = [s for s in signals if s['date'] < '2026-01-20']

print(f'Found {len(old_signals)} signals before 2026-01-20:')
for sig in old_signals:
    print(f"  {sig['id']}: {sig['ticker']} - {sig['date']}")

# Since we don't have delete by ID endpoint, use clear-old with appropriate days
import requests
from datetime import datetime

# Calculate days difference
today = datetime.now()
cutoff = datetime(2026, 1, 20)
days_diff = (today - cutoff).days

print(f'\nDeleting signals older than {days_diff} days...')

response = requests.post(
    f'{API_BASE}/signals/clear-old',
    json={'days': days_diff},
    timeout=10
)

print(f'Result: {response.json()}')