# 🔍 ROOT CAUSE ANALYSIS - TẠI SAO SIGNALS KHÔNG TỰ ĐỘNG CẬP NHẬT?

**Date:** 2026-02-01  
**Status:** ❌ CRITICAL ISSUE - Daily scanner NOT working  
**Impact:** Production showing old signals (20-21 Jan 2026)

---

## 📋 TÓM TẮT VẤN ĐỀ

### **Hiện tượng:**
```
✅ Hệ thống có CI/CD (deploy code tự động)
✅ Backend hoạt động tốt (health check OK)
✅ Frontend hiển thị được signals
❌ Signals KHÔNG tự động cập nhật hàng ngày
❌ Phải trigger manual: POST /api/scan
❌ Production signals cũ: 20-21/1/2026 (10+ days old)
```

### **Mong đợi:**
```
✅ Signals tự động quét 343 mã cổ phiếu MỖI NGÀY
✅ Signals mới nhất luôn hiển thị trên website
✅ Không cần trigger manual
```

---

## 🎯 ROOT CAUSE (Nguyên nhân gốc rễ)

### **Từ Project Documentation:**

```
File: LOCAL_DEV_CICD_SUMMARY.md
Line 40: "❌ Daily auto-scan NOT configured"
Line 84: ".github/workflows/daily-scanner.yml (needs setup)"
Line 304: "File: daily-scanner.yml (created but not active)"
```

### **Phân tích:**

```
┌─────────────────────────────────────────────────────┐
│  WORKFLOW FILE daily-scanner.yml                    │
│  Status: CREATED (in docs) but NOT ACTIVE           │
└─────────────────────────────────────────────────────┘
               │
               ├─ Scenario 1: File KHÔNG có trong Git repo
               │   → Chưa được push lên GitHub
               │   → GitHub Actions không nhìn thấy
               │   → Không tự động chạy
               │
               ├─ Scenario 2: File CÓ trong Git repo
               │   nhưng workflow bị DISABLED
               │   → GitHub Actions tắt workflow
               │   → Không chạy theo schedule
               │
               └─ Scenario 3: GitHub Actions chưa được ENABLE
                   → Repository settings chưa bật Actions
                   → Tất cả workflows không chạy
```

---

## 🔍 DIAGNOSTIC STEPS

### **Bước 1: Kiểm tra file trong Git repo**

```powershell
cd C:\ai-advisor1

# Check if file exists in Git
git ls-files .github/workflows/

# Expected output:
# .github/workflows/ci-cd.yml
# .github/workflows/daily-scanner.yml  ← SHOULD SEE THIS

# If daily-scanner.yml NOT listed → ROOT CAUSE = Scenario 1
```

### **Bước 2: Kiểm tra GitHub Actions status**

```
Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions

Look for:
1. Workflow list in left sidebar
2. "Daily Signal Scanner" workflow
3. If NOT listed → Scenario 1 (file not in repo)
4. If listed but grayed out → Scenario 2 (disabled)
5. If no workflows at all → Scenario 3 (Actions disabled)
```

### **Bước 3: Kiểm tra file nội dung (nếu có)**

```powershell
# If file exists, check schedule
cat .github\workflows\daily-scanner.yml | Select-String "cron"

# Should see:
# - cron: '30 8 * * *'  # 08:30 UTC = 15:30 Vietnam
```

---

## ✅ SOLUTION - 3 SCENARIOS

### **SCENARIO 1: File chưa có trong Git repo** ⬅️ MỌT KHẢ NĂNG CAO NHẤT

**Symptom:**
```powershell
git ls-files .github/workflows/daily-scanner.yml
# Output: (empty) ← File KHÔNG có trong Git
```

**Root Cause:**
- File được tạo local hoặc trong docs
- CHƯA được commit và push lên GitHub
- GitHub Actions không biết file tồn tại

