# HOURLY SELL SCANNER V5.2 - DEPLOYMENT GUIDE

**Date:** 2026-03-01  
**Purpose:** Fix failed "Hourly SELL Signal Scanner" + Update V5.2  
**Status:** Production Ready  

---

## 🔴 VẤN ĐỀ HIỆN TẠI

**Screenshot shows:**
```
❌ Hourly SELL Signal Scanner #77: Failed (1m 5s)
❌ Hourly SELL Signal Scanner #78: Failed (2s)
```

**Possible causes:**
1. Old scanner code có bug
2. Missing vietnam_holidays.json
3. API compatibility issues
4. Timeout too short

---

## ✅ GIẢI PHÁP: UPDATE V5.2

### BƯỚC 1: Upload Files Lên GitHub (5 phút)

```powershell
cd C:\ai-advisor1

# 1. Copy V5.2 scanner (đã download từ Claude)
# Đặt file sell_signal_scanner_v5.2.py vào thư mục chính

# 2. Copy vietnam_holidays.json (đã download từ Claude)
# Đặt file vietnam_holidays.json vào thư mục chính

# 3. Verify files
ls sell_signal_scanner_v5.2.py
ls vietnam_holidays.json

# 4. Commit & Push
git add sell_signal_scanner_v5.2.py vietnam_holidays.json
git commit -m "feat: Add SELL Scanner V5.2 with T+2 trading days + MA20 strict"
git push origin main
```

---

### BƯỚC 2: Update Workflow File (3 phút)

```powershell
# 1. Backup workflow cũ (nếu có)
cd C:\ai-advisor1\.github\workflows

# Tìm file workflow hiện tại:
ls *sell*.yml
# Có thể là: hourly-sell-scanner.yml hoặc scan-sell-hourly.yml

# Backup
Copy-Item hourly-sell-scanner.yml hourly-sell-scanner.yml.backup

# 2. Download workflow mới từ Claude
# Copy hourly-sell-scanner.yml (new) vào .github/workflows/

# 3. Verify
cat .github\workflows\hourly-sell-scanner.yml | Select-String "v5.2"
# Expected: Thấy "sell_signal_scanner_v5.2.py"

# 4. Commit & Push
git add .github/workflows/hourly-sell-scanner.yml
git commit -m "fix: Update Hourly SELL Scanner to V5.2"
git push origin main
```

---

### BƯỚC 3: Test Workflow (5 phút)

**Manual trigger on GitHub:**

1. Vào: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click: "Hourly SELL Signal Scanner" (left sidebar)
3. Click: "Run workflow" (top right)
4. Select: Branch "main"
5. Click: "Run workflow" (green button)

**Wait 2-3 minutes, then check:**

```
Expected output:
✅ Setup Python
✅ Install dependencies
✅ Wake backend
📊 Active BUY positions: 30
🔍 Running SELL Scanner V5.2...
✅ Scanner completed: 1-3 SELL signals
📊 Summary
```

**If SUCCESS:**
- ✅ Workflow fixed!
- ✅ V5.2 running
- ✅ Hourly automation ready

**If FAILED:**
- Check logs for error
- See "TROUBLESHOOTING" below

---

## 🐛 TROUBLESHOOTING

### Issue 1: "sell_signal_scanner_v5.2.py not found"

**Cause:** File chưa được push lên GitHub

**Fix:**
```powershell
cd C:\ai-advisor1
git add sell_signal_scanner_v5.2.py
git commit -m "Add V5.2 scanner"
git push origin main
```

---

### Issue 2: "vietnam_holidays.json not found"

**Cause:** File chưa được push lên GitHub

**Fix:**
```powershell
cd C:\ai-advisor1
git add vietnam_holidays.json
git commit -m "Add holidays calendar"
git push origin main
```

---

### Issue 3: "ModuleNotFoundError: No module named 'vnstock3'"

**Cause:** Workflow không install vnstock3

**Fix:** Check workflow file có dòng:
```yaml
- name: Install dependencies
  run: |
    pip install requests vnstock3  # ← Must have vnstock3!
```

