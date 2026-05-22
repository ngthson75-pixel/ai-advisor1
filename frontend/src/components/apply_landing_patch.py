#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tự động patch LandingPage.jsx:
  - handleSubmit: thêm trial logic 15 ngày
  - Register form: cập nhật text UI
Chạy từ thư mục src/components/:  python apply_landing_patch.py
"""

import re, sys

FILE = 'LandingPage.jsx'

try:
    with open(FILE, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"❌ Không tìm thấy {FILE}. Chạy script từ thư mục chứa LandingPage.jsx")
    sys.exit(1)

errors = 0

# ════════════════════════════════════════════════════════════════
# PATCH 1: handleSubmit — thêm trial 15 ngày khi đăng ký
# ════════════════════════════════════════════════════════════════
OLD_SUBMIT = '''  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Mock authentication
    const userData = {
      email: formData.email,
      name: formData.name || formData.email.split('@')[0],
      loginTime: new Date().toISOString()
    }
    
    localStorage.setItem('user', JSON.stringify(userData))
    onLogin(userData)
  }'''

NEW_SUBMIT = '''  const handleSubmit = (e) => {
    e.preventDefault()

    if (isLogin) {
      // ── ĐĂNG NHẬP ──
      const storedRaw = localStorage.getItem('user')
      if (!storedRaw) {
        alert('Tài khoản không tồn tại. Vui lòng đăng ký trước.')
        return
      }
      try {
        const stored = JSON.parse(storedRaw)
        if (stored.email !== formData.email) {
          alert('Email không đúng hoặc không tìm thấy tài khoản.')
          return
        }
        // Kiểm tra trial hết hạn → tự động downgrade về Free
        if (stored.tier === 'basic_trial') {
          const end = stored.trialEndDate ? new Date(stored.trialEndDate) : null
          if (!end || new Date() > end) {
            stored.tier = 'free'
            delete stored.trialEndDate
            delete stored.trialStartDate
            localStorage.setItem('user', JSON.stringify(stored))
          }
        }
        // Migrate khách cũ (beta) chưa có tier → free
        if (!stored.tier && !stored.isVip) {
          stored.tier = 'free'
          localStorage.setItem('user', JSON.stringify(stored))
        }
        onLogin(stored)
      } catch {
        alert('Lỗi đọc dữ liệu. Vui lòng thử lại.')
      }
    } else {
      // ── ĐĂNG KÝ MỚI: Basic Trial 15 ngày ──
      const trialStart = new Date()
      const trialEnd   = new Date()
      trialEnd.setDate(trialEnd.getDate() + 15)

      const userData = {
        email:          formData.email,
        name:           formData.name || formData.email.split(\'@\')[0],
        tier:           'basic_trial',
        trialStartDate: trialStart.toISOString(),
        trialEndDate:   trialEnd.toISOString(),
        loginTime:      trialStart.toISOString(),
      }

      localStorage.setItem('user', JSON.stringify(userData))
      onLogin(userData)
    }
  }'''

if OLD_SUBMIT in content:
    content = content.replace(OLD_SUBMIT, NEW_SUBMIT)
    print("✅ PATCH 1: handleSubmit — OK")
else:
    print("❌ PATCH 1: Không tìm thấy handleSubmit cũ. Thực hiện thủ công.")
    errors += 1

# ════════════════════════════════════════════════════════════════
# PATCH 2: Auth modal header — subtitle & trial info box
# ════════════════════════════════════════════════════════════════
OLD_HEADER = '''              <h2>{isLogin ? 'Đăng nhập' : 'Đăng ký'}</h2>
              <p style={{color:"#64748b",fontSize:"13px",marginTop:"4px"}}>Đầu tư thông minh với AI</p>'''

NEW_HEADER = '''              <h2>{isLogin ? 'Đăng nhập' : 'Dùng thử Basic miễn phí'}</h2>
              <p style={{color:"#64748b",fontSize:"13px",marginTop:"4px"}}>
                {isLogin ? 'Đầu tư thông minh với AI' : '15 ngày trải nghiệm đầy đủ — không cần thẻ'}
              </p>
              {!isLogin && (
                <div style={{
                  margin:'10px 0 0',
                  padding:'8px 14px',
                  background:'linear-gradient(90deg,#0a1628,#0d1f3a)',
                  border:'1px solid #00d4aa44',
                  borderRadius:'8px',
                  fontSize:'12px',
                  color:'#94a3b8',
                  lineHeight:'1.7',
                }}>
                  ✅ Tín hiệu mua/bán real-time &nbsp;•&nbsp; ✅ AI Coach<br/>
                  ✅ Bản tin hàng ngày &nbsp;•&nbsp; ✅ Analytics đầy đủ<br/>
                  <span style={{color:'#f59e0b',fontWeight:600}}>
                    ⏰ Sau 15 ngày tự động chuyển về Free (tín hiệu delay 3 ngày)
                  </span>
                </div>
              )}'''

if OLD_HEADER in content:
    content = content.replace(OLD_HEADER, NEW_HEADER)
    print("✅ PATCH 2: Auth header — OK")
else:
    print("❌ PATCH 2: Không tìm thấy auth header cũ. Thực hiện thủ công.")
    errors += 1

# ════════════════════════════════════════════════════════════════
# PATCH 3: Submit button text
# ════════════════════════════════════════════════════════════════
OLD_BTN = "              <button type=\"submit\" className=\"btn-submit\">\n                {isLogin ? 'Đăng nhập' : 'Tạo tài khoản'}\n              </button>"
NEW_BTN = "              <button type=\"submit\" className=\"btn-submit\">\n                {isLogin ? 'Đăng nhập' : '🚀 Bắt đầu dùng thử 15 ngày miễn phí'}\n              </button>"

if OLD_BTN in content:
    content = content.replace(OLD_BTN, NEW_BTN)
    print("✅ PATCH 3: Submit button — OK")
else:
    print("❌ PATCH 3: Không tìm thấy button cũ. Thực hiện thủ công.")
    errors += 1

# ════════════════════════════════════════════════════════════════
# PATCH 4: Switch link text
# ════════════════════════════════════════════════════════════════
OLD_SWITCH = "                {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}"
NEW_SWITCH = "                {isLogin ? 'Dùng thử Basic miễn phí →' : 'Đăng nhập'}"

if OLD_SWITCH in content:
    content = content.replace(OLD_SWITCH, NEW_SWITCH)
    print("✅ PATCH 4: Switch text — OK")
else:
    print("❌ PATCH 4: Không tìm thấy switch text. Thực hiện thủ công.")
    errors += 1

# ════════════════════════════════════════════════════════════════
# GHI FILE
# ════════════════════════════════════════════════════════════════
if errors == 0:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n🎉 Tất cả 4 patches áp dụng thành công vào {FILE}")
elif errors < 4:
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n⚠️ {4-errors}/4 patches OK, {errors} cần thực hiện thủ công. File đã được lưu.")
else:
    print(f"\n❌ Không có patch nào được áp dụng. Kiểm tra lại file encoding hoặc thực hiện thủ công.")
