# 📊 VNSTOCK ANALYSIS - MVP READINESS

## 🎯 THÔNG TIN TỪ ADMIN (VŨ THỊNH)

### **VNStock Capabilities:**

✅ **Timeframes available:**
- 1m (1 phút)
- 5m (5 phút)
- 15m (15 phút)
- 1H (1 giờ)
- 1D (1 ngày - EOD)
- 1W (1 tuần)

✅ **Data coverage:**
- Tất cả mã trên HOSE/HNX/UPCOM
- Data đã chuẩn hoá (ready to use)
- Columns: `time, open, high, low, close, volume`
- Time format: ISO standard (not raw numbers)

⚠️ **Limitations:**
- Rate limit: **60 requests/phút** (1 request/giây)
- Một số nguồn public có thể bị chặn (occasional errors)
- Không cần làm sạch data (đã chuẩn hoá)

---

## ✅ ĐÁNH GIÁ CHO MVP

### **1. Data đủ không? → YES!**

**Current need:**
- ✅ EOD data → VNStock có (1D)
- ✅ Intraday → VNStock có (1H, 15m, 5m, 1m)
- ✅ Multiple stocks → VNStock có (all symbols)
- ✅ Historical → VNStock có (nhiều năm)

**Conclusion:** VNStock **ĐỦ** cho MVP và production!

---

### **2. Timeframe strategy cho MVP**

#### **Option A: EOD (1D) - Current**

**Pros:**
- ✅ Đơn giản, ổn định
- ✅ Rate limit không vấn đề (1 call/stock/day)
- ✅ Phù hợp Swing Trading (3-5 ngày)

**Cons:**
- ⚠️ Tín hiệu chậm (chỉ sau đóng cửa)
- ⚠️ Miss cơ hội intraday

**Use case:**
```
End of day (15:00):
→ Fetch EOD data
→ Calculate indicators
→ Generate signals
→ User check trước khi market mở hôm sau
```

---

#### **Option B: 1H (Recommended cho MVP+)**

**Pros:**
- ✅ Tín hiệu sớm hơn (real-time trong ngày)
- ✅ Catch breakout/reversal nhanh
- ✅ Phù hợp Day Trading
- ✅ Rate limit OK (60/min = 60 stocks mỗi phút)

**Cons:**
- ⚠️ Nhiều noise hơn EOD
- ⚠️ Cần filter false signals
- ⚠️ Rate limit nếu có 100+ stocks

**Use case:**
```
Every hour (9:00, 10:00, 11:00, 13:00, 14:00):
→ Fetch 1H data
→ Calculate indicators
→ Generate signals
→ Push notification to user
→ User có thể act ngay trong ngày
```

---

#### **Option C: 15m / 5m (Advanced)**

**Pros:**
- ✅ Very real-time
- ✅ Scalping opportunities

**Cons:**
- ❌ Too much noise
- ❌ High false signal rate
- ❌ Rate limit issues
- ❌ Need advanced algorithms

**Verdict:** Skip for MVP, consider for v2.0

---

## 🎯 RECOMMENDATION: HYBRID APPROACH

### **MVP Strategy:**

```
EOD (1D) + 1H Intraday
```

**Implementation:**

1. **Morning (8:00):**
   - Fetch EOD data từ hôm trước
   - Generate "Daily Signals" (Swing T+)
   - Display in app

2. **Intraday (Every hour: 10:00, 11:00, 14:00):**
   - Fetch 1H data
   - Generate "Intraday Signals"
   - Push notifications
   - Separate tab: "Tín hiệu trong ngày" 🔔

3. **Benefits:**
   - ✅ Swing traders: Check EOD signals
   - ✅ Day traders: Get hourly updates
   - ✅ Best of both worlds
   - ✅ Rate limit OK (60 stocks/min)

---

## 💾 STORAGE & SCALABILITY

### **Current: 6 stocks**

**EOD (1D):**
```
6 stocks × 1 request/day = 6 requests/day
Rate: 6/60 = 0.1 min = 6 seconds

Storage: Minimal (just latest prices)
No issues ✅
```

**1H Intraday:**
```
6 stocks × 7 hours/day = 42 requests/day
Rate: 42/60 = 0.7 min = 42 seconds

Storage: Still minimal
No issues ✅
```

---

### **Scaling: 30 stocks**

**EOD (1D):**
```
30 stocks × 1 request/day = 30 requests/day
Rate: 30/60 = 0.5 min = 30 seconds

Storage: ~100KB/day
No issues ✅
```

