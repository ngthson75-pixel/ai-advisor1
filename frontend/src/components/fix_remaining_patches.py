#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix PATCH 1 và PATCH 4 còn lại cho LandingPage.jsx
Chạy từ: C:\\ai-advisor1\\frontend\\src\\components\\
"""
import sys

FILE = 'LandingPage.jsx'

try:
    with open(FILE, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"❌ Không tìm thấy {FILE}")
    sys.exit(1)

errors = 0

# ── PATCH 1: handleSubmit ────────────────────────────────────────────────
# Dùng repr() để tìm exact bytes nếu cần debug
OLD1 = (
    "  const handleSubmit = (e) => {\n"
    "    e.preventDefault()\n"
    "    \n"
    "    // Mock authentication\n"
    "    const userData = {\n"
    "      email: formData.email,\n"
    "      name: formData.name || formData.email.split('@')[0],\n"
    "      loginTime: new Date().toISOString()\n"
    "    }\n"
    "    \n"
    "    localStorage.setItem('user', JSON.stringify(userData))\n"
    "    onLogin(userData)\n"
    "  }"
)

NEW1 = (
    "  const handleSubmit = (e) => {\n"
    "    e.preventDefault()\n"
    "\n"
    "    if (isLogin) {\n"
    "      // ── ĐĂNG NHẬP ──\n"
    "      const storedRaw = localStorage.getItem('user')\n"
    "      if (!storedRaw) {\n"
    "        alert('Tài khoản không tồn tại. Vui lòng đăng ký trước.')\n"
    "        return\n"
    "      }\n"
    "      try {\n"
    "        const stored = JSON.parse(storedRaw)\n"
    "        if (stored.email !== formData.email) {\n"
    "          alert('Email không đúng hoặc không tìm thấy tài khoản.')\n"
    "          return\n"
    "        }\n"
    "        // Kiểm tra trial hết hạn → tự động downgrade về Free\n"
    "        if (stored.tier === 'basic_trial') {\n"
    "          const end = stored.trialEndDate ? new Date(stored.trialEndDate) : null\n"
    "          if (!end || new Date() > end) {\n"
    "            stored.tier = 'free'\n"
    "            delete stored.trialEndDate\n"
    "            delete stored.trialStartDate\n"
    "            localStorage.setItem('user', JSON.stringify(stored))\n"
    "          }\n"
    "        }\n"
    "        // Migrate khách cũ beta chưa có tier → free\n"
    "        if (!stored.tier && !stored.isVip) {\n"
    "          stored.tier = 'free'\n"
    "          localStorage.setItem('user', JSON.stringify(stored))\n"
    "        }\n"
    "        onLogin(stored)\n"
    "      } catch {\n"
    "        alert('Lỗi đọc dữ liệu. Vui lòng thử lại.')\n"
    "      }\n"
    "    } else {\n"
    "      // ── ĐĂNG KÝ MỚI: Basic Trial 15 ngày ──\n"
    "      const trialStart = new Date()\n"
    "      const trialEnd   = new Date()\n"
    "      trialEnd.setDate(trialEnd.getDate() + 15)\n"
    "\n"
    "      const userData = {\n"
    "        email:          formData.email,\n"
    "        name:           formData.name || formData.email.split('@')[0],\n"
    "        tier:           'basic_trial',\n"
    "        trialStartDate: trialStart.toISOString(),\n"
    "        trialEndDate:   trialEnd.toISOString(),\n"
    "        loginTime:      trialStart.toISOString(),\n"
    "      }\n"
    "      localStorage.setItem('user', JSON.stringify(userData))\n"
    "      onLogin(userData)\n"
    "    }\n"
    "  }"
)

if OLD1 in content:
    content = content.replace(OLD1, NEW1)
    print("✅ PATCH 1: handleSubmit — OK")
else:
    # Thử với CRLF line endings (Windows)
    OLD1_crlf = OLD1.replace('\n', '\r\n')
    if OLD1_crlf in content:
        content = content.replace(OLD1_crlf, NEW1)
        print("✅ PATCH 1: handleSubmit (CRLF) — OK")
    else:
        print("❌ PATCH 1: Không khớp. Chạy debug bên dưới...")
        # Debug: tìm vị trí gần đúng
        idx = content.find("const handleSubmit")
        if idx >= 0:
            snippet = repr(content[idx:idx+300])
            print(f"   Đoạn thực tế:\n   {snippet}")
        errors += 1

# ── PATCH 4: switch text ─────────────────────────────────────────────────
OLD4 = (
    "                  {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}"
)
NEW4 = (
    "                  {isLogin ? 'Dùng thử Basic miễn phí →' : 'Đăng nhập'}"
)

if OLD4 in content:
    content = content.replace(OLD4, NEW4)
    print("✅ PATCH 4: Switch text — OK")
else:
    # Thử indent khác
    variants = [
        "                {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}",
        "              {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}",
        "                  {isLogin ? 'Đăng k\u00fd ngay' : '\u0110\u0103ng nh\u1eadp'}",
    ]
    replaced = False
    for v in variants:
        if v in content:
            new_v = v.replace("Đăng ký ngay", "Dùng thử Basic miễn phí →")
            content = content.replace(v, new_v)
            print(f"✅ PATCH 4: Switch text (variant indent) — OK")
            replaced = True
            break
    if not replaced:
        print("❌ PATCH 4: Không khớp. Debug:")
        idx = content.find("Đăng ký ngay")
        if idx >= 0:
            snippet = repr(content[max(0,idx-30):idx+60])
            print(f"   Đoạn thực tế: {snippet}")
        errors += 1

# ── GHI FILE ─────────────────────────────────────────────────────────────
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

if errors == 0:
    print(f"\n🎉 Tất cả patches hoàn thành. {FILE} đã được lưu.")
else:
    print(f"\n⚠️ {errors} patch cần xử lý thủ công. Xem debug output bên trên.")
    print("Hướng dẫn thủ công:")
    if errors >= 1:
        print("\nPATCH 1 — Trong LandingPage.jsx, tìm hàm handleSubmit và thay toàn bộ thân hàm")
        print("bằng nội dung trong file DEPLOY_GUIDE_02_05_2026.md mục 3.1")
    print("\nPATCH 4 — Tìm dòng có 'Đăng ký ngay' trong phần auth-switch, đổi thành:")
    print("          {isLogin ? 'Dùng thử Basic miễn phí →' : 'Đăng nhập'}")
