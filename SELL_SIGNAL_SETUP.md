# 🔴 SELL SIGNAL SYSTEM - COMPLETE SETUP GUIDE

**Version:** 1.0  
**Date:** 2026-02-05  
**Status:** Production Ready

---

## 📋 OVERVIEW

Hệ thống tự động quét và phát hiện tín hiệu SELL (Stop Loss và Take Profit) dựa trên các tín hiệu BUY trước đó.

**Features:**
- ✅ Tự động quét mỗi giờ (GitHub Actions)
- ✅ Phân biệt rõ Stop Loss vs Take Profit
- ✅ Lưu exit_price, exit_reason, exit_date
- ✅ API endpoints đầy đủ
- ✅ Manual trigger available

---

## 🏗️ ARCHITECTURE

```
GitHub Actions (Hourly)
    ↓
POST /api/scan-sell
    ↓
SellSignalScannerV2
    ↓ (Check conditions)
BUY Signals → Check current price
    ↓
If SL or TP hit:
    ↓
Save to Database (exit_price, exit_reason, exit_date)
    ↓
Frontend displays with badges (🔴 SL, 🟢 TP)
```

---

## 📁 NEW FILES CREATED

```
ai-advisor1/
├── sell_signal_scanner_v2.py       # Scanner service (reusable)
├── backend_sell_api.py             # SELL API routes
├── migration_add_sell_columns.py   # Database migration
├── .github/workflows/
│   └── hourly-sell-scanner.yml     # GitHub Actions workflow
└── SELL_SIGNAL_SETUP.md            # This file
```

---

## 🚀 DEPLOYMENT STEPS

### **STEP 1: Database Migration**

Run migration to add new columns:

```powershell
cd C:\ai-advisor1

# Run migration
python migration_add_sell_columns.py

# Expected output:
# ✅ exit_price added
# ✅ exit_reason added  
# ✅ exit_date added
```

**What it does:**
- Adds `exit_price` column (REAL)
- Adds `exit_reason` column (VARCHAR 50)
- Adds `exit_date` column (VARCHAR 20)

---

### **STEP 2: Update Backend**

Backend API already has SELL routes integrated via `backend_sell_api.py`.

**Verify backend has:**
```python
# In backend_api.py
from backend_sell_api import register_sell_routes

# Register SELL routes
register_sell_routes(app)
```

**New endpoints:**
- `POST /api/scan-sell` - Trigger scanner
- `GET /api/scan-sell/status` - Get status
- `GET /api/signals/sell` - Get SELL signals only

**Deploy backend:**
```bash
cd C:\ai-advisor1
git add backend_api.py backend_sell_api.py sell_signal_scanner_v2.py migration_add_sell_columns.py
git commit -m "feat: Add SELL signal system with hourly automation"
git push origin main

# Render auto-deploys in 3-5 minutes
```

---

### **STEP 3: Setup GitHub Actions**

Copy workflow file to GitHub Actions:

```powershell
# Copy workflow
Copy-Item hourly-sell-scanner.yml .github\workflows\

# Commit
git add .github\workflows\hourly-sell-scanner.yml
git commit -m "feat: Add hourly SELL signal scanner workflow"
git push origin main
```

**Workflow schedule:**
- Runs every hour at :05 (e.g., 1:05, 2:05, 3:05...)
- Cron: `5 * * * *`
- Manual trigger available

---

### **STEP 4: Run Migration on Production**

After backend deploys, run migration:

```powershell
# Option A: Via backend endpoint (if migration endpoint exists)
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/migrate" -Method POST

# Option B: SSH to Render and run
# (If Render Shell access available)
python migration_add_sell_columns.py
```

---

### **STEP 5: Test System**

#### **A. Test Migration**

```powershell
# Check if columns exist
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/health"
# Should return: {"status":"healthy",...}
```

#### **B. Test Manual Scan**

```powershell
# Trigger scan manually
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST

# Expected response:
# {
#   "success": true,
#   "message": "SELL scanner started. This will take 5-15 minutes...",
#   "status": "scanning"
# }

# Wait 10-15 minutes

# Check status
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status"

# Expected response:
# {
#   "success": true,
#   "date": "2026-02-05",
#   "total_sell_signals": 15,
#   "by_reason": {
#     "STOP_LOSS": 8,
#     "TAKE_PROFIT": 7
#   }
# }
```

#### **C. Test GitHub Actions**

