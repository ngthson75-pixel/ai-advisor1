# ✅ FIXED: backend_api.py

## 🐛 LỖI GỐC

**Vấn đề:** Code deduplication đặt SAI VỊ TRÍ (ngoài function)

**File của bạn:**
```python
# Line 390-485: Function signals_endpoint()
@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    if request.method == 'GET':
        # ... code ...
        return jsonify(...)
        
    elif request.method == 'POST':
        # ... code ...
        return jsonify(...)
        finally:
            session.close()  # Line 485 - KẾT THÚC FUNCTION

# Line 487-505: CODE NÀY Ở NGOÀI FUNCTION! ❌
seen = {}
deduplicated = []
for signal in signals_data:  # ← LỖI: signals_data không tồn tại ở global scope!
    ...
```

**Lý do lỗi:**
- `signals_data` chỉ tồn tại TRONG function GET handler
- Code deduplication chạy ở GLOBAL SCOPE (ngoài function)
- Python không tìm thấy biến `signals_data` → NameError

---

## ✅ ĐÃ SỬA

### **1. Di Chuyển Code Vào Trong Function**

**Trước (SAI):**
```python
def signals_endpoint():
    if request.method == 'GET':
        signals_data = [...]  # Build list
        
        return jsonify({
            'signals': signals_data  # Trả về ngay, CHƯA deduplicate
        })

# Deduplication ở ngoài function ❌
for signal in signals_data:  # ERROR!
    ...
```

**Sau (ĐÚNG):**
```python
def signals_endpoint():
    if request.method == 'GET':
        signals_data = [...]  # Build list
        
        # Deduplication TRONG function ✅
        seen = {}
        deduplicated = []
        for signal in signals_data:  # OK! signals_data có sẵn
            key = f"{signal['ticker']}_{signal['date']}"
            
            if key not in seen:
                seen[key] = signal
                deduplicated.append(signal)
            else:
                if signal['strength'] > seen[key]['strength']:
                    deduplicated.remove(seen[key])
                    seen[key] = signal
                    deduplicated.append(signal)
        
        return jsonify({
            'signals': deduplicated,  # Trả về SAU KHI deduplicate ✅
            'count': len(deduplicated),
            'total_before_dedup': len(signals_data)
        })
```

---

### **2. Thêm Rounding Cho RSI & Risk/Reward**

**Cũng đã fix:**
```python
# Trước:
'risk_reward': s.risk_reward,  # Nhiều số thập phân
'rsi': s.rsi,                   # Nhiều số thập phân

# Sau:
'risk_reward': round(s.risk_reward, 2) if s.risk_reward else None,  # 2.35 ✅
'rsi': round(s.rsi, 1) if s.rsi else None,                          # 45.3 ✅
```

---

### **3. Xóa Code Global Scope**

**Đã xóa hoàn toàn code lines 487-505 (ở ngoài function)**

---

## 📊 CHANGES SUMMARY

### **Price Rounding (GIỮ NGUYÊN - BẠN ĐÃ LÀM ĐÚNG):**
```python
'entry_price': round(s.entry_price / 100) * 100,    # 87,300 VND ✅
'stop_loss': round(s.stop_loss / 100) * 100,        # 84,100 VND ✅
'take_profit': round(s.take_profit / 100) * 100,    # 94,500 VND ✅
```

### **Additional Rounding (THÊM MỚI):**
```python
'risk_reward': round(s.risk_reward, 2) if s.risk_reward else None,  # 2.35 ✅
'rsi': round(s.rsi, 1) if s.rsi else None,                          # 45.3 ✅
```

### **Deduplication (SỬA VỊ TRÍ):**
- ❌ Trước: Ở global scope (line 487-505)
- ✅ Sau: Trong GET handler (line 423-443)

### **Response Changes:**
```python
# Trước:
{
  'signals': signals_data,  # Có duplicates
  'count': len(signals_data)
}

# Sau:
{
  'signals': deduplicated,        # Không duplicates ✅
  'count': len(deduplicated),      # Số lượng sau deduplicate
  'total_before_dedup': len(signals_data)  # Debug info
}
```

---

## 🚀 DEPLOYMENT STEPS

### **STEP 1: Replace File**

```powershell
cd C:\ai-advisor1

# Backup current file
Copy-Item backend_api.py backend_api.py.backup

# Download backend_api_FIXED.py from outputs
# Save as: C:\ai-advisor1\backend_api.py
```

---

### **STEP 2: Test Local**

