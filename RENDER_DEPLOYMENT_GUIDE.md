# 🚀 DEPLOY BACKEND API TO RENDER - COMPLETE GUIDE

**Full-featured backend with signal management, admin panel, and database**

---

## 📋 FILES OVERVIEW

### **New Backend (Complete):**

```
backend_api.py - Full-featured Flask API
├── SQLite database
├── Admin panel (/admin)
├── REST API endpoints
├── Signal management
└── Scan history tracking
```

### **Old Backend (Simple):**

```
admin_api_simple.py - Basic admin API
└── Only admin user management
```

**→ Replace with backend_api.py!**

---

## 🎯 WHAT'S NEW

### **Features:**

```
✅ SQLite database for signal storage
✅ Admin panel (web interface)
✅ REST API endpoints (GET, POST, DELETE)
✅ Signal management (add, update, delete)
✅ Scan history tracking
✅ CORS enabled for frontend
✅ Auto-init database
✅ Bulk signal upload
```

### **Endpoints:**

```
Public:
GET  /                    - API info
GET  /health              - Health check
GET  /api/signals         - Get all signals
GET  /api/signals/:ticker - Get signal detail
GET  /api/signals/summary - Get summary stats
GET  /api/scan-history    - Get scan history

Admin:
GET  /admin               - Admin panel (web UI)
POST /api/admin/signals   - Add single signal
POST /api/admin/signals/bulk - Add multiple signals
DELETE /api/admin/signals/:id - Delete signal
```

---

## 🚀 DEPLOYMENT STEPS

### **Step 1: Update GitHub Repository**

```bash
cd C:\ai-advisor1

# Add new backend file
git add backend_api.py

# Remove old file (optional)
git rm admin_api_simple.py

# Update requirements.txt
# Make sure it has:
```

**requirements.txt:**

```txt
flask==3.0.0
flask-cors==4.0.0
vnstock==3.3.0
pandas==2.1.4
numpy==1.26.2
requests==2.31.0
```

```bash
# Commit
git add requirements.txt
git commit -m "Add complete backend API with admin panel"

# Push
git push origin main
```

---

### **Step 2: Update Render Configuration**

#### **Option A: Via Render Dashboard (RECOMMENDED)**

```
1. Go to: https://dashboard.render.com
2. Find service: ai-advisor1-backend
3. Click service → Settings
4. Update Start Command:
   
   OLD: gunicorn admin_api_simple:app
   NEW: gunicorn backend_api:app
   
5. Save Changes
6. Service will auto-redeploy
```

#### **Option B: Via render.yaml** 

Update render.yaml in repo:

```yaml
services:
  - type: web
    name: ai-advisor1-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn backend_api:app  # ← Changed!
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

---

### **Step 3: Verify Deployment**

After deploy completes (~5 minutes):

```bash
# Test health endpoint
curl https://ai-advisor1-backend.onrender.com/health

# Should return:
{
  "status": "healthy",
  "timestamp": "2025-12-20T...",
  "database": "connected"
}
```

---

### **Step 4: Access Admin Panel**

```
URL: https://ai-advisor1-backend.onrender.com/admin

Features:
✅ View all active signals
✅ Stats dashboard
✅ Delete signals
✅ Auto-refresh every 5 minutes
```

---

## 📊 UPLOAD SIGNALS TO BACKEND

### **Step 1: Run Scanner**

```bash
cd C:\ai-advisor1\scripts
python run_daily_scanner.py

# Output:
signals/signals_latest.json
```

### **Step 2: Upload to Backend**

```bash
python upload_signals.py

# Expected output:
======================================
UPLOAD SIGNALS TO BACKEND
======================================
Backend: https://ai-advisor1-backend.onrender.com
File: signals/signals_latest.json

✅ Loaded signals:
   PULLBACK: 12
   EMA_CROSS: 5

Testing backend connectivity...
✅ Backend is online
   Status: healthy
   Database: connected

Uploading to .../api/admin/signals/bulk...
✅ Upload successful!
   Added: 17 signals
   Message: Added 17 signals successfully

Verifying upload...
✅ Backend verification:
   Total signals: 17
   PULLBACK: 12
   EMA_CROSS: 5