**Solution:**
```powershell
cd C:\ai-advisor1

# 1. Copy file vào đúng vị trí
# (Download daily-scanner.yml from chat above)
Copy-Item daily-scanner.yml .github\workflows\

# 2. Verify file
cat .github\workflows\daily-scanner.yml

# 3. Add to Git
git add .github\workflows\daily-scanner.yml

# 4. Commit
git commit -m "feat: Add daily signal scanner GitHub Action

- Auto-scan 343 stocks daily at 15:30 Vietnam time
- Runs on schedule (cron: 30 8 * * *)
- Also supports manual trigger (workflow_dispatch)
- Monitors scan progress for 30 minutes
- Sends notifications on failure"

# 5. Push to main
git push origin main

# 6. Verify on GitHub
# Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
# Should see: "Daily Signal Scanner" in workflow list
```

**Verification:**
```powershell
# After 5 minutes:
# 1. Visit GitHub Actions
# 2. Click "Daily Signal Scanner"
# 3. Click "Run workflow" (manual trigger to test)
# 4. Select "production"
# 5. Click "Run workflow"
# 6. Watch logs for 30 minutes
```

---

### **SCENARIO 2: File có trong Git nhưng workflow disabled**

**Symptom:**
```
GitHub Actions → Workflow list → "Daily Signal Scanner" (grayed out)
```

**Root Cause:**
- Workflow file exists in repo
- But disabled in GitHub settings
- Or has syntax error causing it to not load

**Solution:**

**Option A: Enable in GitHub UI**
```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click: "Daily Signal Scanner" (if listed)
3. Click: "Enable workflow" button
4. Refresh page
5. Should now show as active
```

**Option B: Fix syntax error**
```powershell
# Validate YAML syntax
cat .github\workflows\daily-scanner.yml

# Look for:
# - Proper indentation (2 spaces)
# - No tabs
# - Correct YAML structure

# If error found, fix and push:
git add .github\workflows\daily-scanner.yml
git commit -m "fix: Correct daily-scanner.yml syntax"
git push origin main
```

---

### **SCENARIO 3: GitHub Actions chưa được enable**

**Symptom:**
```
GitHub repo → Settings → Actions → Disabled
All workflows don't run
```

**Root Cause:**
- Repository settings have Actions disabled
- All workflows inactive

**Solution:**
```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/settings/actions
2. Under "Actions permissions":
   → Select: "Allow all actions and reusable workflows"
3. Click: "Save"
4. Return to: https://github.com/ngthson75-pixel/ai-advisor1/actions
5. All workflows should now be visible
```

---

## 🚀 RECOMMENDED ACTION PLAN

### **Phase 1: Diagnosis (5 minutes)**

```powershell
# Run diagnostic script (download from chat above)
cd C:\ai-advisor1
.\diagnostic_daily_scanner.ps1

# This will check:
# ✅ File exists in .github/workflows/
# ✅ File tracked by Git
# ✅ File content correct
# ✅ Backend endpoints working
# ✅ Current signal status
```

**Then send me:**
1. Screenshot of command output
2. Screenshot of GitHub Actions page
3. Result of: `git ls-files .github/workflows/`

---

### **Phase 2: Fix (10 minutes)**

**Based on diagnostic results, I will:**

**If Scenario 1 (file not in Git):**
```powershell
# Copy workflow file
Copy-Item daily-scanner.yml .github\workflows\

# Commit & push
git add .github\workflows\daily-scanner.yml
git commit -m "feat: Add daily scanner workflow"
git push origin main

# Wait 5 min, then verify on GitHub
```

**If Scenario 2 (disabled):**
```
Enable workflow in GitHub UI
Or fix syntax error and re-push
```

**If Scenario 3 (Actions disabled):**
```
Enable Actions in repository settings
```

---

### **Phase 3: Test (35 minutes)**

**Manual trigger test:**
```powershell
# After workflow is active:
# 1. GitHub Actions → Daily Signal Scanner → Run workflow
# 2. Select "production"
# 3. Run

# 4. Monitor logs for 30 minutes
# Expected:
# - Scanner starts: Process ID: 123
# - Progress: Check #1, #2, #3... #15
# - Complete: Found 136 signals!

# 5. Verify results
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan/status"
# Should show:
# last_scan: 2026-02-01 (today!)
# signals_count: 136
# status: complete
```

