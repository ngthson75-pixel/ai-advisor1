# 🧪 COMPREHENSIVE TESTING CHECKLIST

## 📋 PRE-DEPLOYMENT TESTING (Local)

### **TEST 1: Frontend - Portfolio Features**

#### **1.1: Add Stock with Auto-Price**
```
Steps:
1. Tab "Quản trị đầu tư"
2. Nhập: Mã = VCB, Số lượng = 100, Giá mua = 85000
3. Click "Thêm vị thế"

Expected:
✅ Loading indicator xuất hiện
✅ API call to /api/stock/current-price?ticker=VCB
✅ Stock xuất hiện trong list
✅ currentPrice tự động được fetch (ví dụ: 96500)
✅ P/L tính đúng: (96500 - 85000) / 85000 * 100 = +13.5%
✅ Message từ AI: "Đã thêm vị thế VCB! Giá hiện tại đã được cập nhật..."

Pass: ⬜ | Fail: ⬜
Notes: _______________________
```

#### **1.2: Tiền Mặt Field**
```
Steps:
1. Nhập "Tiền mặt khả dụng": 50,000,000
2. Add vài stocks
3. Click "Phân tích danh mục"

Expected:
✅ Tiền mặt hiển thị trong phân tích
✅ Format: "Tiền mặt: 50,000,000 ₫"

Pass: ⬜ | Fail: ⬜
Notes: _______________________
```

#### **1.3: Remove Stock**
```
Steps:
1. Add stock VCB
2. Click "×" button
3. Confirm

Expected:
✅ Stock biến mất khỏi list
✅ API call to DELETE /api/portfolio/VCB
✅ Message từ AI: "Đã xóa vị thế VCB..."

Pass: ⬜ | Fail: ⬜
Notes: _______________________
```

#### **1.4: P/L Calculation**
```
Test data:
- VCB: 100 CP × 85,000 (entry) | 96,500 (current)
- HPG: 200 CP × 27,000 (entry) | 28,300 (current)

Expected calculations:
VCB P/L: (96,500 - 85,000) × 100 = +1,150,000 ₫ (+13.5%)
HPG P/L: (28,300 - 27,000) × 200 = +260,000 ₫ (+4.8%)
Total P/L: +1,410,000 ₫

Pass: ⬜ | Fail: ⬜
Notes: _______________________
```

---

### **TEST 2: Frontend - UI/UX**

#### **2.1: Subtitle Text**
```
Expected:
"Hãy chia sẻ danh mục của bạn và hỏi đáp mua bán để AI hỗ trợ quản lý danh mục và kiểm soát FOMO hay HOẢNG SỢ"

Pass: ⬜ | Fail: ⬜
```

#### **2.2: No "Gemini" Text**
```
Check:
- Chat section header should be "Tư vấn AI"
- NO "(Gemini)" text anywhere

Pass: ⬜ | Fail: ⬜
```

#### **2.3: Responsive Layout - Desktop**
```
Screen: 1920×1080

Expected:
✅ 2 columns side-by-side
✅ Portfolio left, Chat right
✅ Equal width columns
✅ Proper spacing

Pass: ⬜ | Fail: ⬜
```

#### **2.4: Responsive Layout - Tablet**
```
Screen: 768×1024

Expected:
✅ 2 columns (might be narrower)
✅ Still side-by-side
✅ No horizontal scroll

Pass: ⬜ | Fail: ⬜
```

#### **2.5: Responsive Layout - Mobile**
```
Screen: 375×667

Expected:
✅ Single column (stacked)
✅ Portfolio section on TOP
✅ Chat section BELOW
✅ No horizontal scroll
✅ Touch-friendly buttons (44px min)
✅ Input fields full width

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 3: Backend - Price Fetching**

#### **3.1: Auto-fetch Endpoint**
```
Test command:
curl http://localhost:10000/api/stock/current-price?ticker=VCB

Expected response:
{
  "success": true,
  "price": 96500.0,
  "source": "intraday" or "eod",
  "timestamp": "2025-01-24T10:30:00",
  "ticker": "VCB"
}