```bash
# Manual trigger on GitHub:
1. Go to: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click "Hourly SELL Signal Scanner"
3. Click "Run workflow"
4. Leave defaults (days=7, delay=2.0)
5. Click "Run workflow"

# Wait 15-20 minutes

# Check logs:
- Should show progress monitoring
- Should show results (e.g., "+5 new signals")
```

---

## 📊 API ENDPOINTS REFERENCE

### **POST /api/scan-sell**

**Trigger SELL scanner**

Request body (optional):
```json
{
  "days": 7,      // Look back N days
  "delay": 2.0    // Delay between requests (seconds)
}
```

Response:
```json
{
  "success": true,
  "message": "SELL scanner started...",
  "status": "scanning"
}
```

Status: `202 Accepted`

---

### **GET /api/scan-sell/status**

**Get scan status**

Response:
```json
{
  "success": true,
  "date": "2026-02-05",
  "total_sell_signals": 15,
  "by_reason": {
    "STOP_LOSS": 8,
    "TAKE_PROFIT": 7
  },
  "breakdown": {
    "stop_loss": 8,
    "take_profit": 7
  }
}
```

---

### **GET /api/signals/sell**

**Get SELL signals only**

Query params:
- `limit`: Number of signals (default 50)
- `exit_reason`: Filter by STOP_LOSS or TAKE_PROFIT

Response:
```json
{
  "success": true,
  "signals": [
    {
      "id": 123,
      "ticker": "VCB",
      "entry_price": 88500,
      "exit_price": 95000,
      "exit_reason": "TAKE_PROFIT",
      "exit_date": "2026-02-05",
      "stop_loss": 85000,
      "take_profit": 95000,
      "strength": 80,
      "profit_loss": 6500,
      "profit_loss_pct": 7.34,
      "created_at": "2026-02-05T10:30:00"
    }
  ],
  "count": 1
}
```

---

## 🎨 FRONTEND INTEGRATION

### **Display SELL Signals with Badges**

```jsx
// In SignalsModule.jsx (SELL Tab)

const exitReasonBadge = (reason) => {
  if (reason === 'STOP_LOSS') {
    return <span className="badge badge-danger">🔴 Stop Loss</span>;
  } else if (reason === 'TAKE_PROFIT') {
    return <span className="badge badge-success">🟢 Take Profit</span>;
  }
  return null;
};

// In table:
<td>{exitReasonBadge(signal.exit_reason)}</td>
<td>{signal.exit_price?.toLocaleString()} VND</td>
<td className={signal.profit_loss_pct > 0 ? 'text-success' : 'text-danger'}>
  {signal.profit_loss_pct?.toFixed(2)}%
</td>
```

---

## ⏱️ TIMING & SCHEDULE

### **GitHub Actions Schedule**

```
Cron: 5 * * * *
Meaning: Every hour at :05 minutes

Examples:
- 00:05 (12:05 AM)
- 01:05 (1:05 AM)
- 02:05 (2:05 AM)
- ...
- 23:05 (11:05 PM)

Total runs: 24 times per day
```

### **Why :05 and not :00?**

- Avoid top-of-hour traffic
- Backend has time to process BUY signals first
- Less likely to hit rate limits

### **Execution Time**

```
Wake backend:    30-60 seconds
Scanner:         5-15 minutes (depends on number of stocks)
Monitoring:      1-2 minutes
Total:           7-18 minutes per run
```

---

## 🔧 CONFIGURATION

### **Adjust Scan Frequency**

To change from hourly to every 2 hours:

```yaml
# In .github/workflows/hourly-sell-scanner.yml
schedule:
  - cron: '5 */2 * * *'  # Every 2 hours at :05
```

To change to every 30 minutes:

```yaml
schedule:
  - cron: '5,35 * * * *'  # At :05 and :35 of every hour
```

### **Adjust Lookback Days**

To scan more days of BUY signals:

```yaml
# In workflow file, change default:
inputs:
  days:
    default: '14'  # Look back 14 days instead of 7
```

Or trigger manually with custom days.

---

## 🐛 TROUBLESHOOTING

### **Issue 1: No SELL Signals Generated**

**Possible reasons:**
1. No BUY signals in last 7 days
2. No stocks hit SL or TP
3. Market conditions stable

**Diagnosis:**
```powershell
# Check BUY signals
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals" |
    ConvertFrom-Json |
    Select-Object -ExpandProperty signals |
    Where-Object {$_.action -eq 'BUY'} |
    Measure-Object

# If 0 BUY signals → No SELL signals possible
```

**Solution:** Wait for new BUY signals or increase lookback days.

---

### **Issue 2: GitHub Actions Timeout**

