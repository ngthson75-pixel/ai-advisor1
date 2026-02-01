# 🚨 EMERGENCY PLAN - TỪNG BƯỚC SIÊU NHỎ

## ❌ VẤN ĐỀ HIỆN TẠI

1. **Backend 500 error** - `/api/portfolio` crash
2. **Frontend nền trắng** - CSS không load
3. **Deploy nhiều thứ cùng lúc** - Khó debug

---

## ✅ GIẢI PHÁP: LÀM TỪNG BƯỚC 1 THAY ĐỔI

### **ROLLBACK TRƯỚC ĐÃ**

```bash
cd C:\ai-advisor1
git revert HEAD --no-edit
git push origin main
```

**Đợi 10 phút để site hoạt động lại bình thường.**

---

## 📋 **BƯỚC 1: CHỈ SỬA TEXT (KHÔNG ĐỔI CODE)**

### **File: AIPortfolioManager_STEP1.jsx**

**THAY ĐỔI DUY NHẤT:**

1. **Title:** "Quản trị Danh mục Đầu tư" → "Quản trị đầu tư bằng AI"
2. **Subtitle:** Thêm dòng mô tả FOMO/HOẢNG SỢ
3. **Placeholders:** 
   - "Mã CK (VD: VCB)" → "Mã chứng khoán (VD: VCB)"
   - "Số lượng" → "Số lượng (VD: 100)"
   - "Giá trung bình" → "Giá mua (VD: 85000)"

**KHÔNG ĐỔI:**
- ❌ Logic
- ❌ Class names
- ❌ Structure
- ❌ Functions
- ❌ Backend calls

**RỦI RO:** 0% - Chỉ sửa text

---

### **Deploy Bước 1:**

```bash
# 1. Download AIPortfolioManager_STEP1.jsx
# 2. Copy vào
C:\ai-advisor1\frontend\src\components\AIPortfolioManager.jsx

# 3. Deploy
cd C:\ai-advisor1
git add frontend/src/components/AIPortfolioManager.jsx
git commit -m "🎨 Step 1: Chỉ sửa text (title, subtitle, placeholders)"
git push origin main

# 4. Đợi 10 phút

# 5. Test
Visit: https://ai-advisor.vn
Check:
✅ Nền ĐEN (như cũ)
✅ Title mới: "Quản trị đầu tư bằng AI"
✅ Subtitle hiện
✅ Placeholder có "(VD: VCB)"
✅ Tất cả chức năng vẫn work
```

**NẾU BƯỚC 1 OK → Tiếp tục Bước 2**
**NẾU BƯỚC 1 FAIL → Rollback và báo lỗi**

---

## 📋 **BƯỚC 2: BACKEND - THÊM ENDPOINT PRICE (SAU KHI BƯỚC 1 OK)**

### **File: backend_api.py**

**THÊM VÀO CUỐI FILE (trước `if __name__`):**

```python
@app.route('/api/stock/current-price', methods=['GET'])
def get_current_price():
    """Get current EOD price"""
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'success': False, 'error': 'Ticker required'}), 400
    
    try:
        from vnstock import Vnstock
        from datetime import datetime, timedelta
        
        stock_api = Vnstock()
        stock = stock_api.stock(symbol=ticker.upper(), source='VCI')
        
        # Try intraday first
        try:
            intraday = stock.quote.intraday(symbol=ticker.upper(), page_size=1)
            if not intraday.empty:
                price = float(intraday['close'].iloc[-1])
                return jsonify({
                    'success': True,
                    'price': price,
                    'source': 'intraday',
                    'ticker': ticker.upper()
                })
        except:
            pass
        
        # Fallback to EOD
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        daily = stock.quote.history(symbol=ticker.upper(), start=yesterday, end=today)
        
        if not daily.empty:
            price = float(daily['close'].iloc[-1])
            return jsonify({
                'success': True,
                'price': price,
                'source': 'eod',
                'ticker': ticker.upper()
            })
        
        return jsonify({
            'success': False,
            'error': f'No price data for {ticker}'
        }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### **Deploy Bước 2:**

```bash
cd C:\ai-advisor1
git add backend_api.py
git commit -m "🔧 Step 2: Thêm endpoint /api/stock/current-price"
git push origin main