Pass: ⬜ | Fail: ⬜
```

#### **3.2: Invalid Ticker**
```
Test command:
curl http://localhost:10000/api/stock/current-price?ticker=INVALID

Expected response:
{
  "success": false,
  "error": "No price data found for INVALID",
  "ticker": "INVALID"
}

Status code: 404

Pass: ⬜ | Fail: ⬜
```

#### **3.3: Batch Prices**
```
Test command:
curl -X POST http://localhost:10000/api/stock/batch-prices \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["VCB", "HPG", "VNM"]}'

Expected:
{
  "success": true,
  "prices": {
    "VCB": 96500.0,
    "HPG": 28300.0,
    "VNM": 87400.0
  },
  "failed": []
}

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 4: AI Chat Integration**

#### **4.1: Portfolio Context**
```
Steps:
1. Add VCB (100 CP @ 85,000)
2. Chat: "Tôi có mấy mã?"

Expected AI Response:
"Bạn đang có 1 mã trong danh mục: VCB với 100 cổ phiếu."

✅ AI knows portfolio
✅ Correct ticker count
✅ Correct quantity

Pass: ⬜ | Fail: ⬜
```

#### **4.2: Stock IN Signal - Conditional Guidance**
```
Setup:
- Portfolio: VCB (100 CP @ 85,000)
- Question: "Tôi nên mua thêm VCB không?"

Expected AI Response:
✅ Mentions "Buysell Signal"
✅ Provides conditional guidance (if VCB in signal list)
✅ Includes entry/SL/TP
✅ Emphasizes user responsibility
✅ NO direct "MUA NGAY!" command

Pass: ⬜ | Fail: ⬜
```

#### **4.3: Stock NOT IN Signal - Analysis Only**
```
Question: "Tôi nên mua AAPL không?"

Expected AI Response:
✅ Starts with ⚠️ warning
✅ States "KHÔNG nằm trong Buysell Signal"
✅ Says "CHỈ để hiểu biết"
✅ Provides general analysis
✅ NO buy/sell recommendation
✅ Redirects to Signal list

Pass: ⬜ | Fail: ⬜
```

#### **4.4: FOMO Control**
```
Question: "HPG tăng mạnh quá! Tôi sợ lỡ, có nên mua thêm?"

Expected AI Response:
✅ Recognizes FOMO
✅ Uses "🧠 TÂM LÝ FOMO" header
✅ Provides rational analysis
✅ Warns against impulsive buying
✅ Emphasizes discipline

Pass: ⬜ | Fail: ⬜
```

#### **4.5: Panic Control**
```
Setup: VNM at -5.6% loss
Question: "VNM giảm mạnh! Tôi sợ lỗ thêm, bán ngay không?"

Expected AI Response:
✅ Recognizes panic
✅ Uses "🧠 TÂM LÝ HOẢNG SỢ" header
✅ Calm, rational tone
✅ References investment plan
✅ Distinguishes correction vs. trend change

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 5: Data Persistence**

#### **5.1: Portfolio Saved to Backend**
```
Steps:
1. Add VCB
2. Refresh page
3. Check portfolio still there

Expected:
✅ Portfolio loads from backend
✅ All fields correct (ticker, quantity, prices)

Pass: ⬜ | Fail: ⬜
```

#### **5.2: Chat History Saved**
```
Steps:
1. Chat with AI
2. Refresh page
3. Check chat history

Expected:
✅ Previous messages reload
✅ Correct order (oldest → newest)

Pass: ⬜ | Fail: ⬜
```

#### **5.3: User Isolation**
```
Steps:
1. User A adds VCB
2. Open incognito (User B)
3. Check portfolio

Expected:
✅ User B sees empty portfolio
✅ Different userId generated
✅ No data leakage

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 6: Daily Auto-Update Script**

#### **6.1: Manual Run**
```
Command:
python scripts/update_portfolio_prices.py

Expected output:
📊 PORTFOLIO PRICE AUTO-UPDATE
================================================
Started: 2025-01-24 17:00:00

📈 Found 3 portfolio entries
📊 Unique tickers: 2

🔄 Fetching latest prices...

  ✅ VCB   :     96,500 VND
  ✅ HPG   :     28,300 VND

Fetch results: ✅ 2 success, ❌ 0 failed

💾 Updating database...
  📈 VCB: 95,000 → 96,500 (+1.6%)

✅ Updated 3 portfolio entries

Pass: ⬜ | Fail: ⬜
```

