# 🎯 DEDUPLICATION IMPLEMENTATION GUIDE

**Objective:** Mỗi ticker chỉ hiển thị 1 tín hiệu duy nhất  
**Rule:** Nếu có nhiều tín hiệu cùng ticker → Chỉ giữ tín hiệu có SCORE CAO NHẤT

---

## 📦 2 SCRIPTS ĐÃ TẠO

### **1. daily_signal_scanner_eod_DEDUP.py** ⬆️
- **Mục đích:** Scanner mới với logic dedup built-in
- **Khi dùng:** Chạy hàng ngày để tạo tín hiệu mới
- **Output:** Chỉ 1 tín hiệu per ticker

### **2. cleanup_duplicate_signals.py** ⬆️
- **Mục đích:** Dọn dẹp duplicates trong database hiện tại
- **Khi dùng:** Chạy 1 lần để clean existing data
- **Safe:** Có backup + dry run mode

---

## 🚀 DEPLOYMENT PLAN

### **PHASE 1: Clean Existing Database (1 lần)**

#### **Step 1.1: Download Cleanup Script**

```powershell
cd C:\ai-advisor1

# Download cleanup_duplicate_signals.py from outputs above
# Save to C:\ai-advisor1\
```

#### **Step 1.2: Run Dry Run First**

```powershell
# See what will be deleted (doesn't actually delete)
python cleanup_duplicate_signals.py
```

**Expected output:**
```
🔍 DRY RUN - Analyzing duplicates...

📊 VCB on 2026-02-11: 3 signals
  ✅ Keep: ID=874 (score=82%, strategy=PULLBACK)
  🗑️  Delete: 2 signals (IDs: [875, 876])

📊 HPG on 2026-02-11: 2 signals
  ✅ Keep: ID=1001 (score=85%, strategy=BREAKOUT)
  🗑️  Delete: 1 signals (IDs: [1002])

📋 Summary:
  Total signals to delete: 24
  Ticker-date pairs affected: 12

⚠️  DRY RUN MODE - No changes made
```

#### **Step 1.3: Review & Confirm**

**Check the plan:**
- Signals being kept have highest scores? ✅
- Makes sense to delete duplicates? ✅

**If looks good:**
```
Proceed with deletion? (yes/no): yes
```

**Script will:**
1. Create backup: `signals.db.BACKUP_DEDUP_20260217_HHMMSS`
2. Delete duplicates
3. Keep only best signal per ticker

**Verify:**
```powershell
# Check database
python -c "import sqlite3; conn=sqlite3.connect('signals.db'); print('Total BUY signals:', conn.execute('SELECT COUNT(*) FROM signals WHERE action=\"BUY\"').fetchone()[0])"

# Before: 42 signals
# After: ~25 signals (unique tickers)
```

---

### **PHASE 2: Update Scanner Logic (Ongoing)**

#### **Option A: Replace Existing Scanner** (Recommended)

```powershell
cd C:\ai-advisor1

# Backup old scanner
Copy-Item daily_signal_scanner_eod.py daily_signal_scanner_eod.OLD.py

# Download new scanner from outputs
# Save as daily_signal_scanner_eod.py (replace old)

# Test locally
python daily_signal_scanner_eod.py
```

#### **Option B: Integrate Dedup into Existing Scanner**

**Add this function to your current scanner:**

```python
def deduplicate_signals(signals):
    """Keep only best signal per ticker (highest score)"""
    ticker_signals = {}
    
    for signal in signals:
        ticker = signal['ticker']
        
        if ticker not in ticker_signals:
            ticker_signals[ticker] = signal
        else:
            existing = ticker_signals[ticker]
            
            # Higher score wins
            if signal['score'] > existing['score']:
                ticker_signals[ticker] = signal
            # Same score → newer date wins
            elif signal['score'] == existing['score'] and signal.get('date', '') > existing.get('date', ''):
                ticker_signals[ticker] = signal
    
    return list(ticker_signals.values())
```

**Then use it in your main scanner:**

```python
# After getting all signals from scanner
raw_signals = run_all_strategies()  # Your existing code

# DEDUP before saving to DB
deduplicated = deduplicate_signals(raw_signals)

# Save to database
save_to_database(deduplicated)
```

---

### **PHASE 3: Test & Verify (1 ngày)**

#### **Test 1: Local Scanner**

```powershell
# Run scanner
python daily_signal_scanner_eod.py

# Check output
cat scripts/signals/signals_latest.json

# Should see: Each ticker appears only once
```

#### **Test 2: Database Check**

```powershell
python -c "
import sqlite3
import pandas as pd

conn = sqlite3.connect('signals.db')

# Check for duplicates
query = '''
SELECT ticker, date, COUNT(*) as count
FROM signals 
WHERE action='BUY'
GROUP BY ticker, date
HAVING count > 1
'''

df = pd.read_sql_query(query, conn)
print('Duplicates found:', len(df))
print(df)
conn.close()
"

# Expected: Duplicates found: 0
```

#### **Test 3: Frontend Display**

```powershell
# Start frontend
cd frontend
npm run dev

# Open http://localhost:5173
# Go to Signals page
# Verify: Each ticker appears only ONCE
```

---

### **PHASE 4: Deploy to Production**

#### **Step 4.1: Commit Changes**

```powershell
cd C:\ai-advisor1

git add daily_signal_scanner_eod.py
git add cleanup_duplicate_signals.py

git commit -m "feat: Dedup signals - 1 ticker = 1 signal

Prevents signal clutter by showing only best signal per ticker.

Changes:
- Scanner: Dedup logic keeps highest score per ticker
- Cleanup script: Removes existing duplicates in DB
- User experience: Clear, focused signal list

Before: 42 signals (many duplicates)
After: ~25 signals (unique tickers)

Resolves: Signal confusion and decision paralysis"

git push origin staging
```

