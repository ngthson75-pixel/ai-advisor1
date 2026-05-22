#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Đọc LandingPage.jsx thực tế và dump các đoạn cần patch.
Chạy từ: C:\\ai-advisor1\\frontend\\src\\components\\
"""
import re

FILE = 'LandingPage.jsx'
with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# ── Dump handleSubmit (tìm từ dòng khai báo đến closing brace) ──
print("=" * 60)
print("ĐOẠN 1: handleSubmit function")
print("=" * 60)
start = None
for i, line in enumerate(lines):
    if 'handleSubmit' in line and ('const' in line or 'function' in line):
        start = i
        break

if start is not None:
    # In 80 dòng từ đó
    chunk = '\n'.join(lines[start:start+80])
    print(chunk)
else:
    print("Không tìm thấy handleSubmit")

print()
print("=" * 60)
print("ĐOẠN 2: Xung quanh 'Đăng ký ngay' (+/- 10 dòng)")
print("=" * 60)
for i, line in enumerate(lines):
    if 'Đăng ký ngay' in line or 'secLabel' in line:
        ctx_start = max(0, i-10)
        ctx_end   = min(len(lines), i+15)
        for j in range(ctx_start, ctx_end):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1:4d}: {lines[j]}")
        print()

print("=" * 60)
print("ĐOẠN 3: Phần isLogin switch (tìm 'isLogin' gần cuối form)")
print("=" * 60)
# Tìm auth-switch hoặc isLogin toggle gần cuối form
for i, line in enumerate(lines):
    if 'auth-switch' in line or ('isLogin' in line and 'setIsLogin' in line):
        ctx_start = max(0, i-3)
        ctx_end   = min(len(lines), i+12)
        for j in range(ctx_start, ctx_end):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1:4d}: {lines[j]}")
        print()