#### **6.2: Test Single Ticker**
```
Command:
python scripts/update_portfolio_prices.py --ticker VCB

Expected:
✅ VCB: 96,500 VND

Pass: ⬜ | Fail: ⬜
```

#### **6.3: Portfolio Summary**
```
Command:
python scripts/update_portfolio_prices.py --summary

Expected:
Shows all portfolios with P/L

Pass: ⬜ | Fail: ⬜
```

---

## 📱 POST-DEPLOYMENT TESTING (Production)

### **TEST 7: Production Deployment**

#### **7.1: Cloudflare Pages Deploy**
```
URL: https://ai-advisor.vn

Check:
✅ Site loads
✅ New subtitle visible
✅ No "(Gemini)" text
✅ Portfolio features work
✅ Chat works

Pass: ⬜ | Fail: ⬜
```

#### **7.2: Render Backend Deploy**
```
URL: https://ai-advisor1-backend.onrender.com

Test:
curl https://ai-advisor1-backend.onrender.com/health

Expected:
{"status": "healthy"}

Pass: ⬜ | Fail: ⬜
```

#### **7.3: Price Endpoint Production**
```
curl https://ai-advisor1-backend.onrender.com/api/stock/current-price?ticker=VCB

Expected:
{"success": true, "price": 96500, ...}

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 8: Mobile Testing**

#### **8.1: iPhone (Safari)**
```
Device: iPhone 12 (or similar)
Browser: Safari

Check:
✅ Portfolio section on top
✅ Chat section below
✅ No horizontal scroll
✅ Buttons work (touch-friendly)
✅ Input fields work
✅ Chat scrolls properly

Pass: ⬜ | Fail: ⬜
```

#### **8.2: Android (Chrome)**
```
Device: Samsung/Pixel
Browser: Chrome

Same checks as iPhone

Pass: ⬜ | Fail: ⬜
```

---

### **TEST 9: Cross-Browser**

#### **9.1: Chrome Desktop**
```
Pass: ⬜ | Fail: ⬜
```

#### **9.2: Firefox Desktop**
```
Pass: ⬜ | Fail: ⬜
```

#### **9.3: Safari Desktop**
```
Pass: ⬜ | Fail: ⬜
```

#### **9.4: Edge Desktop**
```
Pass: ⬜ | Fail: ⬜
```

---

### **TEST 10: Performance**

#### **10.1: Load Time**
```
Metric: Time to Interactive (TTI)

Target: < 3 seconds

Actual: _______ seconds

Pass: ⬜ | Fail: ⬜
```

#### **10.2: API Response Time**
```
Endpoint: /api/stock/current-price

Target: < 2 seconds

Actual: _______ seconds

Pass: ⬜ | Fail: ⬜
```

#### **10.3: Chat Response Time**
```
Endpoint: /api/chat

Target: < 5 seconds

Actual: _______ seconds

Pass: ⬜ | Fail: ⬜
```

---

## 🐛 BUG TRACKING

| # | Issue | Severity | Status | Fixed By |
|---|-------|----------|--------|----------|
| 1 |       | High/Med/Low | Open/Fixed | Name |
| 2 |       |          |        |          |
| 3 |       |          |        |          |

---

## ✅ SIGN-OFF

### Frontend Tests:
- [ ] All portfolio features work
- [ ] UI/UX matches requirements
- [ ] Responsive on all devices
- [ ] No console errors

### Backend Tests:
- [ ] Price fetching works
- [ ] ChatGPT-4o integration verified
- [ ] Data persistence works
- [ ] Auto-update script tested

### Production Tests:
- [ ] Deployed successfully
- [ ] All features work in prod
- [ ] Mobile tested
- [ ] Performance acceptable

---

**Tester:** _________________
**Date:** _________________
**Version:** 2.0
**All tests passed:** ⬜ Yes | ⬜ No

**Notes:**
_______________________________________________
_______________________________________________
_______________________________________________