---

### Issue 4: "POST /api/signals returns 405"

**Cause:** Backend API chưa support POST

**Fix:** Verify backend có endpoint:
```python
# backend_api.py line 390
@app.route('/api/signals', methods=['GET', 'POST'])  # ← Must have POST!
```

If not, update backend:
```powershell
# Edit backend_api.py, add POST method
git add backend_api.py
git commit -m "feat: Add POST /api/signals"
git push origin main
# Render auto-deploys in 3-5 min
```

---

### Issue 5: "Timeout after 15 minutes"

**Cause:** Scanner quét quá lâu

**Fix:** Tăng timeout trong workflow:
```yaml
jobs:
  scan-sell-signals:
    timeout-minutes: 30  # Increase from 15
```

---

### Issue 6: "No BUY signals to check"

**Cause:** Chưa có BUY signals active

**This is normal if:**
- Chưa chạy BUY scanner
- Tất cả signals đã bán hết
- Market không có cơ hội

**Not an error!** Just skip.

---

## 📊 EXPECTED BEHAVIOR

### Schedule (Automatic):
```
9:00 AM Vietnam (Mon-Fri) → Run
10:00 AM Vietnam → Run
11:00 AM Vietnam → Run
...
3:00 PM Vietnam → Run (last run)

Weekend, Holidays → Skip
```

### Output (Each Run):
```
📊 Active BUY positions: 30
🔍 Scanning 30 signals...

Results:
  🟢 PC1: TP+10% → Sell 30%
  ⏳ BID: Skip T+2 (1 trading day only)
  ✅ CTR: Hold (profit +2.47% >= 2%)

📊 SELL signals: 1
⏳ Skipped T+2: 1
```

---

## 📋 VERIFICATION CHECKLIST

**After deployment:**

- [ ] Files pushed to GitHub:
  - [ ] sell_signal_scanner_v5.2.py
  - [ ] vietnam_holidays.json
  - [ ] .github/workflows/hourly-sell-scanner.yml

- [ ] Workflow file updated:
  - [ ] Uses sell_signal_scanner_v5.2.py
  - [ ] Installs vnstock3
  - [ ] Has vietnam_holidays.json

- [ ] Manual test passed:
  - [ ] Run workflow manually
  - [ ] Check logs (no errors)
  - [ ] Verify SELL signals created

- [ ] Automatic schedule works:
  - [ ] Wait for next hour
  - [ ] Check workflow runs automatically
  - [ ] Verify SELL signals appear

---

## 🎯 SUCCESS CRITERIA

**Hourly automation SUCCESS when:**

1. ✅ Workflow runs every hour (9AM-3PM)
2. ✅ No errors in logs
3. ✅ SELL signals created correctly
4. ✅ T+2 logic working (skip signals < 2 trading days)
5. ✅ MA20 STRICT working (không bán mã lời >= 2%)

**Compare with manual EOD:**

```
Hourly Auto: Catch early exits (TP, SL)
Daily Manual: Final check + adjustments
```

Both complement each other! ✅

---

## 📞 ROLLBACK PLAN

**If V5.2 has issues:**

```powershell
cd C:\ai-advisor1\.github\workflows

# Restore old workflow
Copy-Item hourly-sell-scanner.yml.backup hourly-sell-scanner.yml -Force

git add hourly-sell-scanner.yml
git commit -m "rollback: Restore old hourly scanner"
git push origin main
```

---

## 🚀 NEXT STEPS

**After deployment SUCCESS:**

1. **Monitor Day 1:**
   - Check logs hourly
   - Verify SELL signals correct
   - Compare with manual EOD

2. **Week 1:**
   - Track false sells (if any)
   - Adjust MA20 threshold if needed
   - Monitor T+2 skips

3. **Month 1:**
   - Compare hourly vs daily results
   - Optimize schedule if needed
   - Consider adding alerts (Telegram/Email)

---

**DEPLOY NOW AND FIX THE FAILED RUNS!** 🚀
