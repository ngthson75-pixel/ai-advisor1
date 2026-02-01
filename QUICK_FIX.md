# ⚡ QUICK FIX - DAILY AUTO-SCAN (5 PHÚT)

**Problem:** Signals không tự động cập nhật hàng ngày  
**Root Cause:** File `daily-scanner.yml` chưa được push vào GitHub  
**Solution:** 3 commands, 5 phút, DONE!

---

## 🚀 3 COMMANDS - COPY & RUN

```powershell
# STEP 1: Navigate to project
cd C:\ai-advisor1

# STEP 2: Download & copy workflow file
# (Download daily-scanner.yml from chat above, then run:)
Copy-Item daily-scanner.yml .github\workflows\daily-scanner.yml

# STEP 3: Commit & push
git add .github\workflows\daily-scanner.yml
git commit -m "feat: Add daily auto-scan workflow - 343 stocks at 15:30 VN time"
git push origin main
```

---

## ✅ VERIFY (2 phút)

```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Wait 1-2 minutes for workflow to appear
3. Look for: "Daily Signal Scanner" in left sidebar
4. If visible → SUCCESS! ✅
5. If not visible → Send me screenshot
```

---

## 🧪 TEST IMMEDIATELY (30 phút)

```
1. GitHub Actions → "Daily Signal Scanner"
2. Click "Run workflow" button
3. Select environment: "production"
4. Click green "Run workflow" button
5. Watch progress in logs (30 minutes)
6. Expected result: "Found 136 signals!"
```

---

## 🎯 EXPECTED RESULTS

**After test completes:**
```powershell
# Check signals
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan/status"

# Should show:
# {
#   "last_scan": "2026-02-01 ...",  ← TODAY!
#   "signals_count": 136,           ← NEW SIGNALS!
#   "status": "complete"            ← SUCCESS!
# }
```

**On website:**
```
Visit: https://ai-advisor.vn
Expected: Signals dated 2026-02-01 (today)
```

---

## ⏰ DAILY AUTO-SCAN

**From now on:**
```
✅ Scanner runs AUTOMATICALLY every day at 15:30 Vietnam time
✅ 343 stocks scanned
✅ Signals updated on website
✅ NO manual trigger needed
```

**Check anytime:**
```
GitHub → Actions → Daily Signal Scanner → Recent runs
Should see green checkmarks daily
```

---

## 🆘 IF SOMETHING FAILS

**Workflow not showing on GitHub:**
```powershell
# Check if file in repo
git ls-files .github/workflows/daily-scanner.yml

# If empty → File not committed, retry step 3
```

**Scanner fails during test:**
```
1. Open Render logs: https://dashboard.render.com
2. Select: ai-advisor1-backend
3. Watch for errors
4. Send me screenshot of error
```

**Signals still old after test:**
```powershell
# Wait full 30 minutes, then check
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals"

# If count still low → Scanner might have failed
# Check GitHub Actions logs for errors
```

---

## 📋 COMPLETE CHECKLIST

**NOW:**
- [ ] Download `daily-scanner.yml` from chat
- [ ] Copy to `.github/workflows/`
- [ ] Git add, commit, push
- [ ] Wait 2 min, check GitHub Actions

**TEST:**
- [ ] Manual trigger workflow
- [ ] Watch logs 30 min
- [ ] Verify 136 signals
- [ ] Check website shows today's date

**VERIFY DAILY:**
- [ ] Tomorrow 15:30: Check GitHub Actions ran
- [ ] Check website has new signals
- [ ] Confirm auto-scan working

---

**START NOW! Copy commands above ⬆️**

Time: 5 min setup + 30 min test = 35 min total
Result: ✅ Daily auto-scan FOREVER! 🎉
