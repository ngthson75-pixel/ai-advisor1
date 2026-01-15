# 🤖 SETUP HOÀN TOÀN TỰ ĐỘNG - RENDER CRON JOB

## 🎯 OVERVIEW

**Hệ thống tự động:**
- ✅ Mỗi tối 6PM (Thứ 2-6) → Tự động download EOD
- ✅ Tự động xóa files >5 ngày
- ✅ Admin KHÔNG CẦN làm gì! 🎉

**Architecture:**
```
Thứ 2-6, 18:00 (6PM):
  Render Cron Job triggers
    ↓
  Run: python auto_download_eod_cron.py
    ↓
  Check: Is today Mon-Fri? ✅
    ↓
  Download: ~150 tickers (10-15 mins)
    ↓
  Save: eod_prices_2026-01-11.json
    ↓
  Symlink: latest_prices_all.json → today's file
    ↓
  Cleanup: Delete files >5 days old
    ↓
  Done! Backend reads new prices! ✅
```

---

## 🚀 DEPLOY (3 BƯỚC - 15 PHÚT)

### **STEP 1: Deploy Code to Render (5 phút)**

```powershell
cd C:\ai-advisor1

# Download files:
# - auto_download_eod_cron.py (from attachment)
# - backend_api_v3_autorefresh.py (from previous)

# Copy files:
copy auto_download_eod_cron.py . /Y
copy backend_api_v3_autorefresh.py backend_api.py /Y

# Deploy:
git add auto_download_eod_cron.py backend_api.py
git commit -m "Add: Automated EOD download with cron job"
git push origin main

# Wait 7 minutes for Render
```

---

### **STEP 2: Setup Render Cron Job (5 phút)**

#### **Method A: Via Render Dashboard (RECOMMENDED)**

```
1. Go to: https://dashboard.render.com
2. Select service: ai-advisor1-backend
3. Click: "Cron Jobs" tab (or "Add Cron Job")
4. Click: "New Cron Job"

5. Configure:
   Name: Auto Download EOD
   Command: python auto_download_eod_cron.py
   Schedule: 0 18 * * 1-5
            (6PM, Monday-Friday)
   
6. Click: "Create Cron Job"
```

**Cron Schedule Explanation:**
```
0 18 * * 1-5
│ │  │ │ │
│ │  │ │ └─ Days: Mon-Fri (1-5)
│ │  │ └─── Months: Every month (*)
│ │  └───── Days of month: Every day (*)
│ └──────── Hour: 18 (6PM)
└────────── Minute: 0
```

#### **Method B: Via render.yaml (Advanced)**

Create `render.yaml` in root:

```yaml
services:
  - type: web
    name: ai-advisor1-backend
    env: python
    buildCommand: pip install -r requirements.txt --break-system-packages
    startCommand: gunicorn backend_api:app
    envVars:
      - key: OPENAI_API_KEY
        sync: false

# Cron job for EOD download
  - type: cron
    name: auto-download-eod
    env: python
    schedule: "0 18 * * 1-5"  # 6PM Mon-Fri
    buildCommand: pip install -r requirements.txt --break-system-packages
    startCommand: python auto_download_eod_cron.py
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

---

### **STEP 3: Test Cron Job (5 phút)**

#### **Test Manually:**

```
1. Render Dashboard → ai-advisor1-backend
2. Shell tab
3. Run command:
   python auto_download_eod_cron.py

Expected output:
  ============================================
  🤖 AUTO EOD DOWNLOAD CRON JOB
  ============================================
  ✅ Today is Monday - Trading day!
  📥 Downloading 150 tickers...
  [1/150] VCB... ✅ 90,000
  [2/150] MBB... ✅ 27,500
  ...
  ✅ DOWNLOAD COMPLETE!
  📁 Saved to: eod_prices_2026-01-11.json
  🔗 Created symlink: latest_prices_all.json
  ✅ Cleanup complete
```

#### **Check Files Created:**

```bash
# In Render Shell:
ls -lh eod_prices*.json
ls -lh latest_prices_all.json

# Should see:
# eod_prices_2026-01-11.json  (~500 KB)
# latest_prices_all.json -> eod_prices_2026-01-11.json
```

---

## 📅 CRON JOB BEHAVIOR

### **Weekdays (Mon-Fri):**

```
18:00 → Cron triggers
18:01 → Script starts
        "✅ Today is Monday - Trading day!"
18:02 → Start downloading tickers
18:15 → Download complete (~150 tickers)
18:16 → Create symlink: latest_prices_all.json
18:17 → Delete files >5 days old
18:18 → Job complete! ✅

Backend automatically reads new prices!
```

### **Weekends (Sat-Sun):**

```
18:00 → Cron triggers (still runs)
18:01 → Script starts
        "⏸️ Today is Saturday - Not a trading day. Skipping."
