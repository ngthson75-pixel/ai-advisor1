# 🔍 SIGNAL VERIFICATION - QUICK GUIDE

## 📋 MỤC ĐÍCH

**File `verify_signals.py`** dùng để **verify tín hiệu trong database** (staging hoặc production) có đúng với tính toán thủ công không.

**Use case:**
- ✅ Kiểm tra scanner có chạy đúng không
- ✅ Verify signals trên staging trước khi deploy production
- ✅ Debug khi có bug report từ users
- ✅ Quality assurance định kỳ

---

## 🚀 QUICK START

### **Bước 1: Cài đặt**

```bash
pip install vnstock pandas requests --break-system-packages
```

### **Bước 2: Chạy**

```bash
cd C:\ai-advisor1\scripts
python verify_signals.py
```

### **Bước 3: Chọn environment**

```
Select environment to verify:
1. STAGING (ai-advisor1-staging.onrender.com)
2. PRODUCTION (ai-advisor1-backend.onrender.com)
3. Exit

Enter choice (1-3): 1
```

---

## 📊 OUTPUT MẪU

### **STAGING Verification:**

```
==================================================================
🔍 SIGNAL VERIFIER - STAGING
==================================================================
API: https://ai-advisor1-staging.onrender.com/api

📥 Fetching signals from STAGING database...
✅ Found 8 signals in database

==================================================================
🔍 VERIFYING 8 SIGNALS
==================================================================

──────────────────────────────────────────────────────────────────
Checking VCB...
  DB signals: 1
  Manual signals: 1
  ✅ PULLBACK: MATCH (diff: 0.00%)

──────────────────────────────────────────────────────────────────
Checking VHM...
  DB signals: 1
  Manual signals: 1
  ✅ EMA_CROSS: MATCH (diff: 0.00%)

──────────────────────────────────────────────────────────────────
Checking HPG...
  DB signals: 1
  Manual signals: 0
  ❌ PULLBACK: In DB but NOT in manual calculation

==================================================================
📊 VERIFICATION SUMMARY
==================================================================

Tickers checked: 5
Matching signals: 7
Discrepancies: 0
Missing in DB: 1
Extra in DB: 1

✅ Accuracy: 87.5%

⚠️  EXTRA IN DATABASE (false positives?):
   HPG - PULLBACK
      DB entry: 32,500

⚠️  MISSING IN DATABASE:
   TCB - EMA_CROSS
      Manual entry: 28,300
```

---

## 🎯 WORKFLOW

### **1. Query Database**
```
📥 Fetching signals from STAGING/PRODUCTION...
```
- Get tất cả signals từ database
- Via API endpoint `/api/signals`

### **2. Recalculate Manually**
```
Checking VCB...
```
- Download EOD data từ vnstock
- Tính EMA(20), EMA(50), RSI(14)
- Check điều kiện PULLBACK và EMA_CROSS

### **3. Compare**
```
✅ PULLBACK: MATCH
❌ PULLBACK: In DB but NOT in manual
⚠️  EMA_CROSS: DISCREPANCY (diff: 2.5%)
```

### **4. Report**
```
📊 VERIFICATION SUMMARY
```
- Accuracy %
- Discrepancies details
- Missing/Extra signals

---

## 📈 INTERPRETATION

### **✅ MATCH (diff < 1%)**
- Signal đúng
- Entry price khớp
- Không cần action

### **⚠️ DISCREPANCY (diff > 1%)**
- Entry price khác nhau > 1%
- Có thể do:
  - Data timing (EOD vs intraday)
  - Rounding differences
  - Bug trong scanner

**Action:** Investigate manually

### **❌ Extra in DB**
- Database có signal nhưng manual không tìm thấy
- **False positive?**
- Có thể do:
  - Điều kiện đã thay đổi (giá thay đổi trong ngày)
  - Bug trong scanner (detect sai)

**Action:** Review signal logic

### **⚠️ Missing in DB**
- Manual tìm thấy signal nhưng database không có
- **False negative?**
- Có thể do:
  - Scanner chưa chạy
  - Signal bị filter ra
  - Bug trong scanner (miss signal)

**Action:** Check scanner logs

---

## 🔧 COMPARISON LOGIC

### **Price Tolerance: ±1%**

```python
diff_pct = abs(db_entry - manual_entry) / manual_entry * 100

if diff_pct < 1.0:
    → MATCH ✅
else:
    → DISCREPANCY ⚠️
```

**Tại sao 1%?**
- EOD data có thể khác nhau giữa sources
- Rounding errors
- Timing differences (market close vs API fetch)

---

## 📋 USE CASES

### **Use Case 1: Daily QA (STAGING)**

```bash
# Mỗi ngày trước khi deploy production
python verify_signals.py
# Chọn: 1 (STAGING)

# Nếu accuracy > 90% → OK to deploy
# Nếu accuracy < 90% → Investigate
```

### **Use Case 2: Bug Investigation (PRODUCTION)**

```bash
# User report: "Signal VCB sai"
python verify_signals.py
# Chọn: 2 (PRODUCTION)

# Check VCB results
# Compare với manual calculation
# Find root cause
```

### **Use Case 3: Pre-Deploy Check**

```bash
# Vừa modify scanner logic
# Test trên staging trước

python verify_signals.py
# Chọn: 1 (STAGING)

# If OK → Deploy to production
# If not OK → Fix bugs first
```

---

## 🐛 TROUBLESHOOTING

### **Issue 1: "Timeout - backend sleeping"**

**Reason:** Staging backend trên Render free tier sleeps sau 15 phút không hoạt động.

**Solution:**
```
Script tự động retry sau 30s
Hoặc ping staging backend trước:
curl https://ai-advisor1-staging.onrender.com/health
```

### **Issue 2: "No signals in database"**

**Possible reasons:**
- Scanner chưa chạy hôm nay
- Database empty (fresh deploy)
- API connection issue

**Solution:**
- Trigger scanner manually
- Check deployment logs
- Verify API endpoint

### **Issue 3: "Cannot download data"**

**Reason:** vnstock API issue hoặc ticker delisted

**Solution:**
- Retry
- Check ticker code
- Skip ticker

---

## 📊 ACCURACY BENCHMARKS

### **Good:**
- Accuracy > 95%
- Discrepancies < 5%
- No false positives

### **Acceptable:**
- Accuracy 85-95%
- Minor discrepancies (< 1% price diff)
- 1-2 false positives acceptable

### **Bad:**
- Accuracy < 85%
- Major discrepancies (> 2% price diff)
- Many false positives

**Action if bad:** Review scanner code, check data source

---

## 💾 EXPORT RESULTS

**JSON format:**

```json
{
  "total_checked": 5,
  "matches": [
    {
      "ticker": "VCB",
      "strategy": "PULLBACK",
      "db_entry": 88500.0,
      "manual_entry": 88500.0,
      "diff_pct": 0.0
    }
  ],
  "discrepancies": [...],
  "missing_in_db": [...],
  "extra_in_db": [...]
}
```

**Use for:**
- Archive
- Share with team
- Trend analysis

---

## 🎯 BEST PRACTICES

### **1. Daily Verification**
```bash
# Run mỗi sáng trước 9AM
python verify_signals.py
# Chọn STAGING
# Check accuracy
```

### **2. Pre-Deploy Check**
```bash
# Trước khi deploy production
# Verify staging first
python verify_signals.py
# Chọn STAGING
# Accuracy > 90%? → Deploy
```

### **3. Post-Deploy Verification**
```bash
# Sau khi deploy production
# Wait 1 hour for scanner to run
python verify_signals.py
# Chọn PRODUCTION
# Verify signals correct
```

### **4. Weekly Archive**
```bash
# Mỗi thứ 6
python verify_signals.py
# Export JSON
# Save to reports/ folder
# Track trends over time
```

---

## 📞 SUPPORT

**Questions?**
- Check PULLBACK_EMA_CROSS_STRATEGIES.md for strategy details
- Review ARCHITECTURE.md for staging/production setup
- Contact: ngthson75@gmail.com

---

## ⚙️ ADVANCED USAGE

### **Custom API Endpoint**

Modify trong code:
```python
STAGING_API = "https://your-custom-staging.com/api"
PRODUCTION_API = "https://your-custom-production.com/api"
```

### **Adjust Tolerance**

Modify trong code:
```python
if diff_pct < 1.0:  # Change to 2.0 for looser tolerance
    → MATCH
```

### **Test Specific Tickers**

Modify trong code:
```python
# Filter to specific tickers
tickers_to_check = ['VCB', 'VHM', 'HPG']
db_by_ticker = {k: v for k, v in db_by_ticker.items() if k in tickers_to_check}
```

---

**Ready to verify! 🔍**
