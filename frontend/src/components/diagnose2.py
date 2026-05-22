#!/usr/bin/env python3
# -*- coding: utf-8 -*-
FILE = 'LandingPage.jsx'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')

# Tìm campaign submit handler
keywords = ['handleCampaign', 'handleRegister', 'submitCamp', 'onSubmit',
            'showCampaign', 'setShowCampaign', 'campaign_api', '/api/campaign',
            '/api/register', 'register', 'Register']

print("=" * 60)
print("Tìm campaign/register handlers:")
print("=" * 60)
for i, line in enumerate(lines):
    for kw in keywords:
        if kw in line and 'import' not in line:
            print(f"  {i+1:4d}: {line.rstrip()}")
            break

print()
print("=" * 60)
print("Đoạn 1580–1650 (phần cuối campaign form):")
print("=" * 60)
for j in range(1579, min(1650, len(lines))):
    print(f"  {j+1:4d}: {lines[j].rstrip()}")
