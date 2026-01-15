# ⚡ QUICK START - SELL SIGNAL SYSTEM

## 🎯 WHAT YOU GOT

7 files để setup hệ thống SELL signal tự động:

### **📁 Scripts (Copy vào `scripts/` folder):**
1. ✅ `update_database.py` - Cập nhật database schema
2. ✅ `sell_signal_generator.py` - Core logic tạo SELL signals
3. ✅ `daily_signal_runner.py` - Chạy cả BUY + SELL signals
4. ✅ `test_sell_system.py` - Test toàn bộ hệ thống

### **📁 Backend (Copy vào root folder):**
5. ✅ `backend_sell_api.py` - API endpoints cho SELL signals

### **📁 GitHub Actions (Copy vào `.github/workflows/`):**
6. ✅ `daily-signals.yml` - Tự động chạy mỗi ngày 6 PM

### **📖 Documentation:**
7. ✅ `SETUP_GUIDE.md` - Hướng dẫn chi tiết từng bước

---

## ⚡ SETUP NHANH (15 PHÚT)

### **STEP 1: Copy files (2 mins)**

```bash
cd C:\ai-advisor1

# Copy scripts
copy update_database.py scripts\
copy sell_signal_generator.py scripts\
copy daily_signal_runner.py scripts\
copy test_sell_system.py scripts\

# Copy backend
copy backend_sell_api.py .

# Copy GitHub Actions
mkdir .github\workflows 2>nul
copy daily-signals.yml .github\workflows\
```

### **STEP 2: Update database (2 mins)**

```bash
python scripts\update_database.py
```

Expected:
```
✅ Updated 127 BUY signals to ACTIVE
📊 Active BUY signals: 127
🎯 Ready to generate SELL signals!
```

### **STEP 3: Test system (3 mins)**

```bash
python test_sell_system.py
```

Expected:
```
🎉 ALL TESTS PASSED!
✅ Sell signal system is ready!
```

### **STEP 4: Test generator (3 mins)**

```bash
cd scripts
python sell_signal_generator.py
```

Expected:
```
📊 Checked: 127 BUY signals
🎯 Created: 3 SELL signals
```

### **STEP 5: Update backend (2 mins)**

Edit `backend_api.py`, thêm 2 dòng:

```python
# At top
from backend_sell_api import register_sell_routes

# After app = Flask(__name__)
register_sell_routes(app)
```

### **STEP 6: Push to GitHub (3 mins)**

```bash
git add .
git commit -m "Add SELL signal system"
git push origin main
```

### **STEP 7: Enable GitHub Actions**

1. Go to GitHub repo → Actions tab
2. Enable workflows
3. Click "Daily Signal Generation"
4. Click "Run workflow" → Test manual run

---

## ✅ DONE! 

**Hệ thống sẽ:**
- ✅ Tự động chạy mỗi ngày 6:00 PM
- ✅ Tạo SELL signals dựa trên BUY signals
- ✅ 3 loại: Stop Loss, Take Profit, MA20 Exit
- ✅ Frontend tự động hiển thị (đã sẵn sàng!)

---

## 📊 WORKFLOW HÀNG NGÀY

```
6:00 PM Vietnam
    ↓
Download data
    ↓
Scan BUY signals → Save with status ACTIVE
    ↓
Generate SELL signals:
  • Price ≤ Stop Loss → Sell 100%
  • Price ≥ Take Profit → Sell 50%
  • Price < MA20 (if partial) → Sell 50% còn lại
    ↓
Users xem SELL signals trong app
```

---

## 🚨 TROUBLESHOOTING

**No SELL signals?**
→ Normal! Chỉ tạo khi BUY signals hit exit conditions

**Tests fail?**
→ Run: `python scripts\update_database.py`

**Backend error?**
→ Check backend_api.py có import đúng chưa

---

## 📞 NEED HELP?

**Đọc chi tiết:** `SETUP_GUIDE.md` (hướng dẫn đầy đủ từng bước)

**Test lại:** `python test_sell_system.py`

**Check database:** `python scripts\update_database.py`

---

## 🎉 YOU'RE ALL SET!

KHÔNG cần làm gì thêm! Hệ thống tự động chạy mỗi ngày! 🚀

**Version:** 1.0  
**Date:** January 15, 2026
