# 📊 HƯỚNG DẪN CẬP NHẬT LỊCH SỬ KHUYẾN NGHỊ

## 🎯 OVERVIEW

"Lịch sử khuyến nghị" tự động cập nhật P/L cho các mã đang giữ mỗi khi user load trang hoặc click "Làm mới tín hiệu".

---

## 🔄 AUTO-UPDATE MECHANISM

### **Cách hoạt động:**

1. **User load page** → Call API `/api/history`
2. **API fetch data:**
   - Load history từ database/JSON
   - Với mã "đang giữ" → Fetch giá hiện tại từ VNStock
   - Calculate P/L real-time
3. **Frontend render:**
   - Hiển thị P/L updated
   - Color coding (xanh/đỏ)
   - Summary statistics auto-calculate

### **Flow diagram:**

```
User load page
    ↓
GET /api/history
    ↓
For each "holding" stock:
    ↓
Fetch current price từ VNStock
    ↓
Calculate P/L = (currentPrice - buyPrice) / buyPrice * 100
    ↓
Return updated data
    ↓
Frontend render
```

---

## 💾 DATA SOURCE

### **File:** `/pages/api/history.ts`

```typescript
const history: HoldingStock[] = [
  {
    buyDate: '01/12/2025',
    code: 'SAB',
    signalType: 'Swing T+',
    score: 70,
    buyPrice: 48700,
    status: 'closed'  // Đã chốt → Không update
  },
  {
    buyDate: '04/12/2025',
    code: 'HAG',
    signalType: 'Swing T+',
    score: 60,
    buyPrice: 18400,
    status: 'holding'  // Đang giữ → Auto-update P/L
  }
];
```

---

## ✏️ CÁCH CẬP NHẬT DATA

### **Option 1: Manual Update (Simple)**

**File:** `/pages/api/history.ts`

**Thêm khuyến nghị mới:**
```typescript
const history: HoldingStock[] = [
  // ... existing records
  {
    buyDate: '17/12/2025',      // dd/mm/yyyy
    code: 'MSN',                // Mã CP
    signalType: 'Swing T+',     // Loại tín hiệu
    score: 75,                  // Score từ AI
    buyPrice: 98500,            // Giá mua
    status: 'holding'           // 'holding' hoặc 'closed'
  }
];
```

**Chốt lời/lỗ:**
```typescript
{
  buyDate: '04/12/2025',
  code: 'HAG',
  signalType: 'Swing T+',
  score: 60,
  buyPrice: 18400,
  sellDate: '17/12/2025',    // Thêm ngày bán
  sellPrice: 19100,          // Thêm giá bán
  profitPercent: 3.8,        // Calculate manual
  holdDays: 13,              // Số ngày giữ
  status: 'closed'           // Đổi thành 'closed'
}
```

**Deploy:**
```powershell
git add pages/api/history.ts
git commit -m "Update: Add MSN signal, close HAG"
git push origin main
```

Netlify auto-deploy → Live sau 2-3 phút

---

### **Option 2: JSON File (Recommended)**

**Better approach:** Store trong JSON file

**File:** `/data/history.json`

```json
[
  {
    "buyDate": "01/12/2025",
    "code": "SAB",
    "signalType": "Swing T+",
    "score": 70,
    "buyPrice": 48700,
    "sellDate": "10/12/2025",
    "sellPrice": 51700,
    "profitPercent": 6.16,
    "holdDays": 10,
    "status": "closed"
  },
  {
    "buyDate": "04/12/2025",
    "code": "HAG",
    "signalType": "Swing T+",
    "score": 60,
    "buyPrice": 18400,
    "status": "holding"
  }
]
```

**Update API to read from JSON:**
```typescript
import historyData from '../../data/history.json';

export default async function handler(req, res) {
  const history = historyData;
  
  // Update P/L for holding stocks
  for (const stock of history) {
    if (stock.status === 'holding') {
      const currentPrice = await fetchPrice(stock.code);
      stock.profitPercent = (currentPrice - stock.buyPrice) / stock.buyPrice * 100;
    }
  }
  
  res.json({ success: true, history });
}
```

**Benefits:**
- ✅ Easier to update (just edit JSON)
- ✅ No code changes needed
- ✅ Can integrate với admin panel later

---

### **Option 3: Database (Production)**

**When scaling:**

**Setup Supabase/Firebase:**
```sql
CREATE TABLE recommendation_history (
  id UUID PRIMARY KEY,
  buy_date DATE,
  code VARCHAR(10),
  signal_type VARCHAR(50),
  score INT,
  buy_price DECIMAL,
  sell_date DATE,
  sell_price DECIMAL,
  status VARCHAR(20),
  created_at TIMESTAMP
);
```

**API fetch:**
```typescript
import { supabase } from '../../lib/supabase';

export default async function handler(req, res) {
  const { data: history } = await supabase
    .from('recommendation_history')
    .select('*')
    .order('buy_date', { ascending: false });
  
  // Update P/L for holding
  for (const stock of history) {
    if (stock.status === 'holding') {
      const currentPrice = await fetchPrice(stock.code);
      stock.profitPercent = calculateProfit(currentPrice, stock.buy_price);
    }
  }
  
  res.json({ success: true, history });
}
```

---

## 📊 P/L AUTO-UPDATE

### **Current Price Fetching:**

