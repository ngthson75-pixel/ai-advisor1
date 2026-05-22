#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
out = open('dump4.txt', 'w', encoding='utf-8')
def w(s=''): out.write(str(s)+'\n')

LAND = os.path.join('frontend','src','components','LandingPage.jsx')
with open(LAND, 'rb') as f: raw = f.read()
enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
text = raw.decode(enc, errors='replace')

# Dump các đoạn header của campaign popup
targets = [
    'CHIẾN DỊCH BETA',
    'Tham gia',
    '30 nhà đầu tư',
    'Miễn phí hoàn toàn',
    'AI Advisor mở cửa',
    '30 tài khoản mới',
    'đến 10/4',
    'SUẤT CÒN LẠI',
    'THỜI GIAN CÒN LẠI',
    'urgLabel',
    'hdrTitle',
    'hdrSub',
    'headerBadge',
]
for kw in targets:
    idx = text.find(kw)
    if idx < 0:
        w(f'NOT FOUND: {repr(kw)}')
    else:
        w(f'FOUND [{kw}]:')
        w(repr(text[max(0,idx-40):idx+200]))
    w()

out.close()
print('Done → dump4.txt')
