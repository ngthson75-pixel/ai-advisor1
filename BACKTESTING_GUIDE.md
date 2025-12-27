# 🔬 BACKTESTING SYSTEM - COMPLETE GUIDE

## 🎯 OVERVIEW

**Purpose:** Validate strategies BEFORE deploying to users

**Components:**
1. **backtest_system.py** - Core backtesting engine
2. **optimize_params.py** - Parameter optimization
3. **generate_report.py** - Excel report generator

**Goal:** Ensure win rate > 55%, profit factor > 1.5, max drawdown < 15%

---

## 📊 BACKTESTING PROCESS

### **Phase 1: Data Collection (Week 1)**

**Collect 6-12 months historical data:**

```python
# Automatic in backtest_system.py
from vnstock import Vnstock

stock = Vnstock().stock(symbol='VNM', source='VCI')
df = stock.quote.history(
    symbol='VNM',
    start='2024-06-01',
    end='2024-12-31'
)
```

**Data requirements:**
- Minimum: 6 months
- Recommended: 12 months
- Stocks: VN30 (top 6 for MVP)
- Timeframe: 1D (EOD data)

---

### **Phase 2: Strategy Backtest (Week 1)**

**Run basic backtest:**

```bash
cd C:\ai-advisor1\scripts

# Backtest both strategies
python backtest_system.py > backtest_results.json
```

**What it does:**
1. Fetches historical data (6 months)
2. Replays each strategy day by day
3. Simulates trades with realistic costs:
   - Entry slippage: 0.1%
   - Exit slippage: 0.1%
   - Commission: 0.15% per trade
4. Tracks P&L, equity curve
5. Calculates performance metrics

**Output:**
```json
{
  "results": {
    "breakout": {
      "metrics": {
        "total_trades": 45,
        "win_rate": 58.6,
        "total_return": 12.4,
        "profit_factor": 1.82,
        "max_drawdown": -8.5
      }
    },
    "divergence": {
      "metrics": {
        "total_trades": 38,
        "win_rate": 65.2,
        "total_return": 15.3,
        "profit_factor": 2.14,
        "max_drawdown": -6.2
      }
    }
  }
}
```

---

### **Phase 3: Parameter Optimization (Week 2)**

**Find optimal parameters:**

```bash
python optimize_params.py > optimization_results.json
```

**What it tests:**
- Volume multiplier: 2.5x, 3.0x, 3.5x, 4.0x
- RSI threshold: 65, 70, 75, 80
- Total combinations: 4 × 4 = 16

**Scoring formula:**
```
Score = (Win Rate × 0.67) + (Profit Factor/3 × 30) + 
        (Total Return/2) - (Max Drawdown/2)

Max score: 100
Good score: > 70
Excellent: > 80
```

**Output:**
```json
{
  "breakout": {
    "best_params": {
      "volume_multiplier": 3.0,
      "rsi_threshold": 70
    },
    "best_score": 75.8,
    "best_metrics": {
      "win_rate": 58.6,
      "profit_factor": 1.82,
      "total_return": 12.4
    }
  },
  "divergence": {
    "best_params": {
      "volume_multiplier": 3.5,
      "rsi_threshold": 65
    },
    "best_score": 82.4,
    "best_metrics": {
      "win_rate": 65.2,
      "profit_factor": 2.14,
      "total_return": 15.3
    }
  }
}
```

---

### **Phase 4: Report Generation (Week 2)**

**Generate Excel report:**

```bash
python generate_report.py backtest_results.json
```

**Creates:** `backtest_results_report.xlsx`

**Sheets:**
1. **Comparison** - Side-by-side metrics
2. **BREAKOUT Summary** - Key metrics + pass/fail
3. **BREAKOUT Trades** - Full trade log
4. **BREAKOUT Equity** - Equity curve chart
5. **DIVERGENCE Summary** - Key metrics
6. **DIVERGENCE Trades** - Trade log
7. **DIVERGENCE Equity** - Equity curve

**Excel features:**
- Color-coded pass/fail (green/red)
- Profit/loss highlighting
- Professional formatting
- Charts and visualizations

---

## 🎯 QUALITY GATES

### **Gate 1: Minimum Requirements**

**Both strategies MUST pass:**

| Metric | Minimum | Target |
|--------|---------|--------|
| Win Rate | > 50% | > 55% |
| Profit Factor | > 1.3 | > 1.5 |
| Total Return (6mo) | > 5% | > 10% |
| Max Drawdown | < 20% | < 15% |
| Total Trades | > 20 | > 30 |