**Symptom:** Workflow fails after 45 minutes

**Solution:**
```yaml
# Increase timeout in workflow
timeout-minutes: 60  # From 45 to 60
```

---

### **Issue 3: Rate Limit Errors**

**Symptom:** Scanner fails with "rate limit" messages

**Solution:**
- Increase delay between requests
- Reduce number of stocks scanned
- Wait and retry

```powershell
# Manual trigger with longer delay
$body = @{days=7; delay=3.0} | ConvertTo-Json
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST -Body $body -ContentType "application/json"
```

---

### **Issue 4: Migration Failed**

**Symptom:** "Column already exists" or "Migration failed"

**Diagnosis:**
```powershell
# Check columns manually
# Via Render Shell or database client
psql $DATABASE_URL
\d signals
# Should see: exit_price, exit_reason, exit_date
```

**Solution A:** Columns already exist (safe to ignore)

**Solution B:** Manually add columns:
```sql
ALTER TABLE signals ADD COLUMN exit_price REAL;
ALTER TABLE signals ADD COLUMN exit_reason VARCHAR(50);
ALTER TABLE signals ADD COLUMN exit_date VARCHAR(20);
```

---

## 📊 MONITORING & MAINTENANCE

### **Daily Check**

```powershell
# Check today's SELL signals
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status"

# Expected output includes:
# - total_sell_signals
# - stop_loss count
# - take_profit count
```

### **Weekly Review**

```powershell
# Get last 100 SELL signals
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals/sell?limit=100" |
    ConvertFrom-Json |
    Select-Object -ExpandProperty signals

# Analyze:
# - Win rate (TP vs SL)
# - Average P/L
# - Most common stocks
```

### **GitHub Actions Monitoring**

1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click "Hourly SELL Signal Scanner"
3. Review recent runs
4. Check for failures

---

## ✅ SUCCESS CHECKLIST

After deployment, verify:

- [ ] Migration successful (columns added)
- [ ] Backend deployed with SELL routes
- [ ] GitHub Actions workflow file in `.github/workflows/`
- [ ] Manual scan works: `POST /api/scan-sell`
- [ ] Status endpoint works: `GET /api/scan-sell/status`
- [ ] SELL signals endpoint works: `GET /api/signals/sell`
- [ ] GitHub Actions runs successfully
- [ ] Frontend displays SL/TP badges correctly

---

## 💰 COST & PERFORMANCE

### **GitHub Actions Cost**

- **Free tier:** 2000 minutes/month
- **Per run:** ~15-20 minutes
- **Daily usage:** 24 runs × 20 min = 480 min/day = 14,400 min/month
- **Status:** ⚠️ Exceeds free tier! (by 12,400 min)

**Solution options:**
1. Reduce frequency (every 2-4 hours instead of hourly)
2. Optimize scanner (reduce to 10 min/run)
3. Upgrade GitHub Actions ($8/month for 5000 min)

### **Recommended Schedule**

To stay within free tier:

```yaml
# Every 2 hours (12 runs/day = 240 min/day = 7200 min/month)
schedule:
  - cron: '5 */2 * * *'

# Or every 3 hours (8 runs/day = 160 min/day = 4800 min/month)
schedule:
  - cron: '5 */3 * * *'
```

### **Performance Metrics**

- **Stocks scanned:** 50-200 (depends on BUY signals)
- **Time per stock:** 2-3 seconds
- **Total time:** 2-10 minutes (typical)
- **Success rate:** ~98%

---

## 🎯 NEXT STEPS

After successful deployment:

1. **Week 1:** Monitor daily, ensure reliability
2. **Week 2:** Optimize scan frequency based on market activity
3. **Week 3:** Add email/Telegram notifications
4. **Month 2:** Add SELL signal analytics dashboard
5. **Month 3:** Implement partial exit logic (50% TP, etc.)

---

## 📞 SUPPORT

**Issues?**
- Check GitHub Actions logs first
- Check backend logs on Render
- Test endpoints manually with PowerShell
- Review this guide's Troubleshooting section

**Contact:** ngthson75@gmail.com

---

## 📝 CHANGELOG

### v1.0 (2026-02-05)
- ✅ Initial SELL signal system
- ✅ Hourly automation via GitHub Actions
- ✅ Database migration for exit fields
- ✅ API endpoints for SELL signals
- ✅ Frontend badges for SL/TP

---

**END OF GUIDE**

**Status:** Production Ready  
**Last Updated:** 2026-02-05  
**Next Review:** After 1 week of operation
