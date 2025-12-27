# 📊 CHIẾN LƯỢC 3: TREND FOLLOWING + PULLBACK ENTRY

## 🎯 TRIẾT LÝ CHIẾN LƯỢC

### **Core Concept:**
"Trend là bạn. Nhưng đừng mua ở đỉnh. Đợi pullback rồi entry!"

**Không phải:** Chase giá khi đang tăng mạnh
**Mà là:** Xác nhận trend → Chờ pullback → Entry khi retest support → Ride the trend

**Famous Quote:**
> "The trend is your friend, but timing is everything."
> — Trading Wisdom

---

## 📋 QUY TẮC ENTRY (4 ĐIỀU KIỆN)

### **Điều kiện 1: XÁC NHẬN UPTREND**

**Sử dụng EMA (Exponential Moving Average):**

```python
EMA20 > EMA50  # Short-term above long-term
Price > EMA20  # Price above short-term MA
EMA20 slope positive  # EMA trending up
```

**Ví dụ:**
```
EMA20: 23,000 (trending up)
EMA50: 22,500
Current Price: 23,500
→ Uptrend confirmed ✅
```

**Tại sao EMA thay vì SMA?**
- EMA phản ứng nhanh hơn với price changes
- Ít lag hơn
- Better cho trend following

---

### **Điều kiện 2: PULLBACK (Correction)**

**Price pulls back TO support levels:**

```python
Price retraces from high
Price approaches EMA20 (first support)
But stays ABOVE EMA50 (major support)
RSI enters 40-60 zone (neutral, not oversold)
```

**Pullback Types:**

**A. Shallow Pullback (Best!)**
```
High: 24,000
Pullback to: 23,200 (near EMA20)
Depth: 3-5%
RSI: 50-55
→ Healthy correction
```

**B. Deep Pullback (OK)**
```
High: 24,000
Pullback to: 22,800 (near EMA50)
Depth: 5-8%
RSI: 45-50
→ Stronger correction but still valid
```

**C. Too Deep (Risky!)**
```
High: 24,000
Pullback to: 22,000 (below EMA50)
Depth: >8%
RSI: <40
→ Trend might be breaking
```

---

### **Điều kiện 3: RSI 40-60 ZONE**

**Tại sao RSI 40-60?**

```
RSI > 60: Overbought → Don't buy at top
RSI < 40: Oversold → Trend might reverse
RSI 40-60: Neutral → Healthy pullback ✅
```

**RSI Guide:**
```
RSI 70-100: Overbought (wait for pullback)
RSI 60-70: Strong (trending up, but high)
RSI 40-60: Neutral (ENTRY ZONE) ✅
RSI 30-40: Weak (oversold, risky)
RSI 0-30: Very weak (avoid)
```

**Perfect Entry:**
```
Price pulled back from 24,000 to 23,200
RSI dropped from 70 to 52
Volume decreased (normal pullback)
→ Setup forming ✅
```

---

### **Điều kiện 4: VOLUME CONFIRMATION**

**Volume must increase when trend resumes:**

```python
Entry signal when:
1. Price bounces from EMA20/50
2. Volume increases (>1.5x recent average)
3. Green candle forms
4. RSI starts rising from 40-60 zone
```

**Volume Pattern:**
```
Before Pullback:
Day 1: 5M shares (high volume, uptrend)
Day 2: 4.5M shares

During Pullback:
Day 3: 2M shares (volume decreases)
Day 4: 1.8M shares (sellers exhausted)

Entry Day: (Volume returns!)
Day 5: 3.5M shares (volume increases) ✅
→ Buyers stepping in
→ Trend resuming
→ ENTRY!
```

---

## 🎯 COMPLETE ENTRY SETUP

**All 4 conditions must align:**

```
1. Uptrend: EMA20 > EMA50, Price > EMA20 ✅
2. Pullback: Price retraced 3-8% ✅
3. RSI: In 40-60 zone ✅
4. Volume: Increasing (>1.5x) on bounce ✅

→ ENTRY!
```

---

## 🛡️ RISK MANAGEMENT

### **Stop Loss: EMA50 SUPPORT**

**Công thức:**
```
SL = EMA50 - 1%

Lý do:
- EMA50 là major support
- Nếu break → Trend bị phá
- Exit ngay lập tức
```

**Ví dụ:**
```
Entry: 23,200 (bounce from EMA20)
EMA50: 22,500
Stop Loss: 22,500 - 1% = 22,275
Risk: 925 VND (4%)
```

**Dynamic Stop Loss:**
```
Khi trend tiếp tục:
- EMA50 di chuyển lên
- Stop loss di chuyển lên theo
- Trailing protection
```

---

### **Take Profit: 3 LEVELS**

**Multiple exit strategy:**

**TP1: +5% (Take 1/3)**
```
Entry: 23,200
TP1: 24,360 (+5%)
Action: Close 1/3 position
Lock profit: 5% × 33% = 1.65%
```

**TP2: +10% (Take 1/3)**
```
TP2: 25,520 (+10%)
Action: Close another 1/3
Additional profit: 10% × 33% = 3.3%
Total locked: 4.95%
```

**TP3: TRAILING (Final 1/3)**
```
Trail with EMA20
Exit when: Price closes below EMA20
Let winners run!
```

**Example Trade:**
```
Entry: 23,200 (100% position)
TP1: 24,360 → Sell 33% → Lock 1.65%
TP2: 25,520 → Sell 33% → Lock 3.3%
Trail: 27,000 → Exit at 26,500 (EMA20 break)
Final 33%: +14.2%
Total: 1.65% + 3.3% + 4.7% = 9.65% ✅
```

---

### **Position Sizing**

**Conservative Approach:**
```
Risk per trade: 1.5% capital
Position size: (Capital × Risk%) / (Entry - SL)

Example:
Capital: 100M
Risk: 1.5M
Entry: 23,200
SL: 22,275
Risk per share: 925

Shares: 1,500,000 / 925 = 1,621 shares
Investment: 1,621 × 23,200 = 37.6M (37.6%)
```

---

## 📊 INDICATORS SETUP

**Required:**

1. **EMA(20)** - Short-term trend
2. **EMA(50)** - Long-term trend  
3. **RSI(14)** - Momentum
4. **Volume + 20-period MA** - Confirmation

**Chart Setup:**
```
Main Chart:
- Candlesticks
- EMA20 (Blue line)
- EMA50 (Red line)

Below Chart:
- RSI(14) with 40-60 zone highlighted
- Volume bars with MA

Clean and simple!
```

---

## 🎯 TRADING EXAMPLES

### **Example 1: Perfect Setup**

**Week 1-2 (Uptrend Established):**
```
Day 1: 22,000 | EMA20: 21,800 | EMA50: 21,500
Day 2: 22,500 | EMA20: 22,000 | EMA50: 21,600
Day 3: 23,000 | EMA20: 22,300 | EMA50: 21,700
Day 4: 23,500 | EMA20: 22,600 | EMA50: 21,900
Day 5: 24,000 | EMA20: 22,900 | EMA50: 22,100 | RSI: 72
→ Strong uptrend, but overbought ⚠️
```

**Week 3 (Pullback):**
```
Day 6: 23,800 | Vol: 3M (decreasing)
Day 7: 23,500 | Vol: 2.5M | RSI: 65
Day 8: 23,200 | Vol: 2M | RSI: 58
Day 9: 23,000 | Vol: 1.8M | RSI: 52
→ Healthy pullback to EMA20 ✅
```

**Day 10 (ENTRY!):**
```
Open: 23,100
Price bounces from EMA20 (22,900)
Volume: 3.8M (2.1x increase!) ✅
Green candle: Close 23,400
RSI: 55 → 58 (rising) ✅

All conditions met → ENTRY at 23,200
```

