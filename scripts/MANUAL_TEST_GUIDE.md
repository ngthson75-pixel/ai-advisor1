# 🧪 MANUAL SIGNAL TESTING - USAGE GUIDE

## 📋 OVERVIEW

File `manual_test_signals.py` dùng để **test thủ công** tín hiệu PULLBACK và EMA_CROSS với dữ liệu EOD thực tế từ vnstock.

**Mục đích:**
- ✅ Kiểm tra độ chính xác của signals
- ✅ Verify từng điều kiện chi tiết
- ✅ Debug khi có vấn đề
- ✅ Export kết quả ra CSV

---

## 🚀 QUICK START

### **Bước 1: Cài đặt dependencies**

```bash
pip install vnstock pandas numpy --break-system-packages
```

### **Bước 2: Chạy script**

```bash
cd C:\ai-advisor1\scripts
python manual_test_signals.py
```

### **Bước 3: Chọn chế độ test**

```
Select testing mode:
1. Test single stock
2. Test 5 popular stocks (VCB, VHM, HPG, FPT, MBB)
3. Test 10 stocks (Quick batch)
4. Custom stock list
5. Exit

Enter choice (1-5): 
```

---

## 📖 USAGE EXAMPLES

### **Example 1: Test 1 mã cổ phiếu**

```bash
python manual_test_signals.py
# Chọn: 1
# Nhập: VCB
```

**Output:**
```
##########################################################################
🧪 TESTING STOCK: VCB
##########################################################################
Date: 2026-01-26
📥 Downloading data: 2025-09-18 to 2026-01-26
✅ Downloaded 100 bars

======================================================================
🎯 PULLBACK STRATEGY TEST: VCB
======================================================================

📊 Current Values:
   Date: 2026-01-26
   Close: 88,500 VND
   EMA20: 87,200 VND
   EMA50: 84,300 VND
   RSI: 48.50
   Volume: 5,234,000

✓ Condition Checks:

   1️⃣ UPTREND (EMA20 > EMA50)
      EMA20: 87,200
      EMA50: 84,300
      Result: True ✅

   2️⃣ NEAR EMA20 (within 3%)
      Price: 88,500
      EMA20: 87,200
      Difference: 1,300 VND (1.49%)
      Threshold: 3.00%
      Result: True ✅

   3️⃣ RSI < 60
      RSI: 48.50
      Threshold: 60.00
      Result: True ✅

======================================================================
✅ PULLBACK SIGNAL DETECTED!
======================================================================

💰 Entry/Exit Prices:
   Entry:  88,500 VND
   Stop:   81,771 VND (EMA50 * 0.97)
   Target: 95,580 VND (Entry * 1.08)

📊 Risk/Reward:
   Risk:   6,729 VND (7.60%)
   Reward: 7,080 VND (8.00%)
   R/R:    1.05x

⭐ Quality Score:
   Base: 60
   + Volume > avg (+10)
   Total: 70/100
   Priority: NO
   Type: Blue Chip

======================================================================
📊 SUMMARY FOR VCB
======================================================================
Signals found: 1
  ✅ PULLBACK: 70/100 - R/R 1.05x
```

---

### **Example 2: Test nhiều mã**

```bash
python manual_test_signals.py
# Chọn: 2  (Test 5 stocks)
```

**Output:**
```
##########################################################################
🧪 BATCH TESTING: 5 STOCKS
##########################################################################
Date: 2026-01-26
Stocks: VCB, VHM, HPG, FPT, MBB

[1/5] 
##########################################################################
🧪 TESTING STOCK: VCB
##########################################################################
...

[2/5]
##########################################################################
🧪 TESTING STOCK: VHM
##########################################################################
...

##########################################################################
📊 FINAL TEST SUMMARY
##########################################################################
Date: 2026-01-26
Stocks tested: 5
Successful: 5
Failed: 0
Total signals: 3

📈 By Strategy:
   PULLBACK: 2
   EMA_CROSS: 1
   Priority: 1

⭐ Top 5 Signals:
   1. VHM  - EMA_CROSS  - 85/100 - R/R 2.30x ⭐
   2. VCB  - PULLBACK   - 70/100 - R/R 1.05x
   3. HPG  - PULLBACK   - 65/100 - R/R 1.20x

💾 Export Results:
Export to CSV? (y/n): y
✅ Exported to: test_signals_20260126_143025.csv
   Rows: 3
   Columns: ticker, strategy, entry_price, stop_loss, ...
```

---

### **Example 3: Custom list**

```bash
python manual_test_signals.py
# Chọn: 4
# Nhập: VCB,TCB,MBB,ACB
```

Test 4 mã ngân hàng theo ý muốn.

---

## 📊 OUTPUT DETAILS

### **Màn hình hiển thị:**

**1. Current Values**
- Close, EMA20, EMA50, RSI, Volume

**2. Condition Checks** (từng điều kiện)
- ✅ PASS: Điều kiện thỏa mãn
- ❌ FAIL: Điều kiện không thỏa

