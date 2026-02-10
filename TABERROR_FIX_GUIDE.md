# 🔧 FIX TABERROR - HƯỚNG DẪN CHI TIẾT

## 🚨 LỖI

```
TabError: inconsistent use of tabs and spaces in indentation
```

**Nguyên nhân:** Python không cho phép MIX tabs và spaces!

---

## ✅ GIẢI PHÁP NHANH (3 OPTIONS)

### **OPTION 1: RESTORE & SỬA LẠI ĐÚNG CÁCH (RECOMMENDED)**

#### **Step 1: Restore backup**

```powershell
cd C:\ai-advisor1\scripts
Copy-Item daily_signal_scanner_eod.py.BACKUP_2026-02-09 daily_signal_scanner_eod.py -Force
```

#### **Step 2: Mở bằng editor tốt hơn**

```powershell
# Nếu có VS Code:
code daily_signal_scanner_eod.py

# Nếu có Notepad++:
notepad++ daily_signal_scanner_eod.py

# Nếu chỉ có Notepad (không khuyến khích):
notepad daily_signal_scanner_eod.py
```

#### **Step 3: Tìm & thay thế**

**Tìm function `scan_all_stocks()` (khoảng line 339)**

**Tìm đoạn code này (line ~360-370):**

```python
            pullback = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            
            all_signals.extend(pullback)
            all_signals.extend(ema_cross)
```

**Xóa 2 dòng:**
```python
            all_signals.extend(pullback)
            all_signals.extend(ema_cross)
```

**Paste đoạn MỚI (từ file scan_all_stocks_FIXED.py tôi tạo):**

```python
            # Priority only filter
            for signal in pullback:
                if signal['is_priority'] == 1:
                    all_signals.append(signal)
                    
            for signal in ema_cross:
                if signal['is_priority'] == 1:
                    all_signals.append(signal)
```

#### **Step 4: Kiểm tra indent**

**Trong VS Code:**
- View → Render Whitespace
- Kiểm tra: Phải toàn bộ SPACES, không có TAB

**Trong Notepad++:**
- View → Show Symbol → Show All Characters
- Spaces = dots (·), Tabs = arrows (→)
- Đảm bảo: Không có arrows!

#### **Step 5: Save & Test**

```powershell
# Save file
# Test
cd C:\ai-advisor1\scripts
python daily_signal_scanner_eod.py
```

---

### **OPTION 2: CHUYỂN TẤT CẢ TABS → SPACES (AUTO FIX)**

```powershell
# Restore backup
cd C:\ai-advisor1\scripts
Copy-Item daily_signal_scanner_eod.py.BACKUP_2026-02-09 daily_signal_scanner_eod.py -Force

# Convert tabs to spaces using Python
python -c "import sys; data = open('daily_signal_scanner_eod.py').read(); open('daily_signal_scanner_eod.py', 'w').write(data.expandtabs(4))"

# Sau đó mới sửa code filter như Option 1
```

---

### **OPTION 3: THAY THẾ TOÀN BỘ FUNCTION (SAFEST)**

#### **Step 1: Download file**

Tôi đã tạo file: `scan_all_stocks_FIXED.py` (có indent ĐÚNG 100%)

#### **Step 2: Mở file gốc**

```powershell
notepad C:\ai-advisor1\scripts\daily_signal_scanner_eod.py
```

#### **Step 3: Tìm & thay thế function**

**Tìm:** `def scan_all_stocks():`  (khoảng line 339)

**Xóa:** Toàn bộ function (từ `def scan_all_stocks():` đến dòng `return all_signals` - khoảng 70 dòng)

**Copy:** Toàn bộ nội dung từ file `scan_all_stocks_FIXED.py`

**Paste:** Vào vị trí vừa xóa

#### **Step 4: Save & Test**

```powershell
cd C:\ai-advisor1\scripts
python daily_signal_scanner_eod.py
```

---

## 🧪 TEST COMMANDS

### **Test 1: Syntax Check**

```powershell
python -m py_compile daily_signal_scanner_eod.py
```

**Expected:** Không có output = OK!

**If error:** Còn lỗi indent, cần sửa tiếp

