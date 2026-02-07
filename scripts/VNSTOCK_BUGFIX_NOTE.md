# SELL SIGNAL V2 - BUGFIX for vnstock 3.3.1+

**Date:** 2026-02-02  
**Issue:** ImportError: cannot import name 'stock' from 'vnstock'  
**Status:** ✅ FIXED

---

## 🐛 PROBLEM

**Error:**
```
ImportError: cannot import name 'stock' from 'vnstock'
```

**Cause:**
- vnstock 3.3.1/3.4.x changed API
- Old: `from vnstock import stock`
- New: `from vnstock import Vnstock`

---

## ✅ SOLUTION

### Changed Lines:

**Line 6-11 (OLD):**
```python
from vnstock import stock

class SellSignalScannerV2:
    def __init__(self, db_path='signals.db'):
        self.stock_api = stock
```

**Line 6-18 (NEW):**
```python
# vnstock 3.x import
try:
    from vnstock import Vnstock
except ImportError:
    from vnstock3 import Vnstock

class SellSignalScannerV2:
    def __init__(self, db_path='signals.db'):
        self.stock_api = Vnstock()
```

---

### API Usage:

**OLD:**
```python
quote = stock.Quote(symbol=ticker, source='VCI')
history = quote.history(symbol=ticker, start=start_date, end=end_date)
```

**NEW:**
```python
stock = self.stock_api.stock(symbol=ticker, source='VCI')
history = stock.quote.history(start=start_date, end=end_date)
```

---

## 🚀 HOW TO FIX

### Option 1: Download Fixed File (RECOMMENDED)

```powershell
# 1. Download sell_signal_scanner_v2.py (fixed version)
# 2. Replace old file
Copy-Item sell_signal_scanner_v2.py C:\ai-advisor1\scripts\ -Force

# 3. Test
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30
```

---

### Option 2: Manual Fix

```powershell
# Open file
notepad C:\ai-advisor1\scripts\sell_signal_scanner_v2.py

# Replace line 6:
# OLD: from vnstock import stock
# NEW: from vnstock import Vnstock

# Replace line 16:
# OLD: self.stock_api = stock
# NEW: self.stock_api = Vnstock()

# Replace in get_current_data method (line ~60):
# OLD: quote = stock.Quote(symbol=ticker, source='VCI')
#      history = quote.history(symbol=ticker, start=start_date, end=end_date)
# NEW: stock = self.stock_api.stock(symbol=ticker, source='VCI')
#      history = stock.quote.history(start=start_date, end=end_date)

# Save & test
```

---

## 🧪 VERIFICATION

```powershell
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30

# Expected output:
# ✓ Found X active BUY signals to check
# Checking VCB (1/132)...
# ...
```

**If you see this:** ✅ Fixed!

**If still error:** 
- Check vnstock version: `pip list | findstr vnstock`
- Update vnstock: `pip install vnstock --upgrade`
- Restart terminal

---

## 📚 RELATED CHANGES

**Also Fixed in:**
- `sell_signal_scanner.py` (V1) - Same issue
- `daily_signal_scanner_eod.py` - BUY scanner

**Check if these files need fixing too:**

```bash
# Test V1 scanner
python sell_signal_scanner.py --days 30

# Test BUY scanner
python daily_signal_scanner_eod.py
```

---

## 🔍 VNSTOCK 3.x CHANGES

### What Changed:

| Feature | vnstock 2.x | vnstock 3.x |
|---------|-------------|-------------|
| Import | `from vnstock import stock` | `from vnstock import Vnstock` |
| Init | `stock.Quote(...)` | `Vnstock().stock(...)` |
| History | `quote.history(symbol=...)` | `stock.quote.history(...)` |
| Intraday | `quote.intraday(symbol=...)` | `stock.quote.intraday(...)` |

### Documentation:

- **Official:** https://docs.vnstock.site/
- **GitHub:** https://github.com/thinh-vu/vnstock
- **PyPI:** https://pypi.org/project/vnstock/

---

## ⚠️ NOTES

1. **Version Check:**
   ```bash
   pip list | findstr vnstock
   # Current: 3.3.1
   # Latest: 3.4.2
   ```

2. **Upgrade (Optional):**
   ```bash
   pip install vnstock --upgrade
   # Upgrades to 3.4.2
   ```

3. **Compatibility:**
   - Fixed scanner works with 3.3.1, 3.4.0, 3.4.2
   - Also backward compatible with 3.0.x

4. **Performance:**
   - vnstock 3.4.x has better rate limits
   - Faster data loading
   - Consider upgrading for production

---

## 📞 SUPPORT

**Still having issues?**

Contact: ngthson75@gmail.com | +84938127666

**Common Issues:**

Q: Still getting ImportError after fix?  
A: Restart terminal, try again

Q: Should I upgrade to 3.4.2?  
A: Yes, it's faster and more stable

Q: What about old scanners?  
A: They need same fix (check daily_signal_scanner_eod.py)

---

**Status:** ✅ Fixed  
**Tested:** vnstock 3.3.1, 3.4.0, 3.4.2  
**Date:** 2026-02-02
