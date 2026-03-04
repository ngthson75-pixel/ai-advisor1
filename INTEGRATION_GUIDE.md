# PWA PUSH NOTIFICATION - INTEGRATION GUIDE
# ==========================================
# AI Advisor v1.0
# Tập trung: Tín hiệu MUA/BÁN trước, risk/portfolio sau

## BƯỚC 1: INSTALL BACKEND DEPENDENCY
=====================================
# Trên Render server (thêm vào requirements.txt):
pywebpush==2.0.0

# requirements.txt hiện tại thêm dòng:
echo "pywebpush==2.0.0" >> requirements.txt


## BƯỚC 2: TẠO VAPID KEYS (1 LẦN DUY NHẤT)
============================================
# Option A: Dùng npx (nhanh nhất)
npx web-push generate-vapid-keys

# Option B: Dùng Python sau khi deploy
python pwa_push_backend.py --generate-keys

# Option C: Online generator
# https://vapidkeys.com/

# OUTPUT sẽ như này:
# Public Key:  BNxxxxx...
# Private Key: xxxxx...


## BƯỚC 3: THÊM VÀO .ENV
==========================
# File .env (local) và Render Environment Variables:

VAPID_PUBLIC_KEY=BNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAPID_PRIVATE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VAPID_EMAIL=mailto:admin@ai-advisor.vn

# ⚠️ PUBLIC_KEY cũng cần thêm vào frontend .env:
# File .env.production (frontend):
VITE_VAPID_PUBLIC_KEY=BNxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_API_URL=https://ai-advisor1-backend.onrender.com


## BƯỚC 4: COPY FILES
======================

# Backend (Python):
cp pwa_push_backend.py /path/to/backend/pwa_push_backend.py

# Frontend (React):
cp PWANotificationManager.jsx /path/to/frontend/src/components/
cp sw.js /path/to/frontend/public/sw.js
cp manifest.json /path/to/frontend/public/manifest.json


## BƯỚC 5: TẠO PUSH_SUBSCRIPTIONS TABLE
=========================================
# Chạy SQL này trong pgAdmin4 (production DB):

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    failed_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_push_sub_user_id ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_sub_active ON push_subscriptions(is_active);


## BƯỚC 6: TÍCH HỢP VÀO BACKEND_API.PY
========================================
# Thêm vào đầu file backend_api.py (sau các import hiện có):

# === THÊM VÀO ĐÂY ===
from pwa_push_backend import push_service, init_push_routes, notify_signal_created, SignalPayloadBuilder

# === THÊM SAU KHI TẠO app = Flask(...) ===
# Đặt sau dòng "app = Flask(__name__)" hoặc tương tự:
def get_session():
    return Session()  # Dùng session factory hiện có

init_push_routes(app, get_session)

# === TÍCH HỢP VÀO /api/signals POST (BUY signal tạo mới) ===
# Tìm đoạn code tạo signal BUY, sau khi session.commit() thêm:

    session.commit()
    # --- PUSH NOTIFICATION ---
    try:
        signal_dict = {
            'id': signal.id,
            'ticker': signal.ticker,
            'code': signal.ticker,
            'signal_code': signal.signal_code,
            'strategy_type': signal.strategy_type,
            'entry_price': float(signal.entry_price or 0),
            'stop_loss': float(signal.stop_loss or 0),
            'take_profit': float(signal.take_profit or 0),
            'risk_pct': float(signal.risk_pct or 5),
            'reward_pct': float(signal.reward_pct or 8),
            'rr_ratio': float(signal.rr_ratio or 1.6),
        }
        notify_signal_created(session, signal_dict, signal.action)
    except Exception as push_err:
        print(f"⚠️ Push notification failed (non-critical): {push_err}")
    # --- END PUSH ---

# === TÍCH HỢP VÀO /api/signals/sell (SELL signal) ===
# Tương tự, sau khi tạo sell_signal:

    session.commit()
    # --- PUSH NOTIFICATION ---
    try:
        sell_dict = {
            'id': sell_signal.id,
            'ticker': sell_signal.ticker,
            'code': sell_signal.ticker,
            'entry_price': float(sell_signal.entry_price or 0),
            'sell_reason': data.get('sell_reason', 'MANUAL'),
            'buy_signal_code': sell_signal.buy_signal_code,
        }
        notify_signal_created(session, sell_dict, 'SELL')
    except Exception as push_err:
        print(f"⚠️ Push notification failed (non-critical): {push_err}")
    # --- END PUSH ---


## BƯỚC 7: THÊM VÀO INDEX.HTML (FRONTEND)
==========================================
# File: public/index.html (trong <head>):

<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#3b82f6" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="AI Advisor" />
<link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
<link rel="apple-touch-startup-image" href="/icons/splash.png" />


## BƯỚC 8: THÊM VÀO APP.JSX
=============================
# File: src/App.jsx

import PWANotificationManager from './components/PWANotificationManager'

function App() {
  const { user } = useAuth()  // Dùng auth hook hiện có

  return (
    <>
      {/* ... existing app content ... */}
      
      {/* PWA Notification - đặt cuối cùng */}
      <PWANotificationManager userId={user?.id} />
    </>
  )
}


## BƯỚC 9: TẠO ICONS
=====================
# Cần tạo các icon sizes trong public/icons/:
# - icon-72x72.png
# - icon-96x96.png
# - icon-128x128.png
# - icon-192x192.png   ← Quan trọng nhất
# - icon-512x512.png   ← Cho splash screen
# - badge-72x72.png    ← Small icon trên status bar

# Tool tạo icon nhanh:
# https://realfavicongenerator.net/
# https://pwabuilder.com/


## BƯỚC 10: TEST
=================
# 1. Deploy lên staging
# 2. Mở Chrome DevTools → Application → Service Workers
# 3. Kiểm tra SW registered
# 4. Mở Application → Push Messaging → Subscribe
# 5. Gọi test API:

curl -X POST https://ai-advisor1-backend.onrender.com/api/push/test \
  -H "Content-Type: application/json" \
  -d '{"type": "buy_signal"}'

# 6. Check mobile: Vào https://ai-advisor.vn bằng Chrome Android
#    → Menu → "Add to Home Screen"
#    → Mở app từ home screen
#    → Bật notification khi được hỏi


## IOS NOTES
============
# iOS yêu cầu:
# 1. User phải "Add to Home Screen" TRƯỚC
# 2. Mở app từ home screen icon (không phải browser)
# 3. iOS 16.4+ mới support Web Push
# 4. Nên thêm trong-app prompt hướng dẫn user thêm vào home screen


## PHÂN TẦNG NOTIFICATION (Ưu tiên)
=====================================
# PHASE 1 (Làm ngay - file này):
# ✅ Tín hiệu MUA mới
# ✅ Tín hiệu BÁN (stop loss, take profit, manual)

# PHASE 2 (Làm sau):
# 🔜 Cảnh báo rủi ro thị trường (VN-Index đổi chiều mạnh)
# 🔜 Stop loss alert cá nhân (portfolio)
# 🔜 Nhắc nhở checklist giao dịch hằng ngày
