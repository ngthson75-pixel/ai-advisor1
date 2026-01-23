# 🧹 SIGNAL CLEANUP AUTOMATION GUIDE

## 📋 OVERVIEW

Your AI Advisor platform currently has **17 old signals** from January 20-21, 2026. This guide provides multiple strategies to automate cleanup and keep your database clean.

---

## 🎯 CLEANUP STRATEGIES

### **Strategy 1: Age-based Cleanup**
- Delete signals older than X days (default: 7 days)
- Rationale: Old signals are no longer relevant for trading

### **Strategy 2: State-based Cleanup**
- Delete rejected signals after 3 days
- Delete pending signals after 2 days (if not reviewed)
- Rationale: Keep database focused on actionable signals

### **Strategy 3: Quality-based Cleanup**
- Delete signals with quality score < 30
- Rationale: Low-quality signals waste storage and confuse users

### **Strategy 4: Quantity-based Cleanup**
- Keep only latest N signals (e.g., 100-200)
- Rationale: Database performance and storage optimization

---

## 🚀 OPTION 1: MANUAL CLEANUP (Windows)

### **Setup (One-time):**

```bash
# 1. Copy cleanup script to your project
cd C:\ai-advisor1
# Download signal_cleanup.py to this directory

# 2. Test cleanup (dry run)
python signal_cleanup.py --dry-run

# 3. Run actual cleanup
python signal_cleanup.py

# 4. Aggressive cleanup (3 days instead of 7)
python signal_cleanup.py --aggressive
```

### **Common Commands:**

```bash
# Show statistics only
python signal_cleanup.py --stats-only

# Delete signals older than 14 days
python signal_cleanup.py --old-only --days 14

# Keep only latest 50 signals
python signal_cleanup.py --keep-latest 50

# Preview what would be deleted
python signal_cleanup.py --dry-run --aggressive
```

### **Expected Output:**

```
======================================================================
🧹 SIGNAL DATABASE CLEANUP
======================================================================

📊 Current state:
   Total signals: 17
   By state: {'pending_review': 12, 'approved': 5}
   By date (last 7 days): 2

----------------------------------------------------------------------

1️⃣  Cleanup: Signals older than 7 days
🗑️  Deleting 13 signals older than 2026-01-16...
✅ Deleted 13 old signals

2️⃣  Cleanup: Rejected signals
✅ No rejected signals older than 3 days

3️⃣  Cleanup: Stale pending signals
✅ No stale pending signals

4️⃣  Cleanup: Low-quality signals
🗑️  Deleting 2 low-quality signals (score < 30)
✅ Deleted 2 low-quality signals

----------------------------------------------------------------------

📊 Final state:
   Total signals: 2
   Deleted: 15 signals
   Remaining: 2

======================================================================
✅ CLEANUP COMPLETE
======================================================================
```

---

## ⏰ OPTION 2: AUTOMATED CLEANUP (Windows Task Scheduler)

### **Setup (One-time):**

1. **Copy files to project:**
   ```bash
   cd C:\ai-advisor1
   # Copy signal_cleanup.py and setup_cleanup_task.ps1
   ```

2. **Run setup script:**
   ```powershell
   # Open PowerShell as Administrator
   cd C:\ai-advisor1
   .\setup_cleanup_task.ps1
   ```

3. **Verify task created:**
   ```powershell
   Get-ScheduledTask -TaskName "AI-Advisor-Cleanup"
   ```

### **Task Configuration:**

- **Name:** AI-Advisor-Cleanup
- **Schedule:** Daily at 2:00 AM
- **Command:** `python signal_cleanup.py --aggressive`
- **Retention:** 3 days (aggressive mode)
- **Auto-start:** Yes, even if missed

### **Manual Task Management:**

```powershell
# Run task immediately
Start-ScheduledTask -TaskName "AI-Advisor-Cleanup"

# View task details
Get-ScheduledTask -TaskName "AI-Advisor-Cleanup" | Select *

# View last run result
Get-ScheduledTaskInfo -TaskName "AI-Advisor-Cleanup"

# Disable task (temporarily)
Disable-ScheduledTask -TaskName "AI-Advisor-Cleanup"

# Enable task
Enable-ScheduledTask -TaskName "AI-Advisor-Cleanup"

# Remove task
Unregister-ScheduledTask -TaskName "AI-Advisor-Cleanup" -Confirm:$false
```

