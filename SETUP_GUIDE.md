# 🚀 SELL SIGNAL SYSTEM - COMPLETE SETUP GUIDE

## 📋 OVERVIEW

**What this does:**
- ✅ Automatically creates SELL signals every day at 6:00 PM
- ✅ Based on active BUY signals in database
- ✅ 3 types: Stop Loss (100%), Take Profit (50%), MA20 Exit (50%)
- ✅ Tracks position status: ACTIVE → PARTIAL_SOLD → FULLY_SOLD
- ✅ Frontend already configured to display SELL signals

**Setup time:** 20 minutes  
**Automation:** GitHub Actions (runs daily at 6 PM)

---

## 📁 STEP 1: ADD FILES TO PROJECT (5 minutes)

### **1.1 Copy all scripts to project:**

```bash
cd C:\ai-advisor1

# Create scripts folder if not exists
mkdir scripts 2>nul

# Copy files from downloads/generated location:
copy update_database.py scripts\
copy sell_signal_generator.py scripts\
copy daily_signal_runner.py scripts\
copy test_sell_system.py scripts\
copy backend_sell_api.py .
```

### **1.2 Create GitHub Actions workflow:**

```bash
# Create folders
mkdir .github 2>nul
mkdir .github\workflows 2>nul

# Copy workflow file
copy daily-signals.yml .github\workflows\
```

**Files you should now have:**
```
ai-advisor1/
├── scripts/
│   ├── update_database.py          ✅ NEW
│   ├── sell_signal_generator.py     ✅ NEW
│   ├── daily_signal_runner.py       ✅ NEW
│   ├── test_sell_system.py          ✅ NEW
│   └── daily_signal_scanner_eod.py  (existing)
├── backend_sell_api.py              ✅ NEW
└── .github/
    └── workflows/
        └── daily-signals.yml         ✅ NEW
```

---

## 🗄️ STEP 2: UPDATE DATABASE (3 minutes)

### **2.1 Run database update script:**

```bash
cd C:\ai-advisor1
python scripts\update_database.py
```

**Expected output:**
```
======================================================================
📊 DATABASE SCHEMA UPDATE - SELL SIGNALS
======================================================================

📁 Database: C:\ai-advisor1\signals.db

➕ Adding column: signal_status
   ✅ Done

➕ Adding column: quantity_sold
   ✅ Done

🔄 Updating existing signals...
   ✅ Updated 127 BUY signals to ACTIVE

======================================================================
✅ DATABASE READY!
======================================================================
📊 Active BUY signals: 127
🎯 Ready to generate SELL signals!
======================================================================
```

### **2.2 Verify schema:**

```bash
python -c "
import sqlite3
conn = sqlite3.connect('signals.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(signals)')
columns = [col[1] for col in cursor.fetchall()]
print('✅ signal_status:', 'signal_status' in columns)
print('✅ quantity_sold:', 'quantity_sold' in columns)
conn.close()
"
```

---

## 🧪 STEP 3: TEST SYSTEM (5 minutes)

### **3.1 Run comprehensive test:**

```bash
python test_sell_system.py
```

**Expected output:**
```
======================================================================
🧪 SELL SIGNAL SYSTEM - COMPREHENSIVE TEST
======================================================================

TEST 1: DATABASE SCHEMA
======================================================================
✅ signal_status column: ✅ EXISTS
✅ quantity_sold column: ✅ EXISTS
✅ TEST 1 PASSED

TEST 2: SELL SIGNAL GENERATOR
======================================================================
📊 Found 127 active BUY signals
✅ TEST 2 PASSED

... (more tests)

======================================================================
📊 TEST SUMMARY
======================================================================
✅ PASS | Database Schema
✅ PASS | Signal Generator
✅ PASS | Mock SELL Signal
✅ PASS | Status Transitions
✅ PASS | API Simulation
----------------------------------------------------------------------
Result: 5/5 tests passed
======================================================================

🎉 ALL TESTS PASSED!
✅ Sell signal system is ready!
```

### **3.2 Test sell signal generation manually:**

```bash
cd scripts
python sell_signal_generator.py
```

