import requests
import json

signal_data = {
    "ticker": "TEST",
    "strategy": "EMA_CROSS",
    "entry_price": 100.0,
    "stop_loss": 95.0,
    "take_profit": 108.0,
    "date": "2026-01-20",
    "action": "BUY",
    "risk_reward": 1.6,
    "strength": 75,
    "is_priority": 0,
    "stock_type": "Blue Chip",
    "rsi": 50.0
}

print("Sending test signal...")
print(f"Data: {json.dumps(signal_data, indent=2)}\n")

try:
    response = requests.post(
        'https://ai-advisor1-backend.onrender.com/api/signals/import',
        json=signal_data,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 500:
        print("\n❌ ERROR DETAILS:")
        try:
            error_json = response.json()
            print(json.dumps(error_json, indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"Exception: {str(e)}")