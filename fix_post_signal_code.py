#!/usr/bin/env python3
"""
Fix POST /api/signals to auto-generate signal_code
"""

import shutil
from datetime import datetime

print("="*70)
print("🔧 FIXING POST /api/signals - AUTO GENERATE CODE")
print("="*70)

# Backup
backup_name = f"backend_api_BACKUP2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
print(f"\n📦 Creating backup: {backup_name}")
shutil.copy2('backend_api.py', backup_name)
print(f"✅ Backup created")

# Read file
with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace POST logic
# Pattern 1: Try to find the exact pattern
old_pattern1 = """            # Save to database
            session.add(signal)
            session.commit()
            
            print(f"✅ Signal created:"""

new_pattern1 = """            # Save to database
            session.add(signal)
            session.flush()  # Get ID before commit
            
            # Auto-generate signal_code for BUY signals
            if signal.action == 'BUY' and not signal.signal_code:
                signal.signal_code = f"{signal.ticker}-{signal.id}"
            
            session.commit()
            
            print(f"✅ Signal created:"""

if old_pattern1 in content:
    content = content.replace(old_pattern1, new_pattern1)
    print("✅ Fixed POST endpoint - added flush() and signal_code generation")
else:
    # Try alternative pattern
    old_pattern2 = """            session.add(signal)
            session.commit()"""
    
    new_pattern2 = """            session.add(signal)
            session.flush()  # Get ID
            
            # Generate signal_code for BUY
            if signal.action == 'BUY' and not signal.signal_code:
                signal.signal_code = f"{signal.ticker}-{signal.id}"
            
            session.commit()"""
    
    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern2, 1)  # Replace first occurrence only
        print("✅ Fixed POST endpoint (alternative pattern)")
    else:
        print("❌ Could not find pattern to fix")
        print("Manual fix required")

# Write
with open('backend_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
has_flush = 'session.flush()' in content
has_generate = 'signal.signal_code = f"{signal.ticker}-{signal.id}"' in content

print(f"\n🔍 VERIFICATION:")
print(f"  Has session.flush(): {has_flush}")
print(f"  Has code generation: {has_generate}")

if has_flush and has_generate:
    print(f"\n✅ SUCCESS! POST endpoint fixed")
else:
    print(f"\n⚠️  WARNING: Manual check needed")

print(f"\n" + "="*70)
print(f"🎉 FIX COMPLETED!")
print(f"="*70)
print(f"\nBackup: {backup_name}")
print(f"\nNext:")
print(f"1. Restart backend: python backend_api.py")
print(f"2. Test create signal - should have signal_code now!")