**Expected output:**
```
======================================================================
🎯 SELL SIGNAL GENERATOR
======================================================================
⏰ Time: 2026-01-15 18:00:00

📊 Found 127 active BUY signals to check

🔍 Checking TCB...
   💰 Current: 36,500
   📉 Stop Loss: 34,817
   📈 Take Profit: 39,582
   📊 Status: ACTIVE (0% sold)
   ✅ Price above MA20, holding

... (checks all signals)

======================================================================
✅ COMPLETED
======================================================================
📊 Checked: 127 BUY signals
🎯 Created: 3 SELL signals
======================================================================
```

---

## 🔌 STEP 4: INTEGRATE BACKEND API (3 minutes)

### **4.1 Update backend_api.py:**

Open `backend_api.py` and add at the top (after imports):

```python
# Add at top of file after other imports
from backend_sell_api import register_sell_routes
```

Then add after `app = Flask(__name__)`:

```python
# After app = Flask(__name__)
# Register SELL signal routes
register_sell_routes(app)
```

**Full example:**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from flask_cors import CORS

# ADD THIS LINE
from backend_sell_api import register_sell_routes

app = Flask(__name__)
CORS(app)

# ADD THIS LINE
register_sell_routes(app)

# ... rest of your code
```

### **4.2 Test backend locally:**

```bash
# Start backend
python backend_api.py

# In another terminal, test endpoints:
# Test SELL signals endpoint
curl http://localhost:10000/api/sell-signals

# Test manual generation
curl -X POST http://localhost:10000/api/generate-sell-signals

# Test signal status
curl http://localhost:10000/api/signal-status/TCB
```

---

## 📅 STEP 5: SETUP DAILY AUTOMATION (5 minutes)

### **5.1 Push to GitHub:**

```bash
cd C:\ai-advisor1

# Check status
git status

# Add all new files
git add .

# Commit
git commit -m "Add SELL signal generation system"

# Push
git push origin main
```

### **5.2 Enable GitHub Actions:**

1. Go to: https://github.com/YOUR_USERNAME/ai-advisor1
2. Click "Actions" tab
3. Enable workflows if disabled
4. You should see: "Daily Signal Generation"

### **5.3 Test manual trigger:**

1. Go to Actions → Daily Signal Generation
2. Click "Run workflow"
3. Select branch: main
4. Click "Run workflow"
5. Wait 2-3 minutes
6. Check run logs

**Expected in logs:**
```
🚀 DAILY SIGNAL RUNNER
======================================================================
⏰ Started at: 2026-01-15 11:00:00

📊 STEP 1: SCANNING BUY SIGNALS
... (BUY signal scanning)

🎯 STEP 2: GENERATING SELL SIGNALS
... (SELL signal generation)

======================================================================
📊 DAILY SIGNAL RUNNER - SUMMARY
======================================================================
BUY Signals:  ✅ Success
SELL Signals: ✅ Success
======================================================================
```

### **5.4 Verify schedule:**

The workflow runs at:
- **UTC:** 11:00 AM
- **Vietnam:** 6:00 PM (UTC+7)
- **Frequency:** Every day

To change time, edit `.github/workflows/daily-signals.yml`:

```yaml
schedule:
  - cron: '0 11 * * *'  # 11:00 AM UTC = 6:00 PM Vietnam
  
  # Examples:
  # - cron: '0 10 * * *'  # 5:00 PM Vietnam
  # - cron: '0 12 * * *'  # 7:00 PM Vietnam
```

---

## 🌐 STEP 6: DEPLOY TO PRODUCTION (Optional - if using Render)

### **6.1 Deploy backend to Render:**

Backend should auto-deploy when you push to GitHub.

Check: https://dashboard.render.com

### **6.2 Test production API:**

```powershell
# Test SELL signals
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/sell-signals

# Test manual generation
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/generate-sell-signals -Method POST

