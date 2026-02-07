# 🔧 TROUBLESHOOTING: "No signals found for 2026-02-01"

## ❌ ERROR
```
❌ No signals found for 2026-02-01

Try running scanner first:
  cd C:\ai-advisor1\scripts
  python daily_signal_scanner_eod.py
```

---

## 🎯 NGUYÊN NHÂN

### **Trading Day vs Calendar Day**

```
Hôm nay: 2026-02-01 (Thứ Bảy)
→ KHÔNG PHẢI NGÀY GIAO DỊCH!

Scanner lưu signals với: LAST TRADING DAY
→ Thứ Sáu: 2026-01-31
→ Hoặc sớm hơn nếu là ngày nghỉ
```

**Scanner logic:**
```python
def get_last_trading_day():
    # Returns last weekday (Mon-Fri)
    # Skips weekends and holidays
    # So signals dated 2026-01-31, NOT 2026-02-01!
```

---

## ✅ SOLUTION

### **OPTION 1: Check available dates** ⚡ (30 giây)

```powershell
cd C:\ai-advisor1

# Run check script
.\check_signals_db.ps1
```

**Expected output:**
```
Available dates:
  📅 2026-01-31 - 132 signals ← LATEST
  📅 2026-01-30 - 130 signals
  📅 2026-01-29 - 128 signals

Latest signals: 2026-01-31 (132 signals)
```

---

### **OPTION 2: Use updated push script** 🚀 (Recommended)

**Download updated:** `push_local_signals.py` ⬆️

**Features:**
- ✅ Auto-detects available dates
- ✅ Shows all dates with signal counts
- ✅ Auto-selects latest date
- ✅ Or lets you choose specific date

**Usage:**
```powershell
cd C:\ai-advisor1

# Run updated script
python push_local_signals.py

# Output:
# Available dates:
#   1. 2026-01-31 - 132 signals
#   2. 2026-01-30 - 130 signals
#
# Choose date:
# Enter choice (1-2) or press Enter for latest: [ENTER]
#
# Selected date: 2026-01-31
# ✓ Found 132 signals...
```

---

### **OPTION 3: Manual SQL query** 🔍

```powershell
cd C:\ai-advisor1

# Check dates in database
sqlite3 signals.db "SELECT date, COUNT(*) FROM signals GROUP BY date ORDER BY date DESC;"

# Output:
# 2026-01-31|132
# 2026-01-30|130
# 2026-01-29|128

# Or with Python:
python -c "import sqlite3; conn=sqlite3.connect('signals.db'); [print(f'{d}: {c} signals') for d,c in conn.execute('SELECT date, COUNT(*) FROM signals GROUP BY date ORDER BY date DESC').fetchall()]"
```

---

## 🎯 WORKFLOW

### **Correct workflow:**

```powershell
# STEP 1: Check what's in database
.\check_signals_db.ps1

# Output:
# Latest signals: 2026-01-31 (132 signals)

# STEP 2: Push latest signals
python push_local_signals.py
# Press Enter to use latest (2026-01-31)

# STEP 3: Verify
# Browser: Ctrl + Shift + R
# Visit: https://ai-advisor.vn
# Should see 132 signals dated 2026-01-31
```

---

## 📅 UNDERSTANDING TRADING DAYS

### **Trading vs Calendar:**

```
Monday    2026-01-26  ✅ Trading day
Tuesday   2026-01-27  ✅ Trading day
Wednesday 2026-01-28  ✅ Trading day
Thursday  2026-01-29  ✅ Trading day
Friday    2026-01-30  ✅ Trading day ← LAST TRADING DAY
Saturday  2026-01-31  ❌ Weekend
Sunday    2026-02-01  ❌ Weekend ← TODAY
```

**Scanner on Saturday/Sunday:**
- Detects today is not trading day
- Uses last Friday as date
- Saves signals as 2026-01-30

**Scanner on weekday:**
- Uses today as date
- Saves signals as today's date

---

## 🔍 DEBUG COMMANDS

### **Check database file:**
```powershell
cd C:\ai-advisor1
Test-Path signals.db
# Should return: True
```

### **Check signals count:**
```powershell
python -c "import sqlite3; print(sqlite3.connect('signals.db').execute('SELECT COUNT(*) FROM signals').fetchone()[0])"
# Should return: 132 (or similar)
```

### **Check all dates:**
```powershell
python -c "import sqlite3; [print(row) for row in sqlite3.connect('signals.db').execute('SELECT DISTINCT date FROM signals ORDER BY date DESC').fetchall()]"
# Should return: ('2026-01-31',) or similar
```

### **Check latest signals:**
```powershell
python -c "import sqlite3; [print(f'{r[0]} {r[1]} {r[2]}') for r in sqlite3.connect('signals.db').execute('SELECT ticker, strategy, strength FROM signals ORDER BY strength DESC LIMIT 5').fetchall()]"
# Should return: Top 5 signals
```

---

## ✅ VERIFICATION

After pushing with correct date:

```powershell
# 1. Check backend
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals -UseBasicParsing | Select-Object -Expand Content | ConvertFrom-Json

# Should show:
# count: 132
# signals: [... dated 2026-01-31 ...]

# 2. Check website
# Browser: https://ai-advisor.vn
# Tab: "Tín hiệu mua"
# Should show: 132 signals dated 2026-01-31
```

---

## 📋 QUICK REFERENCE

**Download these files:**
1. ⬆️ `check_signals_db.ps1` - Check database dates
2. ⬆️ `push_local_signals.py` (UPDATED) - Auto-detect dates

**Commands:**
```powershell
# Check database
.\check_signals_db.ps1

# Push signals
python push_local_signals.py
# Press Enter for latest date

# Verify
# Ctrl + Shift + R on browser
```

**Done!** 🎉

---

## 💡 KEY TAKEAWAY

**Always check database dates BEFORE pushing!**

```
❌ Wrong:
  Assume today's date has signals

✅ Correct:
  1. Check: .\check_signals_db.ps1
  2. Use latest date shown
  3. Push that date's signals
```

---

**SOLUTION:**
```powershell
cd C:\ai-advisor1
.\check_signals_db.ps1
python push_local_signals.py
```

**2 commands → Problem solved!** 🚀