```powershell
cd C:\ai-advisor1

# Start backend
python backend_api.py

# Should see:
# ✅ SELL signal routes registered
# ✅ OpenAI configured (or warning if not set)
# ✅ Using PostgreSQL... (or SQLite)
# * Running on http://127.0.0.1:10000
```

**If starts OK → Continue!**

---

### **STEP 3: Test API (In Another Terminal)**

```powershell
# Test health
Invoke-WebRequest -Uri "http://localhost:10000/health" -UseBasicParsing

# Test signals
Invoke-WebRequest -Uri "http://localhost:10000/api/signals" -UseBasicParsing | 
    ConvertFrom-Json | 
    Select-Object count, total_before_dedup

# Expected:
# count: 121              ← After deduplication
# total_before_dedup: 147 ← Before deduplication
```

---

### **STEP 4: Verify Response**

```powershell
# Check first signal
Invoke-WebRequest -Uri "http://localhost:10000/api/signals" -UseBasicParsing | 
    ConvertFrom-Json | 
    Select-Object -ExpandProperty signals | 
    Select-Object -First 1

# Should show:
# ticker: VCB
# entry_price: 87300        ← Rounded!
# stop_loss: 84100          ← Rounded!
# take_profit: 94500        ← Rounded!
# risk_reward: 2.35         ← Rounded to 2 decimals!
# rsi: 45.3                 ← Rounded to 1 decimal!
```

---

### **STEP 5: Deploy to Production**

```powershell
cd C:\ai-advisor1

# Check what changed
git diff backend_api.py

# Stage changes
git add backend_api.py

# Commit
git commit -m "fix: Price rounding and deduplication in GET /api/signals"

# Push
git push origin main
```

---

### **STEP 6: Wait for Render Deploy**

```
Monitor: https://dashboard.render.com
Time: 3-5 minutes
```

---

### **STEP 7: Verify Production**

```powershell
# Check API
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals" -UseBasicParsing | 
    ConvertFrom-Json | 
    Select-Object count, total_before_dedup

# Check website
Start-Process "https://ai-advisor.vn"

# Verify:
# 1. Stop Loss prices clean (84,100 not 84,123.45)
# 2. No duplicate tickers per date
# 3. Signal count reduced
```

---

## ✅ VERIFICATION CHECKLIST

**After Local Test:**
- [ ] Backend starts without errors
- [ ] GET /api/signals returns data
- [ ] Prices rounded to 100 VND
- [ ] No duplicate tickers for same date
- [ ] Response has `total_before_dedup` field
- [ ] RSI rounded to 1 decimal
- [ ] Risk/Reward rounded to 2 decimals

**After Production Deploy:**
- [ ] Render deploy successful
- [ ] API returns deduplicated signals
- [ ] Website shows clean prices
- [ ] No duplicate signals visible
- [ ] Users happy! 🎉

---

## 🎯 WHAT WAS FIXED

| Issue | Status |
|-------|--------|
| Code deduplication in wrong place | ✅ Fixed - moved inside function |
| NameError: signals_data not defined | ✅ Fixed - proper scope |
| Price rounding (entry/SL/TP) | ✅ Already correct in your file |
| RSI not rounded | ✅ Added rounding to 1 decimal |
| Risk/Reward not rounded | ✅ Added rounding to 2 decimals |
| No deduplication in response | ✅ Fixed - duplicates removed |
| Missing debug info | ✅ Added total_before_dedup |

---

## 📝 KEY CHANGES IN CODE

**Line 410-420:** Price rounding (you did this correctly!)
**Line 413:** Added `round(s.risk_reward, 2)`
**Line 416:** Added `round(s.rsi, 1)`
**Line 423-443:** Deduplication logic (moved inside function)
**Line 445-450:** Updated return statement

---

## 🚨 WHAT NOT TO DO

**DON'T:**
- ❌ Put code outside functions (global scope)
- ❌ Access function variables from outside function
- ❌ Copy-paste without checking indentation

**DO:**
- ✅ Keep all logic inside appropriate functions
- ✅ Test locally before deploying
- ✅ Check Python syntax errors
- ✅ Verify response structure

---

## 💡 PYTHON SCOPE LESSON

**Why the error happened:**

```python
def my_function():
    my_variable = "Hello"  # Only exists INSIDE function
    return my_variable

print(my_variable)  # ❌ ERROR! Variable doesn't exist here!
```

**Correct way:**

```python
def my_function():
    my_variable = "Hello"
    processed = my_variable.upper()  # Process INSIDE function
    return processed  # Return result

result = my_function()
print(result)  # ✅ OK! Using returned value
```

---

**Created:** 2026-02-04  
**Status:** ✅ Ready to Deploy  
**File:** backend_api_FIXED.py
