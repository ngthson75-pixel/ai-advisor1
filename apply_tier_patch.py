#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Advisor — Patch tier system cho Basic Trial 15 ngày
Chạy từ thư mục gốc: C:\\ai-advisor1\\
  python apply_tier_patch.py
"""
import sys, os

results = {}

def patch(filepath, old, new, name):
    if not os.path.exists(filepath):
        print(f"  ❌ [{name}] Không tìm thấy file: {filepath}")
        results[name] = 'missing'
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ [{name}]")
        results[name] = 'ok'
    else:
        # Thử CRLF
        old_crlf = old.replace('\n', '\r\n')
        if old_crlf in content:
            content = content.replace(old_crlf, new)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ [{name}] (CRLF)")
            results[name] = 'ok'
        else:
            print(f"  ❌ [{name}] Không khớp — thực hiện thủ công (xem hướng dẫn bên dưới)")
            results[name] = 'fail'

print("\n" + "="*60)
print("AI Advisor — Tier System Patch")
print("="*60)

# ════════════════════════════════════════════════════════════
# FILE 1: campaign_api.py
# ════════════════════════════════════════════════════════════
CAMP = 'campaign_api.py'
print(f"\n📄 {CAMP}")

# 1A: Cập nhật constants
patch(CAMP,
    "CAMPAIGN_LIMIT = 15\n"
    "CAMPAIGN_END   = datetime(2026, 5, 15, 23, 59, 59)\n"
    "TRIAL_EXPIRES  = datetime(2026, 4, 30, 23, 59, 59)",
    "CAMPAIGN_LIMIT = 100\n"
    "CAMPAIGN_END   = datetime(2026, 5, 31, 23, 59, 59)\n"
    "TRIAL_DAYS     = 15   # Số ngày dùng thử Basic Trial",
    "1A constants"
)

# 1B: Tạo user mới → tier='basic_trial' thay vì 'free'
patch(CAMP,
    "                            tier='free', is_active=True,\n"
    "                                notes=f'Beta campaign · Free đến 10/4/2026 · {source}',",
    "                            tier='basic_trial', is_active=True,\n"
    "                                notes=f'Basic Trial 15 ngày · Đăng ký {datetime.now().strftime(\"%d/%m/%Y\")} · {source}',",
    "1B new user tier"
)

# 1C: Update user hiện có (existing_vip)
patch(CAMP,
    "                        existing_vip.subscription_expires_at = TRIAL_EXPIRES\n"
    "                        existing_vip.notes = f'Beta campaign · Free đến 10/4/2026 · {source}'",
    "                        existing_vip.tier = 'basic_trial'\n"
    "                        existing_vip.notes = f'Basic Trial 15 ngày · Cập nhật {datetime.now().strftime(\"%d/%m/%Y\")} · {source}'",
    "1C existing user update"
)

# 1D: Telegram message
patch(CAMP,
    '                        f"✅ Free đến 10/4"',
    '                        f"✅ Basic Trial 15 ngày"',
    "1D telegram msg"
)

# 1E: Check campaign end — thay thông báo lỗi cũ
patch(CAMP,
    "if datetime.now() > CAMPAIGN_END:\n"
    "            return jsonify({'success': False, 'error': 'Chương trình Beta đã kết thúc ngày 10/04/2026'}), 410",
    "if datetime.now() > CAMPAIGN_END:\n"
    "            return jsonify({'success': False, 'error': 'Chương trình đăng ký đã kết thúc. Vui lòng liên hệ 0938127666.'}), 410",
    "1E end message"
)

# ════════════════════════════════════════════════════════════
# FILE 2: vip_auth.py — Thêm trial_end_date vào login response
# ════════════════════════════════════════════════════════════
AUTH = 'vip_auth.py'
print(f"\n📄 {AUTH}")

patch(AUTH,
    "            token = _create_jwt(user.id, user.email)\n"
    "            return jsonify({\n"
    "                'success': True,\n"
    "                'token': token,\n"
    "                'user': {\n"
    "                    'id':              user.id,\n"
    "                    'email':           user.email,\n"
    "                    'full_name':       user.full_name,\n"
    "                    'tier':            user.tier,\n"
    "                    'is_push_enabled': user.is_push_enabled,\n"
    "                }\n"
    "            })",
    "            token = _create_jwt(user.id, user.email)\n"
    "            # Tính trial_end_date on-the-fly (không cần cột DB mới)\n"
    "            trial_end = None\n"
    "            if user.tier == 'basic_trial' and user.created_at:\n"
    "                trial_end = (user.created_at + timedelta(days=15)).isoformat()\n"
    "            return jsonify({\n"
    "                'success': True,\n"
    "                'token': token,\n"
    "                'user': {\n"
    "                    'id':              user.id,\n"
    "                    'email':           user.email,\n"
    "                    'full_name':       user.full_name,\n"
    "                    'tier':            user.tier,\n"
    "                    'is_push_enabled': user.is_push_enabled,\n"
    "                    'trial_end_date':  trial_end,\n"
    "                }\n"
    "            })",
    "2A login trial_end_date"
)

# ════════════════════════════════════════════════════════════
# FILE 3: frontend/src/components/LandingPage.jsx
# ════════════════════════════════════════════════════════════
LAND = os.path.join('frontend', 'src', 'components', 'LandingPage.jsx')
print(f"\n📄 {LAND}")

# 3A: handleSubmit — lưu trialEndDate từ API
patch(LAND,
    "      const userData = {\n"
    "        email: data.user.email,\n"
    "        name: data.user.full_name || data.user.email.split('@')[0],\n"
    "        tier: data.user.tier,\n"
    "        isVip: data.user.tier === 'vip',          // App.jsx dùng isVip để route VIPDashboard\n"
    "        token: data.token,\n"
    "        loginTime: new Date().toISOString()\n"
    "      }",
    "      const userData = {\n"
    "        email:         data.user.email,\n"
    "        name:          data.user.full_name || data.user.email.split('@')[0],\n"
    "        tier:          data.user.tier || 'free',\n"
    "        isVip:         data.user.tier === 'vip',\n"
    "        token:         data.token,\n"
    "        loginTime:     new Date().toISOString(),\n"
    "        // trial_end_date từ server → App.jsx dùng để auto-downgrade\n"
    "        trialEndDate:  data.user.trial_end_date || null,\n"
    "      }",
    "3A userData trialEndDate"
)

# 3B: Cập nhật price display trong campaign form
patch(LAND,
    '              <span style={S.priceOrig}>199.000đ/tháng</span>\n'
    '              <span style={{color:\'#c9a84c\',fontSize:11}}>→</span>\n'
    '              <span style={S.priceNew}>MIỄN PHÍ</span>\n'
    '              <div style={S.priceSub}>Miễn phí đến<br/><strong>hết 10/4/2026</strong></div>',
    '              <span style={S.priceOrig}>199.000đ/tháng</span>\n'
    '              <span style={{color:\'#c9a84c\',fontSize:11}}>→</span>\n'
    '              <span style={S.priceNew}>MIỄN PHÍ</span>\n'
    '              <div style={S.priceSub}>Dùng thử 15 ngày<br/><strong>không cần thẻ</strong></div>',
    "3B price display"
)

# 3C: Cập nhật success message steps
patch(LAND,
    "              {['Mở email từ AI Advisor, lấy mật khẩu tạm (kiểm tra cả spam)','Đăng nhập tại ai-advisor.vn/login → đổi mật khẩu','Tài khoản miễn phí đến hết 10/04/2026 🎉'].map((s,i)=>(",
    "              {['Mở email từ AI Advisor, lấy mật khẩu tạm (kiểm tra cả spam)','Đăng nhập tại ai-advisor.vn/login → đổi mật khẩu','Bạn có 15 ngày dùng thử Basic miễn phí 🎉 (sau đó tự chuyển về Free)'].map((s,i)=>(",
    "3C success steps"
)

# 3D: Label "Đăng ký ngay" → "Đăng ký dùng thử 15 ngày"
patch(LAND,
    "            <div style={S.secLabel}>Đăng ký ngay</div>",
    "            <div style={S.secLabel}>Đăng ký dùng thử 15 ngày</div>",
    "3D form label"
)

# 3E: Slot count display "30 suất" → "100 suất"
patch(LAND,
    "<span style={{fontSize:11,fontWeight:700,color:'#ef4444'}}>{slots.taken}/30 suất</span>",
    "<span style={{fontSize:11,fontWeight:700,color:'#ef4444'}}>{slots.taken}/100 suất</span>",
    "3E slot count"
)

# 3F: btnSub text
patch(LAND,
    "            <div style={S.btnSub}>Còn <strong style={{color:'#ef4444'}}>{slots.remaining}</strong> suất · Miễn phí · Không cần thẻ ngân hàng</div>",
    "            <div style={S.btnSub}>Còn <strong style={{color:'#ef4444'}}>{slots.remaining}</strong> suất · 15 ngày dùng thử miễn phí · Không cần thẻ</div>",
    "3F btnSub text"
)

# ════════════════════════════════════════════════════════════
# KẾT QUẢ
# ════════════════════════════════════════════════════════════
ok    = sum(1 for v in results.values() if v == 'ok')
fail  = sum(1 for v in results.values() if v == 'fail')
miss  = sum(1 for v in results.values() if v == 'missing')
total = len(results)

print(f"\n{'='*60}")
print(f"Kết quả: {ok}/{total} patches OK  |  {fail} không khớp  |  {miss} file thiếu")

if fail > 0:
    print("\n⚠️  Các patches thất bại — thực hiện thủ công:")
    for name, status in results.items():
        if status == 'fail':
            print(f"   • {name}")
    print("\nXem DEPLOY_GUIDE_02_05_2026.md để biết nội dung thay thế.")

if ok == total:
    print("\n🎉 Tất cả patches áp dụng thành công!")
    print("Bước tiếp theo:")
    print("  1. git add -A")
    print("  2. git commit -m 'feat: basic_trial 15d tier, free delay 3d'")
    print("  3. Push staging trước, test, rồi cherry-pick main sau 3PM")
