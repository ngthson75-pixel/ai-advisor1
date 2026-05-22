#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tìm và patch TOÀN BỘ text cũ của campaign. Chạy từ C:\\ai-advisor1\\"""
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
        print(f'⏭  {name} (không tìm thấy — đã patch hoặc text khác)')

print('='*55)
print('Patch toàn bộ campaign popup text')
print('='*55)

# ── Badge trên cùng ──
patch('✦ CHIẾN DỊCH BETA · 25/3 — 10/4/2026',
      '✦ DÙNG THỬ MIỄN PHÍ · 15 NGÀY',
      '0. Badge top')

# Thử các variant badge
patch("CHIẾN DỊCH BETA",      "BASIC TRIAL",           '0b. Badge variant')
patch("25/3 — 10/4/2026",     "Không cần thẻ",         '0c. Badge date')
patch("25/3 – 10/4/2026",     "Không cần thẻ",         '0d. Badge date dash')

# ── Tiêu đề h2 ──
patch(
    "<h2 style={S.title}>Tham gia <em style={{color:'#c9a84c'}}>30 nhà đầu tư</em><br/>đầu tiên — Miễn phí hoàn toàn</h2>",
    "<h2 style={S.title}>Dùng thử <em style={{color:'#c9a84c'}}>Basic miễn phí</em><br/>15 ngày — không cần thẻ</h2>",
    '1. Tiêu đề h2'
)

# ── Subtitle ──
patch(
    "AI Advisor mở cửa cho đúng <strong style={{color:'#f7f5f0'}}>30 tài khoản mới</strong>. Không mất tiền — chỉ cần cam kết trải nghiệm và phản hồi thực tế.",
    "Trải nghiệm đầy đủ tính năng Basic trong <strong style={{color:'#f7f5f0'}}>15 ngày đầu tiên</strong>. Sau đó tự chuyển về Free — không mất phí, không cam kết.",
    '2. Subtitle'
)

# ── Urgency bar labels ──
patch("SUẤT CÒN LẠI",         "SUẤT CÒN LẠI",          '3a. (giữ nguyên)')
patch(">71<",                  ">Còn<",                  '3b. số slot')
patch("THỜI GIAN CÒN LẠI",    "ĐĂNG KÝ NGAY",          '3c. countdown label')
patch(">đến 10/4<",            ">15 ngày<",              '3d. urgVal')
patch("đến 10/4</div>",        "15 ngày</div>",          '3e. urgVal alt')
patch(">Miễn phí<",            ">Dùng thử<",             '3f. urgLabel val')
patch("urgLabel}>Miễn phí<",   "urgLabel}>Dùng thử<",   '3g. urgLabel val alt')

# ── Countdown clock — ẩn hoặc đổi thành text tĩnh ──
# Tìm cdRow (clock digits) và thay bằng message đơn giản
patch(
    "{/* Urgency */}\r\n          <div style={S.urgBar}>",
    "{/* Urgency - Updated */}\r\n          <div style={S.urgBar}>",
    '4. urgBar comment'
)

# ── Slots counter "29/30" → "xx/100" ──
patch("slots.taken}/30 suất",   "slots.taken}/100 suất", '5a. slots counter /30')
patch("{slots.taken}/30",        "{slots.taken}/100",      '5b. slots counter alt')

# ── Price row ──
patch(
    "Miễn phí đến<br/><strong>hết 10/4/2026</strong>",
    "Dùng thử 15 ngày<br/><strong>không cần thẻ</strong>",
    '6. Price sub text'
)
patch(
    "Miễn phí đến hết 10/4/2026",
    "Dùng thử 15 ngày — không cần thẻ",
    '6b. Price sub alt'
)
patch(
    ">MIỄN PHÍ<",
    ">MIỄN PHÍ 15 NGÀY<",
    '6c. MIỄN PHÍ label'
)

# ── Form label ──
patch(
    "<div style={S.secLabel}>Đăng ký ngay</div>",
    "<div style={S.secLabel}>Đăng ký dùng thử 15 ngày</div>",
    '7. Form label'
)

# ── Submit button ──
patch(
    "✦ ĐĂNG KÝ THAM GIA NGAY",
    "✦ BẮT ĐẦU DÙNG THỬ MIỄN PHÍ",
    '8. Submit button'
)

# ── Footer sub button ──
patch(
    "suất · Miễn phí · Không cần thẻ ngân hàng",
    "suất · 15 ngày Basic miễn phí · Không cần thẻ",
    '9. Footer sub'
)
patch(
    "suất · Miễn phí · Không cần thẻ ngân hàng",
    "suất · 15 ngày Basic miễn phí · Không cần thẻ",
    '9b. Footer sub alt'
)

# ── Success screen ──
patch(
    "Tài khoản miễn phí đến hết 10/04/2026",
    "Bạn có 15 ngày dùng thử Basic miễn phí 🎉",
    '10. Success screen'
)

# ── Waiting list email ──
patch(
    "Chương trình Beta 30 người đã <strong>đủ suất</strong>",
    "Chương trình Basic Trial đã <strong>đủ 100 suất</strong>",
    '11. Waiting email'
)

# ── Lưu file ──
if ok > 0:
    with open(LAND, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    print(f'\n✅ Đã lưu {LAND} ({ok} patches)')
    print('\nBước tiếp:')
    print('  git add frontend/src/components/LandingPage.jsx')
    print('  git commit -m "ui: campaign popup - basic trial 15 ngay hoan chinh"')
    print('  git push origin main')
else:
    print('\n⚠️ Không có thay đổi nào — file có thể đã được patch trước đó')

# ── Dump nhanh để verify ──
print('\n── Verify text còn lại ──')
with open(LAND, 'r', encoding='utf-8') as f:
    cur = f.read()
for kw in ['Chiến dịch Beta', 'CHIẾN DỊCH BETA', '30 nhà đầu tư', '30 tài khoản mới',
           'đến 10/4', '10/4/2026', 'Tham gia', 'THAM GIA NGAY']:
    found = kw in cur
    print(f'  {"❌ CÒN" if found else "✅ sạch"}: {repr(kw)}')
