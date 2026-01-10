#!/usr/bin/env python3
"""
BACKEND API TEST SCRIPT
Test và verify tất cả API endpoints hoạt động đúng
"""

import requests
import json

API_BASE = "https://ai-advisor1-backend.onrender.com"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: HEALTH CHECK")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signals():
    """Test signals endpoint"""
    print("\n" + "="*70)
    print("TEST 2: GET SIGNALS")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE}/api/signals", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Signals count: {len(data.get('signals', []))}")
        
        if data.get('signals'):
            print(f"\nFirst signal: {json.dumps(data['signals'][0], indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_portfolio_get():
    """Test GET portfolio"""
    print("\n" + "="*70)
    print("TEST 3: GET PORTFOLIO")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE}/api/portfolio?user_id=1", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_portfolio_add():
    """Test POST portfolio"""
    print("\n" + "="*70)
    print("TEST 4: ADD STOCK TO PORTFOLIO")
    print("="*70)
    
    try:
        payload = {
            "user_id": 1,
            "ticker": "VCB",
            "quantity": 100,
            "price": 85000
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE}/api/portfolio",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat():
    """Test chat endpoint"""
    print("\n" + "="*70)
    print("TEST 5: CHAT WITH AI")
    print("="*70)
    
    try:
        payload = {
            "user_id": 1,
            "message": "Phân tích danh mục của tôi"
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # AI response takes longer
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200 and data.get('success')
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_migrate():
    """Test migration endpoint"""
    print("\n" + "="*70)
    print("TEST 6: RUN MIGRATION")
    print("="*70)
    
    try:
        response = requests.post(f"{API_BASE}/api/migrate", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "🔧 BACKEND API TESTING SCRIPT")
    print("Testing: " + API_BASE)
    
    results = {
        "Health Check": test_health(),
        "Get Signals": test_signals(),
        "Get Portfolio": test_portfolio_get(),
        "Add Stock": test_portfolio_add(),
        "Chat AI": test_chat(),
        "Migration": test_migrate()
    }
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    
    if passed < total:
        print("\n⚠️  SOME ENDPOINTS FAILED!")
        print("Backend may need fixes or is not fully deployed.")
        print("\nPossible issues:")
        print("- Database tables not created (run migration)")
        print("- Backend not deployed properly")
        print("- Missing environment variables (GEMINI_API_KEY)")
        print("- Endpoints not implemented yet")
