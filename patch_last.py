#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch 2 chỗ còn lại trong campaign_api.py (lines 443 và 518)
Chạy từ C:\\ai-advisor1\\
"""
import os

FILE = 'campaign_api.py'
with open(FILE, 'rb') as f:
    raw = f.read()
enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
text = raw.decode(enc, errors='replace')
original = text

# ── Patch A: line ~443 — open-slots waiting list activation ──
OLD_A = (
    "                        tier='free', is_active=True,\r\n"
    "                        notes=f'Basic Trial 15 ngày · Mở từ waiting list"
)
NEW_A = (
    "                        tier='basic_trial', is_active=True,\r\n"
    "                        notes=f'Basic Trial 15 ngày · Mở từ waiting list"
)

# ── Patch B: line ~518 — auto-fill slot ──
OLD_B = (
    "                        tier='free', is_active=True,\r\n"
    "                        notes='Beta campaign (auto-fill) · Free đến 10/4/2026',"
)
NEW_B = (
    "                        tier='basic_trial', is_active=True,\r\n"
    "                        notes=f'Basic Trial 15 ngày · Auto-fill · {__import__(\"datetime\").datetime.now().strftime(\"%d/%m/%Y\")}',"
)

ok = 0
if OLD_A in text:
    text = text.replace(OLD_A, NEW_A, 1)
    print("✅ Patch A (line ~443 open-slots waiting list): OK")
    ok += 1
else:
    print("❌ Patch A: không khớp")

if OLD_B in text:
    text = text.replace(OLD_B, NEW_B, 1)
    print("✅ Patch B (line ~518 auto-fill): OK")
    ok += 1
else:
    print("❌ Patch B: không khớp")

if ok > 0:
    with open(FILE, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(f"\n✅ Đã lưu {FILE} ({ok}/2 patches)")
else:
    print("\n⚠️  Không có thay đổi nào được ghi")

# ── Kiểm tra tổng kết tất cả tier= trong file ──
print("\n── Tất cả tier= trong file hiện tại ──")
lines = text.split('\n')
for i, line in enumerate(lines):
    if "tier=" in line and ("'free'" in line or "'basic_trial'" in line or "'vip'" in line):
        print(f"  {i+1:4d}: {line.rstrip()}")

print("\n── Kết quả mong đợi ──")
print("  Không còn dòng nào có tier='free' trong phần tạo VIPUser mới")
print("  Tất cả register/activate đều dùng tier='basic_trial'")
