# 🚀 SELL SIGNAL V2 - QUICK START GUIDE

**Version:** 2.0  
**Time Required:** 30 minutes  
**Difficulty:** Easy

---

## 🎯 WHAT YOU'LL GET

After completing this guide:

✅ Sell 50% at Take Profit (keep 50% for upside)  
✅ Exit on consecutive MA20 break (fewer false signals)  
✅ Exit on MA20 + high volume (volume confirmation)  
✅ Track partial positions automatically  

---

## ⚡ 3-STEP QUICK DEPLOYMENT

### STEP 1: Update Scanner (5 min)

```bash
# 1. Download V2 scanner
# (You already have: sell_signal_scanner_v2.py)

# 2. Copy to scripts folder
Copy-Item sell_signal_scanner_v2.py C:\ai-advisor1\scripts\

# 3. Test run
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30

# Expected output:
# ✓ Found 132 active BUY signals
# 🟢 TP PARTIAL: VCB - Sell 50% at 96,000
# 🟠 MA20 HIGH VOL: HPG - Sell 100% at 42,000 (Vol: 1.5x)
# ...
```

**✓ Pass if:** Scanner runs and finds signals

---

### STEP 2: Update Database (2 min)

```powershell
# Method A: Via API (recommended)
Invoke-WebRequest -Uri "http://localhost:10000/api/migrate/sell" -Method POST

# Method B: Manual SQL
sqlite3 signals.db
sqlite> ALTER TABLE signals ADD COLUMN exit_quantity_pct REAL DEFAULT 100;
sqlite> ALTER TABLE signals ADD COLUMN buy_signal_id INTEGER;
sqlite> ALTER TABLE signals ADD COLUMN volume_ratio REAL;
sqlite> .quit

# Verify
sqlite3 signals.db "PRAGMA table_info(signals);" | grep exit_quantity_pct
# Should show: exit_quantity_pct column
```

**✓ Pass if:** New columns added successfully

---

### STEP 3: Update Backend (3 min)

```python
# File: backend_api.py

# Change Line 1: Import V2 scanner
from sell_signal_scanner_v2 import SellSignalScannerV2  # V2!

# Change Line ~420: Use V2 in scan endpoint
@app.route('/api/scan/sell', methods=['POST'])
def scan_sell_signals():
    # ...
    scanner = SellSignalScannerV2(db_path='signals.db')  # V2!
    # ...
```

**✓ Pass if:** Backend uses V2 scanner

---

## ✅ VERIFICATION (5 min)

### Test 1: Run Scanner
```bash
cd C:\ai-advisor1\scripts
python sell_signal_scanner_v2.py --days 30
```

**Expected:**
- ✓ Scanner completes
- ✓ Finds SELL signals
- ✓ Shows exit reasons: TP_PARTIAL, MA20_CONSECUTIVE, MA20_HIGH_VOLUME

---

### Test 2: Check Database
```bash
sqlite3 signals.db "SELECT ticker, exit_reason, exit_quantity_pct FROM signals WHERE action='SELL' LIMIT 5;"
```

**Expected:**
```
VCB|TP_PARTIAL|50.0
HPG|MA20_HIGH_VOLUME|100.0
MBB|MA20_CONSECUTIVE|100.0
...
```

---

### Test 3: API Test
```powershell
# Trigger scan
Invoke-WebRequest -Uri "http://localhost:10000/api/scan/sell" -Method POST

# Wait 3 minutes

# Get results
Invoke-WebRequest -Uri "http://localhost:10000/api/signals/sell?days=7" | ConvertFrom-Json
```

**Expected:**
```json
{
  "success": true,
  "signals": [...],
  "summary": {
    "tp_count": 8,
    "sl_count": 4,
    "ma20_count": 3,
    "total_profit": 45.5
  }
}
```

---

## 🎨 FRONTEND UPDATE (Optional, 10 min)

### Add Quantity Column

```jsx
// File: SignalsModule.jsx

// Add column header
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

// Add column data
<tbody>
  {signals.map(signal => (
    <tr key={signal.id}>
      <td>{signal.ticker}</td>
      <td>{signal.entry_price.toLocaleString()}</td>
      <td>{signal.exit_price.toLocaleString()}</td>
      <td>
        <span className="quantity-badge">
          {signal.exit_quantity_pct}%
        </span>
      </td>  {/* NEW */}
      ...
    </tr>
  ))}
</tbody>
```

### Update Exit Reasons

```jsx
const getReasonLabel = (reason) => {
  const labels = {
    'SL': 'Stop Loss',
    'TP_PARTIAL': 'Take Profit (50%)',  // NEW
    'MA20_CONSECUTIVE': 'MA20 Consecutive',  // NEW
    'MA20_HIGH_VOLUME': 'MA20 + Volume',  // NEW
    // OLD (still supported)
    'TP': 'Take Profit',
    'MA20_BREAK': 'MA20 Break'
  };
  return labels[reason] || reason;
};

const getReasonBadge = (reason) => {
  const colors = {
    'SL': 'red',
    'TP_PARTIAL': 'green',
    'MA20_CONSECUTIVE': 'yellow',
    'MA20_HIGH_VOLUME': 'orange',
    'TP': 'green',
    'MA20_BREAK': 'yellow'
  };
  return colors[reason] || 'gray';
};
```

---

## 📊 EXPECTED RESULTS

### Daily Output:

