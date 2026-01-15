# 🚀 DEPLOY AUTO-REFRESH EOD SYSTEM

## 📋 OVERVIEW

**System:**
- Download EOD file 1 lần (~30-60 phút)
- Backend đọc từ file (nhanh <0.1s)
- Auto-delete file sau 5 ngày
- Admin chạy download lại khi cần

**Files:**
1. `backend_api_v3_autorefresh.py` - Backend with auto-refresh
2. `download_all_eod_prices.py` - Download script
3. `latest_prices_all.json` - EOD data file (~5-10 MB)

---

## ⚡ QUICK DEPLOY (30 PHÚT)

### **PHASE 1: DEPLOY BACKEND (5 PHÚT)**

```powershell
cd C:\ai-advisor1

# Download files (from attachments above):
# - backend_api_v3_autorefresh.py
# - download_all_eod_prices.py

# Replace backend:
copy backend_api_v3_autorefresh.py backend_api.py /Y

# Add download script:
copy download_all_eod_prices.py . /Y

# Deploy:
git add backend_api.py download_all_eod_prices.py
git commit -m "Add: Auto-refresh EOD system (5-day TTL)"
git push origin main

# Wait 7 minutes for Render
```

---

### **PHASE 2: DOWNLOAD EOD FILE (30-60 PHÚT)**

#### **Option A: Download Locally (RECOMMENDED)**

```powershell
cd C:\ai-advisor1

# Install vnstock (if not installed):
pip install vnstock --break-system-packages

# Run download (takes 30-60 minutes!):
python download_all_eod_prices.py

# Output: latest_prices_all.json (~5-10 MB)
# Success: ~100-150 tickers (fallback mode)
# With API: ~2000+ tickers (full mode)
```

#### **Option B: Download on Render (via SSH or manual trigger)**

```bash
# SSH into Render (if available)
cd /opt/render/project/src
python download_all_eod_prices.py
```

---

### **PHASE 3: UPLOAD FILE TO BACKEND**

#### **Method 1: Git Commit (Simple)**

```powershell
cd C:\ai-advisor1

# Add EOD file:
git add latest_prices_all.json

# Commit:
git commit -m "Add: EOD prices for all tickers"

# Push (may be slow due to file size):
git push origin main

# Wait 7 minutes for Render deploy
```

#### **Method 2: Manual Upload to Render (Faster)**

```
1. Go to: https://dashboard.render.com
2. Service: ai-advisor1-backend
3. Shell tab
4. Upload latest_prices_all.json
5. Place in: /opt/render/project/src/
```

---

## 🧪 TESTING

### **Test Backend:**

```powershell
# 1. Check EOD status:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/status

# Expected:
# {
#   "file_exists": true,
#   "tickers_count": 150,
#   "file_age_days": 0,
#   "ttl_days": 5,
#   "needs_refresh": false
# }

# 2. Test portfolio with MBB:
$body = @{user_id=1; ticker="MBB"; quantity=100; price=23000} | ConvertTo-Json
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/portfolio -Method POST -Body $body -ContentType "application/json"

# 3. Get portfolio:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/portfolio?user_id=1

# Expected:
# {
#   "portfolio": [{
#     "ticker": "MBB",
#     "current_price": 27500,  ← From EOD file!
#     "pl_pct": 19.57
#   }]
# }
```

### **Test Website:**

```
1. Visit: https://ai-advisor.vn
2. Tab: "Quản trị đầu tư"
3. Delete all stocks
4. Add MBB: 100 CP, 23,000 VND

Expected:
MBB:
  Mua: 23,000 VND
  Hiện tại: 27,500 VND ✅ (from EOD file!)
  P&L: +19.57% (green) ✅
```

---

## 🔄 AUTO-REFRESH SYSTEM

### **How It Works:**

```
Day 0: Download EOD file (latest_prices_all.json)
       Backend loads file: 150+ tickers ✅

Day 1-4: Backend reads from file (fast!)
         Portfolio loads in <0.1s ✅

Day 5: File age = 5 days
       Backend auto-deletes file 🗑️
       Admin downloads new file 📥

Day 6: New file uploaded
       Backend loads new prices ✅
```

### **Backend Auto-Delete Logic:**

```python
# On startup:
if file_age > 5 days:
    delete_file()
    print("File too old - deleted!")
    # Admin needs to download new file
```

---

## 🔄 REFRESH WORKFLOW

### **When to Refresh?**

- Every 5 days (auto-delete triggers)
- When prices seem outdated
- After market closes (get latest EOD)

### **How to Refresh?**

