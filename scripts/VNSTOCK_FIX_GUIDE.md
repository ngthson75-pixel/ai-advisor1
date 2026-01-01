# 🔧 QUICK FIX - VNSTOCK ERROR

## ❌ LỖI BẠN GẶP PHẢI:

```
ModuleNotFoundError: No module named 'IPython'
vnstock3 đã được hợp nhất thành vnstock
```

## ✅ GIẢI PHÁP (2 PHÚT):

### **STEP 1: Uninstall vnstock3**

```bash
cd C:\ai-advisor1\scripts

pip uninstall vnstock3 -y
```

### **STEP 2: Install vnstock + dependencies**

```bash
pip install vnstock ipython pandas numpy --upgrade
```

**Chờ cài đặt xong...**

### **STEP 3: Replace scanner files**

```bash
# Download 2 files mới:
# 1. daily_signal_scanner_eod.py (updated với vnstock)
# 2. test_scanner.py (updated với vnstock)

# Copy vào C:\ai-advisor1\scripts\
# Overwrite files cũ
```

### **STEP 4: Test lại**

```bash
cd C:\ai-advisor1\scripts

python test_scanner.py
```

**Expected output:**
```
==========================================================
TESTING SCANNER ON 10 STOCKS
Date: 2025-01-01
==========================================================

Testing VCB
✓ Got 100 days of data
Latest close: 88,500
✓ PULLBACK signal found!
  Entry: 88,500
  Target: 95,580 (+8.0%)
  Stop: 85,000
  Strength: 75%
  RSI: 45.2

...

TEST SUMMARY
Stocks tested: 10
Stocks with data: 10
Signals found: 5

✓ All signals:
1. VCB  - PULLBACK   -  75% - Entry:   88,500 - Target: +8.0%
2. MBB  - EMA_CROSS  -  80% - Entry:   23,800 - Target: +10.0%
...

✓ TEST PASSED
Generated 5 signals successfully
```

---

## 📋 ĐẦY ĐỦ COMMANDS:

```bash
# 1. Gỡ vnstock3
pip uninstall vnstock3 -y

# 2. Cài vnstock mới
pip install vnstock ipython pandas numpy --upgrade

# 3. Verify
python -c "import vnstock; print('vnstock version:', vnstock.__version__)"
python -c "import IPython; print('IPython OK')"

# 4. Test scanner
cd C:\ai-advisor1\scripts
python test_scanner.py

# 5. Nếu OK, run full scan
python daily_signal_scanner_eod.py
```

---

## 🔍 VERIFY INSTALLATION:

```bash
# Check vnstock
python -c "from vnstock import stock; print('✓ vnstock OK')"

# Check IPython
python -c "import IPython; print('✓ IPython OK')"

# Check pandas
python -c "import pandas; print('✓ pandas OK')"

# Check numpy
python -c "import numpy; print('✓ numpy OK')"
```

**All should print "✓ ... OK"**

---

## 🐛 NẾU VẪN LỖI:

### Lỗi: "pip not found"

```bash
python -m pip install vnstock ipython pandas numpy --upgrade
```

### Lỗi: "Permission denied"

```bash
pip install vnstock ipython pandas numpy --upgrade --user
```

### Lỗi: "Cannot uninstall vnstock3"

```bash
pip uninstall vnstock3 -y --break-system-packages
pip install vnstock ipython --upgrade --break-system-packages
```

### Lỗi: "ImportError: DLL load failed"

```bash
# Reinstall everything
pip uninstall vnstock pandas numpy -y
pip install vnstock pandas numpy --upgrade --force-reinstall
```

---

## 📊 WHAT CHANGED:

### Old Code (vnstock3):
```python
import vnstock3 as vs

stock = vs.stock(symbol=ticker, source='VCI')
df = stock.quote.history(...)
```

### New Code (vnstock):
```python
from vnstock import stock

stock_obj = stock(symbol=ticker, source='VCI')
df = stock_obj.quote.history(...)
```

**Same functionality, new library name!**

---

## ✅ AFTER FIX:

You should be able to:

1. ✓ Run `python test_scanner.py` without errors
2. ✓ See data fetched for stocks
3. ✓ See signals generated
4. ✓ Database populated with signals
5. ✓ Ready to deploy!

---

## 🚀 NEXT STEPS:

```bash
# 1. Test passed?
python test_scanner.py
# → Should show "TEST PASSED"

# 2. Run full scan
python daily_signal_scanner_eod.py
# → Should generate signals

# 3. Check database
sqlite3 signals.db "SELECT COUNT(*) FROM signals;"
# → Should show number > 0

# 4. Deploy
cd C:\ai-advisor1
git add scripts/
git commit -m "Fix scanner with vnstock library"
git push origin main
```

---

## 📞 STILL HAVING ISSUES?

**Copy full error and check:**

1. Python version
```bash
python --version
# Should be Python 3.8+
```

2. Pip version
```bash
pip --version
# Should be pip 20.0+
```

3. Install location
```bash
pip show vnstock
# Check where it's installed
```

4. Try in fresh terminal
```bash
# Close current terminal
# Open new one
# Try commands again
```

---

## 💡 WHY THIS HAPPENED:

- **vnstock3** was old package name
- Now merged into **vnstock** (single package)
- vnstock3 is deprecated
- vnstock requires **IPython** dependency
- Need to uninstall old, install new

**This is a one-time fix!**

---

## ✨ BENEFITS OF NEW VNSTOCK:

```
✓ Actively maintained
✓ Latest features
✓ Better performance  
✓ More data sources
✓ Improved API
✓ Better documentation
```

---

**RUN THESE 4 COMMANDS:**

```bash
pip uninstall vnstock3 -y
pip install vnstock ipython pandas numpy --upgrade
cd C:\ai-advisor1\scripts
python test_scanner.py
```

**DONE! ✅**
