# 🤖 DAILY AUTO-SCANNER - COMPLETE SOLUTION

## ✅ WHAT YOU'RE GETTING

**Automatic Signal Scanner** that runs every day at 9 AM Vietnam time via GitHub Actions.

**Features:**
- ⏰ Automatic daily execution (9 AM Vietnam)
- 🎮 Manual trigger option (anytime)
- 📊 Progress monitoring (5 minutes)
- 📈 Result summary (PULLBACK/EMA_CROSS breakdown)
- 📧 Email notification on failure
- 💰 FREE (GitHub Actions 2000 min/month)

---

## 📦 FILES PROVIDED

**1. daily-scanner.yml** ⬆️ (Workflow file)
   - Main workflow configuration
   - Runs daily at 9 AM
   - Manual trigger enabled
   - Smart monitoring logic
   - **→ MUST COPY TO: `.github/workflows/daily-scanner.yml`**

**2. enable_workflow.ps1** ⬆️ (Setup script)
   - Automated setup process
   - Creates directories
   - Commits and pushes
   - Opens GitHub Actions page
   - **→ RUN THIS TO AUTO-SETUP**

**3. SETUP_DAILY_SCANNER.md** ⬆️ (Full guide)
   - Step-by-step instructions
   - Configuration options
   - Testing procedures
   - Troubleshooting
   - **→ READ THIS FOR DETAILS**

**4. QUICK_REFERENCE_SCANNER.md** ⬆️ (Quick reference)
   - One-page cheat sheet
   - Common commands
   - Quick troubleshooting
   - Daily operations
   - **→ BOOKMARK THIS**

---

## ⚡ QUICK SETUP (5 MINUTES)

### **OPTION 1: AUTOMATED (RECOMMENDED)**

```powershell
# 1. Download files ⬆️
#    - daily-scanner.yml
#    - enable_workflow.ps1

# 2. Save to C:\ai-advisor1\
cd C:\ai-advisor1

# 3. Run setup script
.\enable_workflow.ps1

# 4. Follow prompts
#    - Will create .github/workflows/
#    - Will commit and push
#    - Will open GitHub Actions page

# 5. Enable on GitHub
#    - Click "Enable workflow"
#    - Click "Run workflow" (test)

# Done! ✅
```

**Duration:** 5 minutes  
**Difficulty:** Easy (automated)

---

### **OPTION 2: MANUAL**

```powershell
cd C:\ai-advisor1

# 1. Create directory
New-Item -ItemType Directory -Force -Path .github\workflows

# 2. Download daily-scanner.yml ⬆️
#    Save to: .github\workflows\daily-scanner.yml

# 3. Commit and push
git add .github\workflows\daily-scanner.yml
git commit -m "feat: Add daily signal scanner workflow"
git push origin main

# 4. Enable on GitHub
#    Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
#    Click: "Daily Signal Scanner"
#    Click: "Enable workflow"

# 5. Test
#    Click: "Run workflow"
#    Select: production
#    Click: "Run workflow"
#    Wait: 5 minutes
#    Check: Green ✓
```

**Duration:** 5-10 minutes  
**Difficulty:** Moderate (manual steps)

---

## 🎯 HOW IT WORKS

### **Daily Automatic Run (9 AM Vietnam):**

```
1. GitHub Actions triggers at 9:00 AM
   ↓
2. Wake up backend (Render may be sleeping)
   ↓
3. Health check (verify backend OK)
   ↓
4. Trigger scanner (POST /api/scan)
   ↓
5. Monitor progress (check every 30 seconds)
   ↓
6. Get results (GET /api/signals)
   ↓
7. Display summary (PULLBACK/EMA_CROSS counts)
   ↓
8. ✅ Done! (Signals on website)
```

**Total Duration:** ~5 minutes  
**Cost:** FREE

---

### **Manual Trigger (Anytime):**

```
1. Visit GitHub Actions page
   ↓
2. Click "Daily Signal Scanner"
   ↓
3. Click "Run workflow"
   ↓
4. Select environment (production/staging)
   ↓
5. Click "Run workflow" (green button)
   ↓
6. Watch live logs
   ↓
7. ✅ Done! (Same process as daily)
```

**Use Cases:**
- Test workflow now
- Re-scan after fix
- Scan outside schedule
- Test staging environment

---

## 📊 EXPECTED RESULTS

### **After Setup:**

