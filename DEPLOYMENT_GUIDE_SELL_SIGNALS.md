# DEPLOYMENT GUIDE - SELL SIGNALS WITH EXIT REASON

## 📋 OVERVIEW

Thêm column "Lý do bán" vào bảng tín hiệu BÁN để nhà đầu tư biết rõ:
- 🔴 **Cắt lỗ (Stop Loss)** - Giá chạm stop loss
- 🟢 **Chốt lời (Take Profit)** - Giá chạm take profit

---

## 🚀 DEPLOYMENT STEPS

### BƯỚC 1: Update Backend API

**File: `backend_api.py`**

Ensure API endpoint `/api/signals` trả về field `strategy`:

```python
@app.route('/api/signals', methods=['GET'])
def get_signals():
    action = request.args.get('action')  # 'BUY' or 'SELL'
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if action:
                query = """
                    SELECT 
                        ticker, strategy, entry_price, stop_loss, 
                        take_profit, date, action, created_at
                    FROM signals
                    WHERE action = %s
                    ORDER BY created_at DESC
                """
                cur.execute(query, (action,))
            else:
                query = """
                    SELECT 
                        ticker, strategy, entry_price, stop_loss, 
                        take_profit, date, action, created_at
                    FROM signals
                    ORDER BY created_at DESC
                """
                cur.execute(query)
            
            rows = cur.fetchall()
            
            signals = []
            for row in rows:
                signals.append({
                    'ticker': row[0],
                    'strategy': row[1],        # ← IMPORTANT: Include strategy!
                    'entry_price': float(row[2]) if row[2] else None,
                    'stop_loss': float(row[3]) if row[3] else None,
                    'take_profit': float(row[4]) if row[4] else None,
                    'date': row[5].isoformat() if row[5] else None,
                    'action': row[6],
                    'created_at': row[7].isoformat() if row[7] else None
                })
            
            return jsonify({
                'success': True,
                'count': len(signals),
                'signals': signals
            }), 200
```

**Test backend:**

```bash
# 1. Restart backend
python backend_api.py

# 2. Test API
curl http://localhost:10000/api/signals?action=SELL | jq '.'

# Expected response:
{
  "success": true,
  "count": 13,
  "signals": [
    {
      "ticker": "VCB",
      "strategy": "TAKE_PROFIT",  ← Check field này có
      "entry_price": 85000,
      "stop_loss": 80000,
      "take_profit": 92000,
      ...
    }
  ]
}
```

---

### BƯỚC 2: Update Frontend Component

**Option A: React với Tailwind CSS**

1. Copy file `SellSignalsTable.jsx` vào project:

```bash
# Trong frontend folder
cp SellSignalsTable.jsx src/components/
```

2. Import và sử dụng:

```jsx
// src/pages/Signals.jsx hoặc tương tự
import SellSignalsTable from '../components/SellSignalsTable';

function SignalsPage() {
  return (
    <div>
      <h1>Tín hiệu Đầu tư</h1>
      
      {/* BUY signals */}
      <BuySignalsTable />
      
      {/* SELL signals - NEW */}
      <SellSignalsTable />
    </div>
  );
}
```

**Option B: React không có Tailwind**

1. Copy cả 2 files:

```bash
cp SellSignalsTable.jsx src/components/
cp sell-signals.css src/styles/
```

2. Import CSS:

```jsx
// src/components/SellSignalsTable.jsx
import '../styles/sell-signals.css';

// ... rest of component
```

3. Thay Tailwind classes bằng CSS classes:

```jsx
// Replace:
className="bg-red-50 text-red-700 border-red-200"

// With:
className="exit-reason-stop-loss"
```

**Option C: Mobile-responsive (Card + Table)**

```bash
cp SellSignalCard.jsx src/components/
```

```jsx
import SellSignalsResponsive from '../components/SellSignalCard';

<SellSignalsResponsive />
```

---

### BƯỚC 3: Test Frontend