**3. Signal Result**
- ✅ Signal detected
- ❌ No signal

**4. Entry/Exit Prices**
- Entry, Stop Loss, Take Profit
- Risk %, Reward %, R/R ratio

**5. Quality Score**
- Base score
- Bonuses
- Total strength
- Priority flag

---

## 💾 CSV EXPORT

**File format:** `test_signals_YYYYMMDD_HHMMSS.csv`

**Columns:**
```
ticker          : Mã cổ phiếu (VCB, VHM, ...)
strategy        : PULLBACK hoặc EMA_CROSS
entry_price     : Giá vào lệnh
stop_loss       : Giá cắt lỗ
take_profit     : Giá chốt lời
risk_pct        : % rủi ro
reward_pct      : % lợi nhuận
rr_ratio        : Risk/Reward ratio
strength        : Điểm chất lượng (0-100)
is_priority     : 1 = priority, 0 = normal
stock_type      : Blue Chip / Mid Cap / Penny
rsi             : RSI value
date            : Ngày phát hiện signal
```

**Example CSV:**
```csv
ticker,strategy,entry_price,stop_loss,take_profit,risk_pct,reward_pct,rr_ratio,strength,is_priority,stock_type,rsi,date
VCB,PULLBACK,88500,81771,95580,7.60,8.00,1.05,70,0,Blue Chip,48.5,2026-01-26
VHM,EMA_CROSS,82500,79104,90750,4.12,10.00,2.43,85,1,Blue Chip,55.2,2026-01-26
```

---

## 🔍 VERIFICATION WORKFLOW

### **Khi cần verify signal:**

1. **Chạy test script:**
   ```bash
   python manual_test_signals.py
   # Test ticker cần check
   ```

2. **Đọc output chi tiết:**
   - Kiểm tra từng điều kiện
   - Xem exact values (EMA, RSI)
   - Verify calculations

3. **Cross-check với chart:**
   - Mở chart trên investing.com
   - Add EMA(20), EMA(50), RSI(14)
   - So sánh values

4. **Export CSV:**
   - Lưu kết quả
   - Share với team
   - Archive cho sau này

---

## 🐛 TROUBLESHOOTING

### **Issue 1: "vnstock not installed"**

```bash
pip install vnstock --break-system-packages
```

### **Issue 2: "No data for ticker"**

**Possible reasons:**
- Ticker code sai
- Mã không giao dịch
- API timeout

**Solution:**
- Check ticker code đúng chưa
- Retry sau vài giây
- Check network connection

### **Issue 3: "Not enough data"**

**Reason:** Ít hơn 50 bars

**Solution:**
- Tăng lookback days
- Hoặc mã mới listing (bình thường)

### **Issue 4: Results khác với scanner**

**Debug steps:**
1. Check data date range
2. Verify indicator calculations
3. Compare latest bar (df.iloc[-1])
4. Check rounding differences

---

## 📋 TESTING CHECKLIST

Before deploying scanner updates:

- [ ] Test 5-10 stocks manually
- [ ] Verify both strategies work
- [ ] Check edge cases (RSI=60, EMA20=EMA50)
- [ ] Export CSV and review
- [ ] Compare with production signals
- [ ] Document any discrepancies

---

## 🎯 WHEN TO USE

**Use manual test khi:**

1. ✅ **Debug signals:**
   - Scanner tìm signal nhưng không chắc đúng
   - Users report sai signal
   - Cần verify logic

2. ✅ **Modify strategy:**
   - Test thay đổi trước khi deploy
   - Compare old vs new logic
   - Backtest với historical data

3. ✅ **Onboard new team member:**
   - Hiểu strategies chi tiết
   - Hands-on testing
   - Learning by doing

4. ✅ **Quality assurance:**
   - Weekly spot checks
   - Monthly reviews
   - Before major releases

---

## 📞 SUPPORT

**Questions?**
- Check `PULLBACK_EMA_CROSS_STRATEGIES.md` for strategy details
- Review `daily_signal_scanner_eod.py` for code
- Contact: ngthson75@gmail.com

---

## 🚀 ADVANCED USAGE

### **Test with custom date range:**

Modify in code:
```python
def download_eod_data(self, ticker, days=100):
    # Change days parameter
    # Default: 100 days
```

### **Test with custom thresholds:**

Modify in code:
```python
# PULLBACK
near_ema20 = abs(close - ema20) / ema20 < 0.03  # Change 0.03
rsi_ok = rsi < 60  # Change 60

# EMA_CROSS
near_cross = abs(ema20_curr - ema50_curr) / ema50_curr < 0.02  # Change 0.02
```

### **Export to Excel:**

Modify export function:
```python
def export_to_csv(self, signals):
    filename = f"test_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df = pd.DataFrame(signals)
    df.to_excel(filename, index=False)
```

---

**Ready to test! 🧪**