**Immediate:**
- ✅ Workflow visible in Actions tab
- ✅ Manual trigger works
- ✅ Test run succeeds (green ✓)

**Daily (9 AM):**
- ✅ Workflow runs automatically
- ✅ ~132 signals generated
- ✅ Saved to database
- ✅ Visible on website: https://ai-advisor.vn
- ✅ Email notification (if fails)

---

### **Workflow Output:**

```
🚀 Starting Daily Signal Scanner - PRODUCTION
📅 Date: 2026-02-02 02:00:00 UTC
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
...
Check #8/10 (02:04:30)...
  Status: complete | Signals: 132
✅ Scan completed! Found 132 signals

📈 Getting final scan results...
Total signals: 132

Latest 5 signals:
  - GMC (EMA_CROSS) - 100% - 2026-02-02
  - PGD (EMA_CROSS) - 100% - 2026-02-02
  - VSM (EMA_CROSS) - 100% - 2026-02-02
  - CTG (PULLBACK) - 90% - 2026-02-02
  - VIM (EMA_CROSS) - 90% - 2026-02-02

Strategy breakdown:
  PULLBACK: 67
  EMA_CROSS: 65
  Priority (≥75%): 25

==================================
🎯 DAILY SCAN COMPLETE
==================================
📅 Completed: 2026-02-02 02:05:23 UTC
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

**Common schedules:**
- **8:00 AM Vietnam:** `cron: '0 1 * * *'`
- **9:00 AM Vietnam:** `cron: '0 2 * * *'` ← Default
- **10:00 AM Vietnam:** `cron: '0 3 * * *'`
- **3:00 PM Vietnam:** `cron: '0 8 * * *'`

**Multiple times per day:**
```yaml
schedule:
  - cron: '0 2 * * *'   # 9 AM
  - cron: '0 8 * * *'   # 3 PM
```

**Weekdays only:**
```yaml
schedule:
  - cron: '0 2 * * 1-5'  # Monday-Friday
```

**After changing:**
```powershell
git add .github/workflows/daily-scanner.yml
git commit -m "chore: Update scanner schedule"
git push origin main
```

---

## 🆘 TROUBLESHOOTING

### **Issue 1: Workflow not appearing in Actions tab**

**Cause:** File not pushed to GitHub or wrong location

**Fix:**
```powershell
# Check file exists
Test-Path .github\workflows\daily-scanner.yml
# Should return: True

# Check pushed to GitHub
git log --oneline -1 .github\workflows\daily-scanner.yml
# Should show recent commit

# If not pushed:
git add .github\workflows\daily-scanner.yml
git commit -m "feat: Add daily scanner"
git push origin main
```

---

### **Issue 2: Workflow fails at "Health check"**

**Cause:** Backend sleeping (Render free tier) or down

**Fix:** Workflow automatically retries 3 times. If still fails:
```powershell
# Check backend manually
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health
# Should return: {"status":"healthy"}

# If 503/timeout: Backend sleeping, wait 30s and retry
# If 500: Backend error, check Render logs
```

---

### **Issue 3: Scanner times out (5 minutes)**

**Cause:** Scanner takes >5 minutes for 343 stocks

**Current timeout:** 10 checks × 30 seconds = 5 minutes

**Fix:** Increase monitoring time in workflow:
```yaml
# Line ~120
for i in {1..10}; do  # Change to {1..15} for 7.5 minutes
```

---

### **Issue 4: No signals generated**

**Cause:** Scanner script issue or database problem

**Debug:**
```powershell
# 1. Check backend logs (Render dashboard)
# 2. Test manual scan
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST

# 3. Check scanner script exists on server
# Should be in backend deployment

