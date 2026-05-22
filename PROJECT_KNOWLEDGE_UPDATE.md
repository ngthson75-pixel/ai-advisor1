# PROJECT KNOWLEDGE UPDATE - SELL SIGNALS COMPLETE
**Date:** 2026-03-06  
**Status:** ✅ Production & Staging Deployed

---

## 🎯 WHAT CHANGED

### **1. Backend - Signal Model (backend_api.py)**
```python
# Added 3 columns (lines 269-272):
exit_price = Column(Float, nullable=True)
exit_reason = Column(String(50), nullable=True)  
exit_date = Column(String(20), nullable=True)

# Added to API response (lines 601-604):
'exit_price': round(s.exit_price / 100) * 100 if s.exit_price else None,
'exit_reason': s.exit_reason,
'exit_date': s.exit_date,
```

### **2. Frontend - SELL Signals Table (SignalsModule.jsx)**
```javascript
// Added P/L column (line 543)
// Calculation (lines 555-561):
const exitPrice = signal.exit_price || 0;
const plPct = ((exitPrice - entryPrice) / entryPrice * 100);

// Display: Clean badges, NO icons (user preference)
{plPct >= 0 ? '+' : ''}{plPct.toFixed(2)}%
```

**Table structure (8 columns):**
Mã CK | Giá vào | Giá ra | **P/L** | Lý do bán | Loại | Ngày vào | Ngày ra

### **3. Scanner - Stock Classification (daily_signal_scanner_eod.py)**

**BEFORE (WRONG):**
```python
if close >= 50000: stock_type = "Blue Chip"  # ❌ Price-based
```

**AFTER (CORRECT):**
```python
# Lines 105-127:
BLUE_CHIP_STOCKS = ['VCB', 'VHM', 'HPG', 'STB', ...] # 50 stocks
def get_stock_type(ticker):
    return "Blue Chip" if ticker in BLUE_CHIP_STOCKS else "Mid Cap"

stock_type = get_stock_type(ticker)  # ✅ Ticker-based
```

**Impact:**
- HPG (28k) now Blue Chip ✅ (was Mid Cap ❌)
- CTD (86k) now Mid Cap ✅ (was Blue Chip ❌)

---

## 📊 DATABASE CHANGES

### **Exit Reason Values:**
- `STOP_LOSS` → 🔴 Cắt lỗ (SL)
- `TAKE_PROFIT` → 🟢 Chốt lời (TP)
- `MA20_BREAK` / `MA20_STRICT` / `MA20_CONSECUTIVE` → 🟠 MA20 variants
- Default → ⚪ Thủ công

### **Data Quality Fixes:**
1. **Migration:** 39 old SELL signals filled with exit data
2. **Manual fix:** 4 signals on 06/03/2026 (actual prices vs estimates)
3. **Stock type:** All signals updated to ticker-based classification

---

## 🎓 KEY LEARNINGS

**Price ≠ Market Cap:**
- ❌ Don't classify by price (>= 50k = Blue Chip)
- ✅ Use curated ticker list based on actual market cap

**Migration vs Reality:**
- Migration fills exit_price from SL/TP (estimates)
- Actual market executions differ
- ⚠️ Always verify migrated data manually

**Data Flow:**
```
Database (exit_price) → API → Frontend → User sees accurate P/L
```
If database wrong → frontend shows wrong data (no matter how good the code)

---

## 🔧 CRITICAL CODE PATTERNS

### **Backend - Always include exit fields in API:**
```python
'exit_price': round(s.exit_price / 100) * 100 if s.exit_price else None,
'exit_reason': s.exit_reason,
'exit_date': s.exit_date,
```

### **Frontend - Always use API data (not calculated):**
```javascript
const exitPrice = signal.exit_price || 0;  // From API
// NOT: const exitPrice = signal.take_profit;  // Calculated - WRONG!
```

### **Scanner - Always use ticker list (not price):**
```python
stock_type = get_stock_type(ticker)  # From list
// NOT: if close >= 50000: stock_type = "Blue Chip"  // Price - WRONG!
```

---

## 🚀 DEPLOYMENT NOTES

**Backend deployment:**
- ⚠️ Adding columns to model = must update model BEFORE using in API
- ⚠️ AttributeError if model missing columns → 500 error
- ✅ Test locally, verify model has columns, then deploy

