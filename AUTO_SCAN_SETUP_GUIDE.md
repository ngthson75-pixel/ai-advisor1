# 🚀 AUTO-SCAN SIGNALS SETUP GUIDE

## 📋 OVERVIEW

Hệ thống tự động quét 343 cổ phiếu có thanh khoản cao nhất khi database trống!

### How it works:
1. User vào tab "Tín hiệu mua bán"
2. Nếu chưa có signals → Hiển thị button "Tạo tín hiệu mới"
3. User click button → Backend tự động chạy scanner
4. Scanner download data 343 cổ phiếu → Filter theo Pullback & EMA Cross
5. Signals tự động hiển thị trên frontend

---

## 📥 INSTALLATION

### STEP 1: Update Backend

```bash
cd C:\ai-advisor1

# Replace backend_api.py with new version
# Download: backend_api_updated.py
# Rename to: backend_api.py
```

**Or manually add to existing backend_api.py:**

Add these imports at top:
```python
import subprocess
import threading
```

Add 2 new endpoints:
```python
@app.route('/api/scan', methods=['POST'])
# ... (copy from backend_api_updated.py)

@app.route('/api/scan/status', methods=['GET'])
# ... (copy from backend_api_updated.py)
```

### STEP 2: Update Frontend

```bash
cd C:\ai-advisor1\frontend\src

# Replace components/SignalsModule.jsx
# Download: SignalsModule.jsx (from outputs)
```

### STEP 3: Add CSS

```bash
cd C:\ai-advisor1\frontend\src

# Open App.css
notepad App.css

# Scroll to END
# Copy ALL content from scan-styles.css
# Paste at end
# Save
```

### STEP 4: Verify Scanner Script

```bash
cd C:\ai-advisor1\scripts

# Make sure daily_signal_scanner.py exists
dir daily_signal_scanner.py

# If not exists, you need to create it
# Or make sure backend can find it
```

### STEP 5: Test Backend Locally

```bash
cd C:\ai-advisor1

# Start backend
python backend_api.py

# In another terminal, test endpoints:
curl http://localhost:10000/health
curl http://localhost:10000/api/signals
curl -X POST http://localhost:10000/api/scan
```

### STEP 6: Deploy

```bash
cd C:\ai-advisor1

git add .
git commit -m "Add auto-scan feature for signals"
git push origin main

# Backend (Render) will auto-deploy
# Frontend (Cloudflare) will auto-deploy
# Wait 5-10 minutes
```

---

## 🎯 USER FLOW

### Scenario 1: Empty Database

```
User visits: https://ai-advisor.vn
→ Login
→ Click "Tín hiệu mua bán"
→ See: "Chưa có tín hiệu nào"
→ Click: "Tạo tín hiệu mới (2-3 phút)"
→ Loading: "Đang quét 343 cổ phiếu..."
→ Progress: "Đang phân tích thị trường..."
→ Success: "✅ Đã tìm thấy 15 tín hiệu!"
→ Auto-refresh → See signals table
```

### Scenario 2: Signals Exist

```
User visits: https://ai-advisor.vn
→ Login
→ Click "Tín hiệu mua bán"
→ Immediately see signals table
→ Can use filters
→ Can click "Làm mới" to refresh
```

---

## 🔧 API ENDPOINTS

### GET /api/signals
**Response:**
```json
{
  "success": true,
  "count": 15,
  "signals": [
    {
      "id": 1,
      "ticker": "VCB",
      "strategy": "PULLBACK",
      "entry_price": 88500,
      "stop_loss": 85000,
      "take_profit": 95000,
      "risk_reward": 2.1,
      "strength": 78,
      "is_priority": 1,
      "stock_type": "Blue Chip",
      "rsi": 45.2,
      "date": "2025-01-01",
      "action": "BUY"
    }
  ]
}
```

### POST /api/scan
**Triggers scanner to generate new signals**

**Response:**
```json
{
  "success": true,
  "message": "Signal scanner started. This will take 2-3 minutes.",
  "status": "scanning"
}
```

### GET /api/scan/status
**Check scanning progress**

**Response:**
```json
{
  "success": true,
  "signals_count": 15,
  "last_scan": "2025-01-01T10:30:00",
  "is_recent": true,
  "status": "complete"
}
```

---

## 📊 SCANNER LOGIC

**File:** `scripts/daily_signal_scanner.py`

**Process:**
1. Download 343 stocks with highest liquidity
2. For each stock:
   - Get 100 days historical data
   - Calculate EMA(20), EMA(50), RSI
   - Check Pullback conditions
   - Check EMA Cross conditions
3. Filter signals:
   - Must meet minimum strength (>60%)
   - Valid R/R ratio (>1.5)
   - RSI in valid range
4. Save to database
5. Mark priority signals

**Strategies:**

**PULLBACK:**
- Price near EMA(20)
- Uptrend confirmed
- RSI < 50
- Strong support level

**EMA CROSS:**
- EMA(20) crosses above EMA(50)
- Increasing volume
- RSI 40-60
- Momentum building

---

## 🎨 UI COMPONENTS

### Empty State (No Signals)
```
┌─────────────────────────────────────┐
│         [Clock Icon]                │
│                                     │
│    Chưa có tín hiệu nào            │
│                                     │
│    Hệ thống sẽ tự động quét        │
│    343 cổ phiếu có thanh khoản...  │
│                                     │
│  [Tạo tín hiệu mới (2-3 phút)]    │
└─────────────────────────────────────┘
```

### Scanning State
```
┌─────────────────────────────────────┐
│         [Spinner]                   │
│                                     │
│  Đang quét 343 cổ phiếu...        │
│  Đang phân tích thị trường...      │
│  (2-3 phút)                        │
└─────────────────────────────────────┘
```

### Success State
```
┌─────────────────────────────────────┐
│         [Checkmark]                 │
│                                     │
│  ✅ Đã tìm thấy 15 tín hiệu!       │
│                                     │
│  (Auto-redirecting...)             │
└─────────────────────────────────────┘
```

---

## ⚙️ CONFIGURATION

### Backend Environment Variables

```bash
# .env file (if using)
PORT=10000
SCANNER_TIMEOUT=300  # 5 minutes
MAX_STOCKS=343
```

### Frontend API URL

```javascript
// Already configured in SignalsModule.jsx
const API_URL = import.meta.env.PROD
  ? 'https://ai-advisor1-backend.onrender.com/api'
  : 'http://localhost:10000/api'
```

---

## 🐛 TROUBLESHOOTING

### Issue 1: Scanner not starting

**Check:**
```bash
# Verify scanner exists
ls C:\ai-advisor1\scripts\daily_signal_scanner.py

# Check backend logs
# (In Render.com dashboard)
```

**Fix:**
- Make sure scanner script path is correct in backend_api.py
- Check scanner has all required packages (vnstock, pandas, etc.)

### Issue 2: Scan takes too long

**Reasons:**
- Render free tier: Cold start + slow CPU
- Network: Downloading 343 stocks takes time
- Processing: EMA/RSI calculations

**Solutions:**
- Upgrade Render to paid tier ($7/month)
- Reduce stock count in scanner
- Optimize scanner code

### Issue 3: No signals generated

**Check:**
```bash
# Run scanner manually
cd C:\ai-advisor1\scripts
python daily_signal_scanner.py

# Check if signals were saved
# Open database
sqlite3 signals.db
SELECT COUNT(*) FROM signals;
```

**Possible causes:**
- Market conditions: No stocks meet criteria
- Scanner logic too strict
- API rate limits (vnstock)

### Issue 4: Frontend not updating

**Fix:**
```javascript
// Check browser console for errors
// Clear cache (Ctrl + Shift + Delete)
// Hard refresh (Ctrl + F5)

// Or force refresh in code:
setTimeout(() => {
  window.location.reload()
}, 2000)
```

---

## 📈 PERFORMANCE

### Expected Times (Render Free Tier)

- Cold start: 30-60 seconds
- Scanner execution: 2-3 minutes
- Total from click to signals: 3-4 minutes

### Expected Times (Render Paid Tier)

- Cold start: 0 seconds (always on)
- Scanner execution: 1-2 minutes
- Total: 1-2 minutes

### Optimization Tips

1. **Cache results:** Store signals for 24h
2. **Incremental updates:** Only scan new data
3. **Background jobs:** Run scanner on schedule
4. **Parallel processing:** Scan multiple stocks simultaneously

---

## 🚀 FUTURE ENHANCEMENTS

### Phase 2: Scheduled Scanning
```python
# Run scanner automatically every day at 9 AM
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_scanner, 'cron', hour=9, minute=0)
scheduler.start()
```

### Phase 3: Real-time Updates
```javascript
// Use WebSocket for live updates
const ws = new WebSocket('ws://api.ai-advisor.vn/signals')
ws.onmessage = (event) => {
  const newSignal = JSON.parse(event.data)
  updateSignals(newSignal)
}
```

### Phase 4: Custom Filters
```javascript
// Let users create custom scans
{
  "stock_type": "Blue Chip",
  "min_volume": 1000000,
  "rsi_range": [30, 50],
  "strategies": ["PULLBACK"]
}
```

---

## ✅ CHECKLIST

Before deploying:

- [ ] Backend has `/api/scan` endpoint
- [ ] Backend has `/api/scan/status` endpoint
- [ ] Scanner script exists and works
- [ ] Frontend has updated SignalsModule.jsx
- [ ] CSS for scan UI added to App.css
- [ ] Tested locally
- [ ] Deployed to production
- [ ] Verified on live site
- [ ] User can trigger scan
- [ ] Signals appear after scan

---

## 📞 SUPPORT

If issues persist:
1. Check backend logs in Render.com
2. Check frontend console (F12)
3. Verify API endpoints work (Postman/curl)
4. Check database has signals table
5. Run scanner manually to test

---

**READY TO DEPLOY! 🚀**
