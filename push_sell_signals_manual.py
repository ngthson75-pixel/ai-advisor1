#!/usr/bin/env python3
"""Push SELL signals qua API"""

import requests
from datetime import datetime

# 10 SELL signals
SIGNALS = [
    {'ticker': 'BID', 'entry': 47900, 'exit': 45600, 'strategy': 'STOP_LOSS', 'qty': 100},
    {'ticker': 'SAB', 'entry': 49200, 'exit': 46800, 'strategy': 'STOP_LOSS', 'qty': 100},
    {'ticker': 'BCM', 'entry': 70900, 'exit': 66000, 'strategy': 'STOP_LOSS', 'qty': 100},
    {'ticker': 'CTG', 'entry': 39400, 'exit': 36100, 'strategy': 'STOP_LOSS', 'qty': 100},
    {'ticker': 'KDC', 'entry': 52700, 'exit': 49800, 'strategy': 'STOP_LOSS', 'qty': 100},
    {'ticker': 'PVB', 'entry': 35100, 'exit': 41300, 'strategy': 'TAKE_PROFIT', 'qty': 50},
    {'ticker': 'VSC', 'entry': 23500, 'exit': 25900, 'strategy': 'TAKE_PROFIT', 'qty': 50},
    {'ticker': 'PC1', 'entry': 24200, 'exit': 30150, 'strategy': 'TAKE_PROFIT', 'qty': 30},
    {'ticker': 'PET', 'entry': 34200, 'exit': 37600, 'strategy': 'TAKE_PROFIT', 'qty': 100},
    {'ticker': 'DCM', 'entry': 36600, 'exit': 40300, 'strategy': 'TAKE_PROFIT', 'qty': 100},
]

API_URL = 'https://ai-advisor1-backend.onrender.com/api/signals'
TODAY = datetime.now().strftime('%Y-%m-%d')

print("🚀 PUSH 10 SELL SIGNALS QUA API\n")

success = 0
for sig in SIGNALS:
    pl_pct = ((sig['exit'] - sig['entry']) / sig['entry']) * 100
    
    payload = {
        'ticker': sig['ticker'],
        'action': 'SELL',
        'entry_price': sig['entry'],
        'stop_loss': 0,
        'take_profit': 0,
        'strategy': sig['strategy'],
        'strength': 80,
        'stock_type': 'Mid Cap',
        'rsi': 50,
        'date': TODAY
    }
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            print(f"✅ {sig['ticker']} — {sig['strategy']} ({pl_pct:+.2f}%)")
            success += 1
        else:
            print(f"❌ {sig['ticker']} — HTTP {resp.status_code}")
    except Exception as e:
        print(f"❌ {sig['ticker']} — {e}")

print(f"\n✅ Thành công: {success}/10 signals")
