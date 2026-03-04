# DAILY EOD WORKFLOW - UPDATE SUMMARY

**Date:** 2026-03-02  
**Version:** V5.2  
**Changes:** Thêm Filter step + Update SELL V5.2  

---

## 🔄 CHANGES FROM OLD VERSION

### 1. Thêm Bước 2: Filter & Dedup

**Old workflow:**
```
Bước 1: BUY Scanner
Bước 2: SELL Scanner  ← Direct!
Bước 3: Market Risk
```

**New workflow:**
```
Bước 1: BUY Scanner
Bước 2: Filter & Dedup  ← NEW!
Bước 3: SELL Scanner V5.2
Bước 4: Market Risk
```

**Why:** Lọc signals chất lượng + dedup trước khi review

---

### 2. Update SELL Scanner V3 → V5.2

**Old:**
```python
SELL_SCANNER_PATH = 'sell_signal_scanner_v3.py'
```

**New:**
```python
SELL_SCANNER_PATH = 'sell_signal_scanner_v5.2.py'  # V5.2!
```

**V5.2 Features:**
- ✅ T+2 = 2 trading days (loại weekend + lễ)
- ✅ MA20 STRICT: < MA20 2d AND (loss >= 3% OR profit < 2%)
- ✅ 5-step exit: TP1 50% → TP2 30% → Pullback/Trailing/MA20
- ✅ Skip signals < T+2

---

### 3. SELL Scanner Chạy Dry-Run

**Old:**
```python
subprocess.run([sys.executable, SELL_SCANNER_PATH])
# → Push luôn lên server
```

**New:**
```python
subprocess.run([sys.executable, SELL_SCANNER_PATH, '--dry-run'])
# → Chỉ scan & show kết quả, KHÔNG push
```

**Why:** Review SELL signals trước khi push

---

### 4. Enhanced Output Display

**Added:**
- 📊 SELL signals count
- ⏳ T+2 skipped count
- 📋 Exit reason breakdown
- 💡 Next steps instructions

---

## 📋 DEPLOYMENT

### Step 1: Replace Old File

```powershell
cd C:\ai-advisor1

# Backup old version
Copy-Item daily_eod_workflow.py daily_eod_workflow.py.backup

# Replace with new version
# Download daily_eod_workflow.py từ Claude
# Copy vào C:\ai-advisor1\

# Verify
ls daily_eod_workflow.py
```

---

### Step 2: Verify Dependencies

```powershell
# Check required files exist
Test-Path C:\ai-advisor1\scripts\daily_signal_scanner_eod.py
# Expected: True

Test-Path C:\ai-advisor1\daily_scanner_FILTERED.py
# Expected: True (nếu False → bỏ qua bước 2)

Test-Path C:\ai-advisor1\sell_signal_scanner_v5.2.py
# Expected: True (nếu False → download từ Claude)

Test-Path C:\ai-advisor1\market_risk_analysis.py
# Expected: True
```

---

### Step 3: Test Workflow

```powershell
cd C:\ai-advisor1

# Test run (dry-run mode for SELL)
python daily_eod_workflow.py
```

