# 📊 CHIẾN LƯỢC 2: BREAKOUT CÓ XÁC NHẬN

## 🎯 TRIẾT LÝ CHIẾN LƯỢC

### **Core Concept:**
"Nén → Bật → Xác nhận → Entry"

**Không phải:** Chase mọi breakout
**Mà là:** Chờ nền giá ổn định → Breakout thực sự → Volume confirm → Entry an toàn

---

## 📋 QUY TẮC ENTRY

### **Điều kiện 1: NỀN GIÁ CHẶT (Consolidation)**

**Định nghĩa:**
- Giá dao động trong range hẹp
- Không có đột biến volume
- Thời gian: ≥ 10-15 phiên

**Đo lường:**
```python
# ATR (Average True Range) giảm dần
ATR_current < ATR_20_periods * 0.7

# Hoặc: Bollinger Bands thu hẹp
BB_width < BB_average * 0.6

# Hoặc: Price range nhỏ
(High - Low) / Close < 3% trong 10-15 phiên
```

**Ví dụ:**
```
Phiên 1-10: Giá dao động 22,000 - 22,800 (3.6% range)
Phiên 11-15: Giá dao động 22,200 - 22,600 (1.8% range)
→ Nền giá đang chặt ✅
```

---

### **Điều kiện 2: BREAKOUT VỚI VOLUME**

**Định nghĩa:**
- Giá phá đỉnh range/resistance
- Volume spike ≥ 2x average
- Nến xanh mạnh (close gần high)

**Đo lường:**
```python
# Breakout point
Close > Max(High, 20 periods)

# Volume confirmation
Volume >= Average_Volume_20 * 2.0

# Strong candle
(Close - Low) / (High - Low) > 0.7
```

**Ví dụ:**
```
Range: 22,000 - 22,800
Breakout: Close @ 23,100 (phá đỉnh 22,800)
Volume: 5M shares vs 2M average (2.5x)
→ Breakout hợp lệ ✅
```

---

### **Điều kiện 3: XÁC NHẬN**

**Không entry ngay tại breakout!**
**Chờ phiên kế tiếp xác nhận:**

**3 loại xác nhận (chỉ cần 1):**

**Option A: Pullback Test** (Best!)
```
Phiên sau breakout: Giá về test lại breakout level
Nhưng không phá vỡ (hold support)
Volume giảm (không panic)
→ Entry tại support test
```

**Option B: Continuation** (Good)
```
Phiên sau: Tiếp tục tăng
Close > Yesterday's High
Volume ≥ 1.5x average
→ Entry tại open/pullback nhỏ
```

**Option C: Sideways Consolidation** (OK)
```
Phiên sau: Giá đi ngang trên breakout level
Không về dưới breakout
Volume bình thường
→ Entry khi có dấu hiệu tiếp tục
```

---

## 🛡️ QUẢN LÝ RỦI RO

### **Stop Loss: CHẶT**

**Công thức:**
```
SL = Breakout Level - 2%

Hoặc:
SL = Low của nến breakout - 1%

Chọn level nào cao hơn
```

**Ví dụ:**
```
Breakout: 23,000
SL Option 1: 23,000 - 2% = 22,540
SL Option 2: Low 22,800 - 1% = 22,572
→ Chọn: 22,572 (cao hơn) ✅

Rủi ro: 23,000 - 22,572 = 428 (1.86%)
```

**Lý do SL chặt:**
- Breakout thất bại → Exit nhanh
- Giảm thiểu loss
- Bảo vệ vốn

---

### **Take Profit: MỞ (Trailing)**

**Không set TP cố định!**
**Sử dụng Trailing Stop:**

**Công thức:**
```
Trailing Stop = ATR × 2

Khi giá tăng:
- Stop Loss di chuyển lên theo
- Luôn cách giá hiện tại 2×ATR
- Không bao giờ đi xuống
```

