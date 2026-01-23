import requests

API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

# Delete signals older than 15 days
print('Deleting old signals...')

response = requests.post(
    f'{API_BASE}/signals/clear-old',
    json={'days': 15},
    timeout=10
)

if response.status_code == 200:
    result = response.json()
    print(f'✅ Deleted {result.get("deleted", 0)} old signals')
else:
    print(f'❌ Error: {response.text}')