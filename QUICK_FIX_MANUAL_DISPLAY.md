# QUICK FIX: LỖI "THỦ CÔNG" (1 PHÚT)

**Vấn đề:** Signals hiển thị "⚪ Thủ công" thay vì "Chốt lời/Cắt lỗ"

**Nguyên nhân:** V5.2 push codes frontend không nhận diện

**Fix:** Map codes → Frontend-compatible

---

## 🚀 DEPLOY (1 PHÚT)

```powershell
cd C:\ai-advisor1

# 1. Backup (10s)
Copy-Item sell_signal_scanner_v5.2.py sell_signal_scanner_v5.2_OLD.py

# 2. Replace (20s)
# Download sell_signal_scanner_v5.2_FIXED.py từ Claude
Move-Item sell_signal_scanner_v5.2_FIXED.py sell_signal_scanner_v5.2.py -Force

# 3. Run scanner (30s)
python sell_signal_scanner_v5.2.py

# Confirm: y
```

---

## ✅ EXPECTED

**Before:**
```
PVB: ⚪ Thủ công
SAB: ⚪ Thủ công
```

**After:**
```
PVB: 🟢 Chốt lời (TP)
SAB: ❌ MA20 Break
```

---

## 📋 MAPPING

| Exit Reason | Display |
|-------------|---------|
| TAKE_PROFIT_1 | 🟢 Chốt lời (TP) |
| TAKE_PROFIT_2 | 🟢 Chốt lời (TP) |
| MA20_STRICT | ❌ MA20 Break |
| STOP_LOSS | 🔴 Cắt lỗ (SL) |

**Chi tiết trong note:** "TAKE_PROFIT_1 (50%)"

---

**THAY FILE VÀ CHẠY LẠI!** 🚀
