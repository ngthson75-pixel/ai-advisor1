# 🚀 QUICK TEST GUIDE - SELL SIGNAL V2

**Date:** 2026-02-05  
**Status:** Ready to Test  
**Time:** 2 minutes

---

## ✅ AUTO-MIGRATION ADDED!

Scanner bây giờ **tự động thêm columns** khi chạy lần đầu:

- ✅ `exit_reason` - Lý do bán (SL, TP_PARTIAL, MA20_CONSECUTIVE, MA20_HIGH_VOLUME)
- ✅ `exit_date` - Ngày bán
- ✅ `profit_loss_pct` - % lãi/lỗ
- ✅ `exit_quantity_pct` - % bán (50 hoặc 100)
- ✅ `buy_signal_id` - Link tới BUY signal
- ✅ `volume_ratio` - Volume / AvgVolume20

---

## 🚀 TEST NGAY (2 PHÚT)

### Step 1: Replace File

```powershell
# Download file mới (đã fix)
# File: sell_signal_scanner_v2.py

# Copy vào scripts folder
Copy-Item sell_signal_scanner_v2.py C:\ai-advisor1\scripts\ -Force
```

---

### Step 2: Run Scanner

```powershell
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30
```

---

### Step 3: Expected Output

```
======================================================================
🔍 SELL SIGNAL SCANNER V2.0
======================================================================

NEW LOGIC:
  1. SL: Price <= Stop Loss → SELL 100%
  2. TP: Price >= Take Profit → SELL 50% (partial)
  3. MA20 Consecutive: Close < MA20 AND PrevClose < MA20 → SELL 100%
  4. MA20 High Volume: Close < MA20 AND Volume > AvgVol20 → SELL 100%

Scanning BUY signals from last 30 days...
Date: 2026-02-05 XX:XX:XX

⚙️ Auto-migration: Added columns: exit_reason, exit_date, profit_loss_pct, exit_quantity_pct, buy_signal_id, volume_ratio
✓ Found 132 active BUY signals to check

Checking VCB (1/132)...
  Already sold: 0%
  ✓ No sell condition met

Checking HPG (2/132)...
  Already sold: 0%
  🟢 TP PARTIAL: HPG - Sell 50% at 43,500
     Reason: TP_PARTIAL
     Quantity: 50%
     Entry: 40,000
     Exit: 43,500
     P/L: +8.75%
     ✓ Saved to database

...

======================================================================
📊 SCAN COMPLETE
======================================================================

BUY signals checked: 132
SELL signals generated: 12

📋 SELL Signals by Reason:
  Stop Loss (SL): 2
  Take Profit Partial (50%): 5
  MA20 Consecutive: 3
  MA20 High Volume: 2

🔝 Top 5 Signals:
1. 🟢 VCB - TP_PARTIAL - 50% - +9.20%
2. 🟢 HPG - TP_PARTIAL - 50% - +8.75%
3. 🔴 MBB - SL - 100% - -5.10%
4. 🟡 TCB - MA20_CONSECUTIVE - 100% - -2.30%
5. 🟠 FPT - MA20_HIGH_VOLUME - 100% - -1.50%

======================================================================
```

---

## ✅ VERIFICATION

### Check Database:

```bash
sqlite3 signals.db

# Check columns added
sqlite> PRAGMA table_info(signals);
# Should see: exit_reason, exit_date, profit_loss_pct, exit_quantity_pct, buy_signal_id, volume_ratio

# Check SELL signals
sqlite> SELECT ticker, exit_reason, exit_quantity_pct, profit_loss_pct 
        FROM signals 
        WHERE action='SELL' 
        ORDER BY created_at DESC 
        LIMIT 5;

# Expected:
# VCB|TP_PARTIAL|50.0|9.20
# HPG|TP_PARTIAL|50.0|8.75
# MBB|SL|100.0|-5.10
# ...

sqlite> .quit
```

---

## 🎯 WHAT TO EXPECT

### First Run:

1. **Migration happens automatically**
   - Adds 6 new columns
   - Takes 1-2 seconds
   - Only happens once

2. **Scanner runs**
   - Checks all active BUY signals
   - Applies 4 new conditions
   - Generates SELL signals

3. **Results saved**
   - SELL signals in database
   - Linked to original BUY signals
   - Ready for display in frontend

---

### Subsequent Runs:

- No migration (columns already exist)
- Faster execution
- Only scans new/changed positions

---

## 📊 EXPECTED RESULTS

From 132 BUY signals:

- **TP_PARTIAL (50%):** 4-6 signals
  - Stocks that hit take profit
  - Sell 50%, keep 50%
  - Profit: +8% to +12%

- **MA20_CONSECUTIVE:** 2-4 signals
  - 2 days below MA20
  - Sell 100% remaining
  - P/L: -3% to +2%

- **MA20_HIGH_VOLUME:** 1-3 signals
  - Below MA20 + volume spike
  - Sell 100% remaining
  - P/L: -4% to 0%

- **SL:** 1-2 signals
  - Hit stop loss
  - Sell 100% remaining
  - Loss: -5% to -7%

**Total:** 8-15 SELL signals per run

---

## 🐛 TROUBLESHOOTING

### Issue 1: Still getting "no such column"

**Cause:** Database locked or permission issue

**Solution:**
```bash
# Close any apps using signals.db
# Try again
python sell_signal_scanner_v2.py --days 30
```

---

### Issue 2: No SELL signals generated

**Cause:** No conditions met (market still strong)

**Check:**
```bash
# How many active BUY signals?
sqlite3 signals.db "SELECT COUNT(*) FROM signals WHERE action='BUY' AND date >= '2026-01-05';"

# Any at Take Profit?
sqlite3 signals.db "SELECT ticker, entry_price, take_profit FROM signals WHERE action='BUY' LIMIT 5;"
```

**Expected:** If market is still bullish, few SELL signals is normal

---

### Issue 3: vnstock errors

**Cause:** API rate limit or network issue

**Solution:**
```bash
# Wait 1 minute
# Run with fewer days
python sell_signal_scanner_v2.py --days 7

# Or upgrade vnstock
pip install vnstock --upgrade
```

---

## 📈 NEXT STEPS

After successful test:

1. **Review Results**
   ```bash
   sqlite3 signals.db "SELECT * FROM signals WHERE action='SELL' ORDER BY created_at DESC LIMIT 10;"
   ```

2. **Deploy to Production**
   - Copy scanner to production server
   - Update backend API
   - Schedule daily runs

3. **Update Frontend**
   - Add "Số lượng" column
   - Add new exit_reason badges
   - Display signals

4. **Monitor Daily**
   - Check signal quality
   - Adjust parameters if needed
   - Track performance

---

## ✅ SUCCESS CRITERIA

Scanner is working correctly if:

- [x] Runs without errors
- [x] Auto-migration completes
- [x] Finds active BUY signals
- [x] Generates SELL signals (if conditions met)
- [x] Saves to database successfully
- [x] Shows correct exit reasons
- [x] Calculates profit/loss correctly

---

## 📞 NEED HELP?

**Common Questions:**

**Q: Why only a few SELL signals?**  
A: Normal if market is strong. TP_PARTIAL only triggers if price >= TP.

**Q: Can I test with fake data?**  
A: Yes! Insert test BUY signal:
```sql
INSERT INTO signals (ticker, action, entry_price, stop_loss, take_profit, date, strategy, strength, stock_type)
VALUES ('TEST', 'BUY', 100000, 95000, 108000, '2026-02-01', 'TEST', 70, 'Mid Cap');
```

**Q: How to reset and test again?**  
A: Delete SELL signals:
```sql
DELETE FROM signals WHERE action='SELL';
```

---

**Contact:** ngthson75@gmail.com | +84938127666

---

**Status:** ✅ Ready to Test  
**Time Required:** 2 minutes  
**Expected Result:** 8-15 SELL signals from 132 BUY signals