### **Logs:**

```bash
# Logs are saved to:
C:\ai-advisor1\logs\cleanup.log

# View logs:
type C:\ai-advisor1\logs\cleanup.log | Select-Object -Last 50
```

---

## ☁️ OPTION 3: BACKEND API AUTOMATION (Render)

### **Setup:**

1. **Add cleanup endpoint to backend:**

   ```python
   # In backend_api.py or admin_api.py
   
   from cleanup_endpoints import cleanup_bp
   
   # Register blueprint
   app.register_blueprint(cleanup_bp)
   ```

2. **Set environment variable (optional security):**

   ```bash
   # In Render dashboard → Environment
   CLEANUP_SECRET=your_random_secret_here_change_this
   ```

3. **Deploy to Render:**

   ```bash
   cd C:\ai-advisor1
   git add .
   git commit -m "Add cleanup API endpoints"
   git push origin main
   # Wait 5 minutes for Render deploy
   ```

### **API Endpoints:**

**Get Statistics:**
```bash
GET https://ai-advisor1-backend.onrender.com/api/cleanup/stats

Response:
{
  "success": true,
  "stats": {
    "total": 17,
    "by_state": {"pending_review": 12, "approved": 5},
    "by_date": [["2026-01-21", 4], ["2026-01-20", 13]]
  }
}
```

**Dry Run Cleanup:**
```bash
POST https://ai-advisor1-backend.onrender.com/api/cleanup/signals
Content-Type: application/json

{
  "dry_run": true
}

Response:
{
  "success": true,
  "deleted": 0,
  "remaining": 17,
  "dry_run": true
}
```

**Real Cleanup:**
```bash
POST https://ai-advisor1-backend.onrender.com/api/cleanup/signals
Content-Type: application/json

{
  "secret": "your_secret",
  "aggressive": true
}

Response:
{
  "success": true,
  "deleted": 15,
  "remaining": 2,
  "dry_run": false
}
```

### **PowerShell Testing:**

```powershell
# Get stats
Invoke-WebRequest `
  -Uri "https://ai-advisor1-backend.onrender.com/api/cleanup/stats" `
  -Method GET

# Dry run
$body = @{dry_run=$true} | ConvertTo-Json
Invoke-WebRequest `
  -Uri "https://ai-advisor1-backend.onrender.com/api/cleanup/signals" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"

# Real cleanup
$body = @{secret="your_secret"; aggressive=$true} | ConvertTo-Json
Invoke-WebRequest `
  -Uri "https://ai-advisor1-backend.onrender.com/api/cleanup/signals" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

## 🤖 OPTION 4: EXTERNAL CRON SERVICES

### **Using UptimeRobot (Free):**

1. **Sign up:** https://uptimerobot.com (free tier: 50 monitors)

2. **Create monitor:**
   - Monitor Type: HTTP(s)
   - Friendly Name: AI Advisor Cleanup
   - URL: `https://ai-advisor1-backend.onrender.com/api/cleanup/signals`
   - Monitoring Interval: Every 12 hours (or 24 hours)

3. **Configure POST request:**
   - Method: POST
   - Body: 
     ```json
     {"secret": "your_secret", "aggressive": true}
     ```
   - Headers:
     ```
     Content-Type: application/json
     ```

4. **Alert settings:**
   - Enable alerts for cleanup failures
   - Email notification on error

### **Using EasyCron (Free):**

1. **Sign up:** https://www.easycron.com (free: 1 cron job)

2. **Create cron job:**
   - URL: `https://ai-advisor1-backend.onrender.com/api/cleanup/signals`
   - Cron Expression: `0 2 * * *` (daily at 2:00 AM)
   - Method: POST
   - Post Data: `{"secret": "your_secret", "aggressive": true}`
   - HTTP Headers: `Content-Type: application/json`

3. **Enable email notifications** on failure

---

## 📊 RECOMMENDED SETUP

### **For Your Use Case:**

Given that you have:
- ✅ 17 old signals (2 days old)
- ✅ Local development on Windows
- ✅ Backend on Render (free tier)
- ✅ Need for automated cleanup

**I recommend:**

