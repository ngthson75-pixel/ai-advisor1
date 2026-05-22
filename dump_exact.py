#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump exact content quanh mỗi target để debug patches. Chạy từ C:\\ai-advisor1\\"""
import os

def dump(filepath, keywords, chars=300):
    if not os.path.exists(filepath):
        print(f"  FILE MISSING: {filepath}"); return
    with open(filepath, 'rb') as f:
        raw = f.read()
    # Detect encoding
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    text = raw.decode(enc, errors='replace')
    for kw in keywords:
        idx = text.find(kw)
        if idx < 0:
            print(f"  NOT FOUND: {repr(kw[:40])}")
        else:
            snippet = text[max(0,idx-20):idx+chars]
            print(f"  FOUND '{kw[:30]}':")
            print(repr(snippet))
        print()

print("="*60)
print("campaign_api.py")
print("="*60)
dump('campaign_api.py', [
    'CAMPAIGN_LIMIT',
    "tier='free', is_active=True",
    'Beta campaign',
    'Free đến 10/4',
    'Chương trình Beta',
])

print("="*60)
print("vip_auth.py")
print("="*60)
dump('vip_auth.py', [
    '_create_jwt(user.id',
    'is_push_enabled',
])

print("="*60)
print("LandingPage.jsx")
print("="*60)
dump(os.path.join('frontend','src','components','LandingPage.jsx'), [
    'data.user.tier',
    'priceOrig',
    'Mở email từ AI Advisor',
    'secLabel}',
    'slots.taken',
    'btnSub',
])