```bash
# 1. Install dependencies (if needed)
npm install

# 2. Run dev server
npm run dev

# 3. Open browser
http://localhost:5173
```

**Kiểm tra:**
- ✅ Table hiển thị đúng
- ✅ Column "Lý do bán" xuất hiện
- ✅ 🔴 Cắt lỗ (SL) - màu đỏ
- ✅ 🟢 Chốt lời (TP) - màu xanh
- ✅ P/L tính đúng
- ✅ Responsive trên mobile

---

### BƯỚC 4: Deploy to Production

**Frontend (Cloudflare Pages):**

```bash
# 1. Build
npm run build

# 2. Commit
git add .
git commit -m "feat: Add exit reason column to SELL signals"
git push

# 3. Cloudflare Pages auto-deploy
# Check: https://ai-advisor.vn
```

**Backend (Render):**

```bash
# 1. Commit backend changes
git add backend_api.py
git commit -m "fix: Ensure strategy field in API response"
git push

# 2. Render auto-deploy
# Check: https://ai-advisor1-backend.onrender.com/api/signals?action=SELL
```

---

## 🧪 TESTING CHECKLIST

### Backend Tests

```bash
# Test 1: Get all SELL signals
curl "https://ai-advisor1-backend.onrender.com/api/signals?action=SELL" | jq '.'

# Test 2: Verify strategy field
curl "https://ai-advisor1-backend.onrender.com/api/signals?action=SELL" | jq '.signals[0].strategy'
# Expected: "STOP_LOSS" or "TAKE_PROFIT"

# Test 3: Count by strategy
curl "https://ai-advisor1-backend.onrender.com/api/signals?action=SELL" | jq '[.signals[].strategy] | group_by(.) | map({strategy: .[0], count: length})'
# Expected: [{"strategy":"STOP_LOSS","count":5}, {"strategy":"TAKE_PROFIT","count":8}]
```

### Frontend Tests

**Desktop:**
- [ ] Table loads correctly
- [ ] "Lý do bán" column visible
- [ ] Stop Loss shows 🔴 red badge
- [ ] Take Profit shows 🟢 green badge
- [ ] P/L calculated correctly
- [ ] Hover effects work
- [ ] Footer statistics correct

**Mobile:**
- [ ] Cards display (not table)
- [ ] Exit reason badge visible
- [ ] All data readable
- [ ] Responsive layout works
- [ ] Statistics footer shows

**Edge Cases:**
- [ ] Empty state (no signals)
- [ ] Loading state
- [ ] Error state
- [ ] Large numbers of signals

---

## 🎨 CUSTOMIZATION

### Change Colors

**Tailwind version:**

```jsx
// Change Stop Loss color from red to orange
const reasons = {
  'STOP_LOSS': {
    bgColor: 'bg-orange-50',      // was bg-red-50
    textColor: 'text-orange-700',  // was text-red-700
    borderColor: 'border-orange-200' // was border-red-200
  }
}
```

**CSS version:**

```css
/* sell-signals.css */
.exit-reason-stop-loss {
  background-color: #fff7ed;  /* orange-50 */
  color: #c2410c;             /* orange-700 */
  border-color: #fed7aa;      /* orange-200 */
}
```

### Change Text

```jsx
// Vietnamese → English
const reasons = {
  'STOP_LOSS': {
    text: 'Stop Loss',      // was 'Cắt lỗ (SL)'
    icon: '🔴'
  },
  'TAKE_PROFIT': {
    text: 'Take Profit',    // was 'Chốt lời (TP)'
    icon: '🟢'
  }
}
```

### Add New Exit Reasons

```jsx
// Add MA20 break reason
const reasons = {
  'STOP_LOSS': { ... },
  'TAKE_PROFIT': { ... },
  'MA20_BREAK': {
    text: 'Phá MA20',
    icon: '🟡',
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-700',
    borderColor: 'border-yellow-200'
  }
}
```

---

## 🐛 TROUBLESHOOTING

