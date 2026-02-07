# 🤖 SETUP DAILY AUTO-SCANNER - GITHUB ACTIONS

## 📋 OVERVIEW

**Workflow:** daily-scanner.yml  
**Schedule:** 9:00 AM Vietnam (2:00 AM UTC) daily  
**Target:** Production backend  
**Duration:** ~5 minutes  
**Cost:** FREE (GitHub Actions: 2000 min/month)

---

## ✅ QUICK SETUP (5 PHÚT)

### **STEP 1: Copy workflow file** (1 phút)

```powershell
cd C:\ai-advisor1

# Create workflows directory if not exists
New-Item -ItemType Directory -Force -Path .github\workflows

# Copy workflow file from outputs
# Download: daily-scanner.yml ⬆️
# Save to: C:\ai-advisor1\.github\workflows\daily-scanner.yml
```

---

### **STEP 2: Commit & Push** (2 phút)

```powershell
cd C:\ai-advisor1

# Add workflow
git add .github/workflows/daily-scanner.yml

# Commit
git commit -m "feat: Add daily signal scanner workflow"

# Push to main branch
git push origin main
```

**⚠️ IMPORTANT:** Must push to `main` branch!

---

### **STEP 3: Enable workflow on GitHub** (1 phút)

```
1. Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions

2. Click: "Daily Signal Scanner" (left sidebar)

3. Click: "Enable workflow" button (if disabled)

4. Should see: "This workflow has a workflow_dispatch event trigger"
```

**✅ Workflow is now ENABLED!**

---

### **STEP 4: Test manual trigger** (1 phút)

```
1. Same page: https://github.com/YOUR_USERNAME/ai-advisor1/actions

2. Click: "Daily Signal Scanner"

3. Click: "Run workflow" button (right side)

4. Select:
   - Branch: main
   - Environment: production

5. Click: "Run workflow" (green button)

6. Wait: ~5 minutes

7. Check: Workflow run status
   - Green ✓ = Success
   - Red ✗ = Failed (check logs)
```

---

## 📊 WORKFLOW FEATURES

### **1. Automatic Daily Scan**
- **Time:** 9:00 AM Vietnam every day
- **Cron:** `0 2 * * *` (2 AM UTC)
- **Runs:** Monday-Sunday (7 days/week)

### **2. Manual Trigger**
- **When:** Anytime you need
- **How:** GitHub Actions → Run workflow
- **Options:** Production or Staging

### **3. Smart Monitoring**
- Wakes up backend (Render free tier)
- Health check before scan
- Progress monitoring (5 minutes)
- Result summary with breakdown

### **4. Error Handling**
- Retries backend wake-up (3 attempts)
- Validates health before scan
- Monitors for failures
- Provides detailed logs

---

## 🔍 WHAT IT DOES

### **Step-by-Step Process:**

```
1. ⏰ Wake Backend (30 seconds)
   - Ping /health endpoint
   - Retry up to 3 times
   - Wait for 200 OK

2. 🏥 Health Check (5 seconds)
   - GET /health
   - Verify status: "healthy"
   - Exit if unhealthy

3. 📊 Check Current Signals (5 seconds)
   - GET /api/signals
   - Show current count
   - Show latest date

4. 🔍 Trigger Scanner (2 seconds)
   - POST /api/scan
   - Verify success response
   - Scanner starts running

5. ⏳ Monitor Progress (5 minutes)
   - Check every 30 seconds
   - GET /api/scan/status
   - Wait for "complete" status

6. 📈 Get Results (5 seconds)
   - GET /api/signals
   - Count total signals
   - Show top 5
   - Strategy breakdown

7. 📝 Summary (2 seconds)
   - Display final stats
   - PULLBACK count
   - EMA_CROSS count
   - Priority signals

Total: ~6 minutes
```

---

## 📅 SCHEDULE DETAILS

### **Cron Expression:**
```yaml
cron: '0 2 * * *'
```

**Breakdown:**
- `0` = Minute 0
- `2` = Hour 2 (UTC)
- `*` = Every day of month
- `*` = Every month
- `*` = Every day of week

**Vietnam Time:**
- UTC 2:00 AM = Vietnam 9:00 AM
- Runs every morning at 9 AM
- 7 days per week

**Why 9 AM?**
- ✅ After market open (8:30 AM)
- ✅ Before most traders start
- ✅ Fresh signals for the day
- ✅ Reliable timing

---

## 🧪 TESTING

### **Test Manual Trigger:**

```powershell
# Method 1: GitHub UI
# 1. Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
# 2. Click: Daily Signal Scanner
# 3. Click: Run workflow
# 4. Watch: Live logs

# Method 2: Check logs after run
# 1. Actions tab
# 2. Click latest workflow run
# 3. Click "scan-production" job
# 4. Read logs
```

