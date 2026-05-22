# CTI SIGNAL FIX + SCANNER DEPLOYMENT

**Issue:** CTI SELL signal thiếu exit_price, exit_date  
**Root cause:** Scanner code thiếu 2 fields trong payload  
**Impact:** Website hiển thị P/L = -100%, GIÁ RA = "-"

---

## ⚡ FIX NGAY (3 BƯỚC - 10 PHÚT)

### **STEP 1: FIX CTI SIGNAL QUA SQL (3 PHÚT) ⭐ URGENT**

**Option A: Nếu biết exit price chính xác**

```sql
-- Update CTI với giá thực tế
-- (Thay 22200 bằng giá thực tế từ scanner log hoặc vnstock)
UPDATE signals
SET 
    exit_price = 22200,  -- ← THAY BẰNG GIÁ THỰC!
    exit_date = '2026-03-10'
WHERE ticker = 'CTI'
  AND action = 'SELL'
  AND date = '2026-03-10'
  AND exit_price IS NULL;

-- Verify
SELECT 
    ticker, entry_price, exit_price,
    ROUND(((exit_price - entry_price)::numeric / entry_price * 100), 2) as pnl_pct,
    strategy, exit_date
FROM signals
WHERE ticker = 'CTI'
  AND action = 'SELL'
  AND date = '2026-03-10';
```

**Option B: Get giá từ market data (nếu có vnstock)**

```python
# Run locally để get CTI price ngày 10/3
from vnstock3 import Vnstock
import pandas as pd

stock = Vnstock().stock(symbol='CTI', source='VCI')
df = stock.quote.history(start='2026-03-10', end='2026-03-10')

if not df.empty:
    exit_price = df['close'].iloc[-1] * 1000  # vnstock prices in thousands
    print(f"CTI exit_price: {exit_price:,.0f}")
    # Use this value in SQL above
```

**Option C: Ước lượng từ MA20_STRICT logic**

CTI hit MA20_STRICT → thoả:
- Price < MA20 2 ngày
- P/L >= -3% HOẶC 0% <= P/L < 2%

Entry: 23,800

Nếu P/L = -1%: exit = 23,800 * 0.99 = 23,562  
Nếu P/L = -3%: exit = 23,800 * 0.97 = 23,086

**RECOMMEND: Chạy Option B để get giá chính xác!**

---

### **STEP 2: DEPLOY FIXED SCANNER (5 PHÚT) ⭐⭐⭐ CRITICAL**

**File đã fix:** `sell_signal_scanner_v5_2_FIXED.py`

**Changes:**
```python
# Line 475-476 (ADDED):
'exit_price': sell_signal['exit_price'],  # ← NEW!
'exit_date': datetime.now().strftime('%Y-%m-%d'),  # ← NEW!
```

**Deploy steps:**

```powershell
cd C:\ai-advisor1

# 1. Backup file cũ
copy sell_signal_scanner_v5.2.py sell_signal_scanner_v5.2.py.backup

# 2. Copy fixed file from outputs
copy outputs\sell_signal_scanner_v5_2_FIXED.py sell_signal_scanner_v5.2.py

# 3. Verify changes
Select-String -Path sell_signal_scanner_v5.2.py -Pattern "exit_price.*sell_signal"

# Should see line 475:
# 'exit_price': sell_signal['exit_price'],

# 4. Test local (dry-run)
python sell_signal_scanner_v5.2.py --dry-run

# 5. Commit & push
git add sell_signal_scanner_v5.2.py
git status  # Verify staged

git commit -m "fix: Add exit_price and exit_date to SELL signal payload

CRITICAL FIX:
- Scanner was missing exit_price field → frontend showed -100%
- Scanner was missing exit_date field → frontend showed N/A

Changes:
- Line 475: Added 'exit_price': sell_signal['exit_price']
- Line 476: Added 'exit_date': datetime.now().strftime('%Y-%m-%d')

Impact:
- Future SELL signals will have correct exit_price
- Website will display correct P/L
- NGÀY RA will show actual date

Fixes issue: CTI (10/3/2026) and all future signals"

git push origin main

# 6. Verify pushed
git log --oneline -1
```

