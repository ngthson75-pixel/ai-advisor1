# 🔧 FIX: SIGNALS NOT UPDATING ON WEBSITE

## 📊 VẤN ĐỀ

```
✅ Local scanner chạy thành công: 132 signals
❌ Website vẫn hiển thị signals cũ
❌ GitHub Actions "Daily Signal Scanner" không tạo signals mới
```

---

## 🎯 ROOT CAUSE

### **Local Scanner ≠ Backend Scanner**

```
Local Scanner (PowerShell):
  python daily_signal_scanner_eod.py
  → Lưu vào: C:\ai-advisor1\signals.db (SQLite)
  → ✓ 132 signals
  → ❌ Chỉ ở local, không lên server!

Backend Scanner (GitHub Actions → Render):
  GitHub Actions triggers: POST /api/scan
  → Backend nhận request
  → Backend scanner KHÔNG CHẠY hoặc FAIL
  → PostgreSQL không có signals mới
  → Website vẫn hiển thị old data
```

---

## ✅ SOLUTION - PUSH LOCAL SIGNALS LÊN PRODUCTION

### **Bước 1: Verify local signals**

```powershell
cd C:\ai-advisor1

# Check local database
sqlite3 signals.db "SELECT COUNT(*) FROM signals WHERE date='2026-02-01';"
# Should show: 132

# Or use Python
python -c "import sqlite3; conn=sqlite3.connect('signals.db'); print(conn.execute('SELECT COUNT(*) FROM signals WHERE date=\"2026-02-01\"').fetchone()[0])"
```

**Expected:** 132 signals

---

### **Bước 2: Run diagnostic**

```powershell
# Download diagnostic_backend_scanner.ps1 from chat
cd C:\ai-advisor1
.\diagnostic_backend_scanner.ps1
```

**What to check:**
- Production signals count
- Latest signal date
- If 0 signals or old date → Need to push

---

### **Bước 3: Push local signals**

```powershell
cd C:\ai-advisor1

# Download push_local_signals.py from chat
# Then run:

python push_local_signals.py

# Follow prompts:
# 1. Verify 132 signals found
# 2. Choose: 1 (Production) hoặc 3 (Both)
# 3. Confirm: y
# 4. Wait for completion
```

**Expected output:**
```
✓ Found 132 signals for 2026-02-01
  PULLBACK: 67
  EMA_CROSS: 65
  Priority: 25

🔄 Pushing to Production...
  1/132 ✓ GMC    EMA_CROSS    100%
  2/132 ✓ PGD    EMA_CROSS    100%
  ...
  132/132 ✓ ...

Results for Production:
  ✓ Success: 132
  ✗ Failed: 0

🔍 Verifying Production...
  ✓ Backend has 132 total signals

✅ PUSH COMPLETE!
```

---

### **Bước 4: Verify on website**

```powershell
# Clear browser cache
# Ctrl + Shift + R

# Visit website
# https://ai-advisor.vn
# Tab: "Tín hiệu mua"
```

**Should see:**
- 132 signals
- Date: 2026-02-01
- Top signals: GMC, PGD, VSM, CTG, VIM

---

## 🔍 VERIFY BACKEND

### **Check Production API:**

```powershell
# Get signals
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals -UseBasicParsing | Select-Object -Expand Content | ConvertFrom-Json

# Should see:
# {
#   "count": 132,
#   "signals": [
#     {"ticker": "GMC", "strategy": "EMA_CROSS", "strength": 100, ...},
#     ...
#   ]
# }
```

---

## 🐛 TROUBLESHOOTING

### **Issue 1: "signals.db not found"**

```powershell
# Make sure you're in project root
cd C:\ai-advisor1

# Check file exists
Test-Path signals.db
# Should be: True

# If False, run scanner first:
cd scripts
python daily_signal_scanner_eod.py
```

---

### **Issue 2: "API returns 404 or 500"**

**Backend API endpoint might not exist!**

```powershell
# Check if /api/signals endpoint exists
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals -UseBasicParsing

# If 404:
# → Backend doesn't have /api/signals endpoint
# → Need to update backend_api.py
```

