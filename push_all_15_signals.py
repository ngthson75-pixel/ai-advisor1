import requests

# 6 signals đã push tay + 9 signals mới = 15 tổng
SIGNALS = [
    # Bộ 1: 6 signals đã push tay trước
    {'ticker': 'SZC', 'entry': 32200, 'exit': 35400, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'KBC', 'entry': 37200, 'exit': 40900, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'HDB', 'entry': 27800, 'exit': 26400, 'strategy': 'STOP_LOSS'},
    {'ticker': 'HAH', 'entry': 62500, 'exit': 68800, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'CTR', 'entry': 93000, 'exit': 90700, 'strategy': 'STOP_LOSS'},
    {'ticker': 'BID', 'entry': 47900, 'exit': 45600, 'strategy': 'STOP_LOSS'},
    
    # Bộ 2: 9 signals mới (10 - BID)
    {'ticker': 'SAB', 'entry': 49200, 'exit': 46800, 'strategy': 'STOP_LOSS'},
    {'ticker': 'BCM', 'entry': 70900, 'exit': 66000, 'strategy': 'STOP_LOSS'},
    {'ticker': 'CTG', 'entry': 39400, 'exit': 36100, 'strategy': 'STOP_LOSS'},
    {'ticker': 'KDC', 'entry': 52700, 'exit': 49800, 'strategy': 'STOP_LOSS'},
    {'ticker': 'PVB', 'entry': 35100, 'exit': 41300, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'VSC', 'entry': 23500, 'exit': 25900, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'PC1', 'entry': 24200, 'exit': 30150, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'PET', 'entry': 34200, 'exit': 37600, 'strategy': 'TAKE_PROFIT'},
    {'ticker': 'DCM', 'entry': 36600, 'exit': 40300, 'strategy': 'TAKE_PROFIT'},
]

API_URL = 'https://ai-advisor1-backend.onrender.com/api/signals'

print("🚀 PUSH 15 SELL SIGNALS (ĐẦY ĐỦ)\n")

success = 0
for sig in SIGNALS:
    pl = ((sig['exit'] - sig['entry']) / sig['entry']) * 100
    
    payload = {
        'ticker': sig['ticker'],
        'action': 'SELL',
        'entry_price': sig['entry'],
        'exit_price': sig['exit'],
        'stop_loss': sig['exit'] if 'STOP' in sig['strategy'] else 0,
        'take_profit': sig['exit'] if 'PROFIT' in sig['strategy'] else 0,
        'strategy': sig['strategy'],
        'strength': 80,
        'stock_type': 'Mid Cap',
        'rsi': 50,
        'date': '2026-03-03'
    }
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            emoji = '🟢' if pl > 0 else '🔴'
            print(f"✅ {sig['ticker']:4} — {sig['strategy']:15} {emoji} {pl:+6.2f}% | {sig['exit']:,}")
            success += 1
        else:
            print(f"❌ {sig['ticker']:4} — HTTP {resp.status_code}")
    except Exception as e:
        print(f"❌ {sig['ticker']:4} — {e}")

print(f"\n{'='*60}")
print(f"✅ Thành công: {success}/15 signals")
print(f"{'='*60}")
