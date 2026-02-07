# 🧹 MANUAL CLEANUP GUIDE - WORKFLOWS FOLDER

**Objective:** Chỉ giữ 2 files: `ci-cd.yml` và `daily-scan.yml`

---

## 📋 FILES CẦN GIỮ LẠI

```
✅ ci-cd.yml          - Deploy staging/production
✅ daily-scan.yml     - Auto-scan 343 stocks daily
```

## ❌ FILES CẦN XÓA

```
❌ ci-cd_backup.yml           - Old backup
❌ daily-scan.yml (old)       - Old version
❌ daily-scanner.yml          - Duplicate (will be replaced)
❌ daily-signals.yml          - Duplicate
❌ pr-checks.yml              - Not using
❌ FIX_WORKFLOW_NOT_APPEARING.md - Debug file
```

---

## 🚀 MANUAL STEPS

### **STEP 1: Navigate to workflows folder**

```powershell
cd C:\ai-advisor1\.github\workflows
```

---

### **STEP 2: Delete old files ONE BY ONE**

```powershell
# Delete backups
Remove-Item ci-cd_backup.yml -Force

# Delete old daily files
Remove-Item daily-scan.yml -Force
Remove-Item daily-signals.yml -Force

# Delete pr-checks
Remove-Item pr-checks.yml -Force

# Delete debug file
Remove-Item FIX_WORKFLOW_NOT_APPEARING.md -Force

# Verify
Get-ChildItem
# Should see: ci-cd.yml, daily-scanner.yml
```

---

### **STEP 3: Replace daily-scanner.yml with clean version**

```powershell
# Download daily-scan-clean.yml from chat first
# Then:

cd C:\ai-advisor1\.github\workflows

# Delete old daily-scanner.yml
Remove-Item daily-scanner.yml -Force

# Copy clean version
Copy-Item C:\ai-advisor1\daily-scan-clean.yml daily-scan.yml

# Verify
Get-ChildItem
# Should see ONLY: ci-cd.yml, daily-scan.yml
```

---

### **STEP 4: Commit and push**

```powershell
cd C:\ai-advisor1

# Add changes
git add .github/workflows/

# Check what changed
git status

# Commit
git commit -m "cleanup: Keep only ci-cd and daily-scan workflows"

# Push to staging
git push origin staging

# Merge to main
git checkout main
git merge staging
git push origin main
```

---

### **STEP 5: Verify on GitHub**

```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click: "All workflows" dropdown
3. Should see ONLY 2 workflows:
   - CI/CD Deploy
   - Daily Signal Scanner
```

---

## ✅ EXPECTED FINAL STATE

**Local: `.github/workflows/`**
```
ci-cd.yml        (1 KB)
daily-scan.yml   (7 KB)
```

**GitHub Actions:**
```
Workflows (2):
1. CI/CD Deploy
2. Daily Signal Scanner
```

**No more failed workflows!** ✅

---

## 🆘 TROUBLESHOOTING

### **Problem: Can't delete file "in use"**

```powershell
# Close all editors first
# Then force delete:
Remove-Item filename.yml -Force -ErrorAction SilentlyContinue
```

### **Problem: Git won't commit**

```powershell
# Force add
git add .github/workflows/ --force

# Force commit
git commit --allow-empty -m "cleanup: workflows"
```

### **Problem: Push rejected**

```powershell
git pull origin staging --rebase
git push origin staging
```

---

## 📊 VERIFICATION CHECKLIST

After cleanup:

- [ ] Only 2 .yml files in `.github/workflows/`
- [ ] No backup files (*.backup, *_backup.yml)
- [ ] No markdown files in workflows folder
- [ ] Changes committed to Git
- [ ] Pushed to staging
- [ ] Merged to main
- [ ] GitHub Actions shows 2 workflows only
- [ ] No failed workflows on GitHub

---

**TL;DR:**

```powershell
cd C:\ai-advisor1\.github\workflows

# Delete old files
Remove-Item ci-cd_backup.yml, daily-scan.yml, daily-signals.yml, pr-checks.yml, FIX_WORKFLOW_NOT_APPEARING.md -Force

# Replace daily-scanner with clean version
Remove-Item daily-scanner.yml -Force
Copy-Item C:\ai-advisor1\daily-scan-clean.yml daily-scan.yml

# Commit
cd C:\ai-advisor1
git add .github/workflows/
git commit -m "cleanup: 2 workflows only"
git push origin staging
```

**Done!** 🎉
