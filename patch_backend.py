#!/usr/bin/env python3
"""
Patch backend_api.py to add signal_code columns
"""

import os
import shutil
from datetime import datetime

print("="*70)
print("🔧 PATCHING backend_api.py - ADD SIGNAL_CODE")
print("="*70)

# Backup
backup_name = f"backend_api_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
print(f"\n📦 Creating backup: {backup_name}")
shutil.copy2('backend_api.py', backup_name)
print(f"✅ Backup created")

# Read file
print(f"\n📖 Reading backend_api.py...")
with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# PATCH 1: Add signal_code columns to Signal model
old_model = """    action = Column(String(10), default='BUY')
    created_at = Column(DateTime, default=datetime.now)


class Portfolio(Base):"""

new_model = """    action = Column(String(10), default='BUY')
    created_at = Column(DateTime, default=datetime.now)
    
    # Signal code tracking (Hybrid FIFO) - PATCHED
    signal_code = Column(String(50), unique=True)  # e.g., VCB-1001
    buy_signal_code = Column(String(50))  # For SELL signals to link to BUY


class Portfolio(Base):"""

if old_model in content:
    content = content.replace(old_model, new_model)
    print("✅ PATCH 1: Added signal_code columns to Signal model")
else:
    print("⚠️  PATCH 1: Pattern not found (may already be patched)")

# PATCH 2: Add signal_code to GET response
old_response = """                    'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                    'action': s.action,
                    'created_at': s.created_at.isoformat() if s.created_at else None
                })"""

new_response = """                    'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                    'action': s.action,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    # Signal code fields - PATCHED
                    'signal_code': s.signal_code,
                    'buy_signal_code': s.buy_signal_code
                })"""

if old_response in content:
    content = content.replace(old_response, new_response)
    print("✅ PATCH 2: Added signal_code to GET response")
else:
    print("⚠️  PATCH 2: Pattern not found (may already be patched)")

# PATCH 3: Add signal_code generation in POST
old_post = """            # Save to database
            session.add(signal)
            session.commit()
            
            print(f"✅ Signal created: {signal.ticker} ({signal.strategy}) - {signal.date}")"""

new_post = """            # Save to database
            session.add(signal)
            session.flush()  # Get ID without committing
            
            # Generate signal code for BUY signals - PATCHED
            if signal.action == 'BUY':
                signal.signal_code = f"{signal.ticker}-{signal.id}"
            
            session.commit()
            
            print(f"✅ Signal created: {signal.signal_code or signal.id} ({signal.ticker} - {signal.strategy}) - {signal.date}")"""

if old_post in content:
    content = content.replace(old_post, new_post)
    print("✅ PATCH 3: Added signal_code generation in POST")
else:
    print("⚠️  PATCH 3: Pattern not found (may already be patched)")

# PATCH 4: Add signal_code to POST response
old_post_response = """            return jsonify({
                'success': True,
                'id': signal.id,
                'ticker': signal.ticker,
                'message': 'Signal created successfully'
            }), 201"""

new_post_response = """            return jsonify({
                'success': True,
                'id': signal.id,
                'signal_code': signal.signal_code,  # PATCHED
                'ticker': signal.ticker,
                'message': 'Signal created successfully'
            }), 201"""

if old_post_response in content:
    content = content.replace(old_post_response, new_post_response)
    print("✅ PATCH 4: Added signal_code to POST response")
else:
    print("⚠️  PATCH 4: Pattern not found (may already be patched)")

# Write patched file
print(f"\n💾 Writing patched backend_api.py...")
with open('backend_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ File patched successfully!")

# Verify
print(f"\n🔍 VERIFICATION")
print("="*70)

with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
has_signal_code = 'signal_code = Column(String(50)' in content
has_buy_signal_code = 'buy_signal_code = Column(String(50)' in content

print(f"Signal model has signal_code: {has_signal_code}")
print(f"Signal model has buy_signal_code: {has_buy_signal_code}")

if has_signal_code and has_buy_signal_code:
    print(f"\n✅ SUCCESS! Signal model patched correctly!")
else:
    print(f"\n❌ WARNING: Patch may not be complete")

print(f"\n" + "="*70)
print(f"🎉 PATCHING COMPLETED!")
print(f"="*70)
print(f"\nBackup saved: {backup_name}")
print(f"Next steps:")
print(f"1. Stop backend (Ctrl+C)")
print(f"2. Start backend: python backend_api.py")
print(f"3. Test: Invoke-WebRequest http://localhost:10000/api/signals")
