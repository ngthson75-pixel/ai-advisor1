# SELL SIGNAL SYSTEM V2.0 - NEW LOGIC

**Version:** 2.0  
**Date:** 2026-02-02  
**Status:** Updated Logic  
**Owner:** Nguyễn Thanh Sơn

---

## 🆕 WHAT'S NEW IN V2.0

### Major Changes:

1. **PARTIAL EXIT:** Take Profit now sells **50% only** (keep 50% for more upside)
2. **MA20 CONSECUTIVE:** Changed from "break" to "both days below MA20"
3. **VOLUME SIGNAL:** New condition - MA20 break + high volume
4. **TRACKING:** System tracks % sold for each position (allow multiple exits)

---

## 📊 NEW SELL CONDITIONS

### Condition 1: STOP LOSS (Unchanged)
```
IF current_price <= stop_loss
THEN SELL 100% (remaining)
```

**Reason:** `SL`  
**Quantity:** 100% of remaining position  
**Priority:** **HIGHEST** (exit immediately)

**Example:**
```
Entry: 88,500
SL: 83,044
Current: 82,000

→ SELL 100% at 82,000
→ Loss: -7.3%
```

---

### Condition 2: TAKE PROFIT ⭐ CHANGED
```
IF current_price >= take_profit
AND available_quantity >= 50%
THEN SELL 50% (partial exit)
```

**Reason:** `TP_PARTIAL`  
**Quantity:** 50% only (keep 50%)  
**Priority:** High

**Logic:**
- Lock in profit with 50%
- Keep 50% for potential further upside
- Trailing stop can be used for remaining 50%

**Example:**
```
Entry: 88,500
TP: 95,580 (+8%)
Current: 96,000

→ SELL 50% at 96,000 (chốt lời 50%)
→ KEEP 50% (để chạy thêm)
→ Profit on 50%: +8.5%
```

---

### Condition 3: MA20 CONSECUTIVE ⭐ CHANGED
```
IF current_price < MA20
AND prev_close < prev_MA20
THEN SELL 100% (remaining)
```

**Reason:** `MA20_CONSECUTIVE`  
**Quantity:** 100% of remaining  
**Priority:** Medium

**Logic:**
- Both today AND yesterday below MA20
- Confirms downtrend (not just touching)
- More reliable than single-day break

**Example:**
```
Yesterday: Close 89,000 < MA20 89,500
Today: Close 88,000 < MA20 89,000

→ Both days below MA20 ✓
→ SELL 100% at 88,000
```

**vs OLD logic:**
```
OLD: Break = Yesterday >= MA20, Today < MA20
NEW: Consecutive = Both days < MA20
```

---

### Condition 4: MA20 + HIGH VOLUME ⭐ NEW
```
IF current_price < MA20
AND volume > avg_volume_20
THEN SELL 100% (remaining)
```

**Reason:** `MA20_HIGH_VOLUME`  
**Quantity:** 100% of remaining  
**Priority:** Medium

**Logic:**
- Price below MA20 (weakness)
- High volume (strong selling pressure)
- Confirms breakdown with conviction

**Example:**
```
Current: 88,000 < MA20 89,000
Volume: 2,500,000
AvgVol20: 1,800,000

→ Volume ratio: 2,500,000 / 1,800,000 = 1.39x
→ SELL 100% at 88,000
```

---

## 🔄 PRIORITY ORDER

When multiple conditions trigger:

```
1. STOP LOSS (highest priority)
   ↓ Exit immediately on SL
   
2. TAKE PROFIT PARTIAL (if available >= 50%)
   ↓ Lock in profit
   
3. MA20 CONSECUTIVE (if not sold yet)
   ↓ Confirmed downtrend
   
4. MA20 HIGH VOLUME (if not sold yet)
   ↓ Breakdown with volume
```

**Note:** Conditions 3 and 4 are mutually exclusive in practice.

---

## 📈 POSITION TRACKING

### New Database Fields:

