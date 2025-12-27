# 📊 BREAKOUT STRATEGY - Volume Spike + MACD + RSI

## 🎯 CHIẾN LƯỢC

### **Pattern Recognition:**

Dựa trên chart bạn gửi, chiến lược detect điểm "đảo mua" khi price breakout khỏi consolidation với:

1. **Volume spike** (200%+)
2. **MACD crossover** (âm → dương)
3. **RSI breakout** (> 70)

**Logic:** Đây là dấu hiệu "smart money" đang vào mạnh!

---

## 🔍 3 ĐIỀU KIỆN BẮT BUỘC

### **1. Volume Spike (≥ 200%)**

**Công thức:**
```python
volume_ratio = current_volume / previous_volume
is_spike = volume_ratio >= 3.0  # 3x = 200% increase
```

**Ý nghĩa:**
- Volume tăng đột biến → Có lực mua mạnh đang vào
- Smart money đang accumulate
- Breakout có confirmation

**Example:**
```
Bar 1: Volume = 1,000,000
Bar 2: Volume = 3,500,000  → Ratio = 3.5x (250% increase) ✅
```

---

### **2. MACD Crossover (Âm → Dương)**

**Công thức:**
```python
macd = EMA(12) - EMA(26)
signal = EMA(macd, 9)
histogram = macd - signal

# Crossover khi:
previous_histogram < 0  AND  current_histogram > 0
```

**Ý nghĩa:**
- MACD histogram chuyển từ âm sang dương
- Momentum đang đảo chiều lên
- Xu hướng ngắn hạn bullish

**Visual:**
```
Bar -2: Histogram = -0.03 (âm)
Bar -1: Histogram = -0.01 (âm)
Bar 0:  Histogram = +0.02 (dương) ✅ CROSSOVER!
```

---

### **3. RSI Breakout (> 70)**

**Công thức:**
```python
rsi = RSI(close, period=14)
is_breakout = rsi > 70
```

**Ý nghĩa:**
- RSI > 70 = Overbought (thông thường là sell signal)
- NHƯNG trong breakout context = Momentum mạnh!
- Kết hợp với volume spike = Xác nhận breakout thật

**Lưu ý:**
- RSI > 70 đơn lẻ → Cẩn thận (có thể pullback)
- RSI > 70 + Volume spike + MACD crossover → Strong signal! 💪

---

## 📊 INDICATOR CALCULATIONS

### **RSI (14-period):**

```python
def calculate_rsi(prices, period=14):
    deltas = prices.diff()
    gain = deltas.clip(lower=0)
    loss = -deltas.clip(upper=0)
    
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

### **MACD (12, 26, 9):**

```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return macd, signal_line, histogram
```

---

## 🎯 SIGNAL DETECTION LOGIC

```python
# Step 1: Calculate all indicators
df['rsi'] = calculate_rsi(df['close'])
df['macd'], df['signal'], df['histogram'] = calculate_macd(df['close'])

# Step 2: Check each condition
condition_1 = df['volume'] / df['volume'].shift(1) >= 3.0
condition_2 = (df['histogram'].shift(1) < 0) & (df['histogram'] > 0)
condition_3 = df['rsi'] > 70

# Step 3: Combine (ALL must be True)
df['buy_signal'] = condition_1 & condition_2 & condition_3

# Step 4: Get latest bar
if df['buy_signal'].iloc[-1]:
    return "BUY SIGNAL!"
```

---

## 💯 CONFIDENCE SCORING

**Score từ 0-100 dựa trên strength:**

### **Volume strength (0-40 pts):**
- 500%+ (6x): 40 points
- 400%+ (5x): 35 points
- 300%+ (4x): 30 points
- 200%+ (3x): 25 points

### **RSI strength (0-30 pts):**
- RSI ≥ 80: 30 points
- RSI ≥ 75: 25 points
- RSI ≥ 70: 20 points

### **MACD strength (0-30 pts):**
- Histogram ≥ 0.05: 30 points
- Histogram ≥ 0.03: 25 points
- Histogram ≥ 0.01: 20 points

**Example:**
```
Volume ratio: 3.5x  → 30 points
RSI: 72         → 20 points
Histogram: 0.02  → 20 points
───────────────────────────
Total: 70/100 (Good signal)
```

---

## 🚀 USAGE

### **Scan single stock:**

```python
from breakout_scanner import BreakoutDetector, fetch_1h_data

# Fetch data
df = fetch_1h_data('VNM', lookback_hours=168)

# Create detector
detector = BreakoutDetector(
    volume_multiplier=3.0,  # 200% increase
    rsi_threshold=70
)

# Detect signal
df_with_indicators = detector.detect_signal(df)
signal = detector.get_latest_signal(df_with_indicators)

if signal:
    print(f"BUY {signal['code']} @ {signal['close']}")
    print(f"Confidence: {signal['confidence']}/100")