**Expected Output:**
```
🚀 Starting Daily Signal Scanner - PRODUCTION
📅 Date: 2026-02-01 02:00:00 UTC
🔗 Backend: https://ai-advisor1-backend.onrender.com
==================================
⏰ Waking up backend...
✅ Backend is awake (attempt 1)
🏥 Checking backend health...
✅ Backend is healthy
📊 Current signals before scan:
Current signals: 140
Latest signal date: 2026-01-30
🔍 Triggering signal scanner...
✅ Scanner triggered successfully
⏳ Monitoring scan progress (max 5 minutes)...
Check #1/10 (02:01:00)...
  Status: scanning | Signals: 0
Check #2/10 (02:01:30)...
  Status: scanning | Signals: 0
...
Check #8/10 (02:04:30)...
  Status: complete | Signals: 132
✅ Scan completed! Found 132 signals
📈 Getting final scan results...
Total signals: 132

Latest 5 signals:
  - GMC (EMA_CROSS) - 100% - 2026-02-01
  - PGD (EMA_CROSS) - 100% - 2026-02-01
  - VSM (EMA_CROSS) - 100% - 2026-02-01
  - CTG (PULLBACK) - 90% - 2026-02-01
  - VIM (EMA_CROSS) - 90% - 2026-02-01

Strategy breakdown:
  PULLBACK: 67
  EMA_CROSS: 65
  Priority (≥75%): 25

==================================
🎯 DAILY SCAN COMPLETE
==================================
📅 Completed: 2026-02-01 02:05:23 UTC
🌍 Environment: Production
🔗 View signals: https://ai-advisor.vn
==================================
```

---

## 🔧 CONFIGURATION

### **Change Schedule:**

Edit `.github/workflows/daily-scanner.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Change this line
```

**Common Times (Vietnam):**
- 8:00 AM: `cron: '0 1 * * *'`
- 9:00 AM: `cron: '0 2 * * *'` (current)
- 10:00 AM: `cron: '0 3 * * *'`
- 3:00 PM: `cron: '0 8 * * *'`

### **Run Multiple Times:**

```yaml
schedule:
  - cron: '0 2 * * *'   # 9 AM
  - cron: '0 8 * * *'   # 3 PM
```

### **Weekdays Only:**

```yaml
schedule:
  - cron: '0 2 * * 1-5'  # Monday-Friday only
```

---

## 📊 MONITORING

### **Check Workflow Runs:**

```
1. Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions

2. See: List of all workflow runs
   - ✓ Success (green)
   - ✗ Failed (red)
   - ⏳ In progress (yellow)

3. Click: Any run to see details

4. View: Logs for each step
```

### **Email Notifications:**

GitHub automatically sends email if workflow fails.

**Configure:**
```
1. GitHub Settings → Notifications
2. Actions: ✓ Send notifications for failed workflows only
3. Save
```

---

## 🆘 TROUBLESHOOTING

### **Workflow not appearing:**

```powershell
# Check file location
Test-Path .github\workflows\daily-scanner.yml
# Should return: True

# Check pushed to GitHub
git log --oneline -1 .github\workflows\daily-scanner.yml
# Should show commit

# Check GitHub
# Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
# Should see: "Daily Signal Scanner"
```

### **Workflow fails at health check:**

```
Issue: Backend sleeping (Render free tier)
Fix: Workflow wakes it up (wait 30s)
```

### **Scanner times out:**

```
Issue: Scanner takes >5 minutes
Current: Workflow waits up to 5 minutes
Fix: Increase monitoring timeout in workflow
```

### **No signals generated:**

```
Check:
1. Backend logs (Render dashboard)
2. Scanner script exists on server
3. Database connection OK
4. Manual trigger: POST /api/scan
```

---

## 📋 CHECKLIST

**Setup:**
- [ ] daily-scanner.yml downloaded
- [ ] File copied to .github/workflows/
- [ ] Committed and pushed to GitHub
- [ ] Workflow visible in Actions tab
- [ ] Workflow enabled

**Testing:**
- [ ] Manual trigger works
- [ ] Workflow completes successfully
- [ ] Signals appear on website
- [ ] Logs show correct output

**Monitoring:**
- [ ] Email notifications configured
- [ ] Bookmark Actions page
- [ ] Test failed workflow (optional)

---

## 🎯 EXPECTED RESULTS

### **After Setup:**

**Daily (9 AM Vietnam):**
1. ✅ Workflow runs automatically
2. ✅ Scanner generates ~100-150 signals
3. ✅ Signals saved to database
4. ✅ Website shows new signals
5. ✅ Email if failure

**Manual (Anytime):**
1. ✅ Click "Run workflow"
2. ✅ Select environment
3. ✅ Watch live progress
4. ✅ See results in logs

---

## 💰 COSTS

**GitHub Actions:**
- Free tier: 2000 minutes/month
- This workflow: ~6 minutes/run
- Daily runs: ~180 minutes/month
- **Cost:** FREE! ✅

**Backend:**
- Render: Already paid ($7/month)
- No additional cost

**Total Additional Cost:** $0

---

## 🚀 NEXT STEPS

**After Setup:**

1. **Monitor first run** (next 9 AM)
   - Check Actions tab
   - Verify signals on website
   - Confirm email (if failed)

2. **Adjust if needed**
   - Change schedule time
   - Modify timeout
   - Add notifications

3. **Forget about it!** 🎉
   - Runs automatically every day
   - Signals always fresh
   - No manual work needed

---

## 📞 FILES

**Required:**
- ⬆️ `daily-scanner.yml` - Main workflow file

**Documentation:**
- ⬆️ `SETUP_DAILY_SCANNER.md` - This guide
- ⬆️ `enable_workflow.ps1` - PowerShell setup script

---

**READY TO SETUP?**

```powershell
# 1. Download daily-scanner.yml ⬆️
# 2. Copy to .github\workflows\
# 3. Commit & push
# 4. Enable on GitHub
# 5. Test manual trigger
# 6. Done! 🎉
```

**ESTIMATED TIME:** 5 minutes  
**DIFFICULTY:** Easy  
**RESULT:** Automatic daily signals! 🚀
