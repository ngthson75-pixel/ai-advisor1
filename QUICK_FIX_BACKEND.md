# ⚡ QUICK FIX - ADD BACKEND ENDPOINTS

## 📥 FILE TO ADD

Download: `backend_endpoints_to_add.py` ⬆️

Contains 2 endpoints:
- `POST /api/scan` - Trigger scanner
- `GET /api/scan/status` - Check status

---

## 🚀 DEPLOYMENT (5 PHÚT)

### **STEP 1: Open backend_api.py**

```powershell
cd C:\ai-advisor1
notepad backend_api.py
```

---

### **STEP 2: Add imports (if not exist)**

At top of file, add:

```python
import subprocess
import os
from datetime import datetime
import sqlite3
```

---

### **STEP 3: Add endpoints**

Copy code from `backend_endpoints_to_add.py` ⬆️

Paste anywhere in `backend_api.py` (before `if __name__ == '__main__'`)

---

### **STEP 4: Test local**

```powershell
# Terminal 1: Run backend
cd C:\ai-advisor1
python backend_api.py

# Terminal 2: Test endpoint
Invoke-WebRequest -Uri "http://localhost:10000/api/scan" -Method POST -UseBasicParsing

# Should see: {"status":"scanning",...}
```

---

### **STEP 5: Deploy to staging**

```powershell
git checkout staging
git add backend_api.py
git commit -m "Add: /api/scan and /api/scan/status endpoints"
git push origin staging
```

---

### **STEP 6: Wait for Render**

```
1. https://dashboard.render.com
2. ai-advisor1-staging
3. Wait 5-10 min
4. Status: Live ✅
```

---

### **STEP 7: Test staging**

```powershell
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/scan" -Method POST -UseBasicParsing

# Should return 202
```

---

### **STEP 8: Re-run workflow**

```
GitHub Actions → Daily EOD Signal Scanner → Re-run jobs
```

---

## ✅ SUCCESS CRITERIA

- [ ] Imports added to backend_api.py
- [ ] 2 endpoints added to backend_api.py
- [ ] Local test passes
- [ ] Pushed to staging
- [ ] Render deployed (Live status)
- [ ] Staging endpoint test passes
- [ ] Workflow re-run succeeds ✅

---

## 🎯 EXPECTED RESULT

**Before:**
```
POST /api/scan → 404 Not Found ❌
Workflow fails
```

**After:**
```
POST /api/scan → 202 Accepted ✅
Scanner starts
Workflow succeeds ✅
```

---

**Time:** 5 phút  
**Difficulty:** Easy (copy-paste)  
**Result:** Workflow will work! 🚀