**Ví dụ:**
```
Entry: 23,000
ATR: 500
Initial SL: 22,572

Giá lên 24,000:
New SL = 24,000 - (500 × 2) = 23,000
(Lock profit!)

Giá lên 25,000:
New SL = 25,000 - 1,000 = 24,000
(More profit locked!)

Giá về 24,500:
SL vẫn 24,000 (không giảm)
Exit tại 24,000 → Profit: +4.3%
```

**Hoặc dùng Chandelier Exit:**
```
Exit = Highest High (since entry) - 3 × ATR
```

---

### **Position Sizing: BẢO THỦ**

**Công thức:**
```
Position Size = (Risk per Trade) / (Entry - Stop Loss)

Risk per Trade = 1% capital
```

**Ví dụ:**
```
Capital: 100M
Risk per trade: 1% = 1M
Entry: 23,000
Stop Loss: 22,572
Risk per share: 428

Shares = 1,000,000 / 428 = 2,336 shares
Investment = 2,336 × 23,000 = 53.7M (53% capital)
```

---

## 📊 INDICATORS

**Minimum required:**

1. **Volume** (20-day MA)
2. **ATR(14)** (for volatility)
3. **Highest High(20)** (for breakout level)
4. **Bollinger Bands(20,2)** (optional - for consolidation)

**Không cần:**
- RSI (không quan trọng)
- MACD (không quan trọng)
- Stochastic (không quan trọng)

**Simple is better!**

---

## 🎯 TRADING EXAMPLE

### **Perfect Setup:**

**Week 1-2 (Consolidation):**
```
Day 1: 22,000 - 22,400 | Vol: 2M
Day 2: 22,100 - 22,500 | Vol: 1.8M
Day 3: 21,900 - 22,300 | Vol: 2.2M
...
Day 10: 22,200 - 22,600 | Vol: 1.9M
→ Range chặt, volume bình thường ✅
```

**Day 11 (Breakout):**
```
Open: 22,400
High: 23,200
Low: 22,300
Close: 23,100
Volume: 5.5M (2.75x average)
→ Breakout với volume! ✅
```

**Day 12 (Confirmation - Pullback Test):**
```
Open: 23,000
High: 23,150
Low: 22,850 (test breakout level 22,800)
Close: 23,050
Volume: 3M (giảm, không panic)
→ Test thành công! ENTRY! ✅
```

**Entry Details:**
```
Entry: 23,000 (tại pullback)
Stop Loss: 22,540 (2% dưới breakout)
Risk: 460 (2%)
Initial Target: Trailing stop (2×ATR = 1,000)
```

**Trade Progress:**
```
Day 13: 23,400 | SL: 22,400 (trailing)
Day 14: 23,800 | SL: 22,800
Day 15: 24,500 | SL: 23,500
Day 16: 24,200 | Exit at 23,500
→ Profit: +2.17% (500 / 23,000)
```

---

## 🚫 TRÁNH CÁC SAI LẦM

### **1. Entry ngay tại breakout**
❌ **Wrong:** Giá phá 23,000 → Mua ngay!
✅ **Right:** Giá phá 23,000 → Chờ xác nhận → Mua ở 22,850 (pullback)

### **2. Chase giá**
❌ **Wrong:** Giá lên 24,000 rồi → Vẫn mua vì FOMO
✅ **Right:** Miss thì miss, chờ setup tiếp theo

### **3. Không có SL**
❌ **Wrong:** "Tôi tin vào cổ phiếu này, không cần SL"
✅ **Right:** Set SL trước khi entry, honor it!

### **4. Move SL xuống**
❌ **Wrong:** SL 22,540 nhưng giá về 22,400 → Move SL xuống 22,000
✅ **Right:** SL 22,540 hit → Exit! Không ân hận!

### **5. Take profit quá sớm**
❌ **Wrong:** +3% rồi → Chốt luôn!
✅ **Right:** Trailing stop → Để trend chạy → Exit khi reverse

---

## 📈 BACKTEST PARAMETERS

### **VN100 Test Setup:**

**Universe:**
- 90 stocks (VN30 + VN70)
- Period: Jan 2, 2025 - Dec 17, 2025

**Entry Conditions:**
1. Consolidation ≥ 10 days (ATR declining)
2. Breakout: Close > Highest(20)
3. Volume ≥ 2.0x average
4. Confirmation: Pullback test OR continuation

**Exit Conditions:**
1. Stop Loss: -2% from breakout level
2. Trailing Stop: Current High - 2×ATR
3. Max hold: 60 days (if no exit trigger)

**Position Sizing:**
- Risk 1% per trade
- Max 3 positions open
- 15% capital per position

---

## 🎯 EXPECTED RESULTS

### **Conservative Estimates:**

**Based on historical breakout statistics:**

```
Win Rate: 55-65%
Average Win: +5-8%
Average Loss: -2%
Profit Factor: 2.5-3.5x
Signals: 15-25 per year (VN100)
Max Drawdown: -8-12%
```

**Why more conservative than Strategy 1?**
- Requires consolidation (fewer setups)
- Requires confirmation (miss some trades)
- Chặt SL (stop out more)
- But: Higher quality, lower risk

---

## 💡 ADVANTAGES

✅ **1. Bẫy giả (false breakout) ít hơn**
Confirmation filter out failed breaks

✅ **2. Entry price tốt hơn**
Wait for pullback → Better entry

✅ **3. Risk rõ ràng**
SL chặt → Biết chính xác risk

✅ **4. Tâm lý thoải mái**
Setup rõ ràng → Confident

✅ **5. Win rate cao hơn**
Quality > Quantity

---

## ⚠️ DISADVANTAGES

❌ **1. Miss một số breakout mạnh**
Không entry ngay → Miss explosive moves

❌ **2. Ít tín hiệu**
Chờ consolidation → Ít setup

❌ **3. Cần kiên nhẫn**
Phải chờ confirmation → Test tâm lý

❌ **4. Stop out nhiều hơn**
SL chặt → Stop dễ hit

---

## 🎯 BEST FOR

✅ **Traders bảo thủ**
✅ **Part-time traders** (ít setup → quản lý dễ)
✅ **Risk-averse investors**
✅ **People với full-time job**
✅ **Long-term focused**

---

## 🔥 COMBINE WITH STRATEGY 1?

**Yes! 2 chiến lược bổ sung nhau:**

**Strategy 1 (Momentum):**
- Aggressive
- Volume spike + RSI + MACD
- More signals
- Win rate: 75% (VN30)

**Strategy 2 (Breakout Confirmation):**
- Conservative
- Consolidation + Breakout + Confirmation
- Fewer signals
- Win rate: 55-65% (expected)

**Portfolio approach:**
```
50% capital: Strategy 1 (proven 75%)
50% capital: Strategy 2 (conservative)

Result: Balanced risk/reward
```

---

## 📋 CHECKLIST

**Before Entry:**
- [ ] Consolidation ≥ 10 days verified
- [ ] Breakout level identified
- [ ] Volume ≥ 2x average confirmed
- [ ] Confirmation pattern present
- [ ] Stop loss calculated (2% below breakout)
- [ ] Position size calculated (1% risk)
- [ ] Trailing stop setup ready
- [ ] Mental commitment to honor stops

**After Entry:**
- [ ] Stop loss order placed
- [ ] Trailing stop monitoring active
- [ ] Daily check: Update trailing stop
- [ ] No emotional decisions
- [ ] No moving SL down
- [ ] Trust the process

---

## 🎊 SUMMARY

**Simple Formula:**
```
Nền giá chặt (10+ days)
+ Breakout với volume (2x+)
+ Xác nhận (pullback test/continuation)
= Entry

Stop Loss: Chặt (2% below breakout)
Take Profit: Mở (trailing 2×ATR)
```

**Philosophy:**
"Patience pays. Quality over quantity. Risk management first."

---

**Next: Backtest code để validate! 🚀**