```sql
ALTER TABLE signals ADD COLUMN exit_quantity_pct REAL DEFAULT 100;
ALTER TABLE signals ADD COLUMN buy_signal_id INTEGER;
ALTER TABLE signals ADD COLUMN volume_ratio REAL;
```

### Example Position Lifecycle:

```
Day 1: BUY 100% at 88,500
       buy_signal_id = 1
       
Day 3: TP triggered at 95,580
       → SELL 50% (exit_quantity_pct = 50)
       → Remaining: 50%
       
Day 5: MA20_CONSECUTIVE triggered at 92,000
       → SELL 50% (remaining)
       → Position fully closed
```

### Query to Check Position Status:

```sql
SELECT 
    ticker,
    entry_price,
    SUM(CASE WHEN action = 'SELL' THEN exit_quantity_pct ELSE 0 END) as total_sold_pct,
    100 - SUM(CASE WHEN action = 'SELL' THEN exit_quantity_pct ELSE 0 END) as remaining_pct
FROM signals
WHERE buy_signal_id = 1
GROUP BY ticker;
```

---

## 💡 LOGIC COMPARISON

### Example Scenario:

**Stock:** VCB  
**Entry:** 88,500 (Day 1)  
**TP:** 95,580  
**SL:** 83,044  
**MA20:** 90,000

| Day | Close | MA20 | Volume | V1.0 Action | V2.0 Action |
|-----|-------|------|--------|-------------|-------------|
| 1 | 88,500 | 90,000 | Normal | - | - |
| 2 | 92,000 | 90,500 | Normal | - | - |
| 3 | 96,000 | 91,000 | Normal | SELL 100% (TP) | **SELL 50% (TP)** ⭐ |
| 4 | 93,000 | 91,000 | High | - | - |
| 5 | 89,000 | 90,500 | High | - | **SELL 50% (MA20+Vol)** ⭐ |

**Result:**
- **V1.0:** Sold 100% at 96,000 → Profit: +8.5%
- **V2.0:** Sold 50% at 96,000, 50% at 89,000 → Avg Profit: +4.0%

**Trade-off:**
- V1.0: Higher profit but missed upside if price continues
- V2.0: Lower average but protected profit + kept exposure

---

## 🎯 USE CASES

### Use Case 1: Strong Uptrend
```
Scenario: Stock keeps going up after TP
Result:
- V1.0: Sold 100% at TP, missed further gains
- V2.0: Sold 50% at TP, kept 50% for more upside ✓
```

### Use Case 2: False Breakout
```
Scenario: Price hits TP then drops
Result:
- V1.0: Sold 100% at TP (good exit)
- V2.0: Sold 50% at TP, lost some on remaining 50%
```

### Use Case 3: Gradual Decline
```
Scenario: Price slowly drops below MA20
Result:
- V1.0: Exit only on sharp break (1 day)
- V2.0: Exit on consecutive days or volume spike ✓ (more reliable)
```

---

## 🗄️ DATABASE SCHEMA UPDATE

### New Columns:

```sql
-- For tracking partial exits
exit_quantity_pct REAL DEFAULT 100    -- % sold (50 or 100)

-- For linking to original BUY signal
buy_signal_id INTEGER                 -- References signals.id

-- For volume-based signals
volume_ratio REAL                     -- current_vol / avg_vol_20
```

### Migration Query:

```sql
-- Run this once
ALTER TABLE signals ADD COLUMN exit_quantity_pct REAL DEFAULT 100;
ALTER TABLE signals ADD COLUMN buy_signal_id INTEGER;
ALTER TABLE signals ADD COLUMN volume_ratio REAL;

-- Create index for better performance
CREATE INDEX idx_signals_buy_signal_id ON signals(buy_signal_id);
```

---

## 📊 EXPECTED PERFORMANCE

### Signal Distribution (estimated):

