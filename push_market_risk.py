#!/usr/bin/env python3
"""
PUSH MARKET RISK - Đẩy kết quả local lên staging hoặc production
=================================================================

Chạy sau khi đã có market_risk_latest.json

  cd C:\\ai-advisor1
  python push_market_risk.py              ← mặc định production
  python push_market_risk.py --staging    ← test staging trước
"""

import json
import os
import sys
import requests
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MARKET_RISK_FILE = os.path.join(SCRIPT_DIR, 'market_risk_latest.json')

STAGING_API = 'https://ai-advisor1-staging.onrender.com'
PROD_API = 'https://ai-advisor1-backend.onrender.com'

def main():
    # Chọn environment
    use_staging = '--staging' in sys.argv
    api_url = STAGING_API if use_staging else PROD_API
    env_name = 'STAGING' if use_staging else 'PRODUCTION'
    
    print(f"\n🎯 Target: {env_name} ({api_url})")
    
    if not os.path.exists(MARKET_RISK_FILE):
        print("❌ Chưa có file market_risk_latest.json")
        print("   Chạy trước:")
        print("   cd C:\\ai-advisor1\\scripts && python daily_signal_scanner_eod.py")
        print("   cd C:\\ai-advisor1 && python market_risk_analysis.py")
        return
    
    with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mode_emoji = data.get('mode_emoji', '🟡')
    print(f"\n{mode_emoji} {data.get('mode_label', 'N/A')} | Score: {data.get('risk_score', 0)}/100 | CP: {data.get('allocation', 50)}%")
    print(f"📝 {data.get('description', '')}")
    
    # Hiển thị factors
    for f_item in data.get('factors', []):
        if f_item.get('isRef'):
            status = '📎'
        elif f_item.get('positive'):
            status = '✅'
        else:
            status = '⚠️'
        value = f_item.get('value', '')
        has_data = 'Chưa có' not in str(value)
        print(f"   {status} {f_item.get('label', '')}: {value} {'✓' if has_data else '← THIẾU DATA'}")
    
    confirm = input(f"\nĐẩy lên {env_name}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Đã hủy.")
        return
    
    try:
        print(f"   Đang đẩy lên {env_name}...")
        response = requests.post(
            f"{api_url}/api/market-risk/upload",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            resp = response.json()
            print(f"✅ Đã cập nhật {env_name}! ({resp.get('message', '')})")
        else:
            print(f"❌ Lỗi {response.status_code}: {response.text[:300]}")
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Không kết nối được {env_name} (server đang ngủ?)")
        print(f"   Wake up: Invoke-WebRequest -Uri '{api_url}/health' -UseBasicParsing")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == '__main__':
    main()
