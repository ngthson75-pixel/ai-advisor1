# QUICK DEPLOY: DAILY EOD WORKFLOW V5.2

**Time:** 2 phút  
**Changes:** Old (3 steps) → New (4 steps + manual review)  

---

## 🎯 KEY CHANGES

**OLD:**
```
1. BUY Scanner
2. Market Risk
3. Auto-push Market Risk ← No review!
```

**NEW:**
```
1. BUY Scanner
2. Filter & Dedup ← NEW!
3. SELL V5.2 ← NEW!
4. Market Risk
5-6. Manual review ← Safer!
```

---

## 🚀 DEPLOY (2 PHÚT)

### Step 1: Backup (30 giây)

```powershell
cd C:\ai-advisor1

Copy-Item daily_eod_workflow.py daily_eod_workflow_OLD.py
```

---

### Step 2: Replace (1 phút)

**Option A: Download & Rename**
```powershell
# Download daily_eod_workflow_v5.2.py từ Claude
# Rename:
Move-Item daily_eod_workflow_v5.2.py daily_eod_workflow.py -Force
```

**Option B: Copy Content**
```powershell
# Mở file cũ
notepad daily_eod_workflow.py

# Copy toàn bộ nội dung từ daily_eod_workflow_v5.2.py (từ Claude)
# Paste, Save
```

---

### Step 3: Verify (30 giây)

```powershell
# Check file đã update
Select-String "V5.2" daily_eod_workflow.py
# Should see: "DAILY EOD WORKFLOW - V5.2"

# Check dependencies
ls sell_signal_scanner_v5.2.py
# Should exist (nếu không → download từ Claude)
```

---

## ✅ DONE!

**Test ngay:**
```powershell
python daily_eod_workflow.py
```

**Expected:**
```
🚀 DAILY EOD WORKFLOW - V5.2
📅 2026-03-02 16:00

─────────────────────────────────────────
📊 BƯỚC 1/4: BUY Signal Scanner (20-25 phút)...
🔍 BƯỚC 2/4: Filter & Dedup (vài giây)...
🔴 BƯỚC 3/4: SELL Signal Scanner V5.2 (2-5 phút)...
📊 BƯỚC 4/4: Market Risk Analysis (vài giây)...

📋 TỔNG KẾT - 4 BƯỚC TỰ ĐỘNG HOÀN TẤT
📌 MANUAL REVIEW - CHỌN 1 TRONG 2 CÁCH:
  🔹 CÁCH 1: python signal_reviewer.py
  🔹 CÁCH 2: python push_market_risk.py + push_local_signals.py
```

---

## 📋 DAILY USAGE (1 LỆNH!)

**Cuối mỗi ngày (sau 15h):**

```powershell
cd C:\ai-advisor1

# Chỉ 1 lệnh:
python daily_eod_workflow.py

# Wait 25-30 min
# → 4 bước tự động

# Manual review (chọn 1):
python signal_reviewer.py
# OR
python push_market_risk.py
python push_local_signals.py
```

---

## 🔄 ROLLBACK (Nếu Issues)

```powershell
Copy-Item daily_eod_workflow_OLD.py daily_eod_workflow.py -Force
```

---

**THAY FILE NGAY VÀ TEST!** 🚀