| Exit Reason | % of Signals | Avg P/L |
|-------------|--------------|---------|
| SL | 25-30% | -5% to -7% |
| TP_PARTIAL | 40-45% | +8% to +12% |
| MA20_CONSECUTIVE | 15-20% | -2% to +3% |
| MA20_HIGH_VOLUME | 10-15% | -3% to +1% |

### Overall Metrics:

- **Win Rate:** 55-65% (similar to V1.0)
- **Avg Win:** +9% (on TP_PARTIAL)
- **Avg Loss:** -5% (on SL + MA20)
- **Risk/Reward:** ~1.8x (better with partial exits)

---

## 🚀 DEPLOYMENT GUIDE

### Step 1: Test New Scanner

```bash
# Copy new scanner
cp sell_signal_scanner_v2.py C:\ai-advisor1\scripts\

# Test run
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30

# Expected output:
# ✓ Found X active BUY signals
# 🟢 TP PARTIAL: VCB - Sell 50% at 96,000
# 🟠 MA20 HIGH VOL: HPG - Sell 100% at 42,000 (Vol: 1.5x)
# ...
```

---

### Step 2: Update Database

```powershell
# Run migration
Invoke-WebRequest -Uri "http://localhost:10000/api/migrate/sell" -Method POST

# Or manually:
sqlite3 signals.db
sqlite> ALTER TABLE signals ADD COLUMN exit_quantity_pct REAL DEFAULT 100;
sqlite> ALTER TABLE signals ADD COLUMN buy_signal_id INTEGER;
sqlite> ALTER TABLE signals ADD COLUMN volume_ratio REAL;
sqlite> .quit
```

---

### Step 3: Update Backend API

In `backend_api.py`, update the scan endpoint:

```python
# Change import
from sell_signal_scanner_v2 import SellSignalScannerV2  # V2!

@app.route('/api/scan/sell', methods=['POST'])
def scan_sell_signals():
    # ...
    # Change scanner class
    scanner = SellSignalScannerV2(db_path='signals.db')  # V2!
    # ...
```

---

### Step 4: Update Frontend

Add new exit reasons to UI:

```jsx
const getReasonLabel = (reason) => {
  switch(reason) {
    case 'SL': return 'Stop Loss';
    case 'TP_PARTIAL': return 'Take Profit (50%)';  // NEW
    case 'MA20_CONSECUTIVE': return 'MA20 Consecutive';  // NEW
    case 'MA20_HIGH_VOLUME': return 'MA20 + Volume';  // NEW
    default: return reason;
  }
};

const getReasonBadge = (reason) => {
  switch(reason) {
    case 'SL': return 'red';
    case 'TP_PARTIAL': return 'green';
    case 'MA20_CONSECUTIVE': return 'yellow';
    case 'MA20_HIGH_VOLUME': return 'orange';
    default: return 'gray';
  }
};
```

Add quantity column to table:

```jsx
<table>
  <thead>
    <tr>
      <th>Mã</th>
      <th>Giá mua</th>
      <th>Giá bán</th>
      <th>Số lượng</th>  {/* NEW */}
      <th>Lý do</th>
      <th>Lãi/Lỗ</th>
      <th>Ngày</th>
    </tr>
  </thead>
  <tbody>
    {signals.map(signal => (
      <tr key={signal.id}>
        <td>{signal.ticker}</td>
        <td>{signal.entry_price.toLocaleString()}</td>
        <td>{signal.exit_price.toLocaleString()}</td>
        <td>{signal.exit_quantity_pct}%</td>  {/* NEW */}
        <td><span className={`badge ${getReasonBadge(signal.exit_reason)}`}>
          {getReasonLabel(signal.exit_reason)}
        </span></td>
        <td className={signal.profit_loss_pct > 0 ? 'profit' : 'loss'}>
          {signal.profit_loss_pct > 0 ? '+' : ''}
          {signal.profit_loss_pct.toFixed(2)}%
        </td>
        <td>{signal.exit_date}</td>
      </tr>
    ))}
  </tbody>
</table>
```

