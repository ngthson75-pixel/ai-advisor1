# 🚀 DEPLOYMENT GUIDE - Portfolio v2.0 (P&L + Cash)

## ✅ NEW FEATURES:

### 1. **Giá thị trường EOD (End-of-Day)**
   - Download giá mỗi ngày cuối phiên
   - Lưu vào file `latest_prices.json`
   - Tính P&L (lãi/lỗ) real-time

### 2. **Mục Tiền mặt (Cash Position)**
   - User nhập số tiền mặt
   - Tính phân bổ tài sản (% CP vs % TM)
   - AI phân tích rủi ro với cash

### 3. **Hiển thị P&L**
   - Green/Red cho mỗi stock
   - Tổng P&L danh mục
   - % lãi/lỗ

---

## 📦 FILES TO DEPLOY:

### **Backend:**
1. `backend_api_v2.py` → `backend_api.py` 
2. `requirements_v2.txt` → `requirements.txt`
3. `download_eod_prices.py` (new file)

### **Frontend:**
1. `AIPortfolioManager_v2.jsx` → `AIPortfolioManager.jsx`

---

## 🛠️ STEP-BY-STEP DEPLOYMENT:

### **STEP 1: Backend Deployment**

```bash
cd C:\ai-advisor1

# 1. Download files
# - backend_api_v2.py
# - requirements_v2.txt
# - download_eod_prices.py

# 2. Replace backend
copy backend_api_v2.py backend_api.py /Y
copy requirements_v2.txt requirements.txt /Y

# 3. Add EOD download script (NEW)
copy download_eod_prices.py .

# 4. Commit and push
git add backend_api.py requirements.txt download_eod_prices.py
git commit -m "Add: Portfolio v2 - EOD prices, Cash, P&L"
git push origin main

# 5. Wait for Render deploy (7-10 minutes)
```

---

### **STEP 2: Run Migration (NEW TABLES)**

Backend v2 has new table: `cash_positions`

```powershell
# Run migration
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/migrate" -Method POST

# Should return:
# {
#   "success": true,
#   "tables": ["signals", "portfolios", "cash_positions", "chat_history"]
# }
```

---

### **STEP 3: Download EOD Prices (INITIAL)**

```bash
# On local machine (requires vnstock)
cd C:\ai-advisor1

# Install vnstock if not installed
pip install vnstock==3.3.1 --break-system-packages

# Run download script
python download_eod_prices.py

# This creates: latest_prices.json
# Contains prices for VN30 + popular stocks

# Upload to Render:
# Manual: Dashboard → Files → Upload latest_prices.json
# OR commit to git:
git add latest_prices.json
git commit -m "Add: Initial EOD prices"
git push origin main
```

---

### **STEP 4: Frontend Deployment**

```bash
cd C:\ai-advisor1\frontend\src\components

# 1. Download AIPortfolioManager_v2.jsx

# 2. Replace current file
copy AIPortfolioManager_v2.jsx AIPortfolioManager.jsx /Y

# 3. Commit and push
cd C:\ai-advisor1
git add frontend/src/components/AIPortfolioManager.jsx
git commit -m "Update: Portfolio Manager v2 with P&L and Cash"
git push origin main

# 4. Wait for Cloudflare deploy (10 minutes)
```

---

### **STEP 5: Setup Daily EOD Download (CRON JOB)**

#### **Option A: Render Cron Job** (Recommended for production)

1. Render Dashboard → New → Cron Job
2. Configure:
   ```
   Name: eod-price-downloader
   Command: python download_eod_prices.py
   Schedule: 0 17 * * 1-5
   (Every weekday at 5:00 PM GMT+7)
   
   Environment Variables:
   (Same as backend - copy from backend service)
   ```

#### **Option B: Local Cron (for testing)**

Windows Task Scheduler:
```
Program: python
Arguments: C:\ai-advisor1\download_eod_prices.py
Trigger: Daily at 5:30 PM (weekdays only)
```

#### **Option C: Manual (simplest for MVP)**

```bash
# Run manually every day at 5:30 PM
cd C:\ai-advisor1
python download_eod_prices.py

# Upload latest_prices.json to Render manually
# OR commit to git
git add latest_prices.json
git commit -m "Update: EOD prices $(date +%Y-%m-%d)"
git push origin main
```

---

## 🧪 TESTING:

### **Test 1: Backend API**

```powershell
# 1. Health check (should show prices_loaded)
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health

# Should return:
# {
#   "status": "healthy",
#   "prices_loaded": 60  # Number of tickers
# }

# 2. Get latest prices
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/prices/latest

# 3. Get specific ticker price
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/prices/VCB

# Should return:
# {
#   "success": true,
#   "ticker": "VCB",
#   "data": {
#     "price": 90000,
#     "change": 500,
#     "change_percent": 0.56
#   }
# }

# 4. Test cash endpoint
$body = @{user_id=1; cash=50000000} | ConvertTo-Json
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/cash" -Method POST -Body $body -ContentType "application/json"
```

---

### **Test 2: Frontend (Website)**

1. **Visit:** https://ai-advisor.vn
2. **Clear cache:** Ctrl+Shift+R
3. **Tab:** "Quản trị đầu tư bằng AI"

**Test Portfolio:**
- Add VCB, 100, 85000
- ✅ Should show current price from EOD
- ✅ Should show P&L (green/red)
- ✅ Stats cards show total P&L

