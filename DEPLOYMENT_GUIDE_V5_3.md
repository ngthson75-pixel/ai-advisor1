# SELL SCANNER v5.3 - DEPLOYMENT GUIDE

**Date:** 21/3/2026  
**Version:** 5.3  
**Status:** Ready to Deploy  

---

## 🎯 SUMMARY OF CHANGES

### **REPLACED:**
```
❌ MA20_STRICT (disabled in v5.2)
```

### **NEW EXIT CRITERIA:**
```
✅ 1. Daily MACD + RSI>80 + Support break → BÁN 100% (CRITICAL)
✅ 2. 4H MACD + Volume divergence → BÁN 50% (HIGH)
✅ 3. 1H Volume Climax (BSR pattern) → BÁN 100% (HIGH)
```

### **TIMING CHANGE:**
```
Before: Scanner runs 9:05, 10:05, ..., 15:05
After: Scanner runs 9:30, 10:30, ..., 15:30 ⭐
```

---

## 📋 FILES PROVIDED

### **1. sell_signal_scanner_v5_3.py** ⭐ MAIN FILE
- Complete scanner with 3 new exit criteria
- Replaces `sell_signal_scanner_v5_2.py`
- Ready to deploy

### **2. hourly-sell-scanner-v5-3.yml** ⭐ GITHUB ACTIONS
- Workflow file for automated hourly scans
- Runs 9:30-15:30 VN time (Mon-Fri)
- Place in `.github/workflows/`

### **3. DEPLOYMENT_GUIDE.md** 📖 THIS FILE
- Deployment instructions
- Testing checklist
- Troubleshooting

---

## 🚀 DEPLOYMENT STEPS

### **STEP 1: Backup Current Files**

```bash
cd C:\ai-advisor1

# Backup current scanner
Copy-Item sell_signal_scanner_v5_2.py sell_signal_scanner_v5_2_backup.py

# Backup current workflow (if exists)
Copy-Item .github\workflows\hourly-sell-scanner.yml .github\workflows\hourly-sell-scanner_backup.yml
```

---

### **STEP 2: Deploy New Scanner**

```bash
# Copy v5.3 scanner
Copy-Item sell_signal_scanner_v5_3.py sell_signal_scanner_v5_2.py -Force

# ⚠️ IMPORTANT: Keep filename as v5_2.py (underscore)
# GitHub Actions workflow expects this filename
# OR update workflow to point to v5_3.py
```

**Recommended approach:**
```bash
# Option A: Rename to v5_2.py (no workflow change needed)
Copy-Item sell_signal_scanner_v5_3.py sell_signal_scanner_v5_2.py -Force

# Option B: Keep v5_3.py and update workflow
# (Update workflow file to call sell_signal_scanner_v5_3.py)
```

---

### **STEP 3: Deploy GitHub Actions Workflow**

```bash
# Navigate to workflows directory
cd .github\workflows

# Deploy new workflow
Copy-Item ..\..\hourly-sell-scanner-v5-3.yml hourly-sell-scanner.yml -Force

# Commit and push
git add hourly-sell-scanner.yml
git commit -m "feat: Update sell scanner to v5.3 with technical exit criteria

CHANGES:
- Replace MA20_STRICT with 3 technical criteria:
  1. Daily MACD + RSI>80 + Support break → 100%
  2. 4H MACD + Volume divergence → 50%
  3. 1H Volume Climax (BSR pattern) → 100%
- Change scan timing: 9:30-15:30 (from 9:05-15:05)

IMPACT:
- More accurate exit signals
- Based on proven technical analysis
- Better timing (9:30 start = more data available)"

git push origin main
```

---

### **STEP 4: Verify Deployment**

**Check GitHub Actions:**
```
1. Go to GitHub repo → Actions tab
2. Find "Hourly Sell Signal Scanner v5.3"
3. Check schedule: Should show 2:30, 3:30, ..., 8:30 UTC
4. Trigger manual run (workflow_dispatch)
5. Monitor logs
```

**Check Scanner Output:**
```bash
# Local test first
cd C:\ai-advisor1
python sell_signal_scanner_v5_2.py

# Expected output:
# 🔍 SELL SIGNAL SCANNER v5.3 - TECHNICAL EXIT CRITERIA
# ⏰ Time: 2026-03-21 ...
# 📋 Checking N open positions
# ...
# ✅ Scanner completed!
```