# 4. Check database connection
# Render → PostgreSQL service status
```

---

### **Issue 5: Email notifications not received**

**Cause:** GitHub notifications not configured

**Fix:**
```
1. GitHub → Settings → Notifications
2. Actions: ✓ Send notifications for failed workflows
3. Email: Verify your email address
4. Save
```

---

## 📋 COMPLETE CHECKLIST

### **Setup Phase:**
- [ ] Downloaded daily-scanner.yml
- [ ] Downloaded enable_workflow.ps1
- [ ] Saved files to C:\ai-advisor1\
- [ ] Ran enable_workflow.ps1 (or manual setup)
- [ ] File in .github/workflows/daily-scanner.yml
- [ ] Committed and pushed to GitHub

### **GitHub Activation:**
- [ ] Visited GitHub Actions page
- [ ] Workflow "Daily Signal Scanner" visible
- [ ] Clicked "Enable workflow"
- [ ] Manual trigger tested
- [ ] Test run succeeded (green ✓)

### **Verification:**
- [ ] Logs show correct output
- [ ] Signals generated (~100-150)
- [ ] Signals visible on website
- [ ] Strategy breakdown displayed
- [ ] Date is today

### **Daily Operations:**
- [ ] Next automatic run: Tomorrow 9 AM
- [ ] Email notifications configured
- [ ] Bookmarked Actions page
- [ ] Bookmarked website

---

## 💰 COSTS

**GitHub Actions:**
- Free tier: 2000 minutes/month
- Daily scanner: ~6 minutes/run
- Monthly usage: ~180 minutes (6 min × 30 days)
- **Remaining:** 1820 minutes for other workflows
- **Cost:** $0 FREE ✅

**Backend (No change):**
- Render Starter: $7/month (already paying)
- No additional cost

**Total Additional Cost:** $0

---

## 🎯 BENEFITS

**Before:**
- ❌ Manual push script daily
- ❌ Remember to run scanner
- ❌ Login to server
- ❌ Wait for completion
- ⏱️ 10 minutes manual work daily

**After:**
- ✅ Fully automated
- ✅ Runs while you sleep
- ✅ Email on failure only
- ✅ Zero manual work
- 🎉 Set and forget!

---

## 📚 DOCUMENTATION

**All files provided:**
1. **daily-scanner.yml** - Workflow configuration
2. **enable_workflow.ps1** - Automated setup script
3. **SETUP_DAILY_SCANNER.md** - Complete setup guide
4. **QUICK_REFERENCE_SCANNER.md** - Quick reference card

**Additional resources:**
- GitHub Actions: https://docs.github.com/actions
- Cron syntax: https://crontab.guru

---

## 🚀 GETTING STARTED NOW

### **FASTEST PATH (5 MINUTES):**

```powershell
# 1. Download files ⬆️
cd C:\ai-advisor1

# 2. Save daily-scanner.yml to .github\workflows\
# 3. Save enable_workflow.ps1 to C:\ai-advisor1\

# 4. Run setup
.\enable_workflow.ps1

# 5. Enable on GitHub (opens automatically)
# 6. Test "Run workflow"
# 7. Done! ✅
```

**Next automatic run:** Tomorrow 9:00 AM

---

## 🎉 FINAL RESULT

**After setup:**
- ✅ Signals update automatically every morning
- ✅ Website shows fresh signals daily
- ✅ Zero manual work required
- ✅ Email notification if something fails
- ✅ Complete automation achieved!

**You can:**
- ☕ Relax, scanner runs automatically
- 📱 Check website for new signals
- 📧 Get notified only if issues
- 🎮 Manual trigger when needed

---

## 📞 NEXT STEPS

**After setup complete:**

1. **Tomorrow morning (9 AM):**
   - Check GitHub Actions for run
   - Verify signals on website
   - Should see today's date on signals

2. **Monitor for 1 week:**
   - Confirm daily runs successful
   - Check signal quality
   - Adjust schedule if needed

3. **Then forget about it!** 🎉
   - System runs automatically
   - Signals always fresh
   - Zero maintenance

---

## ✅ SUCCESS CRITERIA

**Setup successful when:**
- [ ] Workflow visible in GitHub Actions
- [ ] Test run shows green ✓
- [ ] Signals appear on website
- [ ] Date shows today
- [ ] Strategy breakdown correct
- [ ] Can trigger manually anytime

**Daily operations successful when:**
- [ ] Runs at 9 AM automatically
- [ ] Completes in ~5 minutes
- [ ] Generates 100-150 signals
- [ ] Signals visible on website
- [ ] No manual intervention needed

---

## 🎊 CONGRATULATIONS!

You've successfully automated the daily signal scanner!

**From now on:**
- 🤖 GitHub Actions runs scanner daily
- 🌅 Fresh signals every morning
- 📊 Users see latest opportunities
- 💪 You focus on growth, not maintenance

**System is now:**
- ✅ Fully automated
- ✅ Self-healing (retry logic)
- ✅ Monitored (email alerts)
- ✅ Cost-effective (FREE)
- ✅ Production-ready

---

**🚀 LET'S GET STARTED!**

Download files ⬆️ → Run enable_workflow.ps1 → Enable on GitHub → Done! 🎉