**Short-term (This Week):**
1. ✅ Manual cleanup NOW to remove old signals
2. ✅ Setup Windows Task Scheduler for daily cleanup
3. ✅ Test automated task for 1 week

**Medium-term (This Month):**
1. ✅ Add API endpoints to backend
2. ✅ Setup UptimeRobot for automated cleanup
3. ✅ Monitor cleanup logs

**Long-term (Production):**
1. ✅ Migrate to PostgreSQL (persistent storage)
2. ✅ Keep API-based cleanup (works even if local PC is off)
3. ✅ Add Telegram notifications for cleanup summary

---

## 🧪 IMMEDIATE ACTION PLAN

### **Step 1: Clean up current old signals (NOW)**

```bash
# Test what will be deleted
cd C:\ai-advisor1
python signal_cleanup.py --dry-run

# Review output, then run actual cleanup
python signal_cleanup.py --aggressive

# Expected: Delete ~15 old signals, keep 2 recent ones
```

### **Step 2: Setup automated cleanup (Today)**

```powershell
# Setup Windows Task Scheduler
cd C:\ai-advisor1
.\setup_cleanup_task.ps1

# Verify task created
Get-ScheduledTask -TaskName "AI-Advisor-Cleanup"
```

### **Step 3: Test automation (Tomorrow)**

```powershell
# Manual trigger to test
Start-ScheduledTask -TaskName "AI-Advisor-Cleanup"

# Check logs
type C:\ai-advisor1\logs\cleanup.log
```

### **Step 4: Add API endpoints (This Weekend)**

```bash
# Add cleanup_endpoints.py to backend
# Update backend_api.py with cleanup blueprint
# Deploy to Render
# Test API endpoints
```

---

## 🔍 VERIFICATION CHECKLIST

### **After Initial Cleanup:**
- [ ] Run `python signal_cleanup.py --stats-only`
- [ ] Verify total signals reduced from 17 → ~2
- [ ] Check no signals older than 3 days remain
- [ ] Test website still shows recent signals

### **After Automation Setup:**
- [ ] Task appears in Task Scheduler
- [ ] Task runs successfully (manual trigger)
- [ ] Logs show cleanup results
- [ ] No errors in logs

### **After API Deployment:**
- [ ] `/api/cleanup/stats` returns correct data
- [ ] `/api/cleanup/signals` (dry_run) previews correctly
- [ ] Real cleanup deletes as expected
- [ ] UptimeRobot/cron job triggers successfully

---

## ⚠️ IMPORTANT NOTES

### **Render Free Tier:**
- Database resets on restart (~15 mins idle)
- Cleanup only helps during active periods
- **Long-term solution:** PostgreSQL migration

### **Backup Before Cleanup:**
```bash
# Optional: Backup database before first cleanup
cd C:\ai-advisor1
copy signals.db signals.db.backup
```

### **Revert if Needed:**
```bash
# If cleanup deleted too much, restore backup
copy signals.db.backup signals.db
```

---

## 📞 TROUBLESHOOTING

### **Issue: Task doesn't run**
**Solution:**
```powershell
# Check task status
Get-ScheduledTaskInfo -TaskName "AI-Advisor-Cleanup"

# Check task settings
Get-ScheduledTask -TaskName "AI-Advisor-Cleanup" | Select *

# Run manually to see errors
cd C:\ai-advisor1
python signal_cleanup.py --aggressive
```

### **Issue: API endpoint 404**
**Solution:**
```bash
# Verify blueprint registered
# Check backend_api.py has: app.register_blueprint(cleanup_bp)
# Redeploy backend
git push origin main
```

### **Issue: All signals deleted**
**Solution:**
```bash
# Restore backup
copy signals.db.backup signals.db

# Adjust retention period
python signal_cleanup.py --days 14  # Keep 14 days instead of 7
```

---

## 📈 NEXT STEPS

1. **✅ NOW:** Run manual cleanup to remove 15 old signals
2. **✅ TODAY:** Setup Windows Task Scheduler
3. **✅ THIS WEEK:** Add API endpoints for cleanup
4. **✅ THIS MONTH:** Setup UptimeRobot for automation
5. **✅ FUTURE:** Migrate to PostgreSQL for production

---

**Last Updated:** January 23, 2026  
**Owner:** Nguyễn Thanh Sơn  
**Contact:** ngthson75@gmail.com