---

### **STEP 3: VERIFY (2 PHÚT)**

**Test next automated run:**

```powershell
# Wait for next hourly scan (e.g., 10:05 VN)
# Or trigger manual:
Start-Process "https://github.com/ngthson75-pixel/ai-advisor1/actions"
# Run workflow → Check logs
```

**Check website after scan:**
- ✅ New SELL signals should have GIÁ RA
- ✅ P/L should be correct (not -100%)
- ✅ NGÀY RA should show date (not N/A)

---

## 🎯 CTI EXIT PRICE - FIND IT

**METHOD 1: Check scanner logs (if available)**

If you ran scanner and have console output, search for:
```
[X/Y] CTI
  🔴 SELL! MA20_STRICT | P/L: -X.XX% | Bán: 100%
  Entry: 23,800 → Exit: XXXXX  ← This is exit_price
```

**METHOD 2: Get from vnstock**

```powershell
# Run this Python script locally
python -c "
from vnstock3 import Vnstock
stock = Vnstock().stock(symbol='CTI', source='VCI')
df = stock.quote.history(start='2026-03-10', end='2026-03-10')
if not df.empty:
    price = df['close'].iloc[-1] * 1000
    print(f'CTI exit_price on 10/3: {price:,.0f}')
"
```

**METHOD 3: Check market data website**

- Go to: https://finance.vietstock.vn/CTI
- Find close price on 10/3/2026
- Use that price * 1000 (if needed)

---

## 📊 EXPECTED FIX RESULT

**BEFORE (CTI current state):**
```
CTI | Entry: 23,800 | Exit: - | P/L: -100.00% | N/A
```

**AFTER (after SQL + scanner fix):**
```
CTI | Entry: 23,800 | Exit: 22,XXX | P/L: -X.XX% | 10/3/2026
```

**Future signals:**
```
ALL | Entry: XX,XXX | Exit: YY,YYY | P/L: ±Z.ZZ% | DD/MM/YYYY
```

---

## 🚨 CRITICAL NOTES

**WHY CTI FAILED:**
1. Scanner code thiếu exit_price trong payload
2. GitHub Actions workflow chạy code CŨ (chưa có fix)
3. Scanner push signal → database lưu exit_price = NULL
4. Frontend đọc NULL → tính P/L sai = -100%

**FIX ENSURES:**
1. ✅ Payload có exit_price + exit_date
2. ✅ Database lưu đủ fields
3. ✅ Frontend hiển thị đúng
4. ✅ NGÀY RA không còn N/A

**DEPLOY IS CRITICAL:**
- File fix chỉ có trên local
- PHẢI PUSH LÊN GITHUB
- GitHub Actions sẽ dùng code từ repo (không phải local)
- Nếu không push → lần sau vẫn lỗi!

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Get CTI exit_price (vnstock or logs)
- [ ] Run SQL to update CTI signal
- [ ] Verify CTI on website (correct P/L)
- [ ] Copy fixed scanner file
- [ ] Test local (dry-run)
- [ ] Commit with clear message
- [ ] Push to GitHub
- [ ] Verify git log shows commit
- [ ] Wait for next auto scan
- [ ] Check new signals have exit_price

---

## 🎯 BOTTOM LINE

**CTI fix:** 
1. Get exit_price từ vnstock/logs
2. Run SQL UPDATE
3. Verify website

**Scanner fix:**
1. Deploy sell_signal_scanner_v5_2_FIXED.py
2. Push to GitHub (CRITICAL!)
3. Future signals will be correct

**Time:** 10 minutes total

---

**RUN STEP 2 (DEPLOY SCANNER) NGAY ĐỂ FIX PERMANENT!** 🚀
