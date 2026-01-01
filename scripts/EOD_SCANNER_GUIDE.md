# 🔧 EOD SIGNAL SCANNER - INSTALLATION & SETUP GUIDE

## 🎯 PROBLEM SOLVED

**Before:** Scanner không tạo được signals vì không lấy được realtime data

**After:** Scanner tự động dùng EOD (End of Day) data của ngày giao dịch gần nhất

---

## 📥 INSTALLATION

### STEP 1: Upload Files to Server

```bash
# Connect to your server
cd C:\ai-advisor1\scripts

# Copy these files:
# 1. daily_signal_scanner_eod.py (main scanner)
# 2. stock_list_343.py (343 stocks list)
# 3. test_scanner.py (test script)
```

### STEP 2: Install Dependencies

```bash
pip install pandas numpy vnstock3 --break-system-packages
```

### STEP 3: Test Scanner

```bash
# Test on 10 stocks first
python test_scanner.py

# Expected output:
# Testing VCB
# ✓ Got 100 days of data
# ✓ PULLBACK signal found!
#   Entry: 88,500
#   Target: 95,580
#   ...
# TEST PASSED - Generated X signals
```

### STEP 4: Run Full Scanner

```bash
# Scan all 343 stocks (takes ~5 minutes)
python daily_signal_scanner_eod.py

# Expected output:
# Starting signal scan...
# Mode: EOD
# Date: 2025-01-01
# Processing VCB (1/343)...
# ✓ Got EOD data for VCB: 100 rows
# ✓ PULLBACK signal for VCB: 75% strength
# ...
# SCAN COMPLETE
# Signals found: 15
# ✓ Saved 15 signals to database
```

### STEP 5: Update Backend API (if needed)

Your backend_api.py already has `/api/scan` endpoint.
Just make sure it runs the new scanner:

```python
# In backend_api.py
scanner_path = 'scripts/daily_signal_scanner_eod.py'
```

---

## 🔧 HOW IT WORKS

### Data Source Strategy:

```
1. Try Realtime Data (if use_eod=False)
   ↓ Failed
2. Fallback to EOD Data ✓
   ↓ Success
3. Use latest trading day data
   (Skip weekends automatically)
```

### Latest Trading Day Logic:

```python
Today = Thursday → Use Thursday data
Today = Friday → Use Friday data  
Today = Saturday → Use Friday data (skip Saturday)
Today = Sunday → Use Friday data (skip Sunday)
Today = Monday → Use Monday data
```

### Signal Generation:

```
For each stock:
  ↓
Get 100 days EOD data
  ↓
Calculate EMA(20), EMA(50), RSI
  ↓
Check PULLBACK conditions
  ↓
Check EMA_CROSS conditions
  ↓
If signal found → Save to database
```

---

## 📊 STRATEGIES

### PULLBACK Strategy (BUY):

**Conditions:**
- ✓ Price near EMA(20) (within 2%)
- ✓ Uptrend confirmed (EMA20 > EMA50)
- ✓ RSI < 50 (not overbought)
- ✓ Volume > 20-day average (optional boost)

**Strength Score:**
- Base: 60%
- +10% if high volume
- +10% if RSI < 40 (strong pullback)
- +10% if strong uptrend (EMA20 > EMA50 * 1.02)
- **Max: 90%**

**Priority:** Strength >= 75%

### EMA_CROSS Strategy (BUY):

**Conditions:**
- ✓ EMA(20) crosses above EMA(50) OR
- ✓ EMA(20) very close to EMA(50) (within 1%)
- ✓ RSI between 40-60 (momentum building)
- ✓ Volume increasing (optional boost)

**Strength Score:**
- Base: 65%
- +15% if golden cross just happened
- +10% if high volume
- +10% if RSI in ideal range
- **Max: 100%**

**Priority:** Strength >= 80%

---

## 🎯 EXPECTED RESULTS

### Typical Output:

**Good Market Conditions:**
```
343 stocks scanned
→ 15-25 signals generated
→ 3-5 priority signals
→ 60-80% PULLBACK
→ 20-40% EMA_CROSS
```

**Neutral Market:**
```
343 stocks scanned
→ 5-10 signals generated
→ 1-2 priority signals
→ Mostly PULLBACK signals
```

