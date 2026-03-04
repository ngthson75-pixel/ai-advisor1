# VIP SYSTEM - HƯỚNG DẪN TÍCH HỢP STAGING
# ==========================================
# Thực hiện theo thứ tự từng bước.
# Test staging xong mới push production.

## ═══════════════════════════════════════════
## BƯỚC 1: INSTALL DEPENDENCIES
## ═══════════════════════════════════════════

### 1.1 Thêm vào requirements.txt (backend):
```
PyJWT==2.8.0
pywebpush==2.0.0
```

### 1.2 Chạy local để test:
```powershell
pip install PyJWT pywebpush --break-system-packages
```

---

## ═══════════════════════════════════════════
## BƯỚC 2: TẠO VAPID KEYS (1 LẦN DUY NHẤT)
## ═══════════════════════════════════════════

### Option A - dùng npx (nhanh nhất):
```powershell
npx web-push generate-vapid-keys
```

### Option B - dùng Python:
```powershell
python pwa_push_backend.py --generate-keys
```

### Kết quả trông như này:
```
Public Key:  BNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Private Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### ⚠️ Lưu keys vào .env (KHÔNG commit lên git!):
```
# File .env local:
VAPID_PUBLIC_KEY=BNxxxxxx...
VAPID_PRIVATE_KEY=xxxxxx...
VAPID_EMAIL=mailto:admin@ai-advisor.vn

# Thêm 2 keys mới:
ADMIN_SECRET=ai-advisor-admin-2026-staging  # Đặt key mạnh hơn cho production
JWT_SECRET=ai-advisor-jwt-2026-staging       # Đặt key mạnh hơn cho production
```

---

## ═══════════════════════════════════════════
## BƯỚC 3: COPY FILES VÀO PROJECT
## ═══════════════════════════════════════════

```
Files mới cần copy vào project:
├── vip_auth.py                    → /backend/vip_auth.py
├── VIPAdminPanel.jsx              → /frontend/src/components/VIPAdminPanel.jsx
├── PWANotificationManager_v2.jsx  → /frontend/src/components/PWANotificationManager.jsx (GHI ĐÈ v1)
│
Files từ conversation cũ (đã có):
├── pwa_push_backend.py            → /backend/pwa_push_backend.py (giữ nguyên)
├── sw.js                          → /frontend/public/sw.js (giữ nguyên)
└── manifest.json                  → /frontend/public/manifest.json (giữ nguyên)
```

---

## ═══════════════════════════════════════════
## BƯỚC 4: SỬA backend_api.py
## ═══════════════════════════════════════════

### 4.1 Thêm imports (sau các imports hiện có, khoảng line 30):
```python
# === VIP SYSTEM (thêm vào) ===
from vip_auth import init_vip_system, push_vip_users
from pwa_push_backend import push_service, init_push_routes, SignalPayloadBuilder, notify_signal_created
```

### 4.2 Thêm init sau khi tạo app và Session (sau dòng "Session = sessionmaker..."):
```python
# === INIT VIP + PUSH ROUTES (thêm vào cuối phần setup) ===
# Đặt sau "engine = create_engine(DATABASE_URL)" và "Session = sessionmaker(bind=engine)"

def get_session():
    return Session()

init_push_routes(app, get_session)  # Routes push notification
init_vip_system(app, engine, Session)  # Routes VIP auth + admin
```

### 4.3 Sửa hàm notify_signal_created trong /api/signals (POST):
```python
# TÌM đoạn code sau session.commit() khi tạo BUY signal:
session.commit()

# THÊM VÀO NGAY SAU:
try:
    signal_dict = {
        'id': signal.id,
        'ticker': signal.ticker,
        'signal_code': getattr(signal, 'signal_code', None),
        'strategy_type': getattr(signal, 'strategy', ''),
        'entry_price': float(signal.entry_price or 0),
        'stop_loss': float(signal.stop_loss or 0),
        'take_profit': float(signal.take_profit or 0),
        'risk_pct': 5.0,
        'reward_pct': 8.0,
        'rr_ratio': 1.6,
    }
    from pwa_push_backend import SignalPayloadBuilder
    payload = SignalPayloadBuilder.buy_signal(signal_dict)
    push_vip_users(session, payload)  # ← Dùng push_vip_users thay vì notify_signal_created