---

### **Phase 4: Monitor (Daily)**

**After workflow is working:**

```
✅ Workflow runs automatically at 15:30 Vietnam time daily
✅ No manual intervention needed
✅ Check GitHub Actions logs if needed
✅ Signals auto-update on website

Daily checks:
1. Visit: https://ai-advisor.vn
2. Check signal dates → Should be today
3. GitHub Actions → Recent runs → Should see green checkmarks
```

---

## 📊 EXPECTED TIMELINE

```
Now (15:30):     Run diagnostic
                 ↓
15:35:           Identify scenario
                 ↓
15:40:           Push workflow file (if Scenario 1)
                 ↓
15:45:           Verify on GitHub Actions
                 ↓
15:50:           Manual trigger test
                 ↓
16:20:           Scanner completes (30 min)
                 ↓
16:25:           Verify 136 signals in production
                 ↓
16:30:           ✅ DONE! Daily auto-scan working!
                 ↓
Next day 15:30:  Auto-scan runs automatically
```

---

## 🎯 SUCCESS CRITERIA

**After fix, you should have:**

✅ File `.github/workflows/daily-scanner.yml` in Git repo
✅ Workflow visible in GitHub Actions
✅ Workflow enabled (not grayed out)
✅ Manual trigger test successful
✅ Scanner completes in 30 minutes
✅ 136+ signals generated daily
✅ Signals auto-update on website
✅ No manual intervention needed

---

## 📋 CHECKLIST

**Before starting:**
- [ ] Run diagnostic script
- [ ] Screenshot GitHub Actions page
- [ ] Send results to Claude

**During fix:**
- [ ] Copy daily-scanner.yml to .github/workflows/
- [ ] Git add, commit, push
- [ ] Verify file on GitHub
- [ ] Enable workflow if needed
- [ ] Manual trigger test

**After fix:**
- [ ] 136+ signals generated
- [ ] Website shows today's signals
- [ ] GitHub Actions shows green checkmark
- [ ] Schedule set for daily 15:30

---

## 🔧 DEBUGGING TIPS

**If scanner fails during test:**

```powershell
# Check Render logs
# Visit: https://dashboard.render.com
# Service: ai-advisor1-backend
# Tab: Logs
# Look for: Processing errors, timeouts

# Common issues:
# - Render free tier timeout (15 min) → Upgrade to paid ($7/mo)
# - Memory limit (512MB) → Optimize scanner code
# - Database connection lost → Check PostgreSQL status
```

**If workflow doesn't show in GitHub Actions:**

```powershell
# 1. Verify file in repo
git ls-files .github/workflows/daily-scanner.yml

# 2. Check YAML syntax
cat .github\workflows\daily-scanner.yml

# 3. Verify Actions enabled
# GitHub → Settings → Actions → Allow all actions

# 4. Check workflow runs
# GitHub → Actions → All workflows
```

---

## 📞 NEXT STEPS

**Run these commands NOW:**

```powershell
# 1. Diagnostic
cd C:\ai-advisor1
.\diagnostic_daily_scanner.ps1

# 2. Check Git
git ls-files .github/workflows/

# 3. Screenshot GitHub
# Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
# Send screenshot
```

**Then I will:**
1. Confirm exact scenario (1, 2, or 3)
2. Provide exact fix commands
3. Guide you through testing
4. Verify daily auto-scan working

---

**TL;DR:**

🎯 **Root Cause:** File `daily-scanner.yml` chưa được push vào Git repo  
✅ **Solution:** Copy file → Git add → Commit → Push → Enable  
⏰ **Time:** 15 minutes setup + 30 minutes test = 45 minutes  
🎉 **Result:** Daily auto-scan 343 stocks at 15:30 Vietnam time  

**Download files from chat above and run diagnostic script NOW!** 🚀