**1H Intraday:**
```
30 stocks × 7 hours/day = 210 requests/day
Rate: 210/60 = 3.5 min total
Per hour: 30 stocks/60 sec = OK ✅

Storage: ~500KB/day
No issues ✅
```

---

### **Scaling: 100 stocks**

**EOD (1D):**
```
100 stocks × 1 request/day = 100 requests/day
Rate: 100/60 = 1.7 min = 102 seconds

Storage: ~300KB/day
No issues ✅
```

**1H Intraday:**
```
100 stocks × 7 hours/day = 700 requests/day
Per hour: 100 stocks need 100 seconds (1.7 min)
Rate limit: 60/min → Need to batch!

Solution:
- Split into 2 batches:
  - Batch 1: 60 stocks (1 min)
  - Batch 2: 40 stocks (40 sec)
- Total: ~2 min/hour

Storage: ~1.5MB/day
Manageable ✅
```

---

### **Storage Solutions:**

#### **Phase 1: Memory (Current) - 0-30 stocks**
```javascript
// Just store latest prices in memory
const prices = {
  'VNM': { price: 87415, time: '14:00' },
  'HPG': { price: 24200, time: '14:00' }
};
```
**Cost:** $0
**Limit:** 30 stocks

---

#### **Phase 2: JSON File - 30-100 stocks**
```javascript
// Store in /data/prices.json
{
  "timestamp": "2025-12-17T14:00:00Z",
  "prices": {
    "VNM": { "price": 87415, "volume": 12900000 },
    ...
  }
}
```
**Cost:** $0
**Limit:** 100 stocks
**Storage:** ~50KB per update

---

#### **Phase 3: Database - 100+ stocks**
```sql
CREATE TABLE stock_prices (
  id UUID PRIMARY KEY,
  code VARCHAR(10),
  price DECIMAL,
  volume BIGINT,
  timeframe VARCHAR(5), -- '1H', '1D'
  timestamp TIMESTAMP,
  INDEX(code, timeframe, timestamp)
);
```

**Database options:**

**Supabase (FREE tier):**
- 500MB storage
- Unlimited API requests
- PostgreSQL
- Cost: $0/month
- Limit: ~500K rows (enough cho 100 stocks × 1 năm)

**Cost scaling:**
```
0-30 stocks:   $0/month (memory)
30-100 stocks: $0/month (JSON or Supabase free)
100-500 stocks: $25/month (Supabase Pro)
500+ stocks:   $100/month (dedicated server)
```

---

## 🚀 IMPLEMENTATION PLAN

### **Phase 1: MVP (NOW) - EOD only**

**Current setup:**
- 6 stocks
- EOD data (1D)
- Swing T+ signals
- VNStock FREE tier

**Code:**
```python
# Current: fetch_vnstock.py
def fetch_eod_data(codes):
    for code in codes:
        stock = Vnstock().stock(symbol=code, source='VCI')
        data = stock.quote.history(
            symbol=code,
            start=yesterday,
            end=today
        )
        yield data
```

**Status:** ✅ Working
**Cost:** $0

---

### **Phase 2: Add 1H Intraday (1-2 tuần)**

**Upgrade:**
- Add 1H data fetching
- New endpoint: `/api/intraday-signals`
- New tab: "Tín hiệu trong ngày"
- Hourly cron job

**Code:**
```python
# New: fetch_intraday.py
def fetch_1h_data(codes):
    for code in codes:
        stock = Vnstock().stock(symbol=code, source='VCI')
        data = stock.quote.intraday(
            symbol=code,
            page_size=7  # Last 7 hours
        )
        yield data
```

**Deployment:**
```javascript
// Netlify Functions (Scheduled)
// Run every hour: 9:00, 10:00, 11:00, 13:00, 14:00

export const handler = schedule("0 9-14 * * 1-5", async () => {
  const signals = await generateIntradaySignals();
  await saveToDatabase(signals);
  await notifyUsers(signals);
});
```

**Cost:** $0 (Netlify free tier)

---

### **Phase 3: Scale to 30 stocks (1 tháng)**

**Upgrade:**
- Expand stock list
- Add JSON file storage
- Optimize rate limiting
- Add caching

**Code:**
```javascript
// Smart batching to respect rate limit
async function fetchWithRateLimit(codes) {
  const batches = chunkArray(codes, 60); // 60/min
  
  for (const batch of batches) {
    const results = await Promise.all(
      batch.map(code => fetchPrice(code))
    );
    await sleep(60000); // Wait 1 min
  }
}
```

**Cost:** $0

---

### **Phase 4: Database + 100+ stocks (3 tháng)**

