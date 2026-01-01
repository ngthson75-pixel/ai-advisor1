# ⚡ ONE-LINE FIX

## 🚀 COPY & PASTE THESE COMMANDS:

### **Windows (PowerShell hoặc CMD):**

```bash
pip uninstall vnstock3 -y && pip install vnstock ipython pandas numpy --upgrade && cd C:\ai-advisor1\scripts && python test_scanner.py
```

---

### **Hoặc từng bước:**

```bash
# Step 1: Uninstall vnstock3
pip uninstall vnstock3 -y

# Step 2: Install vnstock + dependencies
pip install vnstock ipython pandas numpy --upgrade

# Step 3: Navigate to scripts folder
cd C:\ai-advisor1\scripts

# Step 4: Test
python test_scanner.py
```

---

## ✅ EXPECTED SUCCESS OUTPUT:

```
==========================================================
TESTING SCANNER ON 10 STOCKS
Date: 2025-01-01
==========================================================

2025-01-01 10:00:00 - INFO - ✓ Database initialized

==========================================================
Testing VCB
==========================================================
2025-01-01 10:00:01 - INFO - Fetching VCB data (2024-09-01 to 2025-01-01)
2025-01-01 10:00:02 - INFO - ✓ Got 100 days of data for VCB
2025-01-01 10:00:02 - INFO - ✓ Processed VCB: 100 valid rows
2025-01-01 10:00:02 - INFO - ✓ Got 100 days of data
2025-01-01 10:00:02 - INFO - Latest close: 88,500
2025-01-01 10:00:02 - INFO - ✓ PULLBACK signal for VCB: 75% strength
2025-01-01 10:00:02 - INFO - ✓ PULLBACK signal found!
2025-01-01 10:00:02 - INFO -   Entry: 88,500
2025-01-01 10:00:02 - INFO -   Target: 95,580 (+8.0%)
2025-01-01 10:00:02 - INFO -   Stop: 85,000
2025-01-01 10:00:02 - INFO -   Strength: 75%
2025-01-01 10:00:02 - INFO -   RSI: 45.2

... (more stocks) ...

==========================================================
TEST SUMMARY
==========================================================
2025-01-01 10:01:00 - INFO - Stocks tested: 10
2025-01-01 10:01:00 - INFO - Stocks with data: 10
2025-01-01 10:01:00 - INFO - Signals found: 5
2025-01-01 10:01:00 - INFO - 
2025-01-01 10:01:00 - INFO - ✓ All signals:
2025-01-01 10:01:00 - INFO - 1. VCB  - PULLBACK   -  75% - Entry:   88,500 - Target: +8.0%
2025-01-01 10:01:00 - INFO - 2. MBB  - EMA_CROSS  -  80% - Entry:   23,800 - Target: +10.0%
2025-01-01 10:01:00 - INFO - 3. HPG  - PULLBACK   -  72% - Entry:   25,200 - Target: +8.0%
2025-01-01 10:01:00 - INFO - 4. FPT  - PULLBACK   -  78% - Entry:  125,000 - Target: +8.0%
2025-01-01 10:01:00 - INFO - 5. TCB  - EMA_CROSS  -  75% - Entry:   24,500 - Target: +10.0%
2025-01-01 10:01:00 - INFO - 
2025-01-01 10:01:00 - INFO - ✓ Saved 5 signals to database
2025-01-01 10:01:00 - INFO - 
2025-01-01 10:01:00 - INFO - Strategy breakdown:
2025-01-01 10:01:00 - INFO -   PULLBACK: 3
2025-01-01 10:01:00 - INFO -   EMA_CROSS: 2
2025-01-01 10:01:00 - INFO -   Priority: 1

==========================================================
✓ TEST PASSED
Generated 5 signals successfully
==========================================================
```

---

## 🎯 AFTER SUCCESS:

### Run full scanner:

```bash
python daily_signal_scanner_eod.py
```

**Expected:**
- Scan 50 stocks
- Take ~2-3 minutes
- Generate 5-15 signals
- Save to database

### Check database:

```bash
sqlite3 signals.db "SELECT ticker, strategy, strength FROM signals ORDER BY strength DESC LIMIT 10;"
```

### Deploy:

```bash
cd C:\ai-advisor1
git add scripts/
git commit -m "Update scanner to use vnstock library"
git push origin main
```

---

## ❌ IF STILL FAILS:

### Check installation:

```bash
python -c "import vnstock; print('vnstock:', vnstock.__version__)"
python -c "import IPython; print('IPython: OK')"
python -c "import pandas; print('pandas: OK')"
python -c "import numpy; print('numpy: OK')"
```

**All should succeed without errors**

### If any fails, reinstall:

```bash
pip install vnstock ipython pandas numpy --upgrade --force-reinstall
```

### If permission error:

```bash
pip install vnstock ipython pandas numpy --upgrade --user
```

### If still fails, try:

```bash
python -m pip uninstall vnstock3 -y
python -m pip install vnstock ipython pandas numpy --upgrade
```

---

## 📞 DETAILED ERROR HELP:

### Error: "ModuleNotFoundError: No module named 'vnstock'"

**Fix:**
```bash
pip install vnstock --upgrade
```

### Error: "ModuleNotFoundError: No module named 'IPython'"

**Fix:**
```bash
pip install ipython --upgrade
```

### Error: "Cannot uninstall vnstock3"

**Fix:**
```bash
pip uninstall vnstock3 -y --break-system-packages
```

### Error: "ImportError: DLL load failed"

**Fix:**
```bash
pip install vnstock --upgrade --force-reinstall --no-cache-dir
```

---

## ✅ VERIFICATION:

After running commands, verify:

```bash
# 1. Libraries installed
pip list | findstr vnstock
pip list | findstr IPython
pip list | findstr pandas

# 2. Can import
python -c "from vnstock import stock; print('OK')"

# 3. Test scanner works
cd C:\ai-advisor1\scripts
python test_scanner.py

# 4. Should output: "TEST PASSED"
```

---

## 🚀 READY!

If test passed:
- ✅ Scanner works
- ✅ Can fetch data
- ✅ Can generate signals
- ✅ Database saves correctly
- ✅ Ready to deploy!

---

**JUST RUN:**

```bash
pip uninstall vnstock3 -y
pip install vnstock ipython pandas numpy --upgrade
cd C:\ai-advisor1\scripts
python test_scanner.py
```

**DONE! ✅**
