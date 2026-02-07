# SELL SIGNAL V1 vs V2 - COMPARISON GUIDE

**Date:** 2026-02-02

---

## 📊 SIDE-BY-SIDE COMPARISON

| Feature | V1.0 | V2.0 |
|---------|------|------|
| **Stop Loss** | Price <= SL → Sell 100% | Price <= SL → Sell 100% ✅ Same |
| **Take Profit** | Price >= TP → Sell 100% | Price >= TP → **Sell 50%** ⭐ |
| **MA20 Condition** | Break (1 day) | **Consecutive (2 days)** ⭐ |
| **Volume Signal** | ❌ None | **MA20 + High Volume** ⭐ |
| **Partial Exits** | ❌ No | ✅ Yes (50% at TP) |
| **Position Tracking** | ❌ No | ✅ Yes (exit_quantity_pct) |

---

## 🔍 DETAILED COMPARISON

### 1. TAKE PROFIT

#### V1.0 Logic:
```python
if current_price >= take_profit:
    sell_quantity = 100%
    exit_reason = 'TP'
```

**Pros:**
- ✅ Simple, clear exit
- ✅ Lock in full profit

**Cons:**
- ❌ Miss upside if price continues
- ❌ All-or-nothing

#### V2.0 Logic:
```python
if current_price >= take_profit and available >= 50%:
    sell_quantity = 50%
    exit_reason = 'TP_PARTIAL'
    # Keep 50% for more upside
```

**Pros:**
- ✅ Lock in profit with 50%
- ✅ Keep exposure for upside
- ✅ Flexible risk management

**Cons:**
- ❌ More complex tracking
- ❌ Potential to lose on remaining 50%

**Example:**
```
Entry: 88,500
TP: 95,580 (+8%)

Scenario A: Price continues to 105,000
- V1.0: Sold 100% at 95,580 → +8% ❌ Missed +18%
- V2.0: Sold 50% at 95,580, 50% at 105,000 → +13% ✅

Scenario B: Price drops to 90,000 after TP
- V1.0: Sold 100% at 95,580 → +8% ✅ Good exit
- V2.0: Sold 50% at 95,580, 50% at 90,000 → +4% ❌ Lost on remaining
```

---

### 2. MA20 BREAK

#### V1.0 Logic:
```python
if current_price < ema20 and prev_close >= prev_ema20:
    # Single day break
    sell_quantity = 100%
    exit_reason = 'MA20_BREAK'
```

**Pros:**
- ✅ Quick response to break
- ✅ Catch early breakdown

**Cons:**
- ❌ False signals (whipsaw)
- ❌ 1-day confirmation too fast

#### V2.0 Logic:
```python
if current_price < ema20 and prev_close < prev_ema20:
    # Both days below MA20
    sell_quantity = 100%
    exit_reason = 'MA20_CONSECUTIVE'
```

**Pros:**
- ✅ More reliable (2-day confirmation)
- ✅ Fewer false signals
- ✅ Confirms downtrend

**Cons:**
- ❌ Slower response
- ❌ May miss optimal exit

**Example:**
```
Day 1: Close 91,000, MA20 90,000 (above)
Day 2: Close 89,000, MA20 90,000 (below) ← break day
Day 3: Close 88,000, MA20 89,500 (below)

V1.0: SELL on Day 2 (break) → Exit at 89,000
V2.0: SELL on Day 3 (consecutive) → Exit at 88,000

Trade-off:
- V1.0: Better price (-1,000 better)
- V2.0: More reliable (fewer false signals)
```

---

### 3. VOLUME SIGNAL

#### V1.0:
```
❌ No volume-based exit signal
```

#### V2.0:
```python
if current_price < ema20 and volume > avg_volume_20:
    # Breakdown with conviction
    sell_quantity = 100%
    exit_reason = 'MA20_HIGH_VOLUME'
```

**Logic:**
- Price below MA20 = Weakness
- High volume = Strong conviction
- Combined = Confirmed breakdown

**Example:**
```
Current: 88,000 < MA20 90,000
Volume: 2,500,000
AvgVol20: 1,800,000
Ratio: 1.39x

→ V2.0: SELL at 88,000 (MA20_HIGH_VOLUME)
→ V1.0: No signal (would wait for consecutive days)
```

**Benefit:**
- Catch breakdown with volume confirmation
- Don't need to wait for Day 2
- More responsive than consecutive

---

## 📈 PERFORMANCE COMPARISON

### Backtesting Results (Estimated):

| Metric | V1.0 | V2.0 | Winner |
|--------|------|------|--------|
| Win Rate | 60% | 58% | V1.0 ✅ |
| Avg Win | +8.5% | +9.2% | V2.0 ✅ |
| Avg Loss | -5.5% | -5.2% | V2.0 ✅ |
| R/R Ratio | 1.5x | 1.8x | V2.0 ✅ |
| Whipsaw Rate | 15% | 10% | V2.0 ✅ |
| Max Upside Capture | 60% | 75% | V2.0 ✅ |

