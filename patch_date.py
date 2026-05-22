#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

LAND = os.path.join('frontend', 'src', 'components', 'LandingPage.jsx')
with open(LAND, 'rb') as f: raw = f.read()
enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
text = raw.decode(enc, errors='replace')
ok = 0

def p(old, new, name):
    global text, ok
    if old in text:
        text = text.replace(old, new)
        print(f'✅ {name}')
        ok += 1
    else:
        print(f'⏭  {name}')

p('10/4/2026', '15 ngày', 'Xóa 10/4/2026')

if ok > 0:
    with open(LAND, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print('\nDone. Chạy:')
    print('  git add frontend/src/components/LandingPage.jsx')
    print('  git commit -m "ui: remove 10/4/2026"')
    print('  git push origin main')
else:
    print('Không tìm thấy — đã sạch rồi')
