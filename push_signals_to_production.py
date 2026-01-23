#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PUSH LOCAL SIGNALS TO PRODUCTION

Reads signals from local signals.db and posts them to production API
"""

import sqlite3
import requests
import json
from datetime import datetime

# Configuration
LOCAL_DB = 'signals.db'
API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

print("=" * 70)
print("📤 PUSH LOCAL SIGNALS TO PRODUCTION")
print("=" * 70)

# Connect to local database
conn = sqlite3.connect(LOCAL_DB)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all BUY signals from today
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute("""
    SELECT * FROM signals 
    WHERE action = 'BUY' 
    AND date = ?
    ORDER BY strength DESC
""", (today,))

signals = cursor.fetchall()

print(f"\n📊 Found {len(signals)} BUY signals from {today}")

if len(signals) == 0:
    print("\n⚠️  No signals to push!")
    print("Run the scanner first: python scripts/daily_signal_scanner_eod.py")
    exit(0)

# Show preview
print("\n📋 Signals to push:")
for i, sig in enumerate(signals[:5], 1):
    print(f"   {i}. {sig['ticker']} - {sig['strategy']} - Score: {sig['strength']}")
if len(signals) > 5:
    print(f"   ... and {len(signals) - 5} more")

# Confirm
response = input(f"\n❓ Push {len(signals)} signals to production? (yes/no): ")
if response.lower() not in ['yes', 'y']:
    print("❌ Cancelled")
    exit(0)

# Push signals
print(f"\n📤 Pushing signals...")

success_count = 0
error_count = 0
errors = []

for sig in signals:
    signal_data = {
        'ticker': sig['ticker'],
        'strategy': sig['strategy'],
        'entry_price': sig['entry_price'],
        'stop_loss': sig['stop_loss'],
        'take_profit': sig['take_profit'],
        'risk_reward': sig['risk_reward'],
        'strength': sig['strength'],
        'is_priority': sig['is_priority'],
        'stock_type': sig['stock_type'],
        'rsi': sig['rsi'],
        'date': sig['date'],
        'action': sig['action']
    }
    
    try:
        # POST to API (need to create this endpoint)
        response = requests.post(
            f'{API_BASE}/signals/import',
            json=signal_data,
            timeout=10
        )
        
        if response.status_code == 200:
            success_count += 1
            print(f"   ✅ {sig['ticker']} - {sig['strategy']}")
        else:
            error_count += 1
            errors.append(f"{sig['ticker']}: {response.status_code}")
            print(f"   ❌ {sig['ticker']} - Error {response.status_code}")
    
    except Exception as e:
        error_count += 1
        errors.append(f"{sig['ticker']}: {str(e)}")
        print(f"   ❌ {sig['ticker']} - {str(e)}")

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"✅ Success: {success_count}")
print(f"❌ Errors: {error_count}")

if errors:
    print(f"\n⚠️  Errors:")
    for err in errors[:5]:
        print(f"   {err}")
    if len(errors) > 5:
        print(f"   ... and {len(errors) - 5} more")

print("\n" + "=" * 70)
print("✅ DONE!")
print("=" * 70)
print("\nRefresh website to see new signals: https://ai-advisor.vn")

conn.close()