**Trade Execution:**
```
Entry: 23,200
SL: 22,100 (EMA50 - 1%)
TP1: 24,360 (+5%)
TP2: 25,520 (+10%)
TP3: Trailing (EMA20)

Day 11: 23,600 | Continue holding
Day 12: 24,000 | Continue holding
Day 13: 24,400 | Hit TP1 → Sell 1/3 ✅
Day 15: 25,600 | Hit TP2 → Sell 1/3 ✅
Day 20: 26,500 | Trail with EMA20
Day 22: 26,200 | Break EMA20 → Exit final 1/3
```

**Result:**
```
TP1: 1/3 × 5% = 1.67%
TP2: 1/3 × 10% = 3.33%
TP3: 1/3 × 13.8% = 4.6%
Total: 9.6% profit ✅
```

---

### **Example 2: Stop Loss Hit**

**Setup:**
```
Entry: 23,200 (bounce from EMA20)
SL: 22,100 (EMA50 - 1%)
```

**What Happened:**
```
Day 1: 23,400 (good start)
Day 2: 23,100 (pullback continues)
Day 3: 22,800 (approaching SL)
Day 4: 22,000 (break EMA50!)
→ SL hit at 22,100 ✅
```

**Result:**
```
Loss: (23,200 - 22,100) / 23,200 = -4.7%
But: Capital protected
Trend broken → Exit was correct
```

---

## 🚫 TRÁNH CÁC SAI LẦM

### **1. Mua ở đỉnh (FOMO)**
❌ **Wrong:** RSI 75, giá cao nhất → Vẫn mua
✅ **Right:** Chờ pullback xuống RSI 40-60

### **2. Không chờ volume confirm**
❌ **Wrong:** Giá bounce → Mua ngay
✅ **Right:** Chờ volume tăng → Confirm trend resuming

### **3. Không respect EMA50**
❌ **Wrong:** Giá break EMA50 → "Tôi tin vào stock này" → Hold
✅ **Right:** Break EMA50 → Trend broken → Exit!

### **4. Exit quá sớm**
❌ **Wrong:** +3% → Chốt luôn
✅ **Right:** Phân chia exits (TP1, TP2, Trail)

### **5. Trade against trend**
❌ **Wrong:** EMA20 < EMA50 → "Giá rẻ, mua"
✅ **Right:** Chỉ trade khi uptrend confirmed

---

## 🎯 MULTI-TIMEFRAME APPROACH

### **Daily Timeframe (Primary)**

**Use for:**
- Trend identification
- Entry signals
- Position trades (hold 2-4 weeks)

**Setup:**
- EMA20/50 on daily
- RSI(14) daily
- Volume on daily

---

### **1H Timeframe (Advanced)**

**Use for:**
- Fine-tune entry
- Earlier signals
- Swing trades (hold 3-10 days)

**How to use:**
```
Step 1: Check daily
→ Is daily trend up? (EMA20 > EMA50)
→ Yes? → Look for 1H entries

Step 2: Switch to 1H
→ Wait for 1H pullback
→ RSI 40-60 on 1H
→ Volume increase on 1H
→ Entry on 1H!

Benefits:
- Earlier entries than daily
- More signals
- Tighter stops
```

**Example:**
```
Daily: Uptrend confirmed (EMA20 > EMA50)
Daily: No pullback yet (RSI 68)

1H: Already pulled back to 1H EMA20
1H: RSI 52, volume increasing
→ Entry on 1H! ✅

Result: Earlier entry than waiting for daily pullback
```

---

## 📊 BACKTEST PARAMETERS

### **VN100 Test Setup:**

**Universe:**
- 90 stocks (VN30 + VN70)
- Period: Jan 2, 2025 - Dec 17, 2025

**Entry Conditions:**
1. EMA20 > EMA50 (uptrend)
2. Price pullback 3-8%
3. RSI between 40-60
4. Volume ≥ 1.5x average on bounce

**Exit Conditions:**
1. Stop Loss: EMA50 - 1% (~4-5%)
2. TP1: +5% (sell 1/3)
3. TP2: +10% (sell 1/3)
4. TP3: Trail with EMA20 (final 1/3)
5. Max hold: 60 days

