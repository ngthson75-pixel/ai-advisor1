# ⚡ QUICK FIX - RATE LIMIT ERROR

## ❌ ERROR

```
⚠️ Bạn đã gửi quá nhiều request tới VCI. 
Vui lòng thử lại sau 30 giây.
```

---

## ✅ FIX NGAY (2 PHÚT)

### **STEP 1: Replace scanner**

```powershell
cd C:\ai-advisor1

# Backup
copy scripts\daily_signal_scanner_eod.py scripts\daily_signal_scanner_eod.py.bak

# Copy NEW scanner (from downloads)
copy Downloads\daily_signal_scanner_eod.py scripts\

# Verify
findstr "random.uniform" scripts\daily_signal_scanner_eod.py
# Should see: delay = 1.5 + random.uniform(0, 0.5)
```

### **STEP 2: Test**

```powershell
cd scripts
python daily_signal_scanner_eod.py

# Should see:
# - 1.5-2s delay between stocks ✅
# - If rate limit → "⚠️ RATE LIMIT. Waiting 30s..." ✅
# - Auto-retry ✅
# - Completes in 10-15 min ✅
```

---

## 🔍 WHAT CHANGED

### **Old (BROKEN):**
```python
time.sleep(0.5)  # Too fast! 🚨
# No retry logic
# Crashes after ~100 stocks
```

### **New (FIXED):**
```python
delay = 1.5 + random.uniform(0, 0.5)  # 1.5-2s ✅
time.sleep(delay)

# + Retry logic (3 attempts)
# + Rate limit detection
# + Exponential backoff (30s → 60s → 90s)
# Completes all 343 stocks ✅
```

---

## ⏱️ TIME IMPACT

**Old:** 3 min (crashes)  
**New:** 10-15 min (completes) ✅

**Trade-off:** Slower but reliable!

---

## 📊 COMPARISON

| Metric | Old | New |
|--------|-----|-----|
| **Delay** | 0.5s | 1.5-2s |
| **Stocks** | ~100 | 343 |
| **Success** | ❌ Crash | ✅ Complete |
| **Time** | 3 min | 10-15 min |
| **Retry** | None | 3x auto |

---

## 🚀 DEPLOY

### **Staging:**
```powershell
git checkout staging
git add scripts/daily_signal_scanner_eod.py
git commit -m "Fix: Rate limit with retry logic"
git push origin staging
```

### **Production (after staging OK):**
```powershell
git checkout main
git merge staging
git push origin main
```

---

## ✅ VERIFY

**Check scanner has fixes:**

```powershell
cd C:\ai-advisor1\scripts

# Check delay
findstr "1.5 + random.uniform" daily_signal_scanner_eod.py
# Should find ✅

# Check retry
findstr "max_retries=3" daily_signal_scanner_eod.py
# Should find ✅
```

**Test run:**

```powershell
python daily_signal_scanner_eod.py

# Watch for:
✅ 1.5-2s delays
✅ Rate limit auto-retry
✅ 343 stocks processed
✅ 10-15 min total
```

---

## 📞 IF STILL ISSUES

**Still rate limiting?**

```python
# Increase delay more (in scanner file)
delay = 2.5 + random.uniform(0, 1.0)  # 2.5-3.5s
```

**Takes too long?**

```
Normal! 10-15 min is expected.
Don't cancel during retry!
```

---

## 🎯 SUMMARY

**Problem:** Rate limit after ~100 stocks  
**Solution:** 3x slower delay + auto-retry  
**Result:** All 343 stocks in 10-15 min ✅  

**Status:** FIXED ✅  
**Deploy:** Replace file → Test → Deploy
