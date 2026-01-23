#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX DATABASE_URL IN BACKEND_API.PY
Automatically adds DATABASE_URL configuration if missing
"""

import re

print("=" * 70)
print("🔧 FIXING backend_api.py - DATABASE_URL")
print("=" * 70)

# Read file
with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if DATABASE_URL already defined
if re.search(r'^DATABASE_URL\s*=', content, re.MULTILINE):
    print("\n✅ DATABASE_URL already defined!")
    print("File is OK, no changes needed.")
    exit(0)

print("\n⚠️  DATABASE_URL not found, adding it...")

# Find the line with "Base = declarative_base()"
pattern = r'(Base = declarative_base\(\))'

# Add DATABASE_URL configuration right after Base
replacement = r'''\1

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)'''

# Check if pattern exists
if not re.search(pattern, content):
    print("\n❌ Could not find 'Base = declarative_base()' in file!")
    print("Please add DATABASE_URL manually.")
    exit(1)

# Replace
new_content = re.sub(pattern, replacement, content)

# Also need to remove the old engine/Session lines if they exist later
# Remove duplicate engine = create_engine lines
new_content = re.sub(r'\nengine = create_engine\(DATABASE_URL\)\nSession = sessionmaker.*?\n', '\n', new_content, count=10)

# Write back
with open('backend_api.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n✅ Successfully added DATABASE_URL configuration!")
print("\n📋 Added lines:")
print("   DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')")
print("   engine = create_engine(DATABASE_URL)")
print("   Session = sessionmaker(bind=engine)")

print("\n" + "=" * 70)
print("✅ FIX COMPLETE!")
print("=" * 70)
print("\nNext steps:")
print("1. git add backend_api.py")
print("2. git commit -m 'Add DATABASE_URL configuration'")
print("3. git push origin main")
print("=" * 70)