```typescript
// Try VNStock API first
async function fetchCurrentPrice(code: string): Promise<number> {
  try {
    const data = await callVNStock(code);
    return data.price;
  } catch (error) {
    // Fallback to mock
    return MOCK_PRICES[code] || 0;
  }
}
```

### **Mock Prices (Fallback):**

```typescript
const MOCK_CURRENT_PRICES = {
  'HAG': 18032,   // -2.0% từ 18400
  'BMP': 173250,  // +5.0% từ 165000
  'VNM': 63342,   // +3.5% từ 61200
};
```

**Update mock prices:** Edit file khi giá thay đổi nhiều

---

## 🔄 UPDATE FREQUENCY

### **Automatic:**
- ✅ Mỗi khi user load page
- ✅ Mỗi khi click "Làm mới tín hiệu"
- ✅ Real-time calculation

### **Manual (for closed positions):**
- Khi chốt lời/lỗ → Edit file manually
- Push to GitHub → Auto-deploy

---

## 📱 USER VIEW

### **"Đang giữ" rows:**
```
Code: VNM
Buy: 61,200
Status: [Đang giữ] (yellow badge)
P/L: +3.5% (green, auto-updated)
```

### **"Đã chốt" rows:**
```
Code: SAB
Buy: 48,700
Sell: 51,700
P/L: +6.16% (green, fixed)
Days: 10
```

### **Summary auto-calculate:**
```
Tổng lệnh: 5
Đã chốt: 2
Đang giữ: 3
Win rate: 100% (2/2 thắng)
Avg P/L: +3.55%
```

---

## ✅ DAILY UPDATE WORKFLOW

### **Mỗi ngày:**

1. **Check giá hiện tại:**
   - Vào vietstock.vn
   - Check giá các mã đang giữ

2. **Nếu chốt lời/lỗ:**
   ```typescript
   // Edit /pages/api/history.ts
   {
     code: 'HAG',
     sellDate: '17/12/2025',
     sellPrice: 19100,
     profitPercent: 3.8,
     holdDays: 13,
     status: 'closed'  // Change to closed
   }
   ```

3. **Nếu có tín hiệu mới:**
   ```typescript
   // Add to array
   {
     buyDate: '17/12/2025',
     code: 'MSN',
     signalType: 'Swing T+',
     score: 78,
     buyPrice: 98500,
     status: 'holding'
   }
   ```

4. **Deploy:**
   ```powershell
   git add .
   git commit -m "Update history: Close HAG, Add MSN"
   git push origin main
   ```

5. **Verify:**
   - Wait 2-3 phút
   - Check https://ai-advisor11.netlify.app
   - Scroll to "Lịch sử khuyến nghị"
   - Verify data updated

---

## 🎯 BEST PRACTICES

### **Data entry:**
- ✅ Format date: dd/mm/yyyy
- ✅ Format price: Number (không dấu phẩy)
- ✅ Calculate P/L accurate (2 decimals)
- ✅ Update ngay khi có thay đổi

### **Git commits:**
```bash
git commit -m "History: Close SAB (+6.16%), Add VNM"
git commit -m "History: Update P/L for holding stocks"
git commit -m "History: Close BMP (+5.0%), Close VNM (+3.5%)"
```

### **Testing:**
- ✅ Test local trước: `npm run dev`
- ✅ Verify calculations
- ✅ Check responsive UI
- ✅ Deploy to production

---

## 📊 MONITORING

### **Track metrics:**
```
Win rate: X/Y thắng (Z%)
Avg P/L: +A%
Max profit: +B%
Max loss: -C%
Avg hold days: D days
```

### **Use for:**
- ✅ Demo với investors
- ✅ Algorithm improvement
- ✅ Marketing materials
- ✅ User trust building

---

## 🚀 FUTURE IMPROVEMENTS

### **Phase 1:** (Current)
- ✅ Manual update trong code
- ✅ Auto P/L calculation
- ✅ Professional UI

### **Phase 2:** (1-2 tuần)
- 📊 Move to JSON file
- 📈 Chart visualization
- 📧 Email notifications

### **Phase 3:** (1-2 tháng)
- 💾 Database integration
- 🎨 Admin panel
- 📱 Mobile app sync
- 🤖 Auto trading signals

---

## 💡 QUICK REFERENCE

### **Add new signal:**
```typescript
{ buyDate: '17/12/2025', code: 'MSN', signalType: 'Swing T+', score: 75, buyPrice: 98500, status: 'holding' }
```

### **Close position:**
```typescript
{ ...existing, sellDate: '17/12/2025', sellPrice: 19100, profitPercent: 3.8, holdDays: 13, status: 'closed' }
```

### **Deploy:**
```bash
git add . && git commit -m "Update history" && git push
```

### **Test:**
```
npm run dev → http://localhost:3000 → Scroll to "Lịch sử khuyến nghị"
```

---

## ✅ CHECKLIST

- [ ] Understand auto-update mechanism
- [ ] Know where to edit data (`/pages/api/history.ts`)
- [ ] Format dates correctly (dd/mm/yyyy)
- [ ] Calculate P/L accurate
- [ ] Test local before deploy
- [ ] Push to GitHub
- [ ] Verify on production
- [ ] Monitor metrics daily

---

**Mỗi ngày chỉ cần 5-10 phút để update! 📊✨**