**Frontend deployment:**
- Clear browser cache after deploy (Ctrl+Shift+R)
- Cloudflare Pages auto-deploys in 2-3 minutes

**Database migrations:**
- Always test on staging first
- Keep backup of data before bulk updates
- Verify with SELECT queries before running UPDATE

---

## 📋 FILES MODIFIED

**Production code:**
- `backend_api.py` - Signal model + API
- `frontend/src/components/SignalsModule.jsx` - SELL table  
- `daily_signal_scanner_eod.py` - Stock classification

**One-time scripts (not in repo):**
- `migrate_old_sell_signals.py` - 39 signals migration
- `update_sell_signals_06032026.py` - 4 manual fixes
- `check_and_fix_stock_type.py` - Fix all stock_type

---

## ✅ FINAL RESULT

**SELL Signals Display:**
```
STB  | 61,100 | 63,800 | +4.42%  | 🟢 Chốt lời | Blue Chip | 6/3/2026
HPG  | 28,300 | 27,000 | -4.59%  | 🔴 Cắt lỗ  | Blue Chip | 6/3/2026
CTD  | 86,000 | 80,600 | -6.28%  | 🔴 Cắt lỗ  | Mid Cap   | 6/3/2026
PHR  | 63,700 | 61,300 | -3.77%  | 🔴 Cắt lỗ  | Mid Cap   | 6/3/2026
```

✅ Accurate P/L  
✅ Actual prices  
✅ Correct classification  
✅ Clean display  

---

## 🔍 TROUBLESHOOTING QUICK REF

| Issue | Cause | Fix |
|-------|-------|-----|
| P/L = -100% | exit_price NULL | Run migration script |
| Wrong stock type | Price-based logic | Deploy fixed scanner |
| Exit price wrong | SL/TP estimate | Manual update with actual |
| Frontend not updating | Cache | Ctrl+Shift+R |
| API 500 error | Model missing columns | Add columns to Signal model first |

---

## 📖 ADD TO USER MEMORIES

**Update these sections:**

### **Technical Architecture:**
```
✅ Signal tracking: status, position_pct, signal_code, buy_signal_code
✅ Exit tracking: exit_price, exit_reason, exit_date (NEW)
✅ Stock classification: BLUE_CHIP_STOCKS list (ticker-based, NOT price)
```

### **Data Models:**
```python
class Signal(Base):
    # ... existing fields ...
    status = Column(String(20), default='open')
    position_pct = Column(Integer, default=100)
    exit_price = Column(Float, nullable=True)      # NEW
    exit_reason = Column(String(50), nullable=True) # NEW  
    exit_date = Column(String(20), nullable=True)   # NEW
```

### **Key Learnings:**
```
- Price ≠ Market Cap: Use ticker list for classification
- Database first: Fix data quality before frontend
- User preferences: Clean display (no emoji clutter)
- Migration requires verification: Estimates ≠ Reality
```

### **Scanner Logic:**
```python
# Stock classification function:
def get_stock_type(ticker):
    if ticker in BLUE_CHIP_STOCKS: return "Blue Chip"
    elif ticker in TOP_343_STOCKS: return "Mid Cap"
    else: return "Penny"

# BLUE_CHIP_STOCKS = 50 large-cap stocks
# TOP_343_STOCKS = 343 high-liquidity stocks (Blue Chip + Mid Cap)
```

---

## 🎯 QUICK COMMANDS REFERENCE

**Check database:**
```powershell
python check_production_db.py  # Verify exit data
python check_and_fix_stock_type.py  # Fix classifications
```

**Deploy:**
```powershell
# Backend
git push origin main  # Auto-deploy to Render

# Frontend  
git push origin main  # Auto-deploy to Cloudflare Pages

# Staging
git checkout staging && git merge main && git push origin staging
```

**Verify:**
```powershell
# API test
Invoke-RestMethod https://ai-advisor1-backend.onrender.com/api/signals

# Frontend
Start-Process https://ai-advisor.vn  # Ctrl+Shift+R
```

---

**Session complete!** ✅  
**Full details:** See SESSION_UPDATE_SELL_SIGNALS_COMPLETE.md
