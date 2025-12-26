#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UPLOAD SIGNALS TO BACKEND
Upload daily scanner results to backend API on Render
"""

import requests
import json
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Backend API URL
BACKEND_URL = "https://ai-advisor1-backend.onrender.com"  # Your Render URL

# Local signals file
SIGNALS_FILE = "signals/signals_latest.json"

print("="*70)
print("UPLOAD SIGNALS TO BACKEND")
print("="*70)
print(f"Backend: {BACKEND_URL}")
print(f"File: {SIGNALS_FILE}")
print()

# ============================================================================
# LOAD SIGNALS
# ============================================================================

def load_signals():
    """Load signals from local file"""
    try:
        with open(SIGNALS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded signals:")
        print(f"   PULLBACK: {len(data.get('pullback', []))}")
        print(f"   EMA_CROSS: {len(data.get('ema_cross', []))}")
        
        return data
    
    except FileNotFoundError:
        print(f"❌ File not found: {SIGNALS_FILE}")
        print("Run scanner first: python run_daily_scanner.py")
        return None
    
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None

# ============================================================================
# UPLOAD TO BACKEND
# ============================================================================

def upload_signals(signals):
    """Upload signals to backend API"""
    
    try:
        # Add metadata if not present
        if 'metadata' not in signals:
            signals['metadata'] = {
                'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'uploaded_at': datetime.now().isoformat()
            }
        
        # Upload endpoint
        url = f"{BACKEND_URL}/api/admin/signals/bulk"
        
        # Add clear_old flag to archive previous signals
        payload = {
            **signals,
            'clear_old': True  # Archive old signals
        }
        
        print(f"\nUploading to {url}...")
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ Upload successful!")
                print(f"   Added: {result.get('added_count')} signals")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ Upload failed:")
                print(f"   Error: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error!")
        print(f"   Cannot connect to {BACKEND_URL}")
        print(f"   Check if backend is running on Render")
        return False
    
    except requests.exceptions.Timeout:
        print(f"❌ Timeout!")
        print(f"   Backend took too long to respond")
        return False
    
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# VERIFY UPLOAD
# ============================================================================

def verify_upload():
    """Verify signals were uploaded correctly"""
    
    try:
        print(f"\nVerifying upload...")
        
        url = f"{BACKEND_URL}/api/signals/summary"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                summary = result['summary']
                
                print(f"✅ Backend verification:")
                print(f"   Total signals: {summary['total_signals']}")
                print(f"   PULLBACK: {summary['by_strategy'].get('PULLBACK', 0)}")
                print(f"   EMA_CROSS: {summary['by_strategy'].get('EMA_CROSS', 0)}")
                print(f"   Blue Chips: {summary['by_type'].get('Blue Chip', 0)}")
                print(f"   Mid Caps: {summary['by_type'].get('Mid Cap', 0)}")
                print(f"   Penny: {summary['by_type'].get('Penny', 0)}")
                
                return True
        
        print(f"⚠️ Could not verify")
        return False
    
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        return False

# ============================================================================
# TEST BACKEND
# ============================================================================

def test_backend():
    """Test if backend is accessible"""
    
    print("Testing backend connectivity...")
    
    try:
        url = f"{BACKEND_URL}/health"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is online")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            return True
        else:
            print(f"⚠️ Backend returned: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend")
        print(f"   URL: {BACKEND_URL}")
        print(f"   Check if deployed on Render")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main upload function"""
    
    # Test backend
    if not test_backend():
        print("\n❌ Backend not accessible!")
        print("Deploy backend first or check Render status")
        return 1
    
    print()
    
    # Load signals
    signals = load_signals()
    if not signals:
        return 1
    
    # Upload
    success = upload_signals(signals)
    
    if success:
        # Verify
        verify_upload()
        
        print("\n" + "="*70)
        print("✅ UPLOAD COMPLETE!")
        print("="*70)
        print(f"Admin Panel: {BACKEND_URL}/admin")
        print(f"API Docs: {BACKEND_URL}/")
        print("="*70)
        
        return 0
    else:
        print("\n" + "="*70)
        print("❌ UPLOAD FAILED!")
        print("="*70)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
