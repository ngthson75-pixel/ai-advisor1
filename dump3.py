#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

out = open('dump3.txt', 'w', encoding='utf-8')
def w(s=''): out.write(str(s)+'\n')

def ctx(filepath, keyword, before=60, after=300):
    with open(filepath, 'rb') as f: raw = f.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    text = raw.decode(enc, errors='replace')
    idx = text.find(keyword)
    if idx < 0:
        w(f'NOT FOUND: {repr(keyword[:50])}')
    else:
        w(f'FOUND [{keyword[:40]}]:')
        w(repr(text[max(0,idx-before):idx+after]))
    w()

CAMP = 'campaign_api.py'
LAND = os.path.join('frontend','src','components','LandingPage.jsx')

w('='*60 + ' campaign_api.py')

# 1B: tìm đoạn register tạo user mới
w('--- 1B/1C: register new user ---')
ctx(CAMP, 'campaign_register', 0, 200)  # Tìm function name

# Tìm tier gần VIPUser
w('--- tier near VIPUser ---')
ctx(CAMP, 'VIPUser(', 0, 400)

w('--- all tier= occurrences ---')
with open(CAMP, 'rb') as f: raw = f.read()
text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')
for i, line in enumerate(lines):
    if "tier=" in line and 'is_active' in line:
        start = max(0, i-2)
        end = min(len(lines), i+4)
        for j in range(start, end):
            w(f"  {j+1:4d}: {repr(lines[j])}")
        w()

w('--- 1D: telegram msg near Free ---')
ctx(CAMP, 'Free đến 10/4', 0, 200)

w('='*60 + ' LandingPage.jsx')

w('--- 3D: secLabel Đăng ký ---')
ctx(LAND, 'secLabel}>Đ', 0, 100)

w('--- 3F: btnSub actual text ---')
ctx(LAND, 'btnSub}>', 0, 200)

out.close()
print('Done → dump3.txt')
