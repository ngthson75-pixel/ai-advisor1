# DAILY EOD WORKFLOW - COMPARISON OLD vs NEW

**Date:** 2026-03-02  
**Update:** V5.2 với Filter + SELL Scanner  

---

## 📊 CHANGES SUMMARY

| Feature | OLD | NEW (V5.2) |
|---------|-----|------------|
| **Số bước** | 3 steps | 4 steps |
| **BUY Scanner** | ✅ Bước 1 | ✅ Bước 1 (same) |
| **Filter & Dedup** | ❌ Thiếu | ✅ Bước 2 (NEW!) |
| **SELL Scanner** | ❌ Thiếu | ✅ Bước 3 (NEW V5.2!) |
| **Market Risk** | ✅ Bước 2 | ✅ Bước 4 (same) |
| **Auto-push Market Risk** | ✅ Có (Bước 3) | ❌ Bỏ (manual review) |
| **Manual Review** | ❌ Sau khi push | ✅ Trước khi push |

---

## 🔍 DETAILED COMPARISON

### OLD WORKFLOW (3 Steps)

```python
# Bước 1: BUY Scanner (20-25 min)
subprocess.run([sys.executable, SCANNER_PATH])

# Bước 2: Market Risk (vài giây)
subprocess.run([sys.executable, MARKET_RISK_PATH])

# Bước 3: AUTO-PUSH Market Risk
requests.post(f"{PROD_API}/api/market-risk/upload", json=risk_data)
# → Đẩy luôn, không review!

# Manual: User phải review signals sau khi đã push
```

**Issues:**
- ❌ Thiếu Filter step → signals có noise
- ❌ Thiếu SELL Scanner → phải chạy riêng
- ❌ Auto-push Market Risk → không review được
- ❌ User review sau khi push (late!)

---

### NEW WORKFLOW (4 Steps + Manual Review)

```python
# Bước 1: BUY Scanner (20-25 min)
subprocess.run([sys.executable, BUY_SCANNER_PATH])

# Bước 2: Filter & Dedup (vài giây) - NEW!
subprocess.run([sys.executable, FILTERED_PATH])

# Bước 3: SELL Scanner V5.2 (2-5 min) - NEW!
subprocess.run([sys.executable, SELL_SCANNER_PATH, '--dry-run'])
# → Dry-run, không push tự động!

# Bước 4: Market Risk (vài giây)
subprocess.run([sys.executable, MARKET_RISK_PATH])

# Bước 5-6: MANUAL REVIEW (user decides)
# Option 1: python signal_reviewer.py
# Option 2: python push_market_risk.py + push_local_signals.py
```

**Improvements:**
- ✅ Có Filter step → signals sạch hơn
- ✅ Có SELL Scanner V5.2 → all-in-one workflow
- ✅ Dry-run SELL → review trước khi push
- ✅ No auto-push → user control 100%
- ✅ Clear instructions cho manual review

---

## 📋 CODE CHANGES

### 1. Added Filter Step

```python
# NEW - Bước 2
FILTERED_PATH = os.path.join(SCRIPT_DIR, 'daily_scanner_FILTERED.py')

if os.path.exists(FILTERED_PATH):
    subprocess.run([sys.executable, FILTERED_PATH])
else:
    print("⚠️ Filter file không tồn tại, bỏ qua...")
```

---

### 2. Added SELL Scanner V5.2

```python
# NEW - Bước 3
SELL_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'sell_signal_scanner_v5.2.py')
SELL_SIGNALS_FILE = os.path.join(SCRIPT_DIR, 'sell_signals_v5.2_latest.json')

if os.path.exists(SELL_SCANNER_PATH):
    # Chạy dry-run
    subprocess.run([sys.executable, SELL_SCANNER_PATH, '--dry-run'])
    
    # Display results
    with open(SELL_SIGNALS_FILE, 'r') as f:
        sell_data = json.load(f)
    print(f"SELL Signals: {sell_data.get('count', 0)}")
else:
    print("⚠️ SELL scanner V5.2 chưa có")
```

---

### 3. Removed Auto-Push Market Risk

