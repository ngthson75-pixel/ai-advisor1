# SIGNAL_REVIEWER.PY - UPDATE FOR V5.2

**Date:** 2026-03-02  
**Issue:** Signal_reviewer.py không thấy SELL signals từ V5.2  
**Fix:** Update để đọc từ `sell_signals_v5.2_latest.json`  

---

## 🔴 VẤN ĐỀ

**User report:**
```
SELL V5.2 tạo ra nhiều tín hiệu bán
Nhưng Signal_reviewer.py chỉ hiển thị 1 signal cũ (VSC từ 2026-02-27)
```

**Root cause:**

```python
# OLD - Line 20
SELL_FILE = 'sell_signals_latest.json'  # V3 file

# V5.2 tạo:
'sell_signals_v5.2_latest.json'  # File mới!
```

→ Tên file khác nhau → Signal_reviewer không tìm thấy → Fallback database cũ

---

## ✅ GIẢI PHÁP

### Change 1: Update File Paths

**OLD:**
```python
SELL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sell_signals_latest.json')
```

**NEW:**
```python
# SELL files - Ưu tiên V5.2, fallback V3
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SELL_FILE_V52 = os.path.join(SCRIPT_DIR, 'sell_signals_v5.2_latest.json')
SELL_FILE_V3 = os.path.join(SCRIPT_DIR, 'sell_signals_latest.json')
```

---

### Change 2: Update view_sell_signals()

**NEW logic:**
```python
def view_sell_signals():
    # Ưu tiên V5.2
    if os.path.exists(SELL_FILE_V52):
        sell_file = SELL_FILE_V52
        version = "V5.2"
    elif os.path.exists(SELL_FILE_V3):
        sell_file = SELL_FILE_V3
        version = "V3"
    else:
        # Fallback database
        ...
    
    # Display version & source
    print(f"📂 Source: {os.path.basename(sell_file)} ({version})")
    
    # Show skipped T+2
    skipped = data.get('skipped_t_plus', [])
    if skipped:
        print(f"⏳ Skip T+2: {len(skipped)} ...")
```

**Output improvements:**
```
📉 SELL SIGNALS
  📂 Source: sell_signals_v5.2_latest.json (V5.2)
  📅 Date: 2026-03-02
  🔴 Total: 5
  ⏳ Skip T+2: 3 (BID, FRT, VHC)

  # Ticker   Reason                  Entry       Exit      P/L   Bán
  ----------------------------------------------------------------------
  1 PC1      TAKE_PROFIT_2          24,200     30,150 🟢 +24.59%   30%
  2 CTR      MA20_STRICT            21,500     22,032 🟢  +2.47%  100%
  3 SAB      MA20_STRICT           124,000    121,976 🔴  -1.63%  100%
  ...
```

---

### Change 3: Update push_sell_signals_to_production()

**NEW logic:**
```python
def push_sell_signals_to_production():
    # Ưu tiên V5.2
    if os.path.exists(SELL_FILE_V52):
        sell_file = SELL_FILE_V52
        version = "V5.2"
    elif os.path.exists(SELL_FILE_V3):
        sell_file = SELL_FILE_V3
        version = "V3"
    
    # V5.2 format với exit_quantity_pct
    payload = {
        'ticker': s['ticker'],
        'action': 'SELL',
        'exit_reason': s['exit_reason'],
        'exit_quantity_pct': s.get('exit_quantity_pct', 100),  # NEW!
        'profit_loss_pct': s.get('profit_loss_pct', 0),        # NEW!
        'exit_price': s.get('exit_price', 0),                  # NEW!
        'status': 'closed' if exit_qty >= 100 else 'partial',  # NEW!
        'position_pct': 0 if exit_qty >= 100 else (100 - exit_qty),
        ...
    }
```

**Output improvements:**
```
📉 5 SELL signals sẽ được push:
   🟢 PC1 — TAKE_PROFIT_2 | P/L: +24.59% | Bán: 30%
   🟢 CTR — MA20_STRICT | P/L: +2.47% | Bán: 100%
   🔴 SAB — MA20_STRICT | P/L: -1.63% | Bán: 100%
   ...

Push 5 SELL signals lên Production? (y/n):
```

---

## 📊 COMPARISON

