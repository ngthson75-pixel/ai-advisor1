# QUICK FIX: HOURLY SELL SCANNER V5.2

**Time:** 10 phút  
**Goal:** Fix failed workflow + Update V5.2  

---

## 🚀 3 BƯỚC ĐƠN GIẢN

### BƯỚC 1: Upload Files (3 phút)

```powershell
cd C:\ai-advisor1

# Copy 2 files từ Claude:
# 1. sell_signal_scanner_v5.2.py → root folder
# 2. vietnam_holidays.json → root folder

git add sell_signal_scanner_v5.2.py vietnam_holidays.json
git commit -m "feat: SELL V5.2 scanner"
git push origin main
```

---

### BƯỚC 2: Update Workflow (3 phút)

```powershell
# Copy file từ Claude:
# hourly-sell-scanner.yml → .github/workflows/

cd .github\workflows
git add hourly-sell-scanner.yml
git commit -m "fix: Update hourly SELL to V5.2"
git push origin main
```

---

### BƯỚC 3: Test (4 phút)

1. Vào: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click: "Hourly SELL Signal Scanner"
3. Click: "Run workflow" → "Run workflow"
4. Wait 2-3 min
5. Check logs: Should see ✅

---

## ✅ EXPECTED RESULT

**Before (Failed):**
```
❌ Hourly SELL Signal Scanner #77: Failed
❌ Hourly SELL Signal Scanner #78: Failed
```

**After (Success):**
```
✅ Hourly SELL Signal Scanner #79: Success
📊 Active BUY positions: 30
🔍 Scanner V5.2 completed
✅ SELL signals: 1-3
```

---

## 📋 FILES TO DOWNLOAD FROM CLAUDE

1. **sell_signal_scanner_v5.2.py** - Scanner code
2. **vietnam_holidays.json** - Holiday calendar
3. **hourly-sell-scanner.yml** - Workflow file
4. **HOURLY_SELL_V5.2_DEPLOYMENT.md** - Full guide (if issues)

---

## 🎯 DONE!

**Hourly automation:**
- ✅ Runs every hour (9AM-3PM)
- ✅ Uses V5.2 (T+2 + MA20 strict)
- ✅ No more failed runs

**Daily manual:**
- ✅ You run EOD for final check
- ✅ Use same V5.2 local

**Perfect combination!** 🚀