```python
# OLD - Bước 3 (REMOVED)
requests.post(f"{PROD_API}/api/market-risk/upload", json=risk_data)

# NEW - No auto-push
# Display instructions for manual review instead
```

---

### 4. Enhanced Instructions

```python
# NEW - End of workflow
print("📌 MANUAL REVIEW - CHỌN 1 TRONG 2 CÁCH:")
print("🔹 CÁCH 1: python signal_reviewer.py")
print("🔹 CÁCH 2: python push_market_risk.py + push_local_signals.py")
```

---

## 🚀 MIGRATION GUIDE

### Step 1: Backup Old File

```powershell
cd C:\ai-advisor1

# Backup
Copy-Item daily_eod_workflow.py daily_eod_workflow_OLD.py
```

---

### Step 2: Replace with New File

```powershell
# Download daily_eod_workflow_v5.2.py từ Claude
# Rename thành daily_eod_workflow.py

# OR copy content từ Claude vào file hiện tại
notepad daily_eod_workflow.py
# Paste new code, Save
```

---

### Step 3: Verify Dependencies

```powershell
# Check required files
ls scripts\daily_signal_scanner_eod.py        # BUY scanner
ls daily_scanner_FILTERED.py                  # Filter (optional)
ls sell_signal_scanner_v5.2.py                # SELL V5.2 (NEW!)
ls market_risk_analysis.py                    # Market risk

# If missing sell_signal_scanner_v5.2.py:
# Download from Claude
```

---

### Step 4: Test New Workflow

```powershell
# Run new workflow
python daily_eod_workflow.py

# Expected output:
# 🚀 DAILY EOD WORKFLOW - V5.2
# ─────────────────────────────────────────
# 📊 BƯỚC 1/4: BUY Signal Scanner...
# 🔍 BƯỚC 2/4: Filter & Dedup...
# 🔴 BƯỚC 3/4: SELL Signal Scanner V5.2...
# 📊 BƯỚC 4/4: Market Risk Analysis...
# 📋 TỔNG KẾT - 4 BƯỚC TỰ ĐỘNG HOÀN TẤT
# 📌 MANUAL REVIEW...
```

---

## 📊 BEFORE/AFTER WORKFLOW

### OLD (Manual 6 Steps):

```
User runs individually:
1. python daily_signal_scanner_eod.py     (20-25 min)
2. python daily_scanner_FILTERED.py       (vài giây)
3. python sell_signal_scanner_v3.py       (2-5 min)
4. python market_risk_analysis.py         (vài giây)
5. python signal_reviewer.py              (manual)
6. python push_market_risk.py             (manual)
   python push_local_signals.py           (manual)

Total: 6 commands, 25-30 min + manual work
```

---

### NEW (1 Command + Manual Review):

```
User runs ONE command:
python daily_eod_workflow.py

→ Runs steps 1-4 automatically (25-30 min)
→ Shows instructions for manual review

Then user chooses:
Option 1: python signal_reviewer.py
Option 2: python push_market_risk.py + push_local_signals.py

Total: 1 automated command + 1-2 manual commands
```

**Time saved:** ~5 minutes (no separate commands)  
**Error reduction:** Less chance of forgetting a step  
**User control:** Review BEFORE push (safer)

---

## ✅ BENEFITS

**Old Workflow:**
- ⚠️ 6 separate commands (easy to miss steps)
- ⚠️ No SELL integration
- ⚠️ Auto-push Market Risk (no review)
- ⚠️ Manual steps error-prone

**New Workflow V5.2:**
- ✅ 1 command for automation (steps 1-4)
- ✅ SELL Scanner integrated
- ✅ Dry-run mode (review before push)
- ✅ Clear instructions for manual review
- ✅ All files checked before run
- ✅ Enhanced error messages

---

## 🔄 ROLLBACK

**If new version has issues:**

```powershell
# Restore old version
Copy-Item daily_eod_workflow_OLD.py daily_eod_workflow.py -Force

# Run old workflow
python daily_eod_workflow.py
```

---

**DEPLOY NEW VERSION NGAY!** Much better workflow! 🚀
