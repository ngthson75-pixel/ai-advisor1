# 🤖 TỰ ĐỘNG DOWNLOAD EOD - QUICK REFERENCE

## ⚡ SETUP 1 LẦN (15 PHÚT)

```powershell
cd C:\ai-advisor1

# 1. Download files (from Claude):
#    - auto_download_eod_cron.py
#    - backend_api_v3_autorefresh.py

# 2. Deploy:
copy auto_download_eod_cron.py . /Y
copy backend_api_v3_autorefresh.py backend_api.py /Y
git add auto_download_eod_cron.py backend_api.py
git commit -m "Add: Automated EOD download"
git push origin main

# 3. Setup Render Cron Job:
#    Dashboard → Cron Jobs → New
#    Command: python auto_download_eod_cron.py
#    Schedule: 0 18 * * 1-5
#    (6PM Monday-Friday)

# 4. Test:
#    Render Shell → python auto_download_eod_cron.py
#    Wait 15 mins → Done!
```

---

## 📅 LỊCH TỰ ĐỘNG

```
THỨ 2-6 (NGÀY GIAO DỊCH):
├─ 15:00: Thị trường đóng cửa
├─ 17:00: EOD data ready
├─ 18:00: 🤖 Cron job tự động chạy
├─ 18:01: ✅ Check: Hôm nay là ngày giao dịch
├─ 18:02: 📥 Start download 150 tickers
├─ 18:15: ✅ Download complete
├─ 18:16: 🔗 Create symlink: latest_prices_all.json
├─ 18:17: 🗑️ Delete files >5 days
└─ 18:18: ✅ Done! Backend reads new prices!

THỨ 7, CHỦ NHẬT:
├─ 18:00: 🤖 Cron still runs (scheduled)
├─ 18:01: ⏸️ "Not a trading day - Skipping"
└─ 18:02: ✅ Exit (no download)
```

---

## 📁 FILE MANAGEMENT

### **Week 1:**
```
Mon: eod_prices_2026-01-06.json ✅
Tue: eod_prices_2026-01-07.json ✅
Wed: eod_prices_2026-01-08.json ✅
Thu: eod_prices_2026-01-09.json ✅
Fri: eod_prices_2026-01-10.json ✅
     latest_prices_all.json → eod_prices_2026-01-10.json
```

### **Week 2 (Auto-cleanup):**
```
Mon: eod_prices_2026-01-13.json ✅ (new)
     🗑️ DELETE: eod_prices_2026-01-06.json (7 days old)
     🗑️ DELETE: eod_prices_2026-01-07.json (6 days old)
     ✅ KEEP: eod_prices_2026-01-08.json (5 days)
     ✅ KEEP: eod_prices_2026-01-09.json (4 days)
     ✅ KEEP: eod_prices_2026-01-10.json (3 days)
     
Result: Always 4-5 most recent files
```

---

## 🔍 MONITORING

### **Check Status:**
```powershell
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/status
```

**Expected Response:**
```json
{
  "success": true,
  "file_exists": true,
  "tickers_count": 142,
  "file_age_days": 0,
  "last_modified": "2026-01-11T18:15:00",
  "needs_refresh": false
}
```

### **Check Render Logs:**
```
Render Dashboard → ai-advisor1-backend → Logs

Look for:
✅ "Loaded 142 prices from EOD file"
✅ "File age: 0 days (TTL: 5 days)"
```

### **Check Cron Job:**
```
Render Dashboard → Cron Jobs → auto-download-eod

Last Run: 2026-01-11 18:00
Status: Success ✅
Duration: 15m 23s
```

---

## 🧪 TEST

### **Manual Test:**
```bash
# Render Shell:
python auto_download_eod_cron.py

# Output:
🤖 AUTO EOD DOWNLOAD CRON JOB
✅ Today is Monday - Trading day!
📥 Downloading 150 tickers...
[1/150] VCB... ✅ 90,000
[2/150] MBB... ✅ 27,500
...
✅ DOWNLOAD COMPLETE!
📁 Saved to: eod_prices_2026-01-11.json
🔗 Created symlink: latest_prices_all.json
🗑️ Deleted 2 old files
✅ CRON JOB COMPLETE
```

### **Website Test:**
```
1. Visit: https://ai-advisor.vn
2. Tab: "Quản trị đầu tư"
3. Add: MBB, 100, 23000

Expected:
  Mua: 23,000 VND
  Hiện tại: 27,500 VND ✅
  P&L: +19.57% (green) ✅
```

---

## ⚙️ CONFIGURATION

### **Change Time:**
```yaml
# Render Cron Job Schedule:

0 18 * * 1-5  # 6PM (default) ✅
0 17 * * 1-5  # 5PM
0 19 * * 1-5  # 7PM
30 18 * * 1-5  # 6:30PM
```

### **Change Retention Days:**
```python
# Edit: auto_download_eod_cron.py
# Line 17:
EOD_FILE_TTL_DAYS = 5  # Change to 3, 7, 10
```

### **Add More Tickers:**
```python
# Edit: auto_download_eod_cron.py
# Function: get_all_tickers()
# Add to major_tickers list:
'YOUR', 'NEW', 'TICKERS', ...
```

---

## 🐛 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Cron not running | Check schedule: `0 18 * * 1-5` |
| Download fails | Check Render logs for errors |
| Old files not deleted | Verify TTL setting (5 days) |
| Prices not updating | Check symlink: `latest_prices_all.json` |
| MBB still shows 27.3 | Backend hasn't reloaded → Restart Render |

---

## 💰 COST

**Render Free Tier:**
- ✅ 400 hours/month
- ✅ Usage: ~5.5 hours/month (1.4%)
- ✅ Cost: **$0** 🎉

**vnstock API:**
- ✅ Free
- ✅ Rate limited (handled by script)

**Total: $0/month** ✅

---

## ✅ CHECKLIST

### **One-Time Setup:**
- [ ] Download 2 files
- [ ] Push to GitHub
- [ ] Setup Render Cron Job
- [ ] Test manual run
- [ ] Verify files created

### **Daily (Automatic):**
- [x] 6PM: Cron runs ✅
- [x] Download completes ✅
- [x] Files cleaned up ✅
- [x] **Admin does NOTHING!** 🎉

---

## 🎯 SUMMARY

**What You Get:**
1. ✅ Tự động download EOD (Thứ 2-6, 6PM)
2. ✅ Tự động cleanup files cũ
3. ✅ Giá chính xác: MBB = 27,500
4. ✅ Portfolio load nhanh: <0.1s
5. ✅ Zero maintenance
6. ✅ Free forever

**Admin chỉ cần:**
- ✅ Setup 1 lần (15 phút)
- ✅ Kiểm tra logs thỉnh thoảng (optional)
- ✅ **KHÔNG CẦN LÀM GÌ THÊM!** 🎉

---

## 📞 QUICK COMMANDS

```powershell
# Deploy:
cd C:\ai-advisor1
git add auto_download_eod_cron.py backend_api.py
git commit -m "Add: Auto EOD"
git push origin main

# Check status:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/status

# Check files (Render Shell):
ls -lh eod_prices*.json
ls -lh latest_prices_all.json

# Manual run (Render Shell):
python auto_download_eod_cron.py
```

---

**Setup: 15 minutes**  
**Daily work: 0 minutes** ✅  
**Cost: $0** ✅  
**Peace of mind: Priceless** 🎉