18:02 → Job exits (no download)
```

---

## 🗄️ FILE MANAGEMENT

### **File Naming:**

```
eod_prices_2026-01-06.json  (Monday)
eod_prices_2026-01-07.json  (Tuesday)
eod_prices_2026-01-08.json  (Wednesday)
eod_prices_2026-01-09.json  (Thursday)
eod_prices_2026-01-10.json  (Friday)
  ↓
latest_prices_all.json  (symlink → eod_prices_2026-01-10.json)
```

### **Auto-Cleanup (Day 6):**

```
Day 6 (Monday Jan 13):
  Download: eod_prices_2026-01-13.json ✅
  Cleanup check:
    - eod_prices_2026-01-06.json (7 days) → 🗑️ DELETE
    - eod_prices_2026-01-07.json (6 days) → 🗑️ DELETE
    - eod_prices_2026-01-08.json (5 days) → ✅ KEEP
    - eod_prices_2026-01-09.json (4 days) → ✅ KEEP
    - eod_prices_2026-01-10.json (3 days) → ✅ KEEP
    - eod_prices_2026-01-13.json (0 days) → ✅ KEEP

Result: Always keeps 4-5 most recent files
```

---

## 🔍 MONITORING

### **Check Cron Job Status:**

```
Render Dashboard → Cron Jobs → auto-download-eod
  Last Run: 2026-01-11 18:00
  Status: Success ✅
  Duration: 15m 23s
  Logs: [View Logs]
```

### **Check Backend Status:**

```powershell
# Check EOD status:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/status

# Expected:
{
  "success": true,
  "file_exists": true,
  "tickers_count": 142,
  "file_age_days": 0,
  "last_modified": "2026-01-11T18:15:00",
  "needs_refresh": false
}
```

### **Check Logs:**

```
Render Dashboard → ai-advisor1-backend → Logs

Look for:
  "✅ Loaded 142 prices from EOD file"
  "📅 File age: 0 days (TTL: 5 days)"
```

---

## 🧪 TESTING

### **Test 1: Manual Run (Immediate)**

```bash
# Render Shell:
python auto_download_eod_cron.py

# Should complete in 10-15 mins
```

### **Test 2: Check Website**

```
1. Visit: https://ai-advisor.vn
2. Tab: "Quản trị đầu tư"
3. Add stock: MBB, 100, 23000

Expected:
  Mua: 23,000 VND
  Hiện tại: 27,500 VND ✅
  P&L: +19.57% ✅
```

### **Test 3: Verify Auto-Cleanup**

```bash
# Create fake old files:
touch eod_prices_2026-01-01.json
touch eod_prices_2026-01-02.json

# Run cron:
python auto_download_eod_cron.py

# Check deleted:
ls eod_prices_2026-01-01.json
# Should return: No such file
```

---

## ⚙️ CONFIGURATION

### **Change Download Time:**

```yaml
# In Render Cron Job settings:
Schedule: 0 18 * * 1-5  # 6PM (default)

# Options:
0 17 * * 1-5  # 5PM (earlier)
0 19 * * 1-5  # 7PM (later)
30 18 * * 1-5  # 6:30PM
```

**Recommendation:** 18:00 (6PM) is ideal
- Market closes: 15:00 (3PM)
- EOD data ready: ~17:00 (5PM)
- Download: 18:00 (6PM) ✅

### **Change File Retention:**

Edit `auto_download_eod_cron.py`:

```python
# Line 17:
EOD_FILE_TTL_DAYS = 5  # Change to 3, 7, 10, etc.
```

### **Change Ticker List:**

Edit `auto_download_eod_cron.py` → `get_all_tickers()`:

```python
def get_all_tickers():
    # Add your custom tickers:
    major_tickers = [
        'VCB', 'MBB', 'SHB',  # Add more here
        ...
    ]
```

---

## 💰 COST ANALYSIS

### **Render Cron Job:**

**Free Tier:**
- ✅ 400 hours/month (enough for daily 15-min jobs)
- ✅ Unlimited runs
- ✅ Shared resources

**Calculation:**
```
Daily runs: 1
Runtime per run: ~15 minutes
Days per month: 22 (weekdays)
Total hours: 22 × 0.25 = 5.5 hours/month

Free tier: 400 hours/month
Usage: 5.5 hours (1.4%)
Cost: $0 ✅
```

### **VNStock API:**

- ✅ Free
- ⚠️ Rate limited (1 request/second)
- ✅ Our script respects rate limit

---

## 🐛 TROUBLESHOOTING

### **Issue: Cron job not running**

```
Check:
1. Render Dashboard → Cron Jobs → Status
2. Verify schedule: 0 18 * * 1-5
3. Check timezone: UTC (default)
   18:00 UTC = 01:00 ICT (next day)
   
