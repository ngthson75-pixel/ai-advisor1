import requests

response = requests.get('https://ai-advisor1-backend.onrender.com/api/signals')
signals = response.json()['signals']

if signals:
    print("Current signal fields in production:")
    print(signals[0].keys())
    
print("\nRequired fields for import:")
required = ['ticker', 'strategy', 'entry_price', 'stop_loss', 'take_profit', 'date']
print(required)