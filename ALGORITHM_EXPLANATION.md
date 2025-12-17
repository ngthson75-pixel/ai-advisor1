# 📊 THUẬT TOÁN LỌC TÍN HIỆU MUA/BÁN

## 🎯 OVERVIEW

AI Advisor sử dụng 2 phương pháp để tạo tín hiệu:
1. **Gemini AI Analysis** (Primary)
2. **Rule-Based System** (Fallback)

---

## 🤖 GEMINI AI ANALYSIS (Primary)

### **Input Data:**
```javascript
{
  code: 'VNM',
  price: 87415,           // Giá hiện tại (VNStock)
  open: 85200,            // Giá mở cửa
  change: +2215,          // Thay đổi (VND)
  changePercent: +2.6,    // Thay đổi (%)
  volume: 12870000,       // Khối lượng giao dịch
  high: 87502,            // Cao nhất
  low: 87015,             // Thấp nhất
  rsi: 71,                // Calculated RSI
  macd: +1.8              // Calculated MACD
}
```

### **Gemini Prompt:**
```
Bạn là chuyên gia phân tích chứng khoán Việt Nam.
Phân tích cổ phiếu với dữ liệu THỰC TẾ từ VNStock:

Mã: VNM
Giá hiện tại: 87,415 VND
Thay đổi: +2,215 (+2.6%)
Khối lượng: 12.9M
RSI: 71
MACD: +1.8

→ Đưa ra tín hiệu MUA/BÁN + phân tích chi tiết
```

### **Gemini Output:**
```json
{
  "signal": "MUA",
  "signalType": "SWING T+",
  "score": 81,
  "probability": 73,
  "entryPrice": 87852,
  "stopLoss": 83044,
  "takeProfit": 94408,
  "positionSize": 15,
  "maxDrawdown": 5,
  "analysis": "VNM đang có tín hiệu tích cực với giá 87,415 VND (+2.6% so với mở cửa). RSI 71 cho thấy cổ phiếu đã điều chỉnh. Khối lượng 12.9M phản ánh thanh khoản tốt. Data từ VNStock real-time."
}
```

---

## 🔧 RULE-BASED SYSTEM (Fallback)

### **Khi nào dùng:**
- Gemini API fail
- Timeout
- Rate limit exceeded
- Error parsing JSON

### **Logic:**

#### **1. Tín hiệu MUA (isBuy = true):**

```javascript
// Điều kiện 1: RSI thấp + MACD positive + không giảm quá mạnh
(rsi < 45 && macd > 0 && changePercent > -2)

// HOẶC

// Điều kiện 2: Tăng mạnh + Volume cao
(changePercent > 2 && volume > 10000000)
```

**Ví dụ MUA:**
```
VNM: 87,415 (+2.6%)
RSI: 71 (> 45) ❌
MACD: +1.8 (> 0) ✅
changePercent: +2.6 (> 2) ✅
volume: 12.9M (> 10M) ✅

→ Điều kiện 2 thỏa → isBuy = true → Tín hiệu MUA
```

#### **2. Tín hiệu BÁN (isSell = true):**

```javascript
// Điều kiện 1: RSI cao + MACD negative
(rsi > 65 && macd < 0)

// HOẶC

// Điều kiện 2: Giảm mạnh
(changePercent < -3)
```

**Ví dụ BÁN:**
```
HPG: 24,200 (-3.5%)
RSI: 42 (< 65) ❌
MACD: -1.2 (< 0) ✅
changePercent: -3.5 (< -3) ✅

→ Điều kiện 2 thỏa → isSell = true → Tín hiệu BÁN
```

#### **3. Tín hiệu GIỮ (Hold):**

```javascript
// Không thỏa điều kiện MUA và BÁN
!isBuy && !isSell → signal = 'GIỮ'
```

### **Score & Probability:**

```javascript
// MUA
score = 75 + random(0-10) = 75-85
probability = 68 + random(0-8) = 68-76%

// BÁN
score = 65 + random(0-10) = 65-75
probability = 62 + random(0-8) = 62-70%

// GIỮ
score = 50
probability = 50%
```

### **Entry/SL/TP Calculation:**

```javascript
// MUA
entryPrice = currentPrice * 1.005  // +0.5%
stopLoss = currentPrice * 0.95     // -5%
takeProfit = currentPrice * 1.08   // +8%

// BÁN
entryPrice = currentPrice * 0.995  // -0.5%
stopLoss = currentPrice * 1.05     // +5%
takeProfit = currentPrice * 0.92   // -8%
```

---

## 📊 TECHNICAL INDICATORS

### **RSI Calculation:**

```javascript
function calculateRSI(price: number, open: number): number {
  const changePercent = ((price - open) / open) * 100;
  
  if (changePercent > 0) {
    return Math.min(50 + changePercent * 8, 75);
  } else {
    return Math.max(50 + changePercent * 8, 25);
  }
}
```

**Ví dụ:**
```
VNM:
price = 87,415
open = 85,200
changePercent = +2.6%

RSI = 50 + (2.6 * 8) = 50 + 20.8 = 70.8 ≈ 71
```

### **MACD Calculation:**

```javascript
function calculateMACD(price: number, open: number): number {
  const change = price - open;
  return Number((change / open * 100).toFixed(2));
}
```

**Ví dụ:**
```
VNM:
price = 87,415
open = 85,200
change = 2,215

MACD = (2,215 / 85,200) * 100 = 2.60%
```

---

## 🎯 STOCK FILTERING

### **Current List:**

```javascript
const STOCK_CODES = ['MBB', 'VNM', 'HPG', 'FPT', 'VCB', 'VIC'];
```

### **Criteria:**
- ✅ Large cap (> 1 tỷ USD market cap)
- ✅ High liquidity (> 5M shares/day)
- ✅ Blue chips
- ✅ VN30 index members
- ✅ Good financial health

### **To expand:**
```javascript
// Thêm mã khác
const STOCK_CODES = [
  'MBB', 'VNM', 'HPG', 'FPT', 'VCB', 'VIC',
  'MSN', 'VHM', 'GVR', 'SAB'  // ← Thêm
];
```

---

## ⚠️ VẤN ĐỀ HIỆN TẠI

### **Quan sát từ screenshot:**

```
VNM: 87,415 VND (+2.6%)
KL: 12.87M
Score: 81/100
Xác suất: 73%
Tín hiệu: MUA
```

### **Potential Issues:**

1. **RSI = 71 (quá cao?)**
   - RSI > 70 thường báo hiệu "overbought"
   - Nhưng rule cho MUA khi changePercent > 2%
   - → **Cần điều chỉnh threshold**

2. **Volume 12.9M (bình thường cho VNM)**
   - Average volume VNM: 10-15M
   - Không có dấu hiệu bất thường

3. **Giá tăng 2.6% (mạnh)**
   - Có thể đã "miss" điểm entry tốt
   - Nên có tín hiệu sớm hơn

---

## 🔧 ĐỀ XUẤT CẢI TIẾN

### **Option 1: Tighten RSI Filter**

```javascript
// CŨ
const isBuy = (rsi < 45 && macd > 0 && changePercent > -2) ||
              (changePercent > 2 && volume > 10000000);

// MỚI (stricter)
const isBuy = (rsi < 45 && macd > 0 && changePercent > -2) ||
              (changePercent > 1.5 && changePercent < 3 && volume > 10000000 && rsi < 70);
              //         ↑ Lower threshold     ↑ Upper limit            ↑ RSI filter
```

### **Option 2: Add Volume Confirmation**

```javascript
// Cần volume tăng 20% so với average
const avgVolume = 10000000;  // Historical average
const volumeRatio = stock.volume / avgVolume;

const isBuy = (rsi < 45 && macd > 0 && changePercent > -2) ||
              (changePercent > 2 && volumeRatio > 1.2 && rsi < 70);
              //                     ↑ Volume confirmation
```

### **Option 3: Multi-Timeframe**

```javascript
// Check trend trong 3-5 ngày
const shortTermTrend = calculateTrend(prices_3days);
const mediumTermTrend = calculateTrend(prices_5days);

const isBuy = (rsi < 45 && macd > 0 && shortTermTrend === 'UP') ||
              (changePercent > 2 && mediumTermTrend === 'UP' && rsi < 70);
```

---

## 📈 BACKTESTING NEEDED

### **Để validate thuật toán:**

1. **Historical data:**
   - Fetch 6 tháng data (VNStock)
   - Run algorithm trên mỗi ngày
   - Track P/L

2. **Metrics:**
   - Win rate: % tín hiệu thắng
   - Avg P/L: Trung bình lãi/lỗ
   - Max drawdown: Lỗ tối đa
   - Sharpe ratio: Risk-adjusted return

3. **Optimize parameters:**
   - RSI threshold: 30? 40? 45?
   - Volume threshold: 5M? 10M? 15M?
   - ChangePercent: 1.5%? 2%? 2.5%?

---

## 🎯 RECOMMENDATION

### **Ngắn hạn (Now):**
1. **Điều chỉnh RSI threshold:**
   ```javascript
   const isBuy = (rsi < 45 && macd > 0 && changePercent > -2) ||
                 (changePercent > 1.5 && rsi < 70 && volume > 10M);
   ```

2. **Add disclaimer:**
   ```
   "Tín hiệu chỉ mang tính tham khảo. 
   Nhà đầu tư tự chịu trách nhiệm quyết định."
   ```

### **Trung hạn (1-2 tuần):**
1. **Collect historical data**
2. **Backtest với parameters khác nhau**
3. **Optimize based on results**

### **Dài hạn (1-2 tháng):**
1. **Machine Learning model**
2. **Sentiment analysis (news)**
3. **Fundamentals integration (P/E, P/B)**

---

## 💡 TÓM TẮT

**Thuật toán hiện tại:**
- ✅ Simple & transparent
- ✅ Fast execution
- ⚠️ Có thể cho tín hiệu sai khi RSI quá cao
- ⚠️ Chưa có backtesting

**Cần làm:**
- 🔧 Tighten RSI filter (< 70 for BUY)
- 📊 Backtest với data lịch sử
- 🎯 Optimize parameters

**Demo với investors:**
- ✅ Giải thích logic rõ ràng
- ✅ Show transparency
- ✅ Commit to continuous improvement