**Upgrade:**
- Supabase database
- Historical data storage
- Advanced analytics
- API caching layer

**Cost:** $0-25/month

---

## 📊 RATE LIMIT MANAGEMENT

### **Current limit: 60 requests/minute**

**Strategies:**

#### **1. Sequential with delay:**
```javascript
for (const code of codes) {
  await fetchPrice(code);
  await sleep(1000); // 1 sec delay
}
// Max: 60 stocks/min
```

#### **2. Batch processing:**
```javascript
const batches = chunkArray(codes, 60);
for (const batch of batches) {
  await Promise.all(batch.map(fetchPrice));
  await sleep(60000); // Wait 1 min
}
// Max: 60 stocks/min per batch
```

#### **3. Priority queue:**
```javascript
// High priority: User watchlist
// Medium priority: VN30 index
// Low priority: Other stocks

const queue = [
  ...userWatchlist,  // Fetch first
  ...vn30Stocks,     // Fetch second
  ...otherStocks     // Fetch last
];
```

#### **4. Caching:**
```javascript
// Cache for 1 hour
const cache = new Map();

async function fetchWithCache(code) {
  const cached = cache.get(code);
  if (cached && Date.now() - cached.time < 3600000) {
    return cached.data;
  }
  
  const data = await fetchPrice(code);
  cache.set(code, { data, time: Date.now() });
  return data;
}
```

---

## 🎯 REVISED ALGORITHM: 1H SIGNALS

### **Current EOD algorithm:**

```javascript
// Chỉ check 1 lần/ngày sau close
isBuy = (rsi < 45 && macd > 0) || (changePercent > 2%)
```

**Problem:** Tín hiệu chậm, miss opportunities

---

### **New 1H algorithm:**

```javascript
// Check mỗi giờ, more sensitive

// 1H Momentum
const momentum1h = (close1h - open1h) / open1h * 100;
const volume1h_ratio = volume1h / avgVolume1h;

// RSI(14) on 1H data
const rsi1h = calculateRSI(closes_14h);

// Signal rules
const isBuy_1H = (
  // Strong momentum + volume
  (momentum1h > 0.5 && volume1h_ratio > 1.2 && rsi1h < 70) ||
  
  // Breakout
  (close1h > high_24h && volume1h_ratio > 1.5) ||
  
  // Oversold bounce
  (rsi1h < 30 && momentum1h > 0)
);

const isSell_1H = (
  // Weak momentum
  (momentum1h < -0.5 && volume1h_ratio > 1.2) ||
  
  // Overbought
  (rsi1h > 75 && momentum1h < 0)
);
```

**Benefits:**
- ✅ Faster signals (hourly vs daily)
- ✅ Catch intraday reversals
- ✅ Better entry/exit timing

**Challenges:**
- ⚠️ More noise → Need filters
- ⚠️ Higher false signal rate → Add confirmation

---

## 💡 FINAL RECOMMENDATIONS

### **For MVP (Next 2 weeks):**

1. ✅ **Keep EOD (1D) working**
   - Current 6 stocks
   - Swing T+ signals
   - Stable, proven

2. ✅ **Add 1H intraday (New!)**
   - Same 6 stocks
   - Separate tab "Intraday"
   - Hourly updates
   - Push notifications

3. ✅ **Storage: Memory + JSON**
   - No database needed yet
   - Save to `/data/prices.json`
   - Commit to git

4. ✅ **Rate limit: OK**
   - 6 stocks × 7 hours = 42 requests/day
   - Well under 60/min limit

---

### **Scaling path (Next 1-3 months):**

**Month 1:**
- 30 stocks (EOD + 1H)
- JSON storage
- Manual updates

**Month 2:**
- 50 stocks
- Migrate to Supabase (FREE)
- Auto cron jobs

**Month 3:**
- 100 stocks
- Database + caching
- Advanced analytics

---

## ✅ CONCLUSION

**VNStock is PERFECT cho MVP:**

✅ **Data:** Đầy đủ (1m, 5m, 15m, 1H, 1D, 1W)
✅ **Quality:** Chuẩn hoá, ready to use
✅ **Coverage:** All stocks
✅ **Cost:** $0 (FREE tier)
✅ **Rate limit:** 60/min - OK cho 30-60 stocks
✅ **Scalability:** Dễ dàng scale to 100+ stocks

**Next action:**
1. ✅ Test 1H data locally
2. ✅ Implement 1H signals
3. ✅ Deploy MVP+ với intraday
4. ✅ Demo với investors

**Timeline:** 1-2 tuần để implement 1H intraday

---

**VNStock là game-changer! 🚀**
