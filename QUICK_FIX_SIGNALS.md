# ⚡ QUICK FIX - SIGNALS NOT UPDATING (5 PHÚT)

## 🎯 VẤN ĐỀ
- ✅ Scanner local chạy OK: 132 signals
- ❌ Website vẫn hiển thị signals cũ

## ✅ GIẢI PHÁP - 3 BƯỚC

### **1️⃣ DOWNLOAD FILES (30 giây)**

Download 2 files từ chat:
1. `push_local_signals.py` ⬆️
2. `diagnostic_backend_scanner.ps1` ⬆️

Copy vào: `C:\ai-advisor1\`

---

### **2️⃣ PUSH SIGNALS (3 phút)**

```powershell
cd C:\ai-advisor1

# Run push script
python push_local_signals.py
```

**Follow prompts:**
```
✓ Found 132 signals for 2026-02-01
  PULLBACK: 67
  EMA_CROSS: 65
  Priority: 25

Choose environment:
  1. Production (ai-advisor1-backend.onrender.com)
  2. Staging (ai-advisor1-staging.onrender.com)
  3. Both

Enter choice (1/2/3): 1  ← Type này

⚠️  About to push 132 signals to:
  - Production

Continue? (y/n): y  ← Type y
```

**Wait 2-3 minutes:**
```
🔄 Pushing to Production...
  1/132 ✓ GMC    EMA_CROSS    100%
  2/132 ✓ PGD    EMA_CROSS    100%
  ...
  132/132 ✓ ...

Results for Production:
  ✓ Success: 132
  ✗ Failed: 0

✅ PUSH COMPLETE!
```

---

### **3️⃣ VERIFY (30 giây)**

```powershell
# Clear browser cache
# Press: Ctrl + Shift + R

# Visit:
https://ai-advisor.vn

# Tab: "Tín hiệu mua"
```

**Should see:**
- 132 signals
- Date: 2026-02-01 (today!)
- Top: GMC, PGD, VSM, CTG, VIM

---

## ✅ DONE! 🎉

Website giờ có 132 signals mới!

---

## 🔍 IF STILL NOT WORKING

Run diagnostic:
```powershell
cd C:\ai-advisor1
.\diagnostic_backend_scanner.ps1
```

Check output for errors.

---

## 📋 DAILY WORKFLOW (Tạm thời)

Until backend scanner fixed:

```powershell
# Mỗi ngày:

# 1. Run scanner local
cd C:\ai-advisor1\scripts
python daily_signal_scanner_eod.py

# 2. Push to production
cd C:\ai-advisor1
python push_local_signals.py
# Choose: 1 (Production)
# Confirm: y

# 3. Done! Website updated!
```

---

## 🆘 TROUBLESHOOTING

### **Error: "signals.db not found"**
```powershell
cd C:\ai-advisor1
cd scripts
python daily_signal_scanner_eod.py
cd ..
```

### **Error: "module requests not found"**
```powershell
pip install requests --break-system-packages
```

### **Website still shows old signals**
```
1. F12 → Console → Check errors
2. Clear cache: Ctrl + Shift + R
3. Try incognito: Ctrl + Shift + N
4. Wait 2 minutes for CDN cache
```

---

**READ FULL GUIDE:** `FIX_SIGNALS_NOT_UPDATING.md` ⬆️

---

**Total time:** 5 phút  
**Files needed:** 2  
**Commands:** 2  

**LET'S GO!** 🚀