# Đợi 5 phút (Render deploy)

# Test backend
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/stock/current-price?ticker=VCB

# Expected: {"success":true,"price":96500,...}
```

**NẾU BƯỚC 2 OK → Tiếp tục Bước 3**

---

## 📋 **BƯỚC 3: FRONTEND - AUTO-FETCH PRICE (SAU KHI BƯỚC 2 OK)**

### **Modifications:**

CHỈ THÊM 2 FUNCTIONS VÀ SỬA 1 FUNCTION:

```jsx
// ✅ THÊM FUNCTION NÀY (sau line ~60)
const fetchCurrentPrice = async (ticker) => {
  try {
    const response = await fetch(`${API_BASE}/stock/current-price?ticker=${ticker}`);
    const data = await response.json();
    return data.success ? data.price : null;
  } catch (error) {
    console.error('Error fetching price:', error);
    return null;
  }
};

// ✅ SỬA FUNCTION handleAddStock (line ~70)
const handleAddStock = async (e) => {
  e.preventDefault();
  
  if (!newStock.ticker || !newStock.quantity || !newStock.price) {
    alert('Vui lòng điền đầy đủ thông tin');
    return;
  }

  setIsLoading(true); // ✅ THÊM

  try {
    // ✅ THÊM: Fetch current price
    const currentPrice = await fetchCurrentPrice(newStock.ticker.toUpperCase());
    
    const response = await fetch(`${API_BASE}/portfolio`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        ticker: newStock.ticker.toUpperCase(),
        quantity: parseInt(newStock.quantity),
        price: parseFloat(newStock.price),
        current_price: currentPrice || parseFloat(newStock.price) // ✅ THÊM
      })
    });

    const data = await response.json();
    
    if (data.success) {
      fetchPortfolio();
      setNewStock({ ticker: '', quantity: '', price: '' });
      
      // ✅ THÊM: Alert về giá
      if (currentPrice) {
        alert(`✅ Đã thêm ${newStock.ticker.toUpperCase()}!\nGiá hiện tại: ${currentPrice.toLocaleString()} VND`);
      }
    } else {
      alert('Error: ' + data.error);
    }
  } catch (error) {
    console.error('Error adding stock:', error);
    alert('Lỗi khi thêm cổ phiếu');
  } finally {
    setIsLoading(false); // ✅ THÊM
  }
};
```

### **Deploy Bước 3:**

```bash
cd C:\ai-advisor1
git add frontend/src/components/AIPortfolioManager.jsx
git commit -m "✨ Step 3: Thêm auto-fetch price khi add stock"
git push origin main
```

**Test:**
1. Nhập VCB, 100, 85000
2. Click Thêm
3. Should see alert: "Đã thêm VCB! Giá hiện tại: XX,XXX VND"

---

## 📋 **BƯỚC 4: HIỂN THỊ P/L (SAU KHI BƯỚC 3 OK)**

Cuối cùng mới thêm P/L display...

---

## 🎯 **TẠI SAO PHẢI LÀM TỪNG BƯỚC?**

### **Lợi ích:**
1. ✅ Dễ debug - Biết chính xác bước nào lỗi
2. ✅ An toàn - Rollback nhanh nếu fail
3. ✅ Tự tin - Mỗi bước test kỹ
4. ✅ Học được - Hiểu rõ từng thay đổi

### **So sánh:**

**Cách CŨ (FAIL):**
```
Deploy tất cả → FAIL → Không biết lỗi ở đâu → Rollback toàn bộ
```

**Cách MỚI (SUCCESS):**
```
Bước 1 → TEST → OK ✅
Bước 2 → TEST → OK ✅
Bước 3 → TEST → OK ✅
Bước 4 → TEST → OK ✅
→ DONE! 🎉
```

---

## 🚀 **BẮT ĐẦU NGAY**

### **1. Rollback về bản cũ:**
```bash
cd C:\ai-advisor1
git revert HEAD --no-edit
git push origin main
```

### **2. Sau khi site hoạt động, deploy Bước 1:**
- Download: **AIPortfolioManager_STEP1.jsx**
- Copy vào project
- Push
- Test
- ✅ OK → Tiếp tục Bước 2

---

**Chúng ta sẽ làm CHẬM nhưng CHẮC! 🐢🎯**