---

## 🧪 TESTING CHECKLIST

### **Before Production:**

- [ ] **Local test:** Run scanner manually
- [ ] **Database check:** Verify DB connection works
- [ ] **Data availability:** Check if 1H/4H data is available for test tickers
- [ ] **Indicator calculation:** Verify MACD, RSI calculate correctly
- [ ] **Signal detection:** Test with known patterns (if possible)
- [ ] **Timing check:** Verify 9:30-15:30 time window logic
- [ ] **Error handling:** Test with ticker that has no data

### **Test Tickers:**
```python
# Large caps (should have 1H/4H data):
test_tickers = ['VIC', 'VHM', 'VNM', 'HPG', 'VCB', 'GAS', 'MSN']

# Test each:
for ticker in test_tickers:
    print(f"\nTesting {ticker}...")
    df_daily = get_daily_data(ticker)
    df_4h = get_intraday_4h_data(ticker)
    df_1h = get_intraday_1h_data(ticker)
    
    print(f"  Daily bars: {len(df_daily) if df_daily is not None else 0}")
    print(f"  4H bars: {len(df_4h) if df_4h is not None else 0}")
    print(f"  1H bars: {len(df_1h) if df_1h is not None else 0}")
```

---

### **After Deployment:**

- [ ] **First run:** Monitor first automated run @ 9:30
- [ ] **Check logs:** Review GitHub Actions logs
- [ ] **Database:** Verify signals are saved correctly
- [ ] **False positives:** Check if any unexpected signals
- [ ] **Performance:** Monitor execution time (should be < 5 min)
- [ ] **Week 1:** Daily monitoring
- [ ] **Week 2-4:** Regular checks
- [ ] **Month 1:** Review signal accuracy

---

## 📊 SIGNAL PRIORITY MATRIX

**Scanner checks in this order:**

| Priority | Criterion | Action | Exit % | Notes |
|----------|-----------|--------|--------|-------|
| **1** | Stop Loss | SELL | 100% | Urgent! |
| **2** | Daily Critical (MACD+RSI+Support) | SELL | 100% | Very strong signal |
| **3** | 1H Volume Climax | SELL | 100% | BSR pattern |
| **4** | 4H Medium (MACD+Volume div) | SELL | 50% | Reduce position |
| **5** | Take Profit | SELL | 50/30% | Partial exit |

**Once a signal triggers, scanner STOPS checking lower priorities!**

---

## ⚙️ CONFIGURATION

### **Tunable Parameters:**

**Daily Critical Exit:**
```python
# In check_daily_critical_exit()
RSI_THRESHOLD = 80  # Default: 80, can adjust 75-85
SUPPORT_LOOKBACK = 50  # Days to find support
VOLUME_CONFIRMATION = 1.2  # Volume multiplier for break
```

**4H Medium Exit:**
```python
# In check_4h_medium_exit()
MACD_LOOKBACK_4H = 15  # Bars to check divergence
VOLUME_LOOKBACK_4H = 15  # Bars for volume div
```

**1H Volume Climax:**
```python
# In detect_climax_volume_1h()
LOOKBACK_HOURS = 40  # Hours for average volume
VOLUME_MULTIPLIER = 2.5  # Spike threshold (2.5x avg)
RANGE_POSITION = 0.90  # Must be in top 10%
```

**Adjust based on backtesting results!**

---

## 🐛 TROUBLESHOOTING

### **Issue 1: No 1H/4H data available**

**Symptom:**
```
⚠️ VCI: No intraday data for 4H aggregation
⚠️ VCI: Error getting 1H data
```

**Solution:**
- vnstock may not have intraday data for all stocks
- Scanner will skip 1H/4H checks for these stocks
- Only Daily criteria and SL/TP will work
- This is EXPECTED for small-cap stocks

**Action:** Focus on large/mid caps that have intraday data

---

### **Issue 2: Scanner runs outside trading hours**

**Symptom:**
```
⏰ Before market hours (08:30)
Scanner runs 9:30-15:30 VN time
```