```
9:00 AM: BUY scanner runs
         → Generates 100-150 BUY signals

9:30 AM: SELL scanner V2 runs
         → Checks 100-150 active positions
         → Generates:
           - 5-8 TP_PARTIAL signals (50% exits)
           - 3-5 MA20_CONSECUTIVE signals
           - 2-4 MA20_HIGH_VOLUME signals
           - 2-3 SL signals

Result: 12-20 SELL signals per day
```

### Example Signals:

| Ticker | Entry | Exit | Qty | Reason | P/L |
|--------|-------|------|-----|--------|-----|
| VCB | 88,500 | 96,000 | 50% | TP_PARTIAL | +8.5% |
| HPG | 42,000 | 41,000 | 100% | MA20_HIGH_VOLUME | -2.4% |
| MBB | 25,500 | 24,800 | 100% | MA20_CONSECUTIVE | -2.7% |
| TCB | 30,000 | 28,500 | 100% | SL | -5.0% |

---

## 🔧 CUSTOMIZATION (Advanced)

### Adjust TP Partial %

```python
# In sell_signal_scanner_v2.py, line ~180

# Default: Sell 50%
'exit_quantity_pct': 50

# Change to sell 30%
'exit_quantity_pct': 30

# Change to sell 70%
'exit_quantity_pct': 70
```

### Adjust Volume Threshold

```python
# In sell_signal_scanner_v2.py, line ~250

# Default: Volume > AvgVol20
if volume > avg_volume_20:

# Change to 1.2x
if volume > avg_volume_20 * 1.2:

# Change to 1.5x
if volume > avg_volume_20 * 1.5:
```

### Adjust MA20 Consecutive Days

```python
# In sell_signal_scanner_v2.py, line ~220

# Default: 2 days (current + previous)
if current_price < ema20 and prev_close < prev_ema20:

# Change to 3 days (need more logic)
# Requires tracking 3-day history
```

---

## 🐛 TROUBLESHOOTING

### Issue 1: Column doesn't exist

**Error:** `no such column: exit_quantity_pct`

**Solution:**
```bash
# Run migration again
Invoke-WebRequest -Uri "http://localhost:10000/api/migrate/sell" -Method POST
```

---

### Issue 2: No signals generated

**Cause:** No active BUY signals or no conditions met

**Check:**
```bash
# How many active BUY signals?
sqlite3 signals.db "SELECT COUNT(*) FROM signals WHERE action='BUY';"

# Any recent signals?
sqlite3 signals.db "SELECT ticker, date FROM signals WHERE action='BUY' ORDER BY date DESC LIMIT 5;"
```

---

### Issue 3: TP_PARTIAL not triggering

**Check:**
```python
# Condition requires >= 50% available
if current_price >= take_profit and available_pct >= 50:
```

**Solution:** If already sold >50%, TP_PARTIAL won't trigger (as designed)

---

## 📈 MONITORING

### Daily Health Check

```bash
# 1. Check signals generated
curl http://localhost:10000/api/signals/sell?days=1 | jq '.count'

# 2. Check by reason
sqlite3 signals.db "SELECT exit_reason, COUNT(*) FROM signals WHERE action='SELL' AND date='2026-02-02' GROUP BY exit_reason;"

# Expected:
# TP_PARTIAL|5
# MA20_CONSECUTIVE|3
# MA20_HIGH_VOLUME|2
# SL|1
```

### Weekly Review

```sql
-- Win rate
SELECT 
  COUNT(CASE WHEN profit_loss_pct > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM signals 
WHERE action='SELL' AND date >= '2026-01-26';

-- Average P/L by reason
SELECT 
  exit_reason,
  COUNT(*) as count,
  AVG(profit_loss_pct) as avg_pl,
  SUM(profit_loss_pct) as total_pl
FROM signals 
WHERE action='SELL' AND date >= '2026-01-26'
GROUP BY exit_reason;
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

After deployment, verify:

- [ ] Scanner V2 runs without errors
- [ ] Database has new columns (exit_quantity_pct, buy_signal_id, volume_ratio)
- [ ] Backend API uses SellSignalScannerV2
- [ ] SELL signals have new exit_reason values
- [ ] TP_PARTIAL signals show 50% quantity
- [ ] Frontend displays quantity column (if updated)
- [ ] Daily automation works (GitHub Actions)
- [ ] Telegram notifications include new reasons (if configured)

---

## 🎉 DONE!

You now have:

✅ **Partial exits** - 50% at TP, keep 50% for upside  
✅ **Better signals** - Consecutive MA20, volume confirmation  
✅ **Position tracking** - Know exactly what % sold  
✅ **Automated** - Runs daily at 9:30 AM  

---

## 📞 NEED HELP?

**Common Questions:**

Q: Should I use V1 or V2?  
A: V2 for better R/R and upside capture

Q: Can I change 50% to 30%?  
A: Yes! Edit `exit_quantity_pct` in scanner

Q: What if I want full exit at TP?  
A: Use V1 or change TP_PARTIAL to 100%

Q: How to track what % is left?  
A: Query: `SELECT SUM(exit_quantity_pct) FROM signals WHERE ticker='VCB' AND action='SELL'`

---

**Contact:** ngthson75@gmail.com | +84938127666

---

**Time to complete:** 30 minutes  
**Difficulty:** Easy ✅  
**Status:** Production Ready 🚀