**Expected output:**
```
🚀 DAILY EOD WORKFLOW - V5.2
📅 2026-03-02 16:00

─────────────────────────────────────────────────
📊 BƯỚC 1/4: BUY Signal Scanner (20-25 phút)...
─────────────────────────────────────────────────
   Quét 346 mã → Tạo BUY signals + market breadth
   ...
✅ BUY Scanner hoàn tất!
   📊 Breadth: 180 tăng / 166 giảm
      MA20: 195/346 (56.4%)

─────────────────────────────────────────────────
🔍 BƯỚC 2/4: Filter & Dedup BUY Signals (vài giây)...
─────────────────────────────────────────────────
   Lọc signals chất lượng + loại bỏ trùng lặp
   ✅ Filter hoàn tất!

─────────────────────────────────────────────────
🔴 BƯỚC 3/4: SELL Signal Scanner V5.2 (2-5 phút)...
─────────────────────────────────────────────────
   📌 Features:
      - T+2 settlement: Chỉ bán sau 2 trading days
      - MA20 STRICT: 2 days < MA20 AND (loss >= 3% OR profit < 2%)
      - 5-step exit: TP1 50% → TP2 30% → Pullback/Trailing/MA20
   ...
   ✅ SELL Scanner hoàn tất (dry-run)!
   
   📊 SELL Signals: 1
      ⏳ Skip T+2: 3
      Exit reasons:
         TAKE_PROFIT_2: 1

─────────────────────────────────────────────────
📊 BƯỚC 4/4: Market Risk Analysis (vài giây)...
─────────────────────────────────────────────────
   ✅ Market Risk hoàn tất!
   
   🟢 Market Mode: TĂNG KHỎE
   📊 Risk Score: 25/100
   💰 Tỷ trọng: 80% CP / 20% tiền mặt
   📝 Thị trường tích cực...

======================================================================
📋 TỔNG KẾT - 4 BƯỚC TỰ ĐỘNG HOÀN TẤT
======================================================================
   ✅ Bước 1: BUY Scanner → signals.db + market_breadth_eod.json
   ✅ Bước 2: Filter & Dedup → signals.db (cleaned)
   ✅ Bước 3: SELL Scanner V5.2 → sell_signals_v5.2_latest.json
   ✅ Bước 4: Market Risk → market_risk_latest.json

======================================================================
📌 MANUAL REVIEW - CHỌN 1 TRONG 2 CÁCH:
======================================================================

🔹 CÁCH 1: Dùng Signal Reviewer (Khuyến nghị)
   python signal_reviewer.py
   → Review BUY/SELL/Market Risk trong UI
   → Chọn signals muốn giữ
   → Upload thẳng lên staging/production

🔹 CÁCH 2: Push Thủ Công
   python push_market_risk.py      ← Đẩy Market Dashboard
   python push_local_signals.py    ← Đẩy signals đã lọc

💡 LƯU Ý:
   - SELL Scanner chạy --dry-run (chưa push)
   - Nếu SELL signals OK → chạy lại không --dry-run:
     python sell_signal_scanner_v5.2.py
   - Hoặc dùng signal_reviewer.py để review & push
```

---

## 🎯 DAILY USAGE

### Cuối Mỗi Ngày (Sau 15h):

```powershell
cd C:\ai-advisor1

# 1 lệnh duy nhất:
python daily_eod_workflow.py

# Wait 25-30 phút
# → 4 bước tự động hoàn tất

# Manual review (chọn 1):
python signal_reviewer.py        # Option 1 (UI review)
# OR
python push_market_risk.py       # Option 2 (manual push)
python push_local_signals.py
```

---

## 📊 FILES GENERATED

**After workflow completes:**

```
C:\ai-advisor1\
├── signals.db                        ← BUY signals (filtered)
├── market_breadth_eod.json           ← Market breadth data
├── sell_signals_v5.2_latest.json     ← SELL signals (dry-run)
└── market_risk_latest.json           ← Market risk analysis
```

---

## ⚠️ TROUBLESHOOTING

### Issue 1: "daily_scanner_FILTERED.py not found"

**Impact:** Bước 2 bỏ qua, signals không được filter

**Fix:**
- Check file tồn tại: `ls daily_scanner_FILTERED.py`
- Nếu không có → workflow vẫn chạy OK (skip bước 2)
- Signals vẫn ở signals.db nhưng chưa filter

---

### Issue 2: "sell_signal_scanner_v5.2.py not found"

**Impact:** Bước 3 bỏ qua, không có SELL signals

**Fix:**
```powershell
# Download V5.2 từ Claude
# Copy vào C:\ai-advisor1\

# Verify
ls sell_signal_scanner_v5.2.py
# Expected: File found
```

---

### Issue 3: SELL Scanner Chạy Nhưng Không Push

**This is expected!** SELL scanner chạy `--dry-run`

**To push SELL signals:**
```powershell
# Option 1: Chạy lại không dry-run
python sell_signal_scanner_v5.2.py
# Confirm: y

# Option 2: Dùng signal_reviewer.py
python signal_reviewer.py
# Review UI → upload
```

---

## 🔄 ROLLBACK

**If new workflow has issues:**

```powershell
cd C:\ai-advisor1

# Restore old version
Copy-Item daily_eod_workflow.py.backup daily_eod_workflow.py -Force

# Run old workflow
python daily_eod_workflow.py
```

---

## ✅ BENEFITS OF NEW WORKFLOW

**Old (3 steps):**
```
1. BUY Scanner
2. SELL Scanner V3 (auto-push)
3. Market Risk
→ Manual review after push
```

**New (4 steps + review):**
```
1. BUY Scanner
2. Filter & Dedup
3. SELL Scanner V5.2 (dry-run)
4. Market Risk
→ Manual review BEFORE push
```

**Improvements:**
- ✅ Filter step giảm noise
- ✅ V5.2 better logic (T+2 + MA20 strict)
- ✅ Dry-run cho review trước khi push
- ✅ Clear instructions cho manual review
- ✅ Enhanced output display

---

**DEPLOY VÀ TEST NGAY!** 🚀