except Exception as push_err:
    print(f"⚠️ Push notification failed (non-critical): {push_err}")
```

---

## ═══════════════════════════════════════════
## BƯỚC 5: THÊM ROUTE ADMIN VÀO FRONTEND
## ═══════════════════════════════════════════

### 5.1 Thêm vào App.jsx (hoặc router config):
```jsx
import VIPAdminPanel from './components/VIPAdminPanel'

// Trong router:
<Route path="/admin" element={<VIPAdminPanel />} />

// Hoặc nếu không dùng router, thêm conditional render:
{window.location.pathname === '/admin' && <VIPAdminPanel />}
```

### 5.2 Thêm PWANotificationManager vào App.jsx:
```jsx
import PWANotificationManager from './components/PWANotificationManager'

// Trong component App, sau khi có user state:
const [user, setUser] = useState(null)
const [token, setToken] = useState(() => localStorage.getItem('vip_token'))

// Sau khi login thành công:
// setUser(data.user)
// setToken(data.token)
// localStorage.setItem('vip_token', data.token)

// Trong JSX:
<PWANotificationManager
  userId={user?.id}
  token={token}
  isPushEnabled={user?.is_push_enabled}
/>
```

### 5.3 Thêm login logic (ví dụ trong LandingPage.jsx hoặc component mới):
```jsx
const handleLogin = async (email, password) => {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const data = await res.json()
  if (data.success) {
    setUser(data.user)
    setToken(data.token)
    localStorage.setItem('vip_token', data.token)
  }
}

// Khi app load, restore session:
useEffect(() => {
  const token = localStorage.getItem('vip_token')
  if (token) {
    fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(r => r.json()).then(data => {
      if (data.success) setUser(data.user)
    })
  }
}, [])
```

---

## ═══════════════════════════════════════════
## BƯỚC 6: THÊM ENVIRONMENT VARIABLES TRÊN RENDER STAGING
## ═══════════════════════════════════════════

```
Vào Render Dashboard → Staging service → Environment:

Key                    Value
───────────────────    ──────────────────────────────────
VAPID_PUBLIC_KEY       BNxxxxxx... (từ bước 2)
VAPID_PRIVATE_KEY      xxxxxx...   (từ bước 2)
VAPID_EMAIL            mailto:admin@ai-advisor.vn
ADMIN_SECRET           [tạo key mạnh, ví dụ: AdminKey@2026!]
JWT_SECRET             [tạo key mạnh, ví dụ: JwtSecret@2026!]
ENVIRONMENT            staging
```

### Frontend (Cloudflare Pages - staging):
```
VITE_VAPID_PUBLIC_KEY  BNxxxxxx... (same as backend public key)
VITE_API_URL           https://ai-advisor1-staging.onrender.com
```

---

## ═══════════════════════════════════════════
## BƯỚC 7: CHẠY STAGING SQL (tạo bảng)
## ═══════════════════════════════════════════

Bảng sẽ tự tạo khi backend start (qua SQLAlchemy create_all).
Chỉ cần verify sau khi deploy:

```sql
-- Kiểm tra trong pgAdmin4 (staging DB):
SELECT * FROM vip_users;
SELECT * FROM push_subscriptions;
```

Nếu bảng chưa có → backend chưa khởi động đúng, check Render logs.

---

## ═══════════════════════════════════════════
## BƯỚC 8: TEST STAGING
## ═══════════════════════════════════════════

### 8.1 Test tạo VIP user (PowerShell):
```powershell
$headers = @{
  "Content-Type" = "application/json"
  "X-Admin-Key"  = "AdminKey@2026!"
}
$body = @{
  email     = "test@example.com"
  full_name = "Nguyễn Test"
  phone     = "0912345678"
  tier      = "vip"
  notes     = "Test account"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://ai-advisor1-staging.onrender.com/api/admin/users/create" `
  -Method POST `
  -Headers $headers `
  -Body $body `
  -UseBasicParsing
```

### 8.2 Test login:
```powershell
$body = @{
  email    = "test@example.com"
  password = "password-từ-response-trên"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "https://ai-advisor1-staging.onrender.com/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body `
  -UseBasicParsing
```

### 8.3 Test xem danh sách users:
```powershell
Invoke-WebRequest `
  -Uri "https://ai-advisor1-staging.onrender.com/api/admin/users" `
  -Headers @{"X-Admin-Key"="AdminKey@2026!"} `
  -UseBasicParsing
```

### 8.4 Test toggle push:
```powershell
Invoke-WebRequest `
  -Uri "https://ai-advisor1-staging.onrender.com/api/admin/users/1/toggle-push" `
  -Method POST `
  -Headers @{"X-Admin-Key"="AdminKey@2026!"} `
  -UseBasicParsing
```

### 8.5 Test admin panel UI:
```
Mở: https://staging.ai-advisor.vn/admin
Nhập Admin Key
Tạo user test
```

### 8.6 Test push notification end-to-end:
```
1. Login với test account
2. Bật thông báo trên browser
3. Vào admin panel → Bật push cho user đó
4. POST /api/admin/push/test/1 (gửi test push)
5. Kiểm tra notification xuất hiện
```

---

## ═══════════════════════════════════════════
## BƯỚC 9: DEPLOY PRODUCTION (sau khi staging OK)
## ═══════════════════════════════════════════

```powershell
# Sau khi test staging thành công:
git add .
git commit -m "feat: VIP auth + admin-controlled push notifications"
git push origin main

# Thêm env vars vào Render Production (giống staging nhưng keys khác)
# Verify production deploy
# Test lại với 1 VIP account thật
```

---

## ═══════════════════════════════════════════
## WORKFLOW THỰC TẾ KHI CÓ KHÁCH MỚI
## ═══════════════════════════════════════════

```
Bước 1: Sơn và khách thỏa thuận
         ↓
Bước 2: Sơn vào /admin → "Tạo VIP Account"
        → Điền email, tên, phone, tier, notes
        → Copy credentials hiện ra
         ↓
Bước 3: Gửi cho khách (Zalo/Telegram):
        "Tài khoản AI Advisor VIP của anh/chị:
         URL: https://ai-advisor.vn
         Email: xxx@xxx.com
         Pass: xxxxxxxxxx
         Vui lòng đổi mật khẩu sau khi đăng nhập."
         ↓
Bước 4: Khách login → Browser hỏi "Bật thông báo?" → Khách OK
         ↓
Bước 5: Sơn thấy trong admin panel: push_devices = 1
        → Click "Bật Push" cho khách đó
         ↓
Bước 6: Từ đây, mỗi signal mới → khách nhận notification ngay lập tức
```

---

## ═══════════════════════════════════════════
## TROUBLESHOOTING
## ═══════════════════════════════════════════

### Lỗi "ModuleNotFoundError: No module named 'jwt'"
→ Chưa install PyJWT
→ Thêm "PyJWT==2.8.0" vào requirements.txt và redeploy

### Lỗi "ModuleNotFoundError: No module named 'pywebpush'"
→ Thêm "pywebpush==2.0.0" vào requirements.txt

### Push không nhận được dù push_devices > 0
→ Check VAPID keys đã đúng chưa
→ Check is_push_enabled = TRUE chưa
→ Thử POST /api/admin/push/test/<id>

### Admin Panel báo "Unauthorized"
→ ADMIN_SECRET trên Render chưa đúng với ADMIN_KEY nhập vào UI

### Subscription bị là "anonymous" không link với user
→ Đảm bảo truyền token vào PWANotificationManager
→ User phải login trước khi bật thông báo
