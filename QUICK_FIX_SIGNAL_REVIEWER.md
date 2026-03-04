# QUICK FIX: SIGNAL_REVIEWER.PY V5.2

**Time:** 1 phút  
**Issue:** Không thấy SELL V5.2 signals  
**Fix:** Update file path  

---

## 🔴 VẤN ĐỀ

```
SELL V5.2 tạo: sell_signals_v5.2_latest.json
Signal_reviewer đọc: sell_signals_latest.json (V3 cũ)
→ Không tìm thấy file → Không hiển thị!
```

---

## ✅ FIX (1 PHÚT)

### Step 1: Backup (10 giây)

```powershell
cd C:\ai-advisor1

Copy-Item signal_reviewer.py signal_reviewer_OLD.py
```

---

### Step 2: Replace (30 giây)

```powershell
# Download signal_reviewer_v5.2.py từ Claude
# Rename:
Move-Item signal_reviewer_v5.2.py signal_reviewer.py -Force
```

---

### Step 3: Test (20 giây)

```powershell
python signal_reviewer.py

# Chọn: 4 (SELL signals)
```

**Expected:**
```
📉 SELL SIGNALS
  📂 Source: sell_signals_v5.2_latest.json (V5.2)
  🔴 Total: 5

  # Ticker   Reason                  Entry       Exit      P/L   Bán
  ----------------------------------------------------------------------
  1 PC1      TAKE_PROFIT_2          24,200     30,150 🟢 +24.59%   30%
  2 CTR      MA20_STRICT            21,500     22,032 🟢  +2.47%  100%
  ...
```

---

## 🎯 DONE!

**Giờ bạn có thể:**
- ✅ Xem tất cả SELL V5.2 signals
- ✅ Push lên production
- ✅ Review trước khi upload

---

## 🔄 ROLLBACK (Nếu Issues)

```powershell
Copy-Item signal_reviewer_OLD.py signal_reviewer.py -Force
```

---

**THAY FILE NGAY!** 🚀