**Decision:**
- ✅ ALL pass → Proceed to Gate 2
- ❌ ANY fail → Optimize parameters or improve strategy

---

### **Gate 2: Strategy Comparison**

**Compare both strategies:**

```
           | Breakout | Divergence | Winner
-----------+----------+------------+----------
Win Rate   |  58.6%   |   65.2%    | Divergence ✓
Return     |  12.4%   |   15.3%    | Divergence ✓
Profit Fac |  1.82    |   2.14     | Divergence ✓
Drawdown   |  -8.5%   |   -6.2%    | Divergence ✓
-----------+----------+------------+----------
Overall    |   Good   |  Excellent | DIVERGENCE
```

**Decision:**
- ✅ Both pass Gate 1 → Deploy both
- ✅ One stronger → Emphasize stronger strategy
- ❌ Neither reliable → Back to drawing board

---

### **Gate 3: Out-of-Sample Test (Week 3)**

**Forward test with most recent 1 month:**

```bash
# Test on data NOT used in backtest
python backtest_system.py \
  --start-date 2024-11-01 \
  --end-date 2024-12-01
```

**Purpose:** Verify no overfitting

**Decision:**
- ✅ Similar results to backtest → Strategy robust!
- ⚠️ Worse results → Overfitting detected, re-optimize
- ❌ Significantly worse → Strategy not valid

---

## 💻 DETAILED USAGE

### **1. Basic Backtest**

```bash
cd C:\ai-advisor1\scripts

# Install dependencies first
pip install openpyxl scipy --break-system-packages

# Run backtest
python backtest_system.py
```

**Customization:**

```python
# Edit backtest_system.py

STOCK_CODES = [
    'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC',
    'GAS', 'MSN', 'VHM'  # Add more
]

# Change period
START_DATE = '2024-01-01'  # 12 months
END_DATE = '2024-12-31'

# Change capital
INITIAL_CAPITAL = 200_000_000  # 200M
```

---

### **2. Parameter Optimization**

```bash
python optimize_params.py
```

**Takes:** ~10-20 minutes (16 combinations × 2 strategies)

**Custom parameter grid:**

```python
# Edit optimize_params.py

def define_parameter_grid(self):
    # Add more values
    volume_multipliers = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    rsi_thresholds = [60, 65, 70, 75, 80, 85]
    
    # Now: 6 × 6 = 36 combinations
```

---

### **3. Report Generation**

```bash
python generate_report.py backtest_results.json
```

**Opens in Excel, shows:**
- Summary metrics with color coding
- Complete trade history
- Equity curves with charts
- Strategy comparison table

---

## 📈 INTERPRETING RESULTS

### **Win Rate**

```
< 50%  → Strategy losing money, reject
50-55% → Barely profitable, need improvement
55-60% → Good, acceptable for deployment
60-65% → Very good
> 65%  → Excellent (but check for overfitting)
```

**Note:** Professional traders aim for 50-60%

---

### **Profit Factor**

```
Formula: Gross Profit / Gross Loss

< 1.0  → Losing strategy
1.0-1.3 → Break-even to slightly profitable
1.3-1.5 → Acceptable
1.5-2.0 → Good
> 2.0  → Excellent
```

**Example:**
```
Gross profit: 15M
Gross loss: 7M
Profit factor: 15M / 7M = 2.14 ✓
```

---

### **Max Drawdown**

```
Definition: Largest peak-to-trough decline

< 10%  → Excellent, low risk
10-15% → Good, moderate risk
15-20% → Acceptable, higher risk
> 20%  → Too risky for retail investors
```

**Example:**
```
Peak equity: 110M
Trough equity: 102M
Drawdown: (102-110)/110 = -7.3%
```

---

### **Expectancy**

```
Formula: (Win Rate × Avg Win) + ((1-Win Rate) × Avg Loss)

> 0    → Profitable in long run
> 2%   → Good
> 5%   → Excellent
```

**Example:**
```
Win rate: 58.6%
Avg win: +4.2%
Avg loss: -2.1%

Expectancy = (0.586 × 4.2) + (0.414 × -2.1)
           = 2.46 + (-0.87)
           = 1.59% per trade ✓
```

---

## 🚨 RED FLAGS

### **Overfitting Warning Signs:**

1. **Perfect results (win rate > 80%)**
   - Too good to be true
   - Likely curve-fitted to past data
   - Will fail in live trading

2. **Very few trades (< 20)**
   - Not enough statistical significance
   - Need more data or relax criteria

