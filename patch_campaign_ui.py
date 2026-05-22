#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch campaign popup text. Chạy từ C:\\ai-advisor1\\"""
import os

LAND = os.path.join('frontend', 'src', 'components', 'LandingPage.jsx')
with open(LAND, 'rb') as f: raw = f.read()
enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
text = raw.decode(enc, errors='replace')
ok = 0

def patch(old, new, name):
    global text, ok
    if old in text:
        text = text.replace(old, new, 1)
        print(f'✅ {name}')
        ok += 1
    else:
        print(f'❌ {name}')

# ── 1. Tiêu đề chính (h2) ──
patch(
    "<h2 style={S.title}>Tham gia <em style={{color:'#c9a84c'}}>30 nhà đầu tư</em><br/>đầu tiên — Miễn phí hoàn toàn</h2>",
    "<h2 style={S.title}>Đăng ký dùng thử <em style={{color:'#c9a84c'}}>Basic 15 ngày</em><br/>miễn phí — không cần thẻ</h2>",
    '1. Tiêu đề h2'
)

# ── 2. Mô tả (p sub) ──
patch(
    "AI Advisor mở cửa cho đúng <strong style={{color:'#f7f5f0'}}>30 tài khoản mới</strong>. Không mất tiền — chỉ cần cam kết trải nghiệm và phản hồi thực tế.",
    "Trải nghiệm đầy đủ tính năng Basic trong <strong style={{color:'#f7f5f0'}}>15 ngày đầu tiên</strong>. Sau đó tự động chuyển về Free — không mất phí, không cam kết.",
    '2. Mô tả sub'
)

# ── 3. Urgency bar: "đến 10/4" + "Miễn phí" ──
patch(
    "              <div style={S.urgVal}>đến 10/4</div>\r\n              <div style={S.urgLabel}>Miễn phí</div>",
    "              <div style={S.urgVal}>15 ngày</div>\r\n              <div style={S.urgLabel}>Dùng thử</div>",
    '3. Urgency bar label'
)

# ── Lưu file ──
if ok > 0:
    with open(LAND, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(f'\n✅ Đã lưu ({ok}/3 patches). Chạy: npm run build → git commit → git push origin main')
else:
    print('\n⚠️ Không có gì thay đổi')