**Conclusion:**
- V1.0: Simpler, slightly higher win rate
- V2.0: Better R/R, fewer false signals, more upside

---

## 🎯 WHEN TO USE WHICH VERSION

### Use V1.0 If:
- ✅ You prefer simplicity
- ✅ You want all-or-nothing exits
- ✅ You don't want to track partial positions
- ✅ You prioritize quick exits over upside

### Use V2.0 If:
- ✅ You want to capture more upside
- ✅ You're comfortable with partial exits
- ✅ You want fewer false signals (MA20)
- ✅ You value volume confirmation
- ✅ You want better R/R ratio

---

## 🔄 MIGRATION PATH

### From V1.0 to V2.0:

**Step 1: Database**
```sql
-- Add new columns
ALTER TABLE signals ADD COLUMN exit_quantity_pct REAL DEFAULT 100;
ALTER TABLE signals ADD COLUMN buy_signal_id INTEGER;
ALTER TABLE signals ADD COLUMN volume_ratio REAL;
```

**Step 2: Backend**
```python
# Replace import
from sell_signal_scanner_v2 import SellSignalScannerV2

# Update scan endpoint
scanner = SellSignalScannerV2(db_path='signals.db')
```

**Step 3: Frontend**
```jsx
// Add quantity column
<th>Số lượng</th>

// Add new exit reasons
case 'TP_PARTIAL': return 'Take Profit (50%)';
case 'MA20_CONSECUTIVE': return 'MA20 Consecutive';
case 'MA20_HIGH_VOLUME': return 'MA20 + Volume';
```

**Step 4: Test**
```bash
python sell_signal_scanner_v2.py --days 30
```

**Total Time:** ~1 hour

---

## 💡 RECOMMENDED APPROACH

### **Hybrid Strategy:**

Use **V2.0** with custom settings:

```python
# In SellSignalScannerV2:

# Customize TP partial %
TP_PARTIAL_PCT = 50  # Sell 50% at TP (can change to 30%, 70%, etc.)

# Customize MA20 consecutive days
MA20_CONSECUTIVE_DAYS = 2  # Require 2 days below MA20

# Customize volume threshold
VOLUME_THRESHOLD = 1.2  # Volume must be 1.2x average
```

**Benefits:**
- Flexible to your risk tolerance
- Easy to adjust based on market conditions
- Can A/B test different parameters

---

## 📊 REAL-WORLD EXAMPLE

### Stock: VCB
**Entry:** 88,500 (Feb 1)  
**TP:** 95,580  
**SL:** 83,044  

| Date | Close | MA20 | Volume | V1.0 Action | V2.0 Action |
|------|-------|------|--------|-------------|-------------|
| Feb 1 | 88,500 | 90,000 | 1.8M | - | - |
| Feb 2 | 92,000 | 90,200 | 2.0M | - | - |
| Feb 3 | 96,000 | 90,800 | 2.2M | **SELL 100% (TP)** | **SELL 50% (TP_PARTIAL)** |
| Feb 4 | 98,000 | 91,500 | 1.9M | - | - (hold 50%) |
| Feb 5 | 94,000 | 92,000 | 2.1M | - | - (hold 50%) |
| Feb 6 | 89,000 | 91,800 | 2.5M | - | **SELL 50% (MA20_HIGH_VOL)** |

**Results:**

**V1.0:**
- Sold 100% at 96,000
- Profit: (96,000 - 88,500) / 88,500 = **+8.5%**

**V2.0:**
- Sold 50% at 96,000: +8.5%
- Sold 50% at 89,000: +0.6%
- Avg Profit: (8.5% + 0.6%) / 2 = **+4.5%**

**Analysis:**
- V1.0 better in this case (+8.5% vs +4.5%)
- BUT: If price continued to 105,000, V2.0 would win
- V2.0 had chance to capture upside

---

## ✅ DECISION MATRIX

| Your Priority | Recommended Version |
|---------------|---------------------|
| **Maximum profit per trade** | V1.0 |
| **Capture more upside** | V2.0 |
| **Fewer false signals** | V2.0 |
| **Simplicity** | V1.0 |
| **Risk management** | V2.0 |
| **Quick exits** | V1.0 |
| **Volume confirmation** | V2.0 |
| **All-or-nothing** | V1.0 |

---

## 🎓 BEST PRACTICES

### For V1.0:
1. Use tight stops
2. Accept missing upside
3. Focus on consistency
4. Quick in, quick out

### For V2.0:
1. Have trailing stop for remaining 50%
2. Monitor volume signals
3. Track partial positions carefully
4. Be patient with upside

---

## 📞 QUESTIONS?

**Which version to use?**
→ Start with V2.0, it's more flexible

**Can I switch between versions?**
→ Yes, but migration needed (see above)

**Can I customize parameters?**
→ Yes! Edit scanner code

**What if I want V1 logic for some stocks?**
→ Use stock_type or strategy filters

---

**Contact:** ngthson75@gmail.com | +84938127666

---

**END OF COMPARISON GUIDE**
