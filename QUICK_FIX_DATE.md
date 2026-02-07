# ⚡ QUICK FIX - 2 COMMANDS (1 PHÚT)

## ❌ VẤN ĐỀ
```
❌ No signals found for 2026-02-01
```

**Nguyên nhân:** Hôm nay là Thứ Bảy → Không phải ngày giao dịch!  
Scanner lưu signals với ngày: **2026-01-31** (Thứ Sáu)

---

## ✅ GIẢI PHÁP - 2 LỆNH

### **1. Download files mới** ⬆️

Files cần download:
- `check_signals_db.ps1` ⬆️
- `push_local_signals.py` ⬆️ (UPDATED version)

Copy vào: `C:\ai-advisor1\`

---

### **2. Chạy 2 lệnh:**

```powershell
cd C:\ai-advisor1

# Lệnh 1: Check database
.\check_signals_db.ps1

# Output:
# Available dates:
#   📅 2026-01-31 - 132 signals ← LATEST
#
# Latest signals: 2026-01-31 (132 signals)

# Lệnh 2: Push signals
python push_local_signals.py

# Output:
# Available dates:
#   1. 2026-01-31 - 132 signals
#
# Choose date:
# Enter choice (1) or press Enter for latest: [NHẤN ENTER]
#
# Selected date: 2026-01-31
#
# Choose environment:
#   1. Production
#   2. Staging
#   3. Both
#
# Enter choice (1/2/3): 1  ← GÕ 1
#
# Continue? (y/n): y  ← GÕ Y
#
# 🔄 Pushing to Production...
#   1/132 ✓ GMC    EMA_CROSS    100%
#   2/132 ✓ PGD    EMA_CROSS    100%
#   ...
#   132/132 ✓ ...
#
# ✅ PUSH COMPLETE!
```

---

### **3. Verify website:**

```
Browser: Ctrl + Shift + R
Visit: https://ai-advisor.vn
Tab: "Tín hiệu mua"
```

**Should see:**
- 132 signals
- Date: 2026-01-31 (Thứ Sáu)
- Top signals: GMC, PGD, VSM, CTG, VIM

---

## ✅ DONE! 🎉

Total: **2 commands, 1 phút**

---

## 📋 DAILY WORKFLOW

**Mỗi ngày (kể cả cuối tuần):**

```powershell
# 1. Check database
.\check_signals_db.ps1
# Sẽ show ngày giao dịch gần nhất

# 2. Push signals
python push_local_signals.py
# Nhấn Enter → Chọn 1 → Nhấn y
```

**Scanner tự động dùng ngày giao dịch đúng:**
- Thứ 2-6: Ngày hôm đó
- Thứ 7-CN: Thứ 6 tuần trước

---

## 🔍 TẠI SAO KHÔNG DÙNG 2026-02-01?

```
2026-02-01 = Thứ Bảy = Không giao dịch
→ Scanner dùng: Thứ Sáu (2026-01-31)
→ Database có: 2026-01-31
→ Push script tìm: 2026-02-01 → NOT FOUND!

✅ Updated script tự động tìm ngày mới nhất!
```

---

**READ FULL GUIDE:** `TROUBLESHOOT_DATE_MISMATCH.md` ⬆️

---

**TL;DR:**

```powershell
cd C:\ai-advisor1
.\check_signals_db.ps1
python push_local_signals.py
# Enter → 1 → y → Done!
```

🚀