#### **Step 4.2: Test on Staging**

**Wait for scanner to run OR manually trigger:**

```powershell
# SSH to staging OR use Render shell
cd /app
python daily_signal_scanner_eod.py

# Check staging database for duplicates
```

**Frontend test:**
```
https://staging.ai-advisor.vn → Signals page
Verify: No duplicate tickers
```

#### **Step 4.3: Clean Production Database**

**Run cleanup script on PRODUCTION database:**

**Option A: Via pgAdmin4**
```sql
-- First check duplicates
SELECT ticker, date, COUNT(*) as count
FROM signals 
WHERE action='BUY'
GROUP BY ticker, date
HAVING count > 1;

-- Manual cleanup (keep highest score only)
DELETE FROM signals
WHERE id IN (
  SELECT id FROM (
    SELECT id, 
           ROW_NUMBER() OVER (PARTITION BY ticker, date ORDER BY strength DESC, id ASC) as rn
    FROM signals
    WHERE action='BUY'
  ) sub
  WHERE rn > 1
);
```

**Option B: Via Python + Remote DB**
```python
# Modify cleanup script to connect to production DB
# DATABASE_URL from Render environment
```

#### **Step 4.4: Deploy Scanner to Production**

```powershell
git checkout main
git merge staging
git push origin main

# Render auto-deploys
# Wait 10 minutes
```

---

## 📊 BEFORE vs AFTER

### **BEFORE (42 signals):**

```
Tín hiệu MUA (42)

VCB @ 70.8k - 82% - PULLBACK
VCB @ 85.0k - 75% - EMA_CROSS      ← Duplicate!
VCB @ 88.5k - 79% - BREAKOUT       ← Duplicate!
HPG @ 27.0k - 85% - BREAKOUT
HPG @ 30.0k - 80% - PULLBACK       ← Duplicate!
FPT @ 125k - 90% - EMA_CROSS
CTG @ 37.9k - 80% - PULLBACK
CTG @ 39.0k - 75% - BREAKOUT       ← Duplicate!
...

User thinking: "42 mã??? Nhiều quá! Chọn mã nào? VCB có 3 cái?" 😵
```

### **AFTER (25 signals):**

```
Tín hiệu MUA (25)

VCB @ 70.8k - 82% - PULLBACK       ← Chỉ còn 1 (score cao nhất)
HPG @ 27.0k - 85% - BREAKOUT       ← Chỉ còn 1 (score cao nhất)
FPT @ 125k - 90% - EMA_CROSS       ← Giữ nguyên
CTG @ 37.9k - 80% - PULLBACK       ← Chỉ còn 1 (score cao nhất)
...

User thinking: "25 mã! Mỗi mã 1 tín hiệu, rõ ràng! Chọn dễ hơn!" ✅
```

---

## ⚙️ DEDUP LOGIC DETAILS

### **Selection Priority:**

**When multiple signals for same ticker:**

1. **Score (Primary):** Highest score wins
   ```
   VCB @ 70k (82%) vs VCB @ 85k (75%)
   → Keep: VCB @ 70k (score 82%)
   ```

2. **Date (Secondary):** If scores equal, newest date wins
   ```
   VCB @ 70k (80%, 2026-02-11) vs VCB @ 85k (80%, 2026-02-16)
   → Keep: VCB @ 85k (newer date)
   ```

3. **ID (Tertiary):** If both equal, lower ID wins (first created)
   ```
   VCB ID=874 (80%, 2026-02-11) vs VCB ID=875 (80%, 2026-02-11)
   → Keep: VCB ID=874 (first created)
   ```

### **Why Score First?**

**Score = Quality of signal:**
- 90%+ → Very strong signal
- 80-89% → Strong signal
- 70-79% → Good signal

**User wants BEST signal, not newest!**

---

## 🔮 FUTURE ENHANCEMENTS (Optional)

### **Enhancement 1: Quality Filter**

**After dedup, also filter by score:**

```python
# Keep only quality signals (score >= 70%)
quality_signals = [s for s in deduplicated if s['score'] >= 70]

# Result: 25 → 18 high-quality signals
```

### **Enhancement 2: Group by Strength**

```
⭐⭐⭐ MẠNH NHẤT (90-100%) - 4 mã
⭐⭐ TỐT (80-89%) - 10 mã
⭐ ỔN (70-79%) - 4 mã
```

### **Enhancement 3: User Settings**

```python
# Future: Let users choose
USER_SETTINGS = {
    'allow_duplicates': False,  # Default: No duplicates
    'min_score': 70,            # Quality threshold
    'max_signals': 20           # Limit total signals
}
```

---

## ✅ SUCCESS CRITERIA

**After implementation:**

- [ ] No duplicate tickers in signals list
- [ ] Each ticker appears exactly 1 time
- [ ] Signal with highest score is kept
- [ ] Signal count: 42 → ~25 (40% reduction)
- [ ] User feedback: "Dễ chọn hơn!"

---

## 🎯 QUICK START

**Minimal changes to try now:**

```powershell
# 1. Download cleanup script
cd C:\ai-advisor1
# Save cleanup_duplicate_signals.py

# 2. Run dry run
python cleanup_duplicate_signals.py
# Review output

# 3. If looks good, confirm deletion
# Type 'yes' when prompted

# 4. Check results
# Frontend: Fewer signals, no duplicates
```

**Time needed:** 30 minutes  
**Risk level:** Low (has backup + dry run)  
**Impact:** High (immediate UX improvement)

---

**Questions?** Ask me anything! 🚀
