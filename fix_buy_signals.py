#!/usr/bin/env python3
"""Fix BUY signals bi dong nham khi push TAKE_PROFIT SELL signals"""
import requests
import sys

# Chon environment
if '--staging' in sys.argv:
    API = 'https://ai-advisor1-staging.onrender.com/api'
    ENV = 'STAGING'
else:
    API = 'https://ai-advisor1-backend.onrender.com/api'
    ENV = 'PRODUCTION'

print("=" * 60)
print(f"FIX BUY SIGNALS - {ENV}")
print("=" * 60)

# Step 1: Tim BUY signals bi dong nham
print("\n1. Tim BUY signals TAKE_PROFIT bi dong nham...")

r = requests.get(f'{API}/signals')
signals = r.json()['signals']

tickers_to_fix = ['DCM', 'PC1', 'STB', 'SZC']
to_fix = []

for s in signals:
    if (s['ticker'] in tickers_to_fix 
        and s['action'] == 'BUY' 
        and s.get('status') == 'closed'
        and s.get('position_pct', 0) == 0):
        code = s.get('signal_code', f"{s['ticker']}-{s['id']}")
        print(f"  {code} | {s['ticker']} | closed/0% | entry={s.get('entry_price')}")
        to_fix.append(s)

if not to_fix:
    print("  Khong tim thay BUY signal nao can fix!")
    print("\n  Tat ca BUY signals cua 4 ma:")
    for s in signals:
        if s['ticker'] in tickers_to_fix and s['action'] == 'BUY':
            code = s.get('signal_code', f"{s['ticker']}-{s['id']}")
            status = s.get('status', '?')
            pct = s.get('position_pct', '?')
            print(f"    {code} | status={status} | pct={pct}%")
    sys.exit()

print(f"\n2. Fix {len(to_fix)} signals: closed/0% -> partial/50%")
confirm = input("   Tiep tuc? (y/n): ").strip().lower()
if confirm != 'y':
    print("   Huy!")
    sys.exit()

# Step 2: Fix
print("\n3. Dang fix...")
success = 0

for s in to_fix:
    code = s.get('signal_code', f"{s['ticker']}-{s['id']}")
    payload = {
        'signal_id': s['id'],
        'status': 'partial',
        'position_pct': 50
    }
    
    try:
        resp = requests.post(f'{API}/admin/fix-signal', json=payload, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            print(f"  OK {code} -> {result.get('new_status')}/{result.get('new_pct')}%")
            success += 1
        else:
            print(f"  FAIL {code} - {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  FAIL {code} - {e}")

print(f"\nDone: {success}/{len(to_fix)} fixed")
