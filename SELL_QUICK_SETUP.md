# 🚀 QUICK SETUP - SELL SIGNAL SYSTEM (PRODUCTION)

**Time:** 10 minutes  
**Database:** Render PostgreSQL (Production)

---

## ⚡ 1-COMMAND SETUP

Copy DATABASE_URL vào .env và run!

### **STEP 1: Setup .env (2 phút)**

```powershell
cd C:\ai-advisor1

# Create .env from example
if (-not (Test-Path .env)) {
    Copy-Item _env.example .env
}

# Add production DATABASE_URL
@"
# PRODUCTION DATABASE (Render PostgreSQL)
DATABASE_URL=postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5
"@ | Add-Content .env

Write-Host "✅ DATABASE_URL added to .env"
```

---

### **STEP 2: Verify Connection (1 phút)**

```powershell
# Test database connection
python verify_sell_columns.py

# Expected:
# ✅ PRODUCTION PostgreSQL: postgresql://ai_advisor_user...
# 📊 Total columns: 20 or 21
```

---

### **STEP 3: Run Migration (2 phút)**

```powershell
# Add SELL signal columns
python migration_add_sell_columns.py

# Expected:
# ✅ exit_price added
# ✅ exit_reason added
# ✅ exit_date added
```

---

### **STEP 4: Test Scanner (5 phút)**

```powershell
# Test SELL scanner
python test_sell_scanner_manual.py

# Choose: 1 (test 10 tickers)

# Expected:
# ✅ Scanner using PRODUCTION database
# 📊 RESULTS: 5 SELL signals found
# 🎉 Saved 5 signals to PRODUCTION database!
```

---

## ✅ VERIFY SUCCESS

```powershell
# Check SELL signals in database
python -c "
from sqlalchemy import create_engine, text

db_url = 'postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.oregon-postgres.render.com:5432/ai_advisor_ilm5'
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM signals WHERE action=''SELL'''))
    count = result.fetchone()[0]
    print(f'\n✅ SELL signals in production: {count}')
"
```

---

## 🚀 DEPLOY TO PRODUCTION

```powershell
# Replace old files with updated ones
# Copy từ outputs folder:
# - sell_signal_scanner_v2.py
# - backend_sell_api.py
# - migration_add_sell_columns.py
# - verify_sell_columns.py

# Commit và push
git add .
git commit -m "feat: SELL signal system with Render PostgreSQL"
git push origin main

# Render auto-deploys in 3-5 minutes
```

---

## 📋 WHAT YOU GET

After setup:

✅ **SELL signal scanner** - Automated BUY signal monitoring  
✅ **Production database** - Render PostgreSQL (persistent)  
✅ **API endpoints** - POST /api/scan-sell, GET /api/scan-sell/status  
✅ **Frontend ready** - Display SL/TP badges  
✅ **GitHub Actions ready** - Hourly automation (when deployed)

---

## 🔧 TROUBLESHOOTING

**Connection failed?**

```powershell
# Check DATABASE_URL in .env
Select-String -Path .env -Pattern "DATABASE_URL"

# Should show:
# DATABASE_URL=postgresql://ai_advisor_user...

# If wrong, edit:
notepad .env
```

**Still using SQLite?**

```powershell
# Verify environment variable loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"

# Should print PostgreSQL URL
```

---

## 📞 NEED HELP?

- Full guide: `DATABASE_SETUP_CORRECT.md`
- Email: ngthson75@gmail.com

---

**Status:** Production Ready  
**Database:** Render PostgreSQL  
**Last Updated:** 2026-02-05
