#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final patch — dùng exact CRLF content từ dump_output.txt
Chạy từ C:\\ai-advisor1\\
"""
import os, sys

LOG = open('patch_final_log.txt', 'w', encoding='utf-8')
results = {}

def w(s=''):
    LOG.write(str(s) + '\n')
    print(s)

def patch(filepath, old, new, name):
    if not os.path.exists(filepath):
        w(f'  ❌ [{name}] File không tồn tại: {filepath}')
        results[name] = 'missing'; return
    with open(filepath, 'rb') as f:
        raw = f.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    text = raw.decode(enc, errors='replace')

    if old in text:
        text = text.replace(old, new, 1)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        w(f'  ✅ [{name}]')
        results[name] = 'ok'
    else:
        w(f'  ❌ [{name}] Không khớp')
        results[name] = 'fail'

CAMP = 'campaign_api.py'
AUTH = 'vip_auth.py'
LAND = os.path.join('frontend', 'src', 'components', 'LandingPage.jsx')

w('\n' + '='*60)
w('campaign_api.py')
w('='*60)

# ── Tìm tier='basic_trial' trong code register (không phải comment) ──
# Dựa trên dump: "notes='Beta campaign · Free đến 10/4/2026'"
# Cần xem thêm đoạn register — tìm trực tiếp bằng từng chuỗi nhỏ

# Patch 1B: New user register - tier
patch(CAMP,
    "tier='free', is_active=True,\r\n                                notes=f'Beta campaign · Free đến 10/4/2026 · {source}'",
    "tier='basic_trial', is_active=True,\r\n                                notes=f'Basic Trial 15 ngày · {datetime.now().strftime(\"%d/%m/%Y\")} · {source}'",
    '1B register tier'
)

# Patch 1C: Existing user update in register
patch(CAMP,
    "existing_vip.subscription_expires_at = TRIAL_EXPIRES\r\n                        existing_vip.notes = f'Beta campaign · Free đến 10/4/2026 · {source}'",
    "existing_vip.tier = 'basic_trial'\r\n                        existing_vip.notes = f'Basic Trial 15 ngày · {datetime.now().strftime(\"%d/%m/%Y\")} · {source}'",
    '1C existing vip'
)

# Patch 1D: Telegram msg
patch(CAMP,
    'f"✅ Free đến 10/4"',
    'f"✅ Basic Trial 15 ngày"',
    '1D telegram'
)

# Patch 1E: open-slots notes (waiting list)
patch(CAMP,
    "notes='Beta campaign (waiting list) · Free đến 10/4/2026'",
    "notes=f'Basic Trial 15 ngày · Mở từ waiting list · {datetime.now().strftime(\"%d/%m/%Y\")}'",
    '1E open-slots notes'
)

# Patch 1F: Email template - "Chương trình Beta 30 người"
patch(CAMP,
    'Chương trình Beta 30 người đã <strong>đủ suất</strong>',
    'Chương trình Basic Trial đã <strong>đủ 100 suất</strong>',
    '1F email template'
)

# Patch 1G: tier in open-slots activate
patch(CAMP,
    "tier='free', is_active=True,\r\n                        notes=f'Beta campaign · Free đến 10/4/2026 · {source}'",
    "tier='basic_trial', is_active=True,\r\n                        notes=f'Basic Trial 15 ngày · Mở từ waiting list · {datetime.now().strftime(\"%d/%m/%Y\")}'",
    '1G open-slots tier'
)

w('\n' + '='*60)
w('vip_auth.py')
w('='*60)

# Patch 2A: Thêm trial_end_date vào login response
# Từ dump thực tế: có 'is_first_login' trong response (khác project file)
patch(AUTH,
    "            token = _create_jwt(user.id, user.email)\r\n            return jsonify({\r\n                'success': True,\r\n                'token': token,\r\n                'is_first_login': is_first_login,\r\n                'user': {\r\n                    'id':              user.id,\r\n                    'email':           user.email,\r\n                    'full_name':       user.full_name,\r\n                    'tier':       ",
    "            token = _create_jwt(user.id, user.email)\r\n            # Tính trial_end_date từ created_at (không cần cột DB mới)\r\n            _trial_end = None\r\n            if user.tier == 'basic_trial' and user.created_at:\r\n                from datetime import timedelta as _td\r\n                _trial_end = (user.created_at + _td(days=15)).isoformat()\r\n            return jsonify({\r\n                'success': True,\r\n                'token': token,\r\n                'is_first_login': is_first_login,\r\n                'user': {\r\n                    'id':              user.id,\r\n                    'email':           user.email,\r\n                    'full_name':       user.full_name,\r\n                    'trial_end_date':  _trial_end,\r\n                    'tier':       ",
    '2A trial_end_date'
)

w('\n' + '='*60)
w('LandingPage.jsx')
w('='*60)

# Patch 3E: slots.taken / 30 → / 100
patch(LAND,
    '(slots.taken / 30) * 100',
    '(slots.taken / 100) * 100',
    '3E pct calc'
)

# Patch 3D: "Đăng ký ngay" form label
patch(LAND,
    '<div style={S.secLabel}>Đăng ký ngay</div>',
    '<div style={S.secLabel}>Đăng ký dùng thử 15 ngày</div>',
    '3D form label'
)

# Patch 3B: Price display "Miễn phí đến hết 10/4/2026"
patch(LAND,
    'Dùng thử 15 ngày<br/><strong>không cần thẻ</strong>',
    'Dùng thử 15 ngày<br/><strong>không cần thẻ</strong>',
    '3B price (check)'
)
# Thử target thực tế nếu chưa patch
patch(LAND,
    'Miễn phí đến<br/><strong>hết 10/4/2026</strong>',
    'Dùng thử 15 ngày<br/><strong>không cần thẻ</strong>',
    '3B price display'
)

# Patch 3F: btnSub text
patch(LAND,
    'suất · Miễn phí · Không cần thẻ ngân hàng',
    'suất · 15 ngày miễn phí · Không cần thẻ',
    '3F btnSub text'
)

# ── KẾT QUẢ ──
ok   = sum(1 for v in results.values() if v=='ok')
fail = sum(1 for v in results.values() if v=='fail')
total = len(results)

w('\n' + '='*60)
w(f'Kết quả: {ok}/{total} OK  |  {fail} thất bại')

if fail == 0:
    w('\n🎉 Tất cả patches OK!')
    w('Tiếp theo:')
    w('  git add campaign_api.py vip_auth.py frontend/src/components/LandingPage.jsx frontend/src/App.jsx')
    w('  git commit -m "feat: basic_trial 15d, free delay 3d, 100 slots"')
    w('  git push origin staging')
else:
    w('\n⚠️  Patches thất bại:')
    for name, status in results.items():
        if status == 'fail':
            w(f'   • {name}')

LOG.close()
w('\nLog đã lưu: patch_final_log.txt')