**Bad Market (downtrend):**
```
343 stocks scanned
→ 0-3 signals generated
→ 0 priority signals
→ Wait for better conditions
```

---

## ⚙️ CONFIGURATION

### Adjust Stock List:

Edit `stock_list_343.py`:

```python
TOP_343_STOCKS = [
    'VCB', 'VHM', 'VIC',  # Your stocks here
    # Add or remove as needed
]
```

### Adjust Strategy Parameters:

In `daily_signal_scanner_eod.py`:

**Make PULLBACK more sensitive:**
```python
# Line ~180
near_ema20 = abs(close - ema20) / ema20 < 0.03  # Was 0.02 (2%)
rsi_ok = rsi < 60  # Was 50
```

**Make EMA_CROSS more sensitive:**
```python
# Line ~260
rsi_ok = 30 <= rsi <= 70  # Was 40-60
```

**Adjust Strength Thresholds:**
```python
# Line ~200 (PULLBACK)
is_priority = strength >= 70  # Was 75

# Line ~280 (EMA_CROSS)
is_priority = strength >= 75  # Was 80
```

---

## 🐛 TROUBLESHOOTING

### Issue 1: No signals generated

**Possible causes:**
- Market conditions don't meet criteria
- Strategy filters too strict
- Data quality issues

**Solutions:**
```bash
# Test on known good stocks
python test_scanner.py

# Check if data is available
python -c "from daily_signal_scanner_eod import get_stock_data; print(get_stock_data('VCB', use_eod=True))"

# Relax strategy parameters (see Configuration above)
```

### Issue 2: "No module named vnstock3"

**Solution:**
```bash
pip install vnstock3 --break-system-packages --upgrade
```

### Issue 3: Scanner very slow

**Causes:**
- API rate limiting
- Network latency
- Processing 343 stocks

**Solutions:**
```bash
# Reduce stock count for testing
# Edit daily_signal_scanner_eod.py:
# TOP_STOCKS = TOP_STOCKS[:50]  # Test with 50 stocks

# Increase rate limit delay
# Line ~380:
time.sleep(1.0)  # Was 0.5
```

### Issue 4: Database errors

**Solution:**
```bash
# Check database exists
ls signals.db

# Recreate database
python -c "import sqlite3; conn = sqlite3.connect('signals.db'); conn.execute('CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY, ticker TEXT, strategy TEXT, entry_price REAL, stop_loss REAL, take_profit REAL, risk_reward REAL, strength REAL, is_priority INTEGER, stock_type TEXT, rsi REAL, date TEXT, action TEXT)'); conn.close()"
```

### Issue 5: "KeyError: 'Close'"

**Cause:** Data format mismatch

**Solution:**
```python
# Check vnstock version
pip show vnstock3

# Update to latest
pip install vnstock3 --upgrade --break-system-packages
```

---

## 📊 MONITORING & LOGS

### Enable Detailed Logging:

```python
# In daily_signal_scanner_eod.py, line ~10:
logging.basicConfig(
    level=logging.DEBUG,  # Was INFO
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Check Scanner Output:

```bash
# Run and save logs
python daily_signal_scanner_eod.py > scanner_log.txt 2>&1

# View logs
cat scanner_log.txt

# Count signals
grep "signal for" scanner_log.txt | wc -l
```

### Check Database:

```bash
# Install sqlite3 (if not installed)
# Then:
sqlite3 signals.db

# Run queries:
sqlite> SELECT COUNT(*) FROM signals;
sqlite> SELECT ticker, strategy, strength FROM signals ORDER BY strength DESC LIMIT 10;
sqlite> .exit
```

---

## 🚀 DEPLOYMENT

### Local Testing:

```bash
# 1. Test scanner
python test_scanner.py

# 2. Run full scan
python daily_signal_scanner_eod.py

# 3. Check database
sqlite3 signals.db "SELECT COUNT(*) FROM signals;"

# 4. Start backend
python backend_api.py

# 5. Test API
curl http://localhost:10000/api/signals

# 6. Test scan endpoint
curl -X POST http://localhost:10000/api/scan
```

### Production Deployment (Render):

```bash
# 1. Upload files to Git
cd C:\ai-advisor1
git add scripts/daily_signal_scanner_eod.py
git add scripts/stock_list_343.py
git add scripts/test_scanner.py
git commit -m "Add EOD signal scanner with fallback"
git push origin main