3. **Recent performance much worse**
   - Strategy degrading
   - Market conditions changed
   - May not work going forward

4. **High correlation with one stock**
   - All profits from 1-2 stocks
   - Not diversified
   - Risky

---

## ✅ DEPLOYMENT CHECKLIST

### **Before deploying to users:**

- [ ] Backtest completed (6+ months)
- [ ] Win rate > 55%
- [ ] Profit factor > 1.5
- [ ] Max drawdown < 15%
- [ ] Parameters optimized
- [ ] Out-of-sample test passed
- [ ] Excel report generated
- [ ] Results reviewed and understood
- [ ] Risk management rules defined
- [ ] Paper trading plan ready

**Only deploy if ALL boxes checked!**

---

## 📊 EXAMPLE WORKFLOW

### **Week 1: Initial Backtest**

```bash
# Monday: Setup
cd C:\ai-advisor1\scripts
pip install openpyxl scipy --break-system-packages

# Tuesday: Run backtest
python backtest_system.py > results_v1.json

# Wednesday: Review
python generate_report.py results_v1.json
# Open results_v1_report.xlsx
# Check if passing Gate 1
```

**Results:**
```
Breakout:  Win rate 58.6%, Profit factor 1.82 ✅
Divergence: Win rate 65.2%, Profit factor 2.14 ✅

Decision: PASS Gate 1, proceed to optimization
```

---

### **Week 2: Optimization**

```bash
# Monday-Tuesday: Optimize
python optimize_params.py > optimization_v1.json

# Results show best params:
# Breakout: vol=3.0x, rsi=70 (current params OK)
# Divergence: vol=3.5x, rsi=65 (improvement found!)

# Wednesday: Re-backtest with new params
# Edit backtest_system.py with optimized params
python backtest_system.py > results_v2.json

# Thursday: Generate final report
python generate_report.py results_v2.json
```

**Optimized results:**
```
Divergence improved:
- Win rate: 65.2% → 67.8%
- Profit factor: 2.14 → 2.31
- Return: 15.3% → 17.1%

Decision: PASS Gate 2, proceed to out-of-sample
```

---

### **Week 3: Out-of-Sample Test**

```bash
# Monday: Test on most recent month
# Edit dates in backtest_system.py
START_DATE = '2024-11-01'
END_DATE = '2024-12-01'

python backtest_system.py > results_oos.json
```

**Out-of-sample results:**
```
Divergence:
- Win rate: 67.8% (backtest) vs 64.3% (OOS) ✅
- Profit factor: 2.31 vs 2.18 ✅
- Slight degradation but still strong

Decision: PASS Gate 3, READY TO DEPLOY! 🚀
```

---

### **Week 4: Deployment**

```bash
# Update frontend with validated strategies
# Use optimized parameters
# Enable real-time scanning
# Start paper trading
```

---

## 🎯 SUCCESS CRITERIA

### **MVP Target (6-month backtest):**

| Metric | Breakout | Divergence |
|--------|----------|------------|
| Win Rate | > 55% | > 60% |
| Profit Factor | > 1.5 | > 1.8 |
| Total Return | > 10% | > 12% |
| Max Drawdown | < 12% | < 10% |
| Total Trades | > 30 | > 25 |

**If achieved → DEPLOY with confidence! ✅**

---

## 💡 OPTIMIZATION TIPS

### **1. If win rate too low (<50%):**

- Increase volume multiplier (more selective)
- Tighten RSI threshold
- Add confirmation filters
- Extend hold time

### **2. If profit factor too low (<1.3):**

- Widen stop loss (less premature exits)
- Tighten take profit (lock profits earlier)
- Improve entry timing
- Add trend filter

### **3. If max drawdown too high (>20%):**

- Reduce position size
- Add volatility filter
- Skip choppy markets
- Diversify across more stocks

### **4. If too few trades (<20):**

- Decrease volume multiplier
- Relax RSI threshold
- Add more stocks
- Extend backtest period

---

## 🎊 FINAL NOTES

**Backtesting is CRITICAL:**
- Separates winners from losers
- Builds investor confidence
- Protects users from bad strategies
- Validates your work

**Don't skip it!**

**Timeline:**
- Week 1: Backtest (3 days)
- Week 2: Optimize (4 days)
- Week 3: Validate (3 days)
- Week 4: Deploy (if passing)

**Total: 2-3 weeks before public launch**

**Worth every minute! 🎯**

---

**Remember:** Past performance ≠ Future results, but it's the best predictor we have!
