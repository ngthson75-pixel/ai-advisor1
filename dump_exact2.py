#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys

OUT = 'dump_output.txt'
out = open(OUT, 'w', encoding='utf-8')

def w(s=''):
    out.write(str(s) + '\n')

def dump(filepath, keywords, chars=400):
    if not os.path.exists(filepath):
        w(f'  FILE MISSING: {filepath}'); return
    with open(filepath, 'rb') as f:
        raw = f.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    text = raw.decode(enc, errors='replace')
    for kw in keywords:
        idx = text.find(kw)
        if idx < 0:
            w(f'  NOT FOUND: {repr(kw[:50])}')
        else:
            snippet = text[max(0,idx-30):idx+chars]
            w(f'  FOUND [{kw[:40]}]:')
            w(repr(snippet))
        w()

w('='*60)
w('campaign_api.py')
w('='*60)
dump('campaign_api.py', [
    'CAMPAIGN_LIMIT',
    "tier='free'",
    'Beta campaign',
    'Free',
    'Chương trình Beta',
])

w('='*60)
w('vip_auth.py')
w('='*60)
dump('vip_auth.py', [
    '_create_jwt(user.id',
    'is_push_enabled',
])

w('='*60)
w('LandingPage.jsx')
w('='*60)
dump(os.path.join('frontend','src','components','LandingPage.jsx'), [
    'data.user.tier',
    'priceOrig',
    'secLabel}',
    'slots.taken',
    'btnSub',
    'Mở email',
])

out.close()
print(f'Done. Mo file: {OUT}')
