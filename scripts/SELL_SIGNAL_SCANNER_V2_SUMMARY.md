# SELL SIGNAL SCANNER V2 - SUMMARY

**Date:** 2026-02-05  
**Status:** ✅ READY TO USE

---

## ✅ ĐÃ FIX HOÀN TOÀN

### 1. Rate Limit ✓
- **OLD:** 121 API calls → Rate limit
- **NEW:** 15 API calls → No rate limit
- **Giảm:** 87%

### 2. Giá tính sai ✓
- **OLD:** Entry 70,800, Exit 71 → P/L -99.90% ❌
- **NEW:** Entry 70,800, Exit 71,000 → P/L +0.28% ✓
- **Fix:** vnstock prices × 1000

### 3. Database ✓
- **Auto-migration:** Tự động thêm columns mới
- **Columns:** exit_reason, exit_date, profit_loss_pct, exit_quantity_pct, buy_signal_id, volume_ratio

### 4. Flow ✓
- **NEW LOGIC:**
  1. Lấy danh sách TICKERS từ BUY signals (2 ngày)
  2. Loop TICKERS → Quét VCI (delay 2s)
  3. Check điều kiện SELL (4 rules)
  4. Lưu SELL signals vào database

---

## 🚀 SỬ DỤNG

### Quick Start

```powershell
# 1. Backup file cũ
Copy-Item scripts\sell_signal_scanner_v2.py scripts\sell_signal_scanner_v2_OLD.py

# 2. Copy file mới
Copy-Item sell_signal_scanner_v2_FINAL.py scripts\sell_signal_scanner_v2.py -Force

# 3. Chạy
python scripts/sell_signal_scanner_v2.py
```

### Tùy chỉnh

```powershell
# Quét 3 ngày, delay 3s
python scripts/sell_signal_scanner_v2.py --days 3 --delay 3.0

# Xem help
python scripts/sell_signal_scanner_v2.py --help
```

---

## 📊 KẾT QUẢ MONG ĐỢI

```
✓ Found 15 unique tickers
✓ SELL signals generated: 8

By Reason:
  SL: 1
  TP_PARTIAL (50%): 3
  MA20_CONSECUTIVE: 3
  MA20_HIGH_VOLUME: 1

Top 5:
1. 🟢 VCB - TP_PARTIAL - 50% - +8.14%
2. 🟢 MBB - TP_PARTIAL - 50% - +7.89%
3. 🟢 VNM - TP_PARTIAL - 50% - +6.52%
4. 🔴 HPG - MA20_CONSECUTIVE - 100% - -3.64%
5. 🔴 TCB - SL - 100% - -5.00%
```

---

## 🔍 KIỂM TRA

```sql
-- Xem SELL signals mới
SELECT 
    ticker, exit_reason, entry_price, exit_price, 
    profit_loss_pct, exit_quantity_pct
FROM signals 
WHERE action='SELL' 
ORDER BY created_at DESC 
LIMIT 5;

-- Kiểm tra giá đúng
-- Entry: 70,000-90,000 → Exit: 70,000-90,000 ✓
-- Entry: 70,800 → Exit: 71 ❌ (file cũ)
```

---

## 📁 FILES

**Scanner:** `sell_signal_scanner_v2_FINAL.py`  
**Guide:** `SELL_SIGNAL_SCANNER_V2_GUIDE.md`  
**This file:** `SELL_SIGNAL_SCANNER_V2_SUMMARY.md`

All files in: `/mnt/user-data/outputs/`

---

## 🎯 NEXT STEPS

1. ✅ Download files
2. ✅ Backup old scanner
3. ✅ Copy new scanner
4. ✅ Run test
5. ✅ Check results
6. ✅ Deploy to production

---

**Contact:** ngthson75@gmail.com | +84938127666
