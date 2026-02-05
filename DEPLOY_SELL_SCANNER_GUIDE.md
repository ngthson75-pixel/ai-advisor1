# DEPLOY SELL SCANNER TO STAGING & SETUP GITHUB ACTIONS

**Date:** 2026-02-05  
**Status:** Ready to Deploy  

---

## 📋 OVERVIEW

Bạn sẽ thực hiện:
1. ✅ Push SELL scanner lên staging
2. ✅ Setup GitHub Actions cho quét tự động mỗi 1h
3. ✅ Test trên staging
4. ✅ Deploy to production

---

## 🚀 PART 1: DEPLOY TO STAGING

### Step 1: Kiểm tra files

```powershell
# Đảm bảo bạn có 2 files:
# 1. sell_signal_scanner_v2_production.py
# 2. hourly-sell-scanner.yml
```

### Step 2: Push scanner lên repo

```powershell
cd C:\ai-advisor1

# Copy scanner file
Copy-Item sell_signal_scanner_v2_production.py sell_signal_scanner_v2.py -Force

# Kiểm tra file
Get-Content sell_signal_scanner_v2.py -Head 20

# Add to git
git add sell_signal_scanner_v2.py
git commit -m "feat: Add SELL signal scanner V2 for hourly scanning"
git push origin staging
```

### Step 3: Verify file on staging

```powershell
# Kiểm tra file đã lên repo chưa
# GitHub → ai-advisor1 → Branch: staging → File: sell_signal_scanner_v2.py
```

---

## ⚙️ PART 2: SETUP GITHUB ACTIONS

### Step 1: Tạo workflow directory

```powershell
cd C:\ai-advisor1

# Tạo thư mục nếu chưa có
New-Item -ItemType Directory -Force -Path .github\workflows

# Kiểm tra
Get-ChildItem .github\workflows
```

### Step 2: Copy workflow file

```powershell
# Copy workflow
Copy-Item hourly-sell-scanner.yml .github\workflows\hourly-sell-scanner.yml -Force

# Kiểm tra
Get-Content .github\workflows\hourly-sell-scanner.yml -Head 30
```

### Step 3: Push workflow to GitHub

```powershell
git add .github\workflows\hourly-sell-scanner.yml
git commit -m "ci: Add hourly SELL signal scanner workflow"
git push origin staging
```

### Step 4: Verify workflow on GitHub

```
1. Vào GitHub: https://github.com/ngthson75-pixel/ai-advisor1
2. Click "Actions" tab
3. Bạn sẽ thấy: "Hourly SELL Signal Scanner"
4. Click vào workflow name để xem details
```

---

## 🧪 PART 3: TEST ON STAGING

### Test 1: Manual Trigger

```
1. GitHub → Actions → Hourly SELL Signal Scanner
2. Click "Run workflow" dropdown
3. Select branch: staging
4. Click "Run workflow" button
5. Wait 2-5 minutes
6. Check logs
```

**Expected output:**
```
🔍 SELL SCANNER - 2026-02-05 14:30:00
✓ Scanning 78 tickers...
🟢 VCB - TP_PARTIAL - +8.14%
🔴 HPG - MA20_CONSECUTIVE - -3.64%
...
✓ Generated 26 SELL signals

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SCAN RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before: 150 signals
After:  176 signals
New:    26 signals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Generated 26 new SELL signals
```

### Test 2: Verify signals in database

```powershell
# Check staging database
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/signals" | 
    ConvertFrom-Json | 
    Select-Object -ExpandProperty signals |
    Where-Object { $_.action -eq 'SELL' } |
    Select-Object -First 5
```

### Test 3: Check schedule

```
1. GitHub → Actions → Hourly SELL Signal Scanner
2. Scroll down to "Next scheduled run"
3. Should show next run time (Vietnam hours: 9, 10, 11, 13, 14)
```

---

## 📅 SCHEDULE DETAILS

### Scan Times (Vietnam Time - UTC+7)

```
🕘 9:00 AM  - Market open
🕙 10:00 AM - Mid-morning
🕚 11:00 AM - Pre-lunch
🕐 1:00 PM  - Post-lunch
🕑 2:00 PM  - Afternoon
```

**Note:** Lịch tự động chỉ chạy:
- Thứ 2-6 (Monday-Friday)
- Không chạy thứ 7, chủ nhật
- Không chạy 11:30-13:00 (nghỉ trưa)

### Cron Expression Explained

```yaml
- cron: '0 2 * * 1-5'   # 9:00 AM Vietnam
        │ │ │ │ └─────── Days (1-5 = Mon-Fri)
        │ │ │ └───────── Month (any)
        │ │ └─────────── Day of month (any)
        │ └───────────── Hour (2 = 9 AM Vietnam)
        └─────────────── Minute (0)
```

---

## 🔧 PART 4: TROUBLESHOOTING

### Issue 1: Workflow not showing up

**Check:**
```powershell
# Verify file exists
Get-Content .github\workflows\hourly-sell-scanner.yml

# Check git status
git status

# Re-push if needed
git add .github\workflows\hourly-sell-scanner.yml
git commit -m "ci: Fix workflow file"
git push origin staging
```

