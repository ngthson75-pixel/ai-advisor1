#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Advisor - Post Deployment Test Suite
Tests all components after v5.3 deployment
"""

import requests
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

FRONTEND_URL = "https://ai-advisor.vn"
BACKEND_URL = "https://ai-advisor1-backend.onrender.com"

print("\n" + "="*80)
print("AI ADVISOR - POST DEPLOYMENT TEST SUITE")
print("="*80)
print(f"Frontend: {FRONTEND_URL}")
print(f"Backend: {BACKEND_URL}")
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ============================================================================
# TEST 1: BACKEND HEALTH CHECK
# ============================================================================

print("\n[TEST 1] Backend Health Check...")

try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=10)
    if response.status_code == 200:
        print("✅ Backend is healthy")
        print(f"   Response: {response.text}")
    else:
        print(f"❌ Backend health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Backend not accessible: {e}")

# ============================================================================
# TEST 2: SIGNALS API
# ============================================================================

print("\n[TEST 2] Signals API...")

try:
    response = requests.get(f"{BACKEND_URL}/api/signals", timeout=30)
    if response.status_code == 200:
        signals = response.json()
        print(f"✅ Signals API working")
        print(f"   Total signals: {len(signals)}")
        
        # Count by action
        buy_signals = [s for s in signals if s.get('action') == 'BUY']
        sell_signals = [s for s in signals if s.get('action') == 'SELL']
        print(f"   BUY signals: {len(buy_signals)}")
        print(f"   SELL signals: {len(sell_signals)}")
        
        # Check for MA20_STRICT after 2026-03-27
        ma20_signals = [
            s for s in sell_signals 
            if s.get('exit_reason') == 'MA20_STRICT' 
            and s.get('date', '') >= '2026-03-27'
        ]
        
        if len(ma20_signals) == 0:
            print(f"✅ NO MA20_STRICT signals after v5.3 deploy")
        else:
            print(f"❌ WARNING: {len(ma20_signals)} MA20_STRICT signals found!")
            for sig in ma20_signals[:3]:
                print(f"   - {sig.get('ticker')}: {sig.get('date')}")
        
        # Check for new exit reasons
        exit_reasons = {}
        for sig in sell_signals:
            if sig.get('date', '') >= '2026-03-27':
                reason = sig.get('exit_reason', 'UNKNOWN')
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        if exit_reasons:
            print(f"\n   Exit reasons after v5.3 deploy:")
            for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
                icon = "✅" if reason != "MA20_STRICT" else "❌"
                print(f"   {icon} {reason}: {count}")
        
    else:
        print(f"❌ Signals API failed: {response.status_code}")
except Exception as e:
    print(f"❌ Signals API error: {e}")

# ============================================================================
# TEST 3: MARKET RISK API
# ============================================================================

print("\n[TEST 3] Market Risk API...")

try:
    response = requests.get(f"{BACKEND_URL}/api/market-risk", timeout=10)
    if response.status_code == 200:
        risk_data = response.json()
        print("✅ Market Risk API working")
        if isinstance(risk_data, dict):
            print(f"   Risk level: {risk_data.get('risk_level', 'N/A')}")
            print(f"   Market mode: {risk_data.get('market_mode', 'N/A')}")
    else:
        print(f"❌ Market Risk API failed: {response.status_code}")
except Exception as e:
    print(f"❌ Market Risk API error: {e}")

# ============================================================================
# TEST 4: FRONTEND ACCESSIBILITY
# ============================================================================

print("\n[TEST 4] Frontend Accessibility...")

try:
    response = requests.get(FRONTEND_URL, timeout=10)
    if response.status_code == 200:
        print("✅ Frontend is accessible")
        print(f"   Response size: {len(response.content)} bytes")
        
        # Check for key content
        content = response.text.lower()
        checks = {
            'react': 'react' in content or 'reactdom' in content,
            'signals': 'signal' in content,
            'vn-index': 'vn-index' in content or 'vnindex' in content
        }
        
        for check, passed in checks.items():
            icon = "✅" if passed else "⚠️"
            print(f"   {icon} Contains '{check}': {passed}")
    else:
        print(f"❌ Frontend not accessible: {response.status_code}")
except Exception as e:
    print(f"❌ Frontend error: {e}")

# ============================================================================
# TEST 5: TNG SIGNAL CHECK
# ============================================================================

print("\n[TEST 5] TNG Signal Verification...")

try:
    response = requests.get(f"{BACKEND_URL}/api/signals", timeout=30)
    if response.status_code == 200:
        signals = response.json()
        
        # Find TNG signals
        tng_signals = [s for s in signals if s.get('ticker') == 'TNG']
        
        if tng_signals:
            print(f"✅ Found {len(tng_signals)} TNG signals")
            
            # Check recent TNG SELL
            tng_sells = [
                s for s in tng_signals 
                if s.get('action') == 'SELL'
            ]
            
            if tng_sells:
                latest_sell = max(tng_sells, key=lambda x: x.get('date', ''))
                print(f"\n   Latest TNG SELL:")
                print(f"   Date: {latest_sell.get('date')}")
                print(f"   Exit reason: {latest_sell.get('exit_reason')}")
                print(f"   Price: {latest_sell.get('exit_price'):,}")
                print(f"   P/L: {latest_sell.get('profit_loss_pct'):.2f}%")
                
                if latest_sell.get('exit_reason') == 'MA20_STRICT':
                    if latest_sell.get('date', '') >= '2026-03-27':
                        print(f"   ❌ WARNING: TNG still selling with MA20_STRICT!")
                    else:
                        print(f"   ✅ Old MA20_STRICT signal (before v5.3)")
        else:
            print("⚠️  No TNG signals found")
            
except Exception as e:
    print(f"❌ TNG check error: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("\nIf all tests show ✅, deployment is successful!")
print("\nNext steps:")
print("1. Monitor GitHub Actions runs tomorrow 9:30 AM")
print("2. Verify no MA20_STRICT in new signals")
print("3. Check scanner logs for v5.3 output")
print("4. Manual verify signals on charts")
print("\n" + "="*80)
