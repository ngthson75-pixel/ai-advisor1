# 🚨 PRICE DATA ISSUE - TROUBLESHOOTING GUIDE

## 🔍 VẤN ĐỀ PHÁT HIỆN

Từ kết quả verify_signals.py:

```
TCB - PULLBACK
  DB: 36,650 VND        ← Giá ĐÚNG (production database)
  Manual: 36 VND        ← Giá SAI (manual calculation)
  Diff: 102,705%        ← Sai 1000 lần!
```

**Nguyên nhân:** vnstock API trả về giá theo đơn vị **NGHÌN VND** (thousands VND), không phải VND!

---

## 🎯 ROOT CAUSE

### **vnstock 3.3.1 Behavior:**

```python
quote = Quote(symbol='TCB', source='VCI')
df = quote.history(...)

# df['close'] trả về: 36.65 (= 36,650 VND ÷ 1000)
# Không phải: 36,650 VND
```

**ĐƠN VỊ:** Giá được trả về theo **NGHÌN VND**
- 36.65 = 36,650 VND
- 140 = 140,000 VND  
- 26.2 = 26,200 VND

---

## 🔧 FIX NGAY

### **STEP 1: Verify vấn đề**

```bash
cd C:\ai-advisor1\scripts
python debug_vnstock_price.py
```

**Output mẫu:**
```
Testing: TCB
✅ Got 100 bars
Raw close value: 36.65
In VND: 37 VND                      ← SAI
In thousands VND: 36,650 VND        ← ĐÚNG

Expected price: ~36,000 VND
If raw = VND: Difference: 35,963 VND
If raw = thousands VND: Difference: 650 VND

✅ Likely: Raw value is in THOUSANDS VND (need × 1000)
```

### **STEP 2: Fix verify_signals.py**

**Thêm conversion × 1000 sau khi download data:**

```python
def download_eod_data(self, ticker, days=100):
    """Download EOD data"""
    try:
        end_date = self.get_last_trading_day()
        start_date = (datetime.strptime(end_date, '%Y-%m-%d') - 
                     timedelta(days=days*2)).strftime('%Y-%m-%d')
        
        quote = Quote(symbol=ticker, source='VCI')
        df = quote.history(start=start_date, end=end_date)
        
        if df is None or len(df) == 0:
            return None
        
        # Process
        mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        for old, new in mapping.items():
            if old in df.columns:
                df = df.rename(columns={old: new})
        
        # 🔧 FIX: Convert from thousands VND to VND
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = df[col] * 1000  # ← THÊM DÒNG NÀY
        
        if 'Open' not in df.columns:
            df['Open'] = df['Close'].shift(1)
        
        df = df.sort_index()
        df = df.dropna()
        
        return df if len(df) >= 50 else None
        
    except Exception as e:
        print(f"⚠️  Error downloading {ticker}: {e}")
        return None
```

### **STEP 3: Fix manual_test_signals.py**

**Cùng cách - thêm conversion × 1000:**

```python
def process_dataframe(self, df, ticker):
    """Process dataframe (EXACT same as scanner)"""
    try:
        # Rename columns
        mapping = {
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        for old, new in mapping.items():
            if old in df.columns:
                df = df.rename(columns={old: new})
        
        # 🔧 FIX: Convert from thousands VND to VND
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = df[col] * 1000  # ← THÊM DÒNG NÀY
        
        # Check required columns
        required = ['Close', 'High', 'Low', 'Volume']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return None
        
        # Add Open if missing
        if 'Open' not in df.columns:
            df['Open'] = df['Close'].shift(1)
        
        df = df.sort_index()
        df = df.dropna()
        
        if len(df) < 50:
            print(f"❌ Not enough data: {len(df)} bars")
            return None
        
        return df
        
    except Exception as e:
        print(f"❌ Process error: {e}")
        return None
```

---

## 🧪 TEST SAU KHI FIX

### **Test 1: Debug script**

```bash
python debug_vnstock_price.py
```

**Expected:** Xác nhận giá theo thousands VND

### **Test 2: Manual test**

```bash
python manual_test_signals.py
# Option 1: TCB

# Should see:
# Close: 36,650 VND (not 36 VND)
# EMA20: ~35,000 VND (not 35 VND)
```

### **Test 3: Verify again**

```bash
python verify_signals.py
# Option 2: PRODUCTION

# Should see:
# TCB - PULLBACK
#   DB: 36,650
#   Manual: 36,650
#   Diff: 0.00% ✅
```

---

## 📋 CHECKLIST

**Before fix:**
- [ ] Run debug_vnstock_price.py
- [ ] Confirm prices in thousands VND
- [ ] Backup files

**Fix files:**
- [ ] Update verify_signals.py (add × 1000)
- [ ] Update manual_test_signals.py (add × 1000)
- [ ] Update daily_signal_scanner_eod.py nếu cần

**After fix:**
- [ ] Test manual_test_signals.py
- [ ] Test verify_signals.py
- [ ] Accuracy should be >90%
- [ ] Commit changes to git

---

## ⚠️ IMPORTANT NOTES

### **1. vnstock Version Differences**

```
vnstock 3.3.1: Returns thousands VND (need × 1000)
vnstock 3.4.0: Might be different (check docs)
```

**Current version:** 3.3.1 (user's output)

### **2. Source Differences**

```python
source='VCI':  Returns thousands VND
source='TCBS': Might be different
source='SSI':  Might be different
```

**Stick with VCI** for consistency.

### **3. Production Scanner**

**Check if production scanner cũng có issue:**

```python
# In daily_signal_scanner_eod.py
# Cần có dòng này:
df[col] = df[col] * 1000  # Convert to VND
```

Nếu không có → Scanner CŨNG BỊ SAI!

---

## 🔍 DEBUG WORKFLOW

```
1. Run debug script
   → Confirm unit issue
   
2. Fix verify_signals.py
   → Add × 1000 conversion
   
3. Fix manual_test_signals.py
   → Add × 1000 conversion
   
4. Test manual test
   → Should show correct prices
   
5. Verify against production
   → Accuracy should be >90%
   
6. Check production scanner
   → Make sure it also converts
   
7. Commit fixes
   → Update all files
```

---

## 📞 NEXT STEPS

1. **NGAY BÂY GIỜ:**
   ```bash
   python debug_vnstock_price.py
   ```

2. **SAU KHI CONFIRM:**
   - Fix verify_signals.py
   - Fix manual_test_signals.py
   - Test lại

3. **CHECK PRODUCTION:**
   - Scanner có convert × 1000 chưa?
   - Nếu chưa → Database có giá SAI!
   - Cần re-run scanner

---

**Status:** CRITICAL BUG - FIX IMMEDIATELY  
**Impact:** All manual tests giving wrong results  
**Priority:** P0 - Highest