# Test signal status
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signal-status/TCB
```

---

## ✅ VERIFICATION CHECKLIST

### **After Setup:**

- [ ] Database has `signal_status` and `quantity_sold` columns
- [ ] All tests pass (run `test_sell_system.py`)
- [ ] Can generate SELL signals manually
- [ ] Backend API endpoints work
- [ ] GitHub Actions workflow enabled
- [ ] Manual workflow trigger works
- [ ] Production API working (if deployed)

### **Daily Operation:**

- [ ] Workflow runs at 6:00 PM daily
- [ ] BUY signals scanned first
- [ ] SELL signals generated automatically
- [ ] Frontend displays SELL signals in tab
- [ ] Status transitions work (ACTIVE → PARTIAL_SOLD → FULLY_SOLD)

---

## 📊 HOW IT WORKS

### **Daily Flow:**

```
6:00 PM Vietnam Time
│
├─ 1. Download latest stock data
│
├─ 2. Scan for BUY signals
│     └─ Save to database with status = ACTIVE
│
├─ 3. Generate SELL signals (automatic!)
│     │
│     ├─ Check each ACTIVE/PARTIAL_SOLD BUY signal:
│     │
│     ├─ Stop Loss Hit (Price ≤ SL)?
│     │   └─ YES → Create SELL signal (100%)
│     │            Update status → FULLY_SOLD
│     │
│     ├─ Take Profit Hit (Price ≥ TP)?
│     │   └─ YES → Create SELL signal (50%)
│     │            Update status → PARTIAL_SOLD
│     │
│     └─ MA20 Exit (Price < MA20 & PARTIAL_SOLD)?
│         └─ YES → Create SELL signal (50% remaining)
│                  Update status → FULLY_SOLD
│
└─ 4. Users see SELL signals in app
```

### **Example Scenario:**

**Day 1:**
```
BUY TCB @ 36,650
Status: ACTIVE (0% sold)
```

**Day 5:** Price hits Take Profit
```
Price: 39,800 (≥ TP: 39,582)
→ Create SELL signal: TAKE_PROFIT (50%)
Status: PARTIAL_SOLD (50% sold)
```

**Day 10:** Price crosses below MA20
```
Price: 38,000 < MA20: 38,500
→ Create SELL signal: MA20_EXIT (50% remaining)
Status: FULLY_SOLD (100% sold)
```

---

## 🚨 TROUBLESHOOTING

### **Issue: Tests fail with "no such table"**

**Solution:**
```bash
python scripts/update_database.py
```

### **Issue: No SELL signals created**

**Reasons:**
1. No BUY signals hit exit conditions yet (normal!)
2. Database not updated (run update_database.py)
3. VNStock API error (check internet)

**Check:**
```bash
# See active BUY signals
python -c "
import sqlite3
conn = sqlite3.connect('signals.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM signals WHERE action=\"BUY\" AND signal_status=\"ACTIVE\"')
print('Active BUY signals:', cursor.fetchone()[0])
conn.close()
"
```

### **Issue: GitHub Actions doesn't run**

**Check:**
1. Workflow file in correct location: `.github/workflows/daily-signals.yml`
2. Workflows enabled in repo settings
3. Check Actions tab for errors
4. Try manual trigger first

### **Issue: Backend 500 error**

**Solution:**
```powershell
# Run migration on production
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/migrate -Method POST
```

---

## 📞 SUPPORT

**Files to reference:**
- `SIMPLE_SELL_INTEGRATION.md` - Original integration doc
- `test_sell_system.py` - Run tests
- `sell_signal_generator.py` - Core logic

**Quick commands:**
```bash
# Test everything
python test_sell_system.py

# Generate SELL signals
python scripts/sell_signal_generator.py

# Check database
python scripts/update_database.py

# Run daily workflow
cd scripts
python daily_signal_runner.py
```

---

## 🎉 YOU'RE DONE!

**What you have now:**

✅ Fully automated SELL signal generation  
✅ Runs every day at 6:00 PM  
✅ 3-tier exit strategy (SL, TP, MA20)  
✅ Position tracking system  
✅ API endpoints for manual control  
✅ Frontend displays SELL signals automatically  
✅ GitHub Actions for automation  

**No manual work needed!** System runs automatically every day! 🚀

---

**Setup Date:** [Fill when complete]  
**Version:** 1.0  
**Author:** AI Advisor Team
