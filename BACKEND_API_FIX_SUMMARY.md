# BACKEND_API.PY - SELL SIGNAL FIX

**Date:** 2026-03-06  
**File:** backend_api.py  
**Change Type:** Add missing fields to API response

---

## ✅ CHANGES MADE

**Location:** Lines 601-604  
**Endpoint:** `/api/signals` (GET method)

### **Added 3 fields to signals API response:**

```python
# Line 601-604
# SELL signal exit fields (for SELL signals display)
'exit_price': round(s.exit_price / 100) * 100 if s.exit_price else None,
'exit_reason': s.exit_reason,
'exit_date': s.exit_date,
```

---

## 📊 BEFORE vs AFTER

### **BEFORE (Missing fields):**

API Response:
```json
{
  "signals": [
    {
      "ticker": "STB",
      "entry_price": 61100,
      "action": "SELL",
      "strategy": "TP_PULLBACK"
      // ❌ Missing: exit_price, exit_reason, exit_date
    }
  ]
}
```

Frontend Display:
```
Ticker: STB
Entry:  61,100
Exit:   -           ← Missing!
P/L:    -100.00%    ← Wrong!
```

---

### **AFTER (With exit fields):**

API Response:
```json
{
  "signals": [
    {
      "ticker": "STB",
      "entry_price": 61100,
      "exit_price": 56000,      ← NEW!
      "exit_reason": "TP_PULLBACK",  ← NEW!
      "exit_date": "2026-03-06",    ← NEW!
      "action": "SELL",
      "strategy": "TP_PULLBACK"
    }
  ]
}
```

Frontend Display:
```
Ticker: STB
Entry:  61,100
Exit:   56,000      ← Fixed!
P/L:    -8.35%      ← Correct!
Reason: ⚪ Thủ công
Date:   6/3/2026
```

---

## 🔧 IMPLEMENTATION DETAILS

### **Field Processing:**

1. **exit_price:**
   - Rounded to nearest 100 VND (same as entry_price)
   - `round(s.exit_price / 100) * 100 if s.exit_price else None`
   - Returns `None` if no exit_price in database

2. **exit_reason:**
   - Direct database value
   - Values: 'STOP_LOSS', 'TAKE_PROFIT', 'MA20_STRICT', 'TP_PULLBACK', etc.
   - Returns `None` if not set

3. **exit_date:**
   - Direct database value
   - Format: 'YYYY-MM-DD' (e.g., '2026-03-06')
   - Returns `None` if not set

---

## ✅ BACKWARD COMPATIBILITY

**Safe for existing features:**
- ✅ Only ADDS new fields, doesn't modify existing ones
- ✅ New fields return `None` for BUY signals (no exit data)
- ✅ Existing frontend code won't break (optional fields)
- ✅ Only affects SELL signals display

**What's preserved:**
- ✅ All existing 18 fields unchanged
- ✅ Deduplication logic unchanged
- ✅ Rounding logic unchanged
- ✅ Signal tracking (status/position_pct) unchanged

---

## 🚀 DEPLOYMENT STEPS

### **1. Copy updated file to project:**

```powershell
cd C:\ai-advisor1

# Backup current file
Copy-Item backend_api.py backend_api.py.backup

# Copy updated file
Copy-Item backend_api.py.NEW backend_api.py -Force
```

---

### **2. Commit and push:**

```powershell
git add backend_api.py

git commit -m "fix: Add exit_price, exit_reason, exit_date to /api/signals response

SELL signals were missing exit data in API response, causing frontend
to display incorrect P/L (-100%) and missing exit prices.

Changes:
- Add exit_price field (rounded to 100 VND, same as entry_price)
- Add exit_reason field (STOP_LOSS, TAKE_PROFIT, MA20_STRICT, etc)
- Add exit_date field (YYYY-MM-DD format)

All fields return None if not set, maintaining backward compatibility.
Only affects SELL signals display - BUY signals unaffected.

Fixes:
- Exit price now displays correctly (not '-')
- P/L percentage calculated correctly (not -100%)
- Exit date displays correctly (not 'N/A')"

git push origin main
```

---

### **3. Wait for Render auto-deploy:**

```powershell
# Open Render dashboard
Start-Process "https://dashboard.render.com"

# Select: ai-advisor1-backend
# Wait for "Deploy" to complete (green checkmark)
# Usually takes 1-2 minutes
```

---

### **4. Test API after deploy:**

```powershell
# Test API returns exit fields
$response = Invoke-RestMethod -Uri "https://ai-advisor1-backend.onrender.com/api/signals"
$sell = $response.signals | Where-Object {$_.action -eq 'SELL'} | Select-Object -First 1

# Check fields
Write-Host "exit_price: $($sell.exit_price)"
Write-Host "exit_reason: $($sell.exit_reason)"
Write-Host "exit_date: $($sell.exit_date)"

# Calculate P/L
if ($sell.exit_price -and $sell.entry_price) {
    $pl = (($sell.exit_price - $sell.entry_price) / $sell.entry_price * 100)
    Write-Host "P/L: $($pl.ToString('F2'))%"
}
```

**Expected output:**
```
exit_price: 56000
exit_reason: TP_PULLBACK
exit_date: 2026-03-06
P/L: -8.35%
```

---

### **5. Verify frontend:**

```powershell
# Open production
Start-Process "https://ai-advisor.vn"

# In browser:
# 1. Hard reload: Ctrl+Shift+R
# 2. Click "Tín hiệu BÁN" tab
# 3. Verify table shows:
#    - Exit prices (not '-')
#    - P/L percentages (not -100%)
#    - Exit dates (not 'N/A')
```

---

## 📋 VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Render deploy completed successfully
- [ ] API returns exit_price field
- [ ] API returns exit_reason field
- [ ] API returns exit_date field
- [ ] Frontend displays exit prices correctly
- [ ] Frontend displays P/L percentages correctly
- [ ] Frontend displays exit dates correctly
- [ ] BUY signals still display correctly (unchanged)
- [ ] No errors in browser console
- [ ] No errors in Render logs

---

## 🔍 TROUBLESHOOTING

### **Issue: API still returns null for exit fields**

**Cause:** Database migration not run on production

**Fix:**
```powershell
python migrate_old_sell_signals.py
# Type 'y' to confirm
```

---

### **Issue: Frontend still shows -100%**

**Cause:** Browser cache or API not deployed

**Fix:**
1. Hard reload: Ctrl+Shift+R
2. Check API directly with curl/PowerShell
3. Verify Render deployment completed

---

### **Issue: BUY signals affected**

**Cause:** Should not happen (exit fields return None for BUY signals)

**Fix:**
- Check browser console for errors
- Verify frontend code handles None values

---

## ✅ SUMMARY

**What was changed:**
- Added 3 lines of code (lines 601-604)
- Total impact: Minimal
- Risk level: Low (only adds fields, doesn't modify existing logic)

**What was NOT changed:**
- All existing 18 fields preserved
- Deduplication logic preserved
- Rounding logic preserved
- Signal tracking preserved
- BUY signals display preserved

**Expected outcome:**
- SELL signals display correctly with P/L percentages
- Exit prices show actual values (not '-')
- Exit dates show actual dates (not 'N/A')
- System fully functional and complete

---

**Status:** ✅ Ready to deploy  
**Risk:** Low  
**Impact:** Frontend SELL signals display only  
**Estimated time:** 5 minutes (2 min deploy + 3 min verify)