**Test Cash:**
- Input: 50,000,000 VND
- Click "Cập nhật"
- ✅ Cash balance displays
- ✅ Stats show asset allocation (% CP vs % TM)

**Test AI Chat:**
- Message: "Phân tích rủi ro danh mục của tôi"
- ✅ AI response includes:
   - Current holdings with P&L
   - Cash position
   - Asset allocation
   - Risk analysis

---

## 📊 NEW API ENDPOINTS:

```
GET  /api/prices/latest           # Get all EOD prices
GET  /api/prices/{ticker}         # Get specific ticker price
GET  /api/cash?user_id=1          # Get cash position
POST /api/cash                    # Update cash position
     Body: {user_id, cash}

GET  /api/portfolio?user_id=1     # Now includes P&L data
     Response: {
       portfolio: [{
         ticker, quantity, avg_price,
         current_price, cost, current_value,
         pl_amount, pl_pct  # NEW!
       }],
       cash  # NEW!
     }
```

---

## 💡 NEW DATABASE TABLES:

### **cash_positions:**
```sql
CREATE TABLE cash_positions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    cash_amount FLOAT NOT NULL,
    updated_at TIMESTAMP
);
```

---

## 📝 UPDATED AI CONTEXT:

**Old context:**
```
Portfolio:
- VCB: 100 shares @ 85,000 VND
Total: 8,500,000 VND
```

**New context:**
```
Portfolio:
CỔ PHIẾU:
- VCB: 100 CP @ 85,000 VND
  Giá hiện tại: 90,000 VND
  Giá trị: 9,000,000 VND (+5.88%)

Tổng vốn: 8,500,000 VND
Giá trị hiện tại: 9,000,000 VND
Lãi/Lỗ: +500,000 VND (+5.88%)

TIỀN MẶT: 50,000,000 VND

TỔNG TÀI SẢN: 59,000,000 VND
Phân bổ: 15.3% cổ phiếu / 84.7% tiền mặt
```

→ AI có context đầy đủ hơn để phân tích rủi ro!

---

## 🎯 EXPECTED RESULTS:

### **Portfolio Display:**
```
┌─────────────────────────────────────┐
│ VCB                        +5.88%   │ ← Green/Red
│ 100 CP × Mua 85,000 VND             │
│ Hiện tại: 90,000 VND (+500,000)     │
└─────────────────────────────────────┘

Tổng tài sản: 59,000,000 VND
Lãi/Lỗ: +500,000 VND (+5.88%)
Phân bổ: 15.3% CP / 84.7% TM
```

### **AI Analysis:**
```
Phân tích danh mục:

1. Hiện tại bạn đang có 100 CP VCB với lãi +5.88%.
   Đây là kết quả tốt!

2. Tỷ lệ cash 84.7% khá cao, cho thấy bạn
   đang thận trọng. Điều này tốt nếu thị
   trường đang có rủi ro.

3. Khuyến nghị: Có thể cân nhắc tăng tỷ lệ
   cổ phiếu lên 30-40% nếu tìm thấy cơ hội tốt.
```

---

## ⚠️ IMPORTANT NOTES:

### **EOD Prices File:**
- File: `latest_prices.json` (60 tickers)
- Size: ~15KB
- Must be in same directory as `backend_api.py`
- Updates: Daily (weekdays) at 5:00 PM

### **If prices not found:**
- Falls back to avg_price (user's buy price)
- P&L shows 0%
- Still functional but no real P&L

### **Render Free Tier:**
- File system is ephemeral (resets)
- Need to commit `latest_prices.json` to git
- OR setup Render Cron Job to download daily

---

## 🐛 TROUBLESHOOTING:

### **Issue: Prices not loading**
```powershell
# Check file exists
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health
# Check: "prices_loaded": 60

# If 0, run download:
python download_eod_prices.py
git add latest_prices.json
git push origin main
```

### **Issue: P&L shows 0%**
→ Ticker not in `latest_prices.json`
→ Add ticker to `TICKERS` list in `download_eod_prices.py`

### **Issue: Cash not saving**
→ Run migration: POST /api/migrate
→ Check table created: `cash_positions`

---

## 📋 DEPLOYMENT CHECKLIST:

- [ ] Download 3 backend files
- [ ] Replace backend_api.py
- [ ] Replace requirements.txt
- [ ] Add download_eod_prices.py
- [ ] Push backend to GitHub
- [ ] Wait for Render deploy
- [ ] Run migration (POST /api/migrate)
- [ ] Run EOD download script locally
- [ ] Upload latest_prices.json (git or manual)
- [ ] Download frontend file
- [ ] Replace AIPortfolioManager.jsx
- [ ] Push frontend to GitHub
- [ ] Wait for Cloudflare deploy
- [ ] Clear browser cache (Ctrl+Shift+R)
- [ ] Test portfolio with P&L
- [ ] Test cash position
- [ ] Test AI chat with new context
- [ ] Setup daily EOD download (cron or manual)

---

## 🎉 SUCCESS CRITERIA:

✅ Portfolio shows current prices  
✅ P&L displays (green/red)  
✅ Cash position editable  
✅ Asset allocation displayed  
✅ AI analyzes with full context  
✅ Daily EOD updates working  

---

**Estimated deployment time:** 30-45 minutes  
**Complexity:** Medium (requires EOD setup)  
**Impact:** HIGH - much better portfolio analysis!

---

Good luck! 🚀