======================================
✅ UPLOAD COMPLETE!
======================================
Admin Panel: https://ai-advisor1-backend.onrender.com/admin
======================================
```

---

## 🔄 DAILY WORKFLOW

### **Automated:**

```
3:45 PM - Scanner runs (Task Scheduler)
4:15 PM - Signals generated
4:16 PM - Auto-upload to backend
4:17 PM - Backend updated
4:18 PM - Admin panel shows new signals
4:20 PM - Frontend fetches from backend
```

### **Script Integration:**

Add to `run_daily_scanner.py` at end of `main()`:

```python
# After save_signals()
try:
    import subprocess
    result = subprocess.run(['python', 'upload_signals.py'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Uploaded to backend")
    else:
        print("⚠️ Upload failed")
        print(result.stderr)
except Exception as e:
    print(f"⚠️ Could not upload: {e}")
```

---

## 🔌 FRONTEND INTEGRATION

### **Update Frontend to Use Backend API:**

```javascript
// In frontend config
const API_BASE_URL = 'https://ai-advisor1-backend.onrender.com/api';

// Fetch signals
const fetchSignals = async () => {
  const response = await fetch(`${API_BASE_URL}/signals`);
  const data = await response.json();
  
  if (data.success) {
    setPullbackSignals(data.signals.filter(s => s.strategy === 'PULLBACK'));
    setEmaCrossSignals(data.signals.filter(s => s.strategy === 'EMA_CROSS'));
  }
};

// Fetch summary
const fetchSummary = async () => {
  const response = await fetch(`${API_BASE_URL}/signals/summary`);
  const data = await response.json();
  
  if (data.success) {
    setSummary(data.summary);
  }
};

// Auto-refresh every 5 minutes
useEffect(() => {
  fetchSignals();
  fetchSummary();
  
  const interval = setInterval(() => {
    fetchSignals();
    fetchSummary();
  }, 5 * 60 * 1000);
  
  return () => clearInterval(interval);
}, []);
```

---

## 📱 API USAGE EXAMPLES

### **Get All Signals:**

```bash
curl https://ai-advisor1-backend.onrender.com/api/signals
```

Response:

```json
{
  "success": true,
  "count": 17,
  "signals": [
    {
      "id": 1,
      "ticker": "TCH",
      "strategy": "PULLBACK",
      "entry_price": 12500,
      "stop_loss": 11800,
      "take_profit": 13800,
      "risk_reward": 1.86,
      "strength": 100,
      "stock_type": "Penny",
      "is_priority": 1,
      "date": "2025-12-20",
      ...
    }
  ]
}
```

### **Filter by Strategy:**

```bash
curl "https://ai-advisor1-backend.onrender.com/api/signals?strategy=pullback&limit=10"
```

### **Get Signal Detail:**

```bash
curl https://ai-advisor1-backend.onrender.com/api/signals/TCH
```

### **Get Summary:**

```bash
curl https://ai-advisor1-backend.onrender.com/api/signals/summary
```

---

## 🗄️ DATABASE

### **SQLite Database (Auto-created):**

```
signals.db
├── signals table        - All trading signals
├── scan_history table   - Scan logs
└── admin_users table    - Admin accounts
```

### **Persistent Storage on Render:**

Render free tier:
- ✅ Database persists during service lifetime
- ⚠️ May reset if service inactive >15 min
- ⚠️ May lose data on redeploy

**Solution for production:**
- Upgrade to paid Render plan
- Or use external database (PostgreSQL, MongoDB)

---

## 🔧 TROUBLESHOOTING

### **Issue 1: "Module not found"**

```bash
# Check requirements.txt includes:
flask==3.0.0
flask-cors==4.0.0
```

### **Issue 2: "Database locked"**

```python
# SQLite limitation on Render
# Solution: Upgrade to PostgreSQL for production
```

### **Issue 3: "Service won't start"**

```bash
# Check Render logs:
1. Go to service dashboard
2. Click "Logs" tab
3. Look for errors

# Common issues:
- Wrong Start Command
- Missing dependencies
- Python version mismatch
```

### **Issue 4: "CORS errors"**

```python
# Already handled with:
from flask_cors import CORS
CORS(app)

# If issues persist, specify origins:
CORS(app, origins=['https://your-frontend.netlify.app'])
```

---

## 📊 MONITORING

### **Health Check:**

```bash
# Automated monitoring
curl https://ai-advisor1-backend.onrender.com/health

# Response should be:
{
  "status": "healthy",
  "timestamp": "...",
  "database": "connected"
}
```

### **Admin Panel:**

```
URL: https://ai-advisor1-backend.onrender.com/admin

Check daily:
- Total signals count
- Last scan time
- Signal quality
```

---

## 🎯 NEXT STEPS

### **Immediate (Today):**

```
1. ✅ Deploy backend_api.py to Render
2. ✅ Test /health endpoint
3. ✅ Access /admin panel
4. ✅ Run scanner + upload
5. ✅ Verify signals in admin panel
```

### **This Week:**

```
1. ✅ Integrate frontend with backend API
2. ✅ Setup automated upload in scanner
3. ✅ Monitor daily scans
4. ✅ Test signal accuracy
```

### **Next Week:**

```
1. ✅ Optimize database queries
2. ✅ Add authentication for admin
3. ✅ Setup email notifications
4. ✅ Consider paid Render plan
```

---

## ✅ CHECKLIST

**Deployment:**

- [ ] Update GitHub with backend_api.py
- [ ] Update Start Command in Render
- [ ] Verify deployment successful
- [ ] Test /health endpoint
- [ ] Access /admin panel

**Signals:**

- [ ] Run daily scanner
- [ ] Upload signals to backend
- [ ] Verify in admin panel
- [ ] Check frontend integration

**Monitoring:**

- [ ] Setup daily health checks
- [ ] Monitor admin panel
- [ ] Check Render logs
- [ ] Verify auto-refresh working

---

## 📞 SUPPORT

**Render Dashboard:**  
https://dashboard.render.com

**Admin Panel:**  
https://ai-advisor1-backend.onrender.com/admin

**API Docs:**  
https://ai-advisor1-backend.onrender.com/

**Owner:**  
Nguyễn Thanh Sơn  
Email: ngthson75@gmail.com

---

**DEPLOY BÂY GIỜ! 🚀**

**UPDATE START COMMAND → REDEPLOY → ACCESS /admin! ⚡**

*Guide Version: 1.0*  
*Last Updated: December 20, 2025*
