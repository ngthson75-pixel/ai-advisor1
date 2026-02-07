# 🔧 DATABASE SETUP - PRODUCTION & STAGING

**Version:** 1.0  
**Date:** 2026-02-05  
**Architecture:** Render PostgreSQL (Production) + Supabase (Staging)

---

## 📋 ARCHITECTURE OVERVIEW

```
PRODUCTION (ai-advisor.vn)
├── Backend: Render Starter ($7/month)
├── Database: Render PostgreSQL ($7/month) ✅
└── Frontend: Cloudflare Pages (Free)

STAGING (staging.ai-advisor.vn)
├── Backend: Render Free (sleeps after 15min)
├── Database: Supabase (Free) ✅
└── Frontend: Cloudflare Pages (Free)
```

**CRITICAL:**
- ✅ Production = Render PostgreSQL
- ✅ Staging = Supabase PostgreSQL
- ❌ NEVER mix these two!

---

## 🎯 PRODUCTION DATABASE (RENDER POSTGRESQL)

### **Current Production DATABASE_URL:**

```bash
# From backend_api.py and test_sell_scanner_manual.py:
DATABASE_URL=postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5
```

**This is already configured on Render!**

### **How to Get Production DATABASE_URL:**

#### **Option A: From Render Dashboard**

1. Visit: https://dashboard.render.com
2. Select **ai-advisor1-backend** (production service)
3. Click **Environment** tab
4. Look for: `DATABASE_URL`
5. Copy the value

#### **Option B: From Project Files**

Production DATABASE_URL is already in:
- `backend_api.py` (as environment variable)
- `test_sell_scanner_manual.py` (hardcoded as DEFAULT)

**Just copy from test_sell_scanner_manual.py:**
```python
DEFAULT_DATABASE_URL = "postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5"
```

### **Verify Production Database:**

```powershell
# Set in .env
$env:DATABASE_URL = "postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5"

# Test connection
python verify_sell_columns.py

# Expected:
# ✅ PRODUCTION PostgreSQL: postgresql://ai_advisor_user...
# 📊 Total columns: 20 (or 21+)
```

---

## 🧪 STAGING DATABASE (SUPABASE)

### **How to Get Staging DATABASE_URL:**

1. Visit: https://supabase.com/dashboard
2. Select your project
3. Click **Settings** → **Database**
4. Scroll to **Connection string**
5. Select **URI** tab
6. Copy connection string

**Format:**
```
postgresql://postgres.[project-id]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

### **Staging Usage:**

**Only use Supabase for:**
- ✅ Testing new features before production
- ✅ Staging branch deploys
- ✅ Internal team testing

**Never use Supabase for:**
- ❌ Production users
- ❌ Live signal generation
- ❌ Main branch deploys

---

## 🔧 LOCAL DEVELOPMENT SETUP

### **STEP 1: Update .env File**

```powershell
cd C:\ai-advisor1

# Create .env if not exists
if (-not (Test-Path .env)) {
    Copy-Item _env.example .env
}

# Edit .env
notepad .env
```

**Add to .env:**

```bash
# PRODUCTION DATABASE (Render PostgreSQL)
DATABASE_URL=postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5

# For staging testing, you can temporarily switch to:
# DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

---

### **STEP 2: Verify Connection**

```powershell
cd C:\ai-advisor1

# Run verify script
python verify_sell_columns.py
```

**Expected output:**

```
======================================================================
🔍 DATABASE COLUMN VERIFICATION
======================================================================
✅ PRODUCTION PostgreSQL: postgresql://ai_advisor_user...

📊 Total columns: 21

🔍 Checking SELL signal columns:
   ✅ exit_price      (double precision)
   ✅ exit_reason     (text)
   ✅ exit_date       (text)

======================================================================
✅ ALL REQUIRED COLUMNS PRESENT!
======================================================================
```

**If columns missing:**

```powershell
# Run migration
python migration_add_sell_columns.py

# Expected:
# ✅ PRODUCTION PostgreSQL: postgresql://ai_advisor_user...
# ✅ exit_price added
# ✅ exit_reason added
# ✅ exit_date added
```

---

### **STEP 3: Test SELL Scanner**

```powershell
cd C:\ai-advisor1

# Test with production database
python test_sell_scanner_manual.py

# Choose option 1 (test 10 tickers)
```

**Expected output:**

```
======================================================================
🧪 SELL SCANNER - TEST MODE
======================================================================
✅ Scanner using PRODUCTION database: postgresql://ai_advisor_user...

Select test mode:
1. Test 10 tickers (fast - 30 seconds)
2. Test all BUY signals (slow - 5-15 minutes)

Your choice: 1

[Running scan...]

======================================================================
📊 RESULTS: 5 SELL signals found
======================================================================
💾 SAVING TO DATABASE
======================================================================
  ✅ VCB (TAKE_PROFIT)
  ✅ HPG (STOP_LOSS)
  ✅ MBB (TAKE_PROFIT)
  ...

🎉 Saved 5 signals to PRODUCTION database!
```