```powershell
cd C:\ai-advisor1

# 1. Run download:
python download_all_eod_prices.py

# 2. Push to GitHub:
git add latest_prices_all.json
git commit -m "Update: EOD prices $(Get-Date -Format 'yyyy-MM-dd')"
git push origin main

# 3. Wait 7 minutes for Render
```

### **Or Trigger via API (Future Enhancement):**

```powershell
# Trigger refresh:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/refresh -Method POST

# Note: This starts download in background (30-60 mins)
```

---

## 📊 FILE DETAILS

### **latest_prices_all.json Structure:**

```json
{
  "timestamp": "2026-01-11T16:00:00",
  "total_tickers": 150,
  "success_count": 142,
  "fail_count": 8,
  "prices": {
    "VCB": {
      "price": 90000,
      "change_percent": 1.5,
      "volume": 5000000
    },
    "MBB": {
      "price": 27500,
      "change_percent": 1.9,
      "volume": 3200000
    },
    ...
  }
}
```

### **File Size:**

- Fallback mode (~150 tickers): ~500 KB
- Full mode (~2000 tickers): ~5-10 MB

---

## ⚙️ CONFIGURATION

### **Adjust TTL (Time To Live):**

Edit `backend_api.py`:

```python
# Line ~40:
EOD_FILE_TTL_DAYS = 5  # Change to 3, 7, 10, etc.
```

### **Change Download Scope:**

Edit `download_all_eod_prices.py`:

```python
# To add more tickers:
def get_all_tickers():
    # Add your custom ticker lists here
    all_tickers = ['VCB', 'MBB', 'SHB', ...]  # Add more
```

---

## 🎯 ADVANTAGES

✅ **Fast:** Portfolio loads in <0.1s (reads from file)  
✅ **Simple:** Download once, use for 5 days  
✅ **No Cron:** No complex scheduling needed  
✅ **Auto-Clean:** Old files deleted automatically  
✅ **All Tickers:** Support ~150-2000 tickers  
✅ **Admin Control:** Download when YOU want  

---

## 📋 CHECKLIST

### **Initial Setup:**

- [ ] Download `backend_api_v3_autorefresh.py`
- [ ] Download `download_all_eod_prices.py`
- [ ] Replace `backend_api.py`
- [ ] Push to GitHub
- [ ] Wait 7 minutes
- [ ] Run `python download_all_eod_prices.py` locally
- [ ] Upload `latest_prices_all.json` to GitHub
- [ ] Push again
- [ ] Test website

### **Every 5 Days:**

- [ ] Check if file deleted (backend logs)
- [ ] Run download script locally
- [ ] Push new file to GitHub
- [ ] Verify website shows correct prices

---

## 🐛 TROUBLESHOOTING

### **Issue: EOD file not found**

```powershell
# Check if file exists:
dir latest_prices_all.json

# If not: Download it!
python download_all_eod_prices.py
```

### **Issue: Prices still wrong (MBB = 27.3 VND)**

```
Cause: EOD file not loaded or doesn't have MBB

Solution:
1. Check logs: "Loaded X prices from EOD file"
2. If X = 0: File not found or empty
3. Re-download file
4. Push to GitHub
```

### **Issue: File age = 6 days but not deleted**

```
Cause: Backend hasn't restarted since day 6

Solution:
1. Restart Render service (auto-delete runs on startup)
2. Or deploy new code (triggers restart)
```

---

## 💡 BEST PRACTICES

1. **Download weekly:** Every Friday after market close
2. **Monitor logs:** Check "Loaded X prices" on startup
3. **Backup file:** Keep local copy of `latest_prices_all.json`
4. **Track age:** Check `/api/eod/status` regularly
5. **Test prices:** Verify a few tickers match real market prices

---

## 🚀 NEXT STEPS

1. ✅ Deploy backend with auto-refresh
2. ✅ Download EOD file locally (30-60 mins)
3. ✅ Push file to GitHub
4. ✅ Test website - MBB should show 27,500 VND!
5. ⏰ Set reminder: Refresh every 5 days

---

## 📞 QUICK COMMANDS

```powershell
# Deploy backend:
cd C:\ai-advisor1
copy backend_api_v3_autorefresh.py backend_api.py /Y
git add backend_api.py download_all_eod_prices.py
git commit -m "Add: Auto-refresh EOD"
git push origin main

# Download EOD:
python download_all_eod_prices.py

# Push EOD file:
git add latest_prices_all.json
git commit -m "Update: EOD prices"
git push origin main

# Check status:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/eod/status

# Test portfolio:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/portfolio?user_id=1
```

---

**Ready to deploy?** 🚀

1. Download 2 files ⬆️
2. Replace backend
3. Push
4. Run download script
5. Push EOD file
6. Test!

Total time: 30-60 minutes (mostly waiting for download)