---

### **Test 2: Run Scanner**

```powershell
python daily_signal_scanner_eod.py
```

**Expected output:**
```
============================================================
Starting scan...
Date: 2026-02-09
Stocks: 343
============================================================
Processing VCB (1/343)...
Processing VHM (2/343)...
...
============================================================
COMPLETE
Processed: 338/343
Failed: 5
Signals: 15                    ← Reduced from 144!
============================================================
PULLBACK: 8                    ← Much better!
EMA_CROSS: 7
Priority: 15                   ← 100% priority!

Top 5:
1. TCO - EMA_CROSS - 100%
2. ASG - EMA_CROSS - 85%
3. NHT - EMA_CROSS - 85%
4. CTG - PULLBACK - 80%
5. HPG - PULLBACK - 75%

✓ Done. 15 signals
```

---

## 📝 PYTHON INDENT RULES

**Python yêu cầu:**
- Phải dùng TOÀN BỘ spaces HOẶC TOÀN BỘ tabs
- KHÔNG được MIX!
- Khuyến khích: **4 spaces** (PEP 8 standard)

**Check indent level:**
```
def function():       # Level 0
    line1             # Level 1 (4 spaces)
    for x in y:       # Level 1 (4 spaces)
        line2         # Level 2 (8 spaces)
        if condition: # Level 2 (8 spaces)
            line3     # Level 3 (12 spaces)
```

**File của bạn:**
```
def scan_all_stocks():              # Level 0
    logger.info(...)                # Level 1 (4 spaces)
    for ticker in TOP_STOCKS:       # Level 1 (4 spaces)
        try:                        # Level 2 (8 spaces)
            logger.info(...)        # Level 3 (12 spaces)
            for signal in pullback: # Level 3 (12 spaces)
                if ...:             # Level 4 (16 spaces)
                    append(...)     # Level 5 (20 spaces)
```

---

## 🔍 DEBUG TIPS

### **Nếu vẫn lỗi sau khi fix:**

```powershell
# Check file encoding
python -c "import sys; print(open('daily_signal_scanner_eod.py', 'rb').read(500))"

# Should be UTF-8, no weird characters
```

### **Nếu báo lỗi line khác:**

```powershell
# Show line numbers
python -c "with open('daily_signal_scanner_eod.py') as f: [print(f'{i+1:4}: {line}', end='') for i, line in enumerate(f)]" | findstr /N "503"
```

---

## ✅ VERIFICATION CHECKLIST

After fix:

- [ ] File compiles: `python -m py_compile daily_signal_scanner_eod.py`
- [ ] Scanner runs without errors
- [ ] Signals reduced from 144 → 15
- [ ] All signals are priority (strength >= 75/80)
- [ ] Top 5 signals display correctly

---

## 🚀 NEXT STEPS

### **After successful test:**

```powershell
# Push to database
cd C:\ai-advisor1
python push_local_signals.py

# Choose: 1 (Production)
# Confirm: y
```

### **Deploy to GitHub:**

```powershell
cd C:\ai-advisor1

git add scripts/daily_signal_scanner_eod.py
git commit -m "fix: Add priority filter, reduce noise signals (15 vs 144)"
git push origin main
```

---

## 📁 FILES PROVIDED

1. **scan_all_stocks_FIXED.py** - Complete function với indent ĐÚNG
2. **TABERROR_FIX_GUIDE.md** - File này

---

## 💡 TIP: PREVENT FUTURE ERRORS

**Dùng VS Code:**
```json
// settings.json
{
  "editor.detectIndentation": false,
  "editor.insertSpaces": true,
  "editor.tabSize": 4,
  "files.trimTrailingWhitespace": true
}
```

**Python Best Practices:**
- ✅ Always use 4 spaces
- ✅ Use good editor (VS Code, PyCharm)
- ❌ Never use Notepad for Python
- ❌ Never mix tabs and spaces

---

**Created:** 2026-02-09  
**Issue:** TabError in daily_signal_scanner_eod.py  
**Cause:** Mixed tabs and spaces  
**Solution:** Use consistent 4-space indentation