# 2. Render will auto-deploy

# 3. Test production
curl https://ai-advisor1-backend.onrender.com/api/signals
curl -X POST https://ai-advisor1-backend.onrender.com/api/scan

# 4. Monitor Render logs
# Visit: https://dashboard.render.com → Your service → Logs
```

---

## 📈 PERFORMANCE OPTIMIZATION

### Speed Up Scanning:

**1. Reduce stock count:**
```python
# Test with top 50 stocks
TOP_STOCKS = TOP_343_STOCKS[:50]
```

**2. Parallel processing:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(process_stock, TOP_STOCKS)
```

**3. Cache data:**
```python
import pickle
from datetime import datetime

cache_file = f"data_cache_{datetime.now().date()}.pkl"
if os.path.exists(cache_file):
    with open(cache_file, 'rb') as f:
        data = pickle.load(f)
```

### Improve Signal Quality:

**1. Add more filters:**
```python
# Require minimum price
if close < 10000:  # Skip penny stocks under 10k
    return signals

# Require minimum liquidity
avg_volume = df['Volume'].tail(20).mean()
if avg_volume < 100000:  # Skip low volume stocks
    return signals
```

**2. Add confirmation:**
```python
# Require 2 consecutive days confirmation
prev_close = df['Close'].iloc[-2]
if close < prev_close:  # Skip if today lower than yesterday
    return signals
```

---

## ✅ SUCCESS CHECKLIST

Verify everything works:

- [ ] Scanner runs without errors
- [ ] Generates at least 1 signal on test stocks
- [ ] Database saves signals correctly
- [ ] Backend API returns signals
- [ ] Frontend displays signals
- [ ] "Tạo tín hiệu mới" button works
- [ ] Signals show in table format
- [ ] Filters work correctly
- [ ] Mobile responsive
- [ ] No console errors

---

## 🔄 MAINTENANCE

### Daily Tasks:

**Automatic (via Render cron or manual trigger):**
- Run scanner once per day (after market close)
- Generate fresh signals
- Update database

**Manual (as needed):**
- Review signal quality
- Adjust strategy parameters
- Update stock list
- Monitor error logs

### Weekly Tasks:

- Check signal success rate
- Analyze which strategies work best
- Update TOP_343_STOCKS list
- Review and optimize code

### Monthly Tasks:

- Full backtest of strategies
- Update documentation
- Review user feedback
- Optimize performance

---

## 📞 SUPPORT

### If scanner still doesn't work:

1. **Check vnstock3 version:**
```bash
pip show vnstock3
# Should be >= 0.2.0
```

2. **Test data source:**
```python
import vnstock3 as vs
stock = vs.stock('VCB', source='VCI')
df = stock.quote.history(start='2024-01-01', end='2025-01-01', interval='1D')
print(df.head())
```

3. **Try alternative data source:**
```python
# In daily_signal_scanner_eod.py
# Change source from 'VCI' to 'TCBS' or 'SSI'
stock = vs.stock(symbol=ticker, source='TCBS')
```

4. **Contact vnstock support:**
- GitHub: https://github.com/thinh-vu/vnstock
- Issues: Report data fetching problems

---

## 🎯 FINAL NOTES

**Key Points:**
- ✓ Scanner now uses EOD data (reliable!)
- ✓ Automatically skips weekends
- ✓ Always uses latest trading day
- ✓ Generates signals even offline
- ✓ Production-ready code
- ✓ Full error handling
- ✓ Comprehensive logging

**Benefits:**
- ✓ No more "no signals" error
- ✓ Works without realtime API
- ✓ Stable and predictable
- ✓ Easy to debug
- ✓ Ready for automation

**Limitations:**
- ✗ Not realtime (EOD only)
- ✗ Signals delayed by 1 day
- ✗ Weekend data not fresh
- ✗ May miss intraday moves

**But this is acceptable because:**
- ✓ Swing trading doesn't need realtime
- ✓ EOD data is sufficient for signals
- ✓ More reliable than realtime
- ✓ Easier to maintain

---

**READY TO DEPLOY! 🚀**

**TEST → DEPLOY → MONITOR → OPTIMIZE!**