**Position Sizing:**
- Risk 1.5% per trade
- Max 3 positions open
- 15-20% capital per position

---

## 🎯 EXPECTED RESULTS

### **Conservative Estimates:**

```
Win Rate: 60-70%
Average Win: +8-12%
Average Loss: -4-5%
Profit Factor: 2.5-3.5x
Signals: 20-35 per year (VN100)
Max Drawdown: -12-18%
Sharpe Ratio: 1.5-2.0
```

**Why better than Strategy 1?**
- More signals (trend following)
- Better entries (pullback)
- Better exits (multiple TPs)
- Works in trending markets

**Why better than Strategy 2?**
- Not too strict
- Enough signals
- Works in VN volatility
- Flexible exits

---

## 💡 ADVANTAGES

✅ **1. Ride strong trends**
Trend following = Catch big moves

✅ **2. Better entry price**
Pullback = Don't buy at top

✅ **3. Clear trend definition**
EMA20/50 = Objective rules

✅ **4. Multiple exits**
TP1/2/3 = Maximize profits

✅ **5. Self-adjusting stops**
EMA50 moves up = Trailing protection

✅ **6. Works on multiple timeframes**
Daily + 1H = More opportunities

✅ **7. Proven methodology**
Used by professional traders worldwide

---

## ⚠️ DISADVANTAGES

❌ **1. Whipsaw in sideways market**
Trend changes → Stop outs

❌ **2. Miss explosive breakouts**
Wait for pullback → Miss strong moves

❌ **3. Need trending market**
Works best in bull/bear, not sideways

❌ **4. Requires patience**
Wait for pullback = Not always immediate

❌ **5. Multiple exits = More management**
Track 3 levels = More work

---

## 🎯 BEST FOR

✅ **Trending markets** (VN 2025 = trending!)
✅ **Patient traders**
✅ **Part-time traders** (daily TF = less monitoring)
✅ **Risk-averse** (clear stops)
✅ **Position traders** (2-4 week holds)

---

## 🔥 COMPARE 3 STRATEGIES

| Feature | **Str 1** (Momentum) | **Str 2** (Breakout) | **Str 3** (Trend) |
|---------|---------------------|---------------------|------------------|
| **Approach** | Catch spike | Wait confirm | Follow trend |
| **Entry** | Immediate | After confirm | On pullback |
| **Signals** | 15/year | 5/year | 25-35/year |
| **Win Rate** | 53-75% | 20% | 60-70% |
| **Avg Win** | +8% | +1.5% | +8-12% |
| **Stop Loss** | -5% | -2% | -4-5% |
| **Complexity** | Medium | High | Medium |
| **Best For** | Volatile | Conservative | Trending |
| **Status** | ✅ Proven | ❌ Failed | 🔄 To test |

---

## 📋 CHECKLIST

**Before Entry:**
- [ ] Daily uptrend (EMA20 > EMA50)
- [ ] Pullback completed (3-8%)
- [ ] RSI 40-60 zone
- [ ] Volume increasing (≥1.5x)
- [ ] Green candle forming
- [ ] Stop loss calculated (EMA50 - 1%)
- [ ] 3 TP levels set
- [ ] Position size calculated

**After Entry:**
- [ ] Monitor daily close
- [ ] Update EMAs daily
- [ ] Check TP1/2/3 levels
- [ ] Trail with EMA20 for final position
- [ ] Honor stop loss if hit
- [ ] No emotional decisions

---

## 🎊 SUMMARY

**Simple Formula:**
```
Uptrend (EMA20 > EMA50)
+ Pullback (3-8%, RSI 40-60)
+ Volume Confirmation (≥1.5x)
= Entry

Exits:
TP1: +5% (1/3)
TP2: +10% (1/3)
TP3: Trail EMA20 (1/3)
SL: EMA50 - 1%
```

**Philosophy:**
"The trend is your friend. Enter on weakness. Exit on strength."

---

**Next: Backtest để validate! Expected win rate 60-70%! 🚀**
