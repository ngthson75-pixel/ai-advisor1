# ⚡ DAILY SCANNER - QUICK REFERENCE

## 🚀 SETUP (ONE TIME)

```powershell
cd C:\ai-advisor1

# Option 1: Automated (RECOMMENDED)
.\enable_workflow.ps1

# Option 2: Manual
New-Item -ItemType Directory -Force -Path .github\workflows
# Download daily-scanner.yml ⬆️ → Save to .github\workflows\
git add .github\workflows\daily-scanner.yml
git commit -m "feat: Add daily scanner"
git push origin main
```

**Then:**
1. Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
2. Click: "Daily Signal Scanner"
3. Click: "Enable workflow"
4. Done! ✅

---

## ⏰ AUTOMATIC SCHEDULE

**When:** Every day at 9:00 AM Vietnam  
**What:** Scans 343 stocks, generates ~100-150 signals  
**Duration:** ~5 minutes  
**Cost:** FREE  

**Next automatic run:** Tomorrow 9:00 AM

---

## 🎮 MANUAL TRIGGER

**When to use:**
- Test workflow now
- Scan outside schedule
- Re-scan after fix

**How:**
```
1. https://github.com/YOUR_USERNAME/ai-advisor1/actions
2. Click: "Daily Signal Scanner"
3. Click: "Run workflow" (right side)
4. Select: 
   - Branch: main
   - Environment: production
5. Click: "Run workflow" (green button)
6. Wait: ~5 minutes
7. Check: Green ✓ or Red ✗
```

---

## 📊 MONITORING

### **Check Status:**
```
GitHub → Actions → Daily Signal Scanner
- Green ✓ = Success
- Red ✗ = Failed (click for logs)
- Yellow ⏳ = Running
```

### **View Logs:**
```
Click workflow run → Click "scan-production" → Read logs
```

### **Expected Output:**
```
✅ Backend is healthy
📊 Current signals: 140
🔍 Triggering signal scanner...
✅ Scanner triggered successfully
⏳ Monitoring scan progress...
✅ Scan completed! Found 132 signals
📈 Getting final scan results...
Total signals: 132
  PULLBACK: 67
  EMA_CROSS: 65
🎯 DAILY SCAN COMPLETE
```

---

## 🔧 TROUBLESHOOTING

### **Workflow not running:**
```
Check:
1. Workflow enabled? (Actions tab)
2. Pushed to main branch?
3. File exists: .github/workflows/daily-scanner.yml?
4. Syntax valid? (GitHub shows errors)
```

### **Scanner fails:**
```
Check backend:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health
# Should return: "healthy"

Test manual scan:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST
```

### **No signals generated:**
```
Check:
1. Backend logs (Render dashboard)
2. Scanner script exists on server?
3. Database connection OK?
4. Run local scanner first?
```

---

## 📅 CHANGE SCHEDULE

Edit `.github/workflows/daily-scanner.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # 9 AM Vietnam (current)
```

**Common times:**
- 8 AM: `'0 1 * * *'`
- 9 AM: `'0 2 * * *'` ← Current
- 10 AM: `'0 3 * * *'`
- 3 PM: `'0 8 * * *'`

**Multiple times:**
```yaml
schedule:
  - cron: '0 2 * * *'   # 9 AM
  - cron: '0 8 * * *'   # 3 PM
```

**Weekdays only:**
```yaml
schedule:
  - cron: '0 2 * * 1-5'  # Mon-Fri
```

**After edit:**
```powershell
git add .github/workflows/daily-scanner.yml
git commit -m "chore: Update scanner schedule"
git push origin main
```

---

## ✅ VERIFICATION

### **After Setup:**
```powershell
# 1. Check file exists
Test-Path .github\workflows\daily-scanner.yml
# Should return: True

# 2. Check on GitHub
# Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
# Should see: "Daily Signal Scanner"

# 3. Test manual trigger
# Click "Run workflow"
# Wait 5 minutes
# Should: Green ✓

# 4. Check website
# Visit: https://ai-advisor.vn
# Tab: "Tín hiệu mua bán"
# Should see: New signals with today's date
```

---

## 💡 TIPS

**Daily Workflow:**
1. ✅ Forget about it! Runs automatically
2. 📧 Email notification if fails
3. 🌐 Check Actions tab if curious
4. 📊 Signals appear on website

**Best Practices:**
- ✅ Let it run automatically (don't manual trigger daily)
- ✅ Check logs only if failed
- ✅ Monitor website for signal updates
- ✅ Keep backend healthy (Render paid tier)

**Cost Savings:**
- ✅ FREE (GitHub Actions 2000 min/month)
- ✅ Uses ~180 min/month (~6 min/day × 30 days)
- ✅ Well within free tier

---

## 📞 QUICK COMMANDS

```powershell
# Setup
.\enable_workflow.ps1

# Manual test
# Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions
# Click: Run workflow

# Check backend
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health

# Check signals
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals

# View website
Start-Process https://ai-advisor.vn
```

---

## 🎯 EXPECTED BEHAVIOR

**Daily (9 AM):**
- ✅ Workflow runs automatically
- ✅ ~5 minutes duration
- ✅ 100-150 signals generated
- ✅ Saved to database
- ✅ Visible on website
- ✅ Email if failure

**Manual (Anytime):**
- ✅ Click "Run workflow"
- ✅ Same process as daily
- ✅ Can choose staging
- ✅ Immediate results

---

## 📋 STATUS CHECKLIST

**Setup Complete:**
- [ ] Workflow file in .github/workflows/
- [ ] Committed and pushed to GitHub
- [ ] Visible in Actions tab
- [ ] Workflow enabled
- [ ] Manual trigger tested
- [ ] Green ✓ success

**Daily Operations:**
- [ ] Runs at 9 AM automatically
- [ ] Signals appear on website
- [ ] Email notifications configured
- [ ] Monitoring Actions tab

---

## 🔗 LINKS

**GitHub Actions:**
https://github.com/YOUR_USERNAME/ai-advisor1/actions

**Website:**
https://ai-advisor.vn

**Backend API:**
https://ai-advisor1-backend.onrender.com/api/signals

**Render Dashboard:**
https://dashboard.render.com

---

## 📚 DOCUMENTATION

**Full Guide:** SETUP_DAILY_SCANNER.md  
**Setup Script:** enable_workflow.ps1  
**Workflow File:** daily-scanner.yml  
**This Card:** QUICK_REFERENCE_SCANNER.md  

---

**🎉 THAT'S IT!**

After setup, workflow runs automatically every day at 9 AM.  
No manual work needed. Just check website for fresh signals! 🚀