### Issue: Exit reason không hiển thị

**Cause:** Backend không trả về field `strategy`

**Fix:**
```bash
# Check API response
curl "YOUR_BACKEND_URL/api/signals?action=SELL" | jq '.signals[0]'

# If strategy missing, update backend query to include it
```

### Issue: Tất cả signals đều hiển thị "Khác"

**Cause:** Strategy value không match 'STOP_LOSS' hoặc 'TAKE_PROFIT'

**Fix:**
```bash
# Check actual strategy values
curl "YOUR_BACKEND_URL/api/signals?action=SELL" | jq '[.signals[].strategy] | unique'

# Update mapping in component to match actual values
```

### Issue: P/L tính sai

**Cause:** Đang dùng `stop_loss` thay vì `exit_price`

**Fix:** Add `exit_price` column to database:

```sql
ALTER TABLE signals ADD COLUMN exit_price NUMERIC(10, 2);
```

Update scanner to save exit_price:

```python
# test_sell_scanner_final.py
def save_sell_signals(engine, sell_signals):
    insert_query = text("""
        INSERT INTO signals (
            ticker, strategy, entry_price, exit_price, 
            stop_loss, take_profit, date, action
        ) VALUES (
            :ticker, :strategy, :entry_price, :exit_price,
            :stop_loss, :take_profit, :date, 'SELL'
        )
    """)
    
    for signal in sell_signals:
        conn.execute(insert_query, {
            'ticker': signal['ticker'],
            'strategy': signal['sell_reason'],
            'entry_price': signal['entry_price'],
            'exit_price': signal['exit_price'],  # ← Add this
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'date': signal['date']
        })
```

### Issue: Mobile layout không responsive

**Cause:** Missing responsive classes

**Fix:** Use `SellSignalsResponsive` component thay vì `SellSignalsTable`:

```jsx
import SellSignalsResponsive from './SellSignalCard';
<SellSignalsResponsive />
```

---

## 📊 EXPECTED RESULT

After deployment, SELL signals table should look like:

```
╔══════════════════════════════════════════════════════════════════════╗
║                         TÍN HIỆU BÁN                                 ║
║                    13 tín hiệu • Cập nhật: 05/02/2026                ║
╠══════╦═══════════╦═══════════╦═══════════════╦══════════════╦═══════╣
║ Mã CP║ Giá vào   ║ Giá ra    ║ Lãi/Lỗ        ║ Lý do bán    ║ Ngày  ║
╠══════╬═══════════╬═══════════╬═══════════════╬══════════════╬═══════╣
║ VCB  ║ 85,000    ║ 92,000    ║ +7,000 (+8.2%)║🟢 Chốt lời  ║05/02  ║
║ HPG  ║ 26,500    ║ 25,000    ║ -1,500 (-5.7%)║🔴 Cắt lỗ    ║05/02  ║
║ MWG  ║ 85,000    ║ 90,000    ║ +5,000 (+5.9%)║🟢 Chốt lời  ║05/02  ║
╠══════╩═══════════╩═══════════╩═══════════════╩══════════════╩═══════╣
║ Thống kê:    13 Tổng    |    5 Cắt lỗ    |    8 Chốt lời         ║
╚══════════════════════════════════════════════════════════════════════╝
```

**User benefits:**
✅ Nhìn ngay biết lý do bán
✅ Màu sắc phân biệt rõ: 🔴 Loss vs 🟢 Profit
✅ Không bối rối giữa SL và TP
✅ Dễ đọc trên cả desktop và mobile

---

## 📞 SUPPORT

Need help? Check:
1. Browser console for errors
2. Network tab for API responses
3. Backend logs in Render dashboard

---

## 🔄 FUTURE ENHANCEMENTS

- [ ] Add filter: Show only Stop Loss or Take Profit
- [ ] Export to CSV/Excel
- [ ] Email notifications when signals trigger
- [ ] Chart view of P/L over time
- [ ] Compare actual exit vs predicted exit