**Fix:**
```python
# backend_api.py should have:
@app.route('/api/signals', methods=['POST'])
def create_signal():
    # Accept signal from push script
    data = request.json
    # Save to PostgreSQL
    # Return success
```

---

### **Issue 3: "Push succeeds but website still old"**

**Frontend might be using wrong API URL or cache:**

```powershell
# Check frontend API URL
cd C:\ai-advisor1\frontend\src\components

# Search for API_URL
Select-String -Path *.jsx -Pattern "API_URL|api/signals"

# Should point to:
# Production: https://ai-advisor1-backend.onrender.com/api
```

**Fix:**
```javascript
// In SignalsModule.jsx or LandingPage.jsx
const API_URL = 'https://ai-advisor1-backend.onrender.com/api';

// Fetch signals
fetch(`${API_URL}/signals`)
```

---

### **Issue 4: "Cannot push - module not found"**

```powershell
# Install required modules
pip install requests sqlite3 --break-system-packages
```

---

## 🔧 LONG-TERM FIX - FIX BACKEND SCANNER

**Why backend scanner doesn't work:**

1. **Scanner script not on Render**
   - File: `scripts/daily_signal_scanner_eod.py`
   - Not included in git or not deployed

2. **Backend /api/scan doesn't call scanner**
   - Endpoint exists but doesn't trigger script

3. **Render free tier timeout (15 min)**
   - Scanner needs 25-30 min
   - Free tier kills after 15 min

**Solutions:**

### **Fix 1: Deploy scanner script**

```powershell
cd C:\ai-advisor1

# Make sure scripts/ folder is in git
git add scripts/daily_signal_scanner_eod.py
git commit -m "feat: Add scanner script for backend"
git push origin main
```

### **Fix 2: Update backend /api/scan**

```python
# backend_api.py
@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger signal scanner"""
    
    # Run scanner in background
    subprocess.Popen([
        'python3', 
        'scripts/daily_signal_scanner_eod.py'
    ])
    
    return {'status': 'started'}, 202
```

### **Fix 3: Upgrade Render tier**

```
Render Starter: $7/month
- No timeout
- Always-on
- Faster CPU

→ Scanner can complete in 25-30 min
```

---

## 📋 CHECKLIST

**After push:**
- [ ] Run diagnostic script
- [ ] Verify backend has 132 signals
- [ ] Clear browser cache
- [ ] Visit website
- [ ] Check "Tín hiệu mua" tab
- [ ] Verify date: 2026-02-01
- [ ] Verify signals match local (GMC, PGD, etc.)

**Daily workflow (until backend fixed):**
- [ ] Run local scanner (PowerShell)
- [ ] Push signals to production
- [ ] Verify on website

---

## 🎯 QUICK COMMANDS

```powershell
# Complete workflow:
cd C:\ai-advisor1

# 1. Run scanner
cd scripts
python daily_signal_scanner_eod.py
cd ..

# 2. Push signals
python push_local_signals.py
# Choose: 1 (Production)
# Confirm: y

# 3. Verify
.\diagnostic_backend_scanner.ps1

# 4. Check website
# Visit: https://ai-advisor.vn
# Ctrl + Shift + R (hard refresh)
```

---

## 📞 SUPPORT

**If still not working:**

1. **Check Render logs:**
   - https://dashboard.render.com
   - Service: ai-advisor1-backend
   - Logs tab
   - Look for errors in /api/scan

2. **Check frontend console:**
   - F12 → Console
   - Look for API errors
   - Verify API URL

3. **Verify database:**
   - Render dashboard → PostgreSQL
   - Check signals table
   - Should have 132 rows

---

**TL;DR:**

```powershell
# Quick fix (5 phút):
cd C:\ai-advisor1
python push_local_signals.py
# Choose: 1
# Confirm: y
# Wait → Done!
# Visit: https://ai-advisor.vn
# Ctrl + Shift + R
```

**DONE!** 🎉