```

### **Scan multiple stocks:**

```bash
python scripts/breakout_scanner.py
```

**Output:**
```json
{
  "success": true,
  "signals_found": 3,
  "signals": [
    {
      "code": "VNM",
      "time": "2025-12-17T14:00:00",
      "close": 87415,
      "volume": 12900000,
      "volume_ratio": 3.5,
      "rsi": 72.3,
      "macd": 0.023,
      "signal": "BUY",
      "confidence": 75
    }
  ]
}
```

---

## ⚠️ RISK MANAGEMENT

### **Entry:**
```
Entry price = Close của bar có signal
```

### **Stop Loss (5%):**
```
Stop loss = Entry * 0.95
```

**Lý do:** Breakout fail thường drop nhanh → Cắt lỗ sớm!

### **Take Profit:**

**Option 1: Fixed (8%):**
```
Take profit = Entry * 1.08
```

**Option 2: Trailing stop:**
```
Exit khi RSI < 50 hoặc volume drop < avg
```

### **Position Size:**
```
Risk per trade: 1-2% of capital
Position size = (Capital × Risk%) / (Entry - Stop Loss)
```

**Example:**
```
Capital: 100,000,000 VND
Risk: 1% = 1,000,000 VND
Entry: 87,415
Stop: 83,044 (5% below)
Risk per share: 4,371

Position size = 1,000,000 / 4,371 = 229 shares
Investment = 229 × 87,415 = 20,018,035 VND (~20% of capital)
```

---

## 📈 BACKTESTING PLAN

### **Test period:** 6-12 tháng

### **Metrics to track:**

1. **Win rate:**
   - Target: > 50%
   - Good: 55-65%
   - Excellent: > 65%

2. **Risk/Reward ratio:**
   - Target: > 1.5
   - Good: 2.0+

3. **Max drawdown:**
   - Target: < 15%

4. **Profit factor:**
   - Total profit / Total loss
   - Target: > 1.5

### **Optimization parameters:**

- Volume multiplier: 2.5x, 3.0x, 3.5x, 4.0x
- RSI threshold: 65, 70, 75, 80
- Timeframe: 1H, 4H (test cả 2)

---

## 🎯 STRATEGY STRENGTHS

### **✅ Pros:**

1. **Clear rules** - Objective, không chủ quan
2. **Volume confirmation** - Smart money validation
3. **Multiple filters** - Giảm false signals
4. **Momentum-based** - Catch strong moves
5. **Visual pattern** - Dễ nhận biết trên chart

### **⚠️ Cons:**

1. **Late entry** - Vào sau khi price đã breakout
2. **False breakouts** - Có thể bị fakeout
3. **RSI > 70** - Risk of pullback
4. **Requires discipline** - Phải cắt lỗ nhanh nếu fail
5. **Market dependent** - Tốt trong uptrend, khó trong sideways

---

## 💡 IMPROVEMENTS

### **Phase 1 (Current):**
- ✅ Basic detection: Volume + MACD + RSI
- ✅ Confidence scoring
- ✅ JSON output

### **Phase 2 (Next):**
- 🔧 Add support/resistance check
- 🔧 Filter: Chỉ trade khi price > MA(50)
- 🔧 Volume profile analysis
- 🔧 Time filter (avoid first/last hour)

### **Phase 3 (Advanced):**
- 🤖 Machine learning cho confidence
- 📊 Real-time alerts (webhook)
- 📈 Auto-entry/exit với API
- 💾 Database tracking

---

## 🧪 TESTING

### **Test với mock data:**

```bash
python scripts/test_breakout.py
```

**Output:**
```
TEST 1: BREAKOUT PATTERN
✅ SIGNAL DETECTED!
  Volume ratio: 3.50x
  RSI: 73.21
  Confidence: 75/100

TEST 2: NO SIGNAL PATTERN
✅ CORRECT! No signal detected
```

### **Test với VNStock data:**

```bash
python scripts/breakout_scanner.py
```

---

## 📚 REFERENCES

**Technical Analysis:**
- RSI: Relative Strength Index (Wilder, 1978)
- MACD: Moving Average Convergence Divergence (Appel, 1979)
- Volume analysis: Wyckoff Method

**Similar strategies:**
- Mark Minervini's Trend Template
- William O'Neil's CAN SLIM
- Nicolas Darvas' Box Theory

---

## ✅ NEXT STEPS

### **Immediate (This week):**
1. ✅ Code complete
2. 🧪 Test với mock data
3. 📊 Test với VNStock real data
4. 📝 Document results

### **Week 2:**
1. 🔬 Backtest 6 months
2. 📊 Calculate win rate
3. 🎯 Optimize parameters
4. ✅ Validate strategy

### **Week 3-4:**
1. 📱 Integrate vào AI Advisor app
2. 🔔 Add real-time scanning
3. 📧 Push notifications
4. 🚀 Deploy to beta users

---

**Chiến lược này rất solid! Ready to backtest! 🚀**