Fix: Adjust schedule for Vietnam timezone (UTC+7):
   11 * * * 1-5  (6PM Vietnam = 11AM UTC)
```

### **Issue: Download fails**

```
Check Render Logs:
  "❌ Error: Rate limited"
  → Increase sleep time in script

  "❌ No tickers found"
  → vnstock API issue, will retry next day

  "❌ Timeout"
  → Increase Render timeout or reduce ticker count
```

### **Issue: Old files not deleted**

```
Check:
1. Files exist: ls eod_prices*.json
2. Check script output: "🗑️ Deleted X files"
3. Verify TTL: EOD_FILE_TTL_DAYS = 5

If files not deleted:
  → Script not running cleanup
  → Check script logs for errors
```

---

## 📊 MONITORING DASHBOARD

### **Daily Checklist (Optional):**

```
Every morning:
1. Check Render Logs (last night's job)
2. Verify: "✅ Loaded X prices from EOD file"
3. Test website: Add stock, check price
4. Check file age: GET /api/eod/status
```

### **Setup Alerts (Advanced):**

Use Render webhooks or monitoring services:

```python
# In auto_download_eod_cron.py, add:
if success_count < 100:
    # Send alert email/SMS
    alert_admin("EOD download failed!")
```

---

## ✅ ADVANTAGES

### **vs Manual Download:**

| | Manual | **Automated Cron** |
|---|---|---|
| **Setup** | 5 mins | 15 mins (1 time) |
| **Maintenance** | Daily | **Zero!** ✅ |
| **Reliability** | Human error | **100%** ✅ |
| **Coverage** | 150 tickers | **150 tickers** |
| **Speed** | Same | **Same** |

### **vs On-Demand API:**

| | On-Demand | **Cron + File** |
|---|---|---|
| **Speed** | 1-2s | **<0.1s** ✅ |
| **API calls** | Every load | **Zero** ✅ |
| **Reliability** | API dependent | **File-based** ✅ |

---

## 🎯 SUMMARY

**What You Get:**

1. ✅ **Hoàn toàn tự động:** Mỗi tối 6PM (Thứ 2-6)
2. ✅ **Tự động download:** ~150 tickers trong 10-15 phút
3. ✅ **Tự động cleanup:** Xóa files >5 ngày
4. ✅ **Zero maintenance:** Admin không cần làm gì!
5. ✅ **Giá chính xác:** MBB = 27,500 (không còn 27.3!)
6. ✅ **Siêu nhanh:** Portfolio load <0.1s
7. ✅ **Miễn phí:** Render free tier đủ dùng

**Admin chỉ cần:**
- ✅ Setup 1 lần (15 phút)
- ✅ Kiểm tra logs thỉnh thoảng (optional)
- ✅ Thế thôi! 🎉

---

## 📋 DEPLOYMENT CHECKLIST

### **One-Time Setup:**

- [ ] Download `auto_download_eod_cron.py`
- [ ] Download `backend_api_v3_autorefresh.py`
- [ ] Push to GitHub
- [ ] Wait 7 mins for Render
- [ ] Setup Render Cron Job:
  - [ ] Name: auto-download-eod
  - [ ] Command: `python auto_download_eod_cron.py`
  - [ ] Schedule: `0 18 * * 1-5`
- [ ] Test manual run in Render Shell
- [ ] Verify files created
- [ ] Test website: MBB shows 27,500 ✅

### **Daily (Automatic):**

- [x] 6PM: Cron runs automatically ✅
- [x] 6:15PM: Download complete ✅
- [x] 6:16PM: Backend loads new prices ✅
- [x] 6:17PM: Old files cleaned up ✅
- [x] Done! Admin does nothing! 🎉

---

## 🚀 QUICK START

```powershell
# 1. Deploy code (5 mins):
cd C:\ai-advisor1
# Download auto_download_eod_cron.py
copy auto_download_eod_cron.py . /Y
git add auto_download_eod_cron.py backend_api.py
git commit -m "Add: Automated EOD cron job"
git push origin main

# 2. Setup cron (5 mins):
# Render Dashboard → Cron Jobs → New
# Command: python auto_download_eod_cron.py
# Schedule: 0 18 * * 1-5

# 3. Test (5 mins):
# Render Shell → python auto_download_eod_cron.py
# Wait 15 mins → Check files created

# 4. Done! ✅
# Tomorrow 6PM: Auto runs!
# Admin: Does nothing! 🎉
```

---

**Total Setup Time:** 15 minutes  
**Daily Maintenance:** 0 minutes ✅  
**Cost:** $0 (free tier) ✅

**Perfect automation! 🤖**