### Issue 2: Scanner fails on GitHub

**Check logs:**
```
1. GitHub → Actions → Latest run
2. Click on job name
3. Expand each step
4. Look for error messages
```

**Common fixes:**

A. **Missing dependencies:**
```yaml
# In workflow, make sure this line exists:
pip install --break-system-packages vnstock pandas requests python-dotenv
```

B. **Database path wrong:**
```python
# Scanner should use environment variable if available
db_path = os.getenv('DATABASE_URL', 'signals.db')
```

C. **Backend sleeping:**
```yaml
# Workflow already includes wake-up step
# If still failing, increase retries:
for i in {1..5}; do  # Was 3, now 5
```

### Issue 3: No signals generated

**This is NORMAL if:**
- Market không có BUY signals nào trigger SELL conditions
- VD: Tất cả stocks đều trên MA20, không có SL trigger

**Verify:**
```sql
-- Check có BUY signals không
SELECT COUNT(*) FROM signals WHERE action='BUY';

-- Check SELL signals
SELECT COUNT(*) FROM signals WHERE action='SELL' AND exit_date='2026-02-05';
```

---

## 📊 PART 5: MONITORING

### Daily Monitoring Checklist

```
1. Check GitHub Actions:
   - Go to: github.com/ngthson75-pixel/ai-advisor1/actions
   - Verify: All 5 daily runs completed ✓
   
2. Check signal count:
   - Before day: X signals
   - After day: Y signals
   - New today: Y - X

3. Check errors:
   - If any run failed → Check logs
   - If rate limit → Increase delay
   - If database error → Check migration
```

### Weekly Monitoring

```powershell
# Get summary for past 7 days
sqlite3 signals.db "
SELECT 
    exit_date,
    COUNT(*) as count,
    COUNT(CASE WHEN profit_loss_pct > 0 THEN 1 END) as wins,
    COUNT(CASE WHEN profit_loss_pct <= 0 THEN 1 END) as losses,
    ROUND(AVG(profit_loss_pct), 2) as avg_pl
FROM signals
WHERE action='SELL' 
    AND exit_date >= DATE('now', '-7 days')
GROUP BY exit_date
ORDER BY exit_date DESC;
"
```

---

## 🎯 PART 6: DEPLOY TO PRODUCTION

**ONLY after staging tests pass!**

### Step 1: Merge staging to main

```powershell
cd C:\ai-advisor1

# Switch to main
git checkout main

# Merge staging
git merge staging

# Push to production
git push origin main
```

### Step 2: Verify production deployment

```
1. Render → ai-advisor1-backend → Latest deploy
2. Wait 3-5 minutes
3. Check scanner file exists
```

### Step 3: Verify workflow on production

```
1. GitHub → Actions
2. Workflow now runs on main branch
3. Monitor first few runs
```

---

## 📈 EXPECTED RESULTS

### Performance Metrics

```
Scan frequency: 5 times/day (Mon-Fri)
Scans per week: 25 scans
Scans per month: ~100 scans

Per scan:
- Duration: 1-3 minutes
- Tickers checked: 50-100
- Signals generated: 0-30
- API calls: 50-100 (VCI)
- Cost: $0 (free tier)
```

### Signal Quality

```
Daily SELL signals: 5-50 (depends on market)

By reason (typical):
- SL: 5-10%
- TP_PARTIAL: 10-20%
- MA20_CONSECUTIVE: 60-70%
- MA20_HIGH_VOLUME: 5-10%
```

---

## 🔐 SECURITY NOTES

### Environment Variables

```yaml
# Already set in workflow:
env:
  API_URL: https://ai-advisor1-backend.onrender.com/api

# If you need secrets:
# GitHub → Settings → Secrets → Actions
# Add: DATABASE_URL, API_KEY, etc.
```

### Rate Limiting

```
Current: 2s delay between VCI requests
GitHub Actions free tier: 2000 minutes/month
Usage: ~5 min/day × 22 days = 110 min/month
Utilization: 5.5% ✓
```

---

## 📞 SUPPORT

**Files:**
- Scanner: `sell_signal_scanner_v2_production.py`
- Workflow: `hourly-sell-scanner.yml`
- This guide: `DEPLOY_SELL_SCANNER_GUIDE.md`

**Resources:**
- GitHub Actions docs: https://docs.github.com/en/actions
- Cron syntax: https://crontab.guru/
- Render docs: https://render.com/docs

**Contact:**
- Owner: Nguyễn Thanh Sơn
- Email: ngthson75@gmail.com
- Phone: +84938127666

---

## ✅ DEPLOYMENT CHECKLIST

**Pre-deployment:**
- [ ] Files downloaded
- [ ] Scanner tested locally
- [ ] Workflow syntax valid

**Staging:**
- [ ] Scanner pushed to staging branch
- [ ] Workflow file pushed
- [ ] Manual trigger successful
- [ ] Signals generated correctly
- [ ] No errors in logs

**Production:**
- [ ] All staging tests pass
- [ ] Merged to main branch
- [ ] Production deploy verified
- [ ] First automated scan successful
- [ ] Monitoring in place

---

**Ready to deploy!** 🚀

Just follow the steps above in order.