---

## 🚀 RENDER ENVIRONMENT SETUP

### **Production Backend Already Has DATABASE_URL**

The production backend on Render (`ai-advisor1-backend`) already has DATABASE_URL configured.

**To verify:**

1. Go to: https://dashboard.render.com
2. Select `ai-advisor1-backend`
3. Click **Environment** tab
4. Verify `DATABASE_URL` exists

**If missing (unlikely):**

1. Click **Add Environment Variable**
2. Key: `DATABASE_URL`
3. Value: `postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5`
4. Click **Save Changes**
5. Wait for redeploy (3-5 min)

---

## 📊 VERIFY PRODUCTION DEPLOYMENT

After backend redeploys:

```powershell
# 1. Health check
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/health"

# 2. Trigger SELL scan
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST

# Expected:
# {
#   "success": true,
#   "message": "SELL scanner started...",
#   "status": "scanning"
# }

# 3. Wait 10-15 minutes

# 4. Check results
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status"

# Expected:
# {
#   "success": true,
#   "total_sell_signals": 10,
#   "by_reason": {
#     "STOP_LOSS": 5,
#     "TAKE_PROFIT": 5
#   }
# }
```

---

## 🔍 VERIFY DATA IN PRODUCTION DATABASE

### **Option A: Via Backend API**

```powershell
# Get recent SELL signals
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals/sell?limit=10" | ConvertFrom-Json
```

### **Option B: Via Render PostgreSQL Dashboard**

1. Go to: https://dashboard.render.com
2. Select **PostgreSQL** service (ai_advisor database)
3. Click **Connect** → **External Connection**
4. Use provided credentials to connect via:
   - pgAdmin
   - DBeaver
   - psql command line

### **Option C: Via Python Script**

```powershell
python -c "
from sqlalchemy import create_engine, text

db_url = 'postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5'
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT ticker, exit_reason, exit_price, exit_date 
        FROM signals 
        WHERE action=''SELL'' 
        ORDER BY created_at DESC 
        LIMIT 10
    '''))
    
    print('\nRecent SELL signals in PRODUCTION:')
    print('Ticker | Reason       | Price   | Date')
    print('-------|--------------|---------|------------')
    for row in result:
        print(f'{row[0]:<6} | {row[1]:<12} | {row[2]:<7} | {row[3]}')
"
```

---

## ⚠️ COMMON ISSUES

### **Issue 1: "Connection refused"**

**Cause:** Database not accessible

**Solution:**
1. Check Render dashboard - database should be running
2. Verify DATABASE_URL is correct
3. Check if IP is whitelisted (Render usually allows all)

---

### **Issue 2: "SSL required"**

**Cause:** PostgreSQL requires SSL connection

**Solution:**
Add `?sslmode=require` to DATABASE_URL:

```bash
DATABASE_URL=postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5?sslmode=require
```

---

### **Issue 3: "Password authentication failed"**

**Cause:** Wrong credentials

**Solution:**
1. Go to Render Dashboard
2. PostgreSQL service → **Info** tab
3. Copy correct `Internal Database URL`
4. Update DATABASE_URL in .env

---

### **Issue 4: Still using SQLite**

**Symptom:**
```
⚠️  Using SQLite - will NOT work in production!
```

**Solution:**
```powershell
# Check .env file
Select-String -Path .env -Pattern "DATABASE_URL"

# Should show PostgreSQL URL, not SQLite
# If shows SQLite or nothing, add PostgreSQL URL
notepad .env
```

---

## ✅ SUCCESS CHECKLIST

After completing setup:

- [ ] .env has DATABASE_URL (Render PostgreSQL)
- [ ] verify_sell_columns.py shows "PRODUCTION PostgreSQL"
- [ ] Migration added 3 columns (exit_price, exit_reason, exit_date)
- [ ] Test scanner saves to production database
- [ ] Can verify SELL signals in Render dashboard
- [ ] Backend API /api/scan-sell returns 202
- [ ] Backend API /api/scan-sell/status shows counts
- [ ] GitHub Actions (when deployed) uses Render DATABASE_URL

---

## 🎯 SUMMARY

**Correct Architecture:**

```
LOCAL DEVELOPMENT:
└── DATABASE_URL → Render PostgreSQL (production)

STAGING (staging branch):
└── DATABASE_URL → Supabase (staging only)

PRODUCTION (main branch):
└── DATABASE_URL → Render PostgreSQL (same as local)
```

**Production DATABASE_URL:**
```
postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5
```

**Key Points:**
- ✅ Use Render PostgreSQL for production
- ✅ Use Supabase only for staging
- ✅ Local dev connects to production database
- ✅ Never mix staging and production databases

---

**Last Updated:** 2026-02-05  
**Author:** AI Advisor Team  
**Contact:** ngthson75@gmail.com