**Solution:**
- Time check is built into scanner
- Will exit gracefully if run too early/late
- No action needed

---

### **Issue 3: False signals on first day**

**Symptom:**
- Scanner generates many signals on first run
- Signals don't match manual chart analysis

**Solution:**
- First day may have "backlog" of signals
- Let scanner run for 2-3 days to stabilize
- Manual verify first few signals
- Adjust parameters if needed (see Configuration)

---

### **Issue 4: Database connection error**

**Symptom:**
```
❌ Error: connection to server failed
```

**Solution:**
```bash
# Check environment variables
echo $DB_HOST
echo $DB_NAME
echo $DB_USER

# Test connection
python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
print('✅ Connection OK')
conn.close()
"
```

---

## 📈 MONITORING

### **Daily Checks:**

**Week 1 (Critical):**
```
✅ Check GitHub Actions runs (should be 7 runs/day)
✅ Review signals generated (manual verify 2-3)
✅ Check database (signals table)
✅ Monitor false positive rate
```

**Week 2-4 (Regular):**
```
✅ Weekly review of signals
✅ Check accuracy vs manual analysis
✅ Adjust parameters if needed
```

**Monthly:**
```
✅ Full backtest on month's data
✅ Calculate win rate
✅ Review parameter effectiveness
✅ User feedback
```

---

## 📊 EXPECTED BEHAVIOR

### **Typical Day:**

```
9:30: Scanner run #1
      → Check all open positions
      → Generate 0-2 signals (typical)
      
10:30: Scanner run #2
       → New 1H data available
       → Possible 1H climax detection
       
...

15:30: Scanner run #7 (last)
       → Full day data
       → Most comprehensive check
```

### **Signal Frequency:**

**Expected (healthy):**
```
Daily Critical: 0-1 per week (rare, strong)
4H Medium: 1-2 per week (moderate)
1H Climax: 2-4 per week (more common)
```

**Too many (adjust parameters):**
```
> 5 signals per day = Too sensitive
→ Increase thresholds (RSI 80→85, volume 2.5x→3.0x)
```

**Too few (verify data):**
```
< 1 signal per week = Too strict OR no data
→ Check if 1H/4H data available
→ Consider lowering thresholds slightly
```

---

## 🔄 ROLLBACK PLAN

**If v5.3 has issues:**

```bash
# Restore v5.2
Copy-Item sell_signal_scanner_v5_2_backup.py sell_signal_scanner_v5_2.py -Force

# Restore old workflow
Copy-Item .github\workflows\hourly-sell-scanner_backup.yml .github\workflows\hourly-sell-scanner.yml -Force

# Commit rollback
git add sell_signal_scanner_v5_2.py .github\workflows\hourly-sell-scanner.yml
git commit -m "revert: Rollback to v5.2 - issues with v5.3"
git push origin main
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

**Immediately after deploy:**
- [ ] First GitHub Actions run successful
- [ ] Scanner output looks correct
- [ ] No Python errors in logs
- [ ] Database updated correctly

**Day 1:**
- [ ] All 7 hourly runs completed
- [ ] Review any signals generated
- [ ] Manual verify signals on charts
- [ ] No performance issues

**Week 1:**
- [ ] Signal accuracy > 60% (estimated)
- [ ] No critical bugs
- [ ] User feedback collected
- [ ] Parameters tuned if needed

**Month 1:**
- [ ] Win rate calculated
- [ ] Strategy effectiveness reviewed
- [ ] Documentation updated with learnings

---

## 📞 SUPPORT

**Issues? Questions?**

1. Check logs: GitHub Actions → Workflow runs → Latest run
2. Test locally: `python sell_signal_scanner_v5_2.py`
3. Review this guide: Troubleshooting section
4. Check vnstock API status
5. Contact Claude for assistance

---

## 🎯 SUCCESS CRITERIA

**v5.3 is successful if:**

✅ Scanner runs reliably every hour (9:30-15:30)  
✅ Generates actionable signals (not too many, not too few)  
✅ Signal accuracy > 60% (over 1 month)  
✅ No critical bugs/crashes  
✅ User confidence in signals  

---

**READY TO DEPLOY!** 🚀

(Review this guide completely before deploying to production!)
