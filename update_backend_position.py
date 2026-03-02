#!/usr/bin/env python3
"""
Update backend_api.py to return status and position_pct
"""

import shutil
from datetime import datetime

print("="*70)
print("🔧 UPDATING BACKEND - ADD STATUS & POSITION TO RESPONSES")
print("="*70)

# Backup
backup_name = f"backend_api_BACKUP3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
print(f"\n📦 Creating backup: {backup_name}")
shutil.copy2('backend_api.py', backup_name)
print(f"✅ Backup created")

# Read file
with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update GET /api/signals response to include status and position_pct
old_response = """                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    # Signal code fields - PATCHED
                    'signal_code': s.signal_code,
                    'buy_signal_code': s.buy_signal_code
                })"""

new_response = """                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    # Signal code fields - PATCHED
                    'signal_code': s.signal_code,
                    'buy_signal_code': s.buy_signal_code,
                    # Position tracking fields - PATCHED
                    'status': getattr(s, 'status', 'open'),
                    'position_pct': getattr(s, 'position_pct', 100)
                })"""

if old_response in content:
    content = content.replace(old_response, new_response)
    print("✅ Updated GET /api/signals response")
else:
    print("⚠️  GET response pattern not found - may need manual update")

# Write
with open('backend_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
has_status = "'status': getattr(s, 'status'" in content
has_position = "'position_pct': getattr(s, 'position_pct'" in content

print(f"\n🔍 VERIFICATION:")
print(f"  Has status in response: {has_status}")
print(f"  Has position_pct in response: {has_position}")

if has_status and has_position:
    print(f"\n✅ SUCCESS! Backend updated")
else:
    print(f"\n⚠️  WARNING: Manual check needed")

print(f"\n" + "="*70)
print(f"🎉 BACKEND UPDATE COMPLETED!")
print(f"="*70)
print(f"\nBackup: {backup_name}")
print(f"\nNext:")
print(f"1. Restart backend: python backend_api.py")
print(f"2. Test: GET /api/signals should include status & position_pct")