### Before (OLD):

**View SELL:**
```
📉 SELL SIGNALS
  (Chưa chạy SELL scanner hoặc không có file sell_signals_latest.json)
  
  📊 Tìm thấy 1 SELL signals trong database:
  🔴 VSC — TAKE_PROFIT | Date: 2026-02-27
```

**Issue:** Không thấy V5.2 signals!

---

### After (NEW):

**View SELL:**
```
📉 SELL SIGNALS
  📂 Source: sell_signals_v5.2_latest.json (V5.2)
  📅 Date: 2026-03-02
  🔴 Total: 5
  ⏳ Skip T+2: 3 (BID, FRT, VHC)

  # Ticker   Reason                  Entry       Exit      P/L   Bán
  ----------------------------------------------------------------------
  1 PC1      TAKE_PROFIT_2          24,200     30,150 🟢 +24.59%   30%
  2 CTR      MA20_STRICT            21,500     22,032 🟢  +2.47%  100%
  3 SAB      MA20_STRICT           124,000    121,976 🔴  -1.63%  100%
  4 VCS      MA20_STRICT            23,600     23,284 🔴  -1.34%  100%
  5 KDC      MA20_STRICT            64,200     62,492 🔴  -2.66%  100%
```

**✅ Thấy tất cả V5.2 signals!**

---

## 📋 DEPLOYMENT

### Step 1: Backup Old File

```powershell
cd C:\ai-advisor1

# Backup
Copy-Item signal_reviewer.py signal_reviewer_OLD.py
```

---

### Step 2: Replace with New File

```powershell
# Download signal_reviewer_v5.2.py từ Claude
# Rename:
Move-Item signal_reviewer_v5.2.py signal_reviewer.py -Force
```

---

### Step 3: Verify

```powershell
# Check file updated
Select-String "V5.2" signal_reviewer.py
# Expected: "SELL_FILE_V52", "version = \"V5.2\"", etc.
```

---

### Step 4: Test

```powershell
# Run reviewer
python signal_reviewer.py

# Chọn option 4 (SELL signals)
# Expected:
# 📉 SELL SIGNALS
#   📂 Source: sell_signals_v5.2_latest.json (V5.2)
#   🔴 Total: 5
#   ...
```

---

## ✅ FEATURES ADDED

1. **Auto-detect V5.2 file** - Ưu tiên `sell_signals_v5.2_latest.json`
2. **Fallback V3** - Nếu không có V5.2, dùng `sell_signals_latest.json`
3. **Show version** - Display "V5.2" hoặc "V3" khi xem signals
4. **Show T+2 skipped** - Hiển thị signals bị skip do T+2
5. **V5.2 push format** - Include `exit_quantity_pct`, `profit_loss_pct`, `exit_price`
6. **Better output** - Reason column rộng hơn (20 chars) cho "TAKE_PROFIT_2"

---

## 🎯 EXPECTED BEHAVIOR

### After Update:

**Chọn option 4 (View SELL):**
```
📉 SELL SIGNALS
  📂 Source: sell_signals_v5.2_latest.json (V5.2)
  📅 Date: 2026-03-02
  🔴 Total: 5
  ⏳ Skip T+2: 3 (BID, FRT, VHC)

  [Table with 5 signals from V5.2]
```

**Chọn option 15 (Push SELL):**
```
📂 Source: sell_signals_v5.2_latest.json (V5.2)
📉 5 SELL signals sẽ được push:
   🟢 PC1 — TAKE_PROFIT_2 | P/L: +24.59% | Bán: 30%
   ...

Push 5 SELL signals lên Production? (y/n): y
   ✅ PC1 — TAKE_PROFIT_2 (30%)
   ✅ CTR — MA20_STRICT (100%)
   ...
```

---

## 🔄 ROLLBACK

**If issues:**

```powershell
Copy-Item signal_reviewer_OLD.py signal_reviewer.py -Force
```

---

## 💡 BACKWARD COMPATIBILITY

**File vẫn hoạt động với:**
- ✅ V5.2 (ưu tiên)
- ✅ V3 (fallback)
- ✅ Database cũ (fallback cuối)

**Không breaking changes!**

---

**DEPLOY NGAY VÀ TEST!** 🚀
