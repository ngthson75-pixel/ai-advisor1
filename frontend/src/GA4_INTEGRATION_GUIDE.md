# HƯỚNG DẪN TÍCH HỢP GA4 — AI ADVISOR
# Chỉ cần sửa 3 file: App.jsx, SignalsModule.jsx, AIPortfolioManager.jsx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BƯỚC 1: Copy file analytics.js vào src/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Đặt file analytics.js vào: src/analytics.js
→ Thay G-XXXXXXXXXX bằng Measurement ID thật của bạn


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BƯỚC 2: Sửa App.jsx — thêm 4 dòng
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// Dòng 1: Import ở đầu file (sau các import hiện có)
import { initGA, trackLogin, trackTabView } from './analytics'

// Dòng 2: Init GA khi app load — thêm vào useEffect đầu tiên
useEffect(() => {
  initGA()  // ← THÊM DÒNG NÀY
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      setUser(JSON.parse(storedUser))
    } catch (e) {
      console.error('Error parsing stored user:', e)
      localStorage.removeItem('user')
    }
  }
}, [])

// Dòng 3: Track login — sửa hàm handleLogin
const handleLogin = (userData) => {
  setUser(userData)
  trackLogin(userData.id || userData.email, userData.name)  // ← THÊM DÒNG NÀY
}

// Dòng 4: Track tab switching — sửa các button tab trong JSX
// Tìm dòng: onClick={() => setActiveTab('signals')}
// Sửa thành:
onClick={() => { setActiveTab('signals'); trackTabView('signals') }}

// Tìm dòng: onClick={() => setActiveTab('portfolio')}  
// Sửa thành:
onClick={() => { setActiveTab('portfolio'); trackTabView('portfolio') }}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BƯỚC 3: Sửa SignalsModule.jsx — thêm 2 dòng
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// Import ở đầu file
import { trackSignalClick, trackSignalsLoaded, trackSignalRefresh } from '../analytics'

// Khi signals load xong — tìm chỗ setSignals() hoặc signals render
// Thêm vào sau khi signals hiển thị:
useEffect(() => {
  if (signals && signals.length > 0) {
    trackSignalsLoaded(signals.length)  // ← THÊM
  }
}, [signals])

// Khi user click vào 1 signal — tìm onClick của signal card/row
// Thêm vào handler:
trackSignalClick(signal.ticker, signal.action, signal.confidence)

// Khi user bấm refresh — tìm onRefresh hoặc nút refresh
// Thêm vào handler:
trackSignalRefresh()


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BƯỚC 4: Sửa AIPortfolioManager.jsx — thêm 1 dòng
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// Import ở đầu file
import { trackPortfolioAction } from '../analytics'

// Tìm các action quan trọng trong component và thêm tracking:
// Khi user thêm cổ phiếu:
trackPortfolioAction('add_stock')

// Khi user bấm phân tích AI:
trackPortfolioAction('analyze')

// Khi user chat với AI coach:
trackPortfolioAction('chat')


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BƯỚC 5: Verify hoạt động
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Chạy npm run dev
2. Mở Chrome DevTools → Console
   → Phải thấy: "✅ GA4 initialized: G-XXXXXXXXXX"
3. Mở GA4 → Reports → Realtime
   → Thao tác trên app, phải thấy events xuất hiện trong vòng 1-2 phút
4. Kiểm tra Network tab trong DevTools
   → Filter "google-analytics" hoặc "gtag"
   → Phải thấy requests đến GA4


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REPORTS CẦN XEM TRONG GA4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAU 1 TUẦN — trả lời được 3 câu hỏi PMF:

1. Ai đang active? 
   → Reports → Engagement → Events → lọc "login"
   → Xem user_id nào login nhiều nhất

2. Feature nào được dùng?
   → Reports → Engagement → Events → xem "tab_view"
   → So sánh signals vs portfolio

3. Depth of engagement?
   → Reports → Engagement → Sessions
   → Average session duration > 5 phút = good sign
   → Bounce rate < 60% = users đang explore

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LƯU Ý QUAN TRỌNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  GA4 mất 24-48h để hiển thị đầy đủ data
    (Realtime report hiển thị ngay, nhưng full reports cần 1-2 ngày)

⚠️  Nếu dùng ad blocker khi test, GA4 sẽ bị block
    → Test bằng Chrome không có extension

⚠️  Thêm vào Privacy Policy:
    "Chúng tôi sử dụng Google Analytics để phân tích hành vi
    người dùng nhằm cải thiện sản phẩm"