---

## 🧪 TESTING SCENARIOS

### Test 1: Partial Exit

```
Setup:
- BUY VCB at 88,500 (Day 1)
- Price reaches 96,000 (Day 3)

Test:
python sell_signal_scanner_v2.py --days 30

Expected:
✓ TP PARTIAL: VCB - Sell 50% at 96,000
✓ Remaining: 50%

Verify database:
SELECT * FROM signals WHERE ticker='VCB' AND action='SELL';
→ exit_quantity_pct = 50 ✓
```

---

### Test 2: Consecutive MA20

```
Setup:
- Already sold 50% via TP_PARTIAL
- Day 4: Close 89,000 < MA20 90,000
- Day 5: Close 88,000 < MA20 89,500

Test:
python sell_signal_scanner_v2.py --days 30

Expected:
✓ MA20 CONSECUTIVE: VCB - Sell 50% (remaining) at 88,000

Verify:
Total sold = 50% (TP) + 50% (MA20) = 100% ✓
Position fully closed ✓
```

---

### Test 3: Volume Signal

```
Setup:
- BUY HPG at 42,000
- Day 2: Close 41,000 < MA20 42,500
- Volume 2,500,000 > AvgVol 1,700,000

Test:
python sell_signal_scanner_v2.py --days 30

Expected:
✓ MA20 HIGH VOL: HPG - Sell 100% at 41,000 (Vol: 1.47x)

Verify:
→ exit_reason = 'MA20_HIGH_VOLUME' ✓
→ volume_ratio = 1.47 ✓
```

---

## ⚠️ IMPORTANT NOTES

### 1. Position Management

**Issue:** User manually sold some shares outside system

**Solution:**
- System tracks % based on signals only
- Recommend: Manual adjustment in admin panel
- Or: User reports actual remaining %

---

### 2. Partial Exit Tracking

**Issue:** Multiple SELL signals for same BUY signal

**Query to get position status:**
```sql
SELECT 
    b.ticker,
    b.entry_price,
    b.date as buy_date,
    COALESCE(SUM(s.exit_quantity_pct), 0) as total_sold,
    100 - COALESCE(SUM(s.exit_quantity_pct), 0) as remaining
FROM signals b
LEFT JOIN signals s ON s.buy_signal_id = b.id AND s.action = 'SELL'
WHERE b.action = 'BUY' AND b.ticker = 'VCB'
GROUP BY b.id;
```

---

### 3. Edge Cases

**Case 1:** TP triggered but only 25% remaining
```
Solution: Don't sell (need >= 50% available)
Result: Wait for other exit conditions
```

**Case 2:** Both MA20_CONSECUTIVE and MA20_HIGH_VOLUME trigger
```
Solution: MA20_CONSECUTIVE has priority (checked first)
Result: Only one SELL signal created
```

**Case 3:** SL triggered after partial TP exit
```
Solution: Sell remaining 50% at SL price
Result: Final P/L = (50% * +8%) + (50% * -6%) = +1%
```

---

## 📞 SUPPORT

**Questions?** Contact:
- **Email:** ngthson75@gmail.com
- **Phone:** +84938127666

**Files:**
- Scanner V2: `sell_signal_scanner_v2.py`
- Documentation: `SELL_SIGNAL_V2_DOCUMENTATION.md`
- Migration: See Step 2 in Deployment Guide

---

## 📚 CHANGELOG

### V2.0 (2026-02-02)
- ⭐ Changed TP to partial exit (50%)
- ⭐ Changed MA20 break to consecutive days
- ⭐ Added MA20 + high volume condition
- ⭐ Added position tracking (exit_quantity_pct)
- ⭐ Added buy_signal_id for linking

### V1.0 (2026-02-02)
- Initial release
- TP/SL/MA20_BREAK logic
- 100% exits only

---

**END OF DOCUMENTATION V2.0**

**Status:** ✅ Ready for Testing & Deployment
