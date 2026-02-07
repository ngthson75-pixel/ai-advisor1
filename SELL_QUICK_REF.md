# 🔴 SELL SIGNAL SYSTEM - QUICK REFERENCE

**Version:** 1.0 | **Date:** 2026-02-05

---

## ⚡ QUICK COMMANDS

### **Deploy Everything**

```powershell
cd C:\ai-advisor1

# Add all new files
git add sell_signal_scanner_v2.py backend_sell_api.py migration_add_sell_columns.py SELL_SIGNAL_SETUP.md SELL_QUICK_REF.md

# Copy workflow
Copy-Item hourly-sell-scanner.yml .github\workflows\

# Commit all
git add .
git commit -m "feat: Complete SELL signal system with hourly automation"
git push origin main

# Wait 5 minutes for Render deploy
```

---

### **Run Migration**

```powershell
# After backend deploys
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/migrate" -Method POST
```

---

### **Test Scan**

```powershell
# Trigger scan
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST

# Wait 10-15 minutes

# Check results
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status" | ConvertFrom-Json
```

---

## 📊 API ENDPOINTS

```
POST /api/scan-sell          - Trigger scanner
GET  /api/scan-sell/status   - Get status
GET  /api/signals/sell       - Get SELL signals

Status codes:
202 - Scanner started
200 - Success
500 - Error
```

---

## 🔧 TROUBLESHOOTING

### **No signals?**
```powershell
# Check BUY signals exist
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals | ConvertFrom-Json | Select -ExpandProperty count
```

### **Rate limit?**
```powershell
# Increase delay
$body = @{days=7; delay=3.0} | ConvertTo-Json
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST -Body $body -ContentType "application/json"
```

### **GitHub Actions failed?**
```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click failed workflow
3. Check logs for errors
4. Most common: Timeout (increase timeout-minutes)
```

---

## ⏱️ SCHEDULE

**Current:** Every hour at :05  
**Cron:** `5 * * * *`

**Change to every 2 hours:**
```yaml
schedule:
  - cron: '5 */2 * * *'
```

**Change to every 3 hours:**
```yaml
schedule:
  - cron: '5 */3 * * *'
```

---

## 🎯 BADGES (Frontend)

```jsx
// Stop Loss
<span className="badge badge-danger">🔴 SL</span>

// Take Profit
<span className="badge badge-success">🟢 TP</span>
```

---

## 📁 FILES

```
ai-advisor1/
├── sell_signal_scanner_v2.py           # Scanner
├── backend_sell_api.py                 # API routes
├── migration_add_sell_columns.py       # Migration
├── .github/workflows/
│   └── hourly-sell-scanner.yml         # Automation
├── SELL_SIGNAL_SETUP.md                # Full guide
└── SELL_QUICK_REF.md                   # This file
```

---

## ✅ CHECKLIST

Deployment:
- [ ] Pushed to GitHub
- [ ] Backend deployed (3-5 min)
- [ ] Migration run
- [ ] Test scan works
- [ ] GitHub Actions workflow active

Verification:
- [ ] Manual scan: 202 response
- [ ] Status endpoint: Returns counts
- [ ] Signals endpoint: Returns data
- [ ] Frontend: Badges display

---

## 📞 HELP

**Full guide:** `SELL_SIGNAL_SETUP.md`  
**Issues:** Check GitHub Actions logs  
**Contact:** ngthson75@gmail.com

---

**Last Updated:** 2026-02-05
