# DEPLOY SELL SCANNER - CORRECT ARCHITECTURE

**Date:** 2026-02-05  
**Version:** Fixed Architecture  
**Status:** Ready to Deploy  

---

## 🎯 PROBLEM & SOLUTION

### ❌ OLD ARCHITECTURE (WRONG):
```
GitHub Actions → Run scanner LOCAL → SQLite local
                                   ↓
                            NO BUY signals!
                            ↓
                      0 SELL signals generated
```

### ✅ NEW ARCHITECTURE (CORRECT):
```
GitHub Actions → Backend API /api/scan-sell
                           ↓
                PostgreSQL Production (447 BUY signals)
                           ↓
                Get BUY tickers → VCI data → Check conditions
                           ↓
                Save SELL signals → Display on website
```

---

## 📋 DEPLOYMENT STEPS

### STEP 1: Add Scanner to Backend (5 phút)

```powershell
cd C:\ai-advisor1

# 1. Copy scanner file to backend location
Copy-Item sell_signal_scanner_v2.py . -Force

# 2. Verify file exists
Get-Content sell_signal_scanner_v2.py -Head 20

# 3. Add to git
git add sell_signal_scanner_v2.py
git commit -m "feat: Add SELL scanner for backend"
git push origin main
```

**Wait 3-5 minutes for Render to deploy**

---

### STEP 2: Add API Endpoint to Backend (10 phút)

**File:** `backend_api.py`

**Location:** Find the section after `/api/scan` endpoint

**Add this code:**

```python
# ============================================================================
# SELL SIGNAL SCANNER ENDPOINT
# ============================================================================

import threading
from sell_signal_scanner_v2 import SellSignalScannerV2

@app.route('/api/scan-sell', methods=['POST'])
def scan_sell_signals():
    """Trigger SELL signal scanner"""
    
    def run_scanner():
        try:
            days = request.json.get('days', 2) if request.json else 2
            print(f"🔍 Starting SELL scanner (days={days})...")
            
            # Use production database
            db_path = os.getenv('DATABASE_URL', 'signals.db')
            if db_path.startswith('postgres://'):
                db_path = db_path.replace('postgres://', 'postgresql://')
            
            # Run scanner
            scanner = SellSignalScannerV2(db_path=db_path)
            sell_signals = scanner.scan(days=days, delay=2.0)
            
            print(f"✓ Generated {len(sell_signals)} SELL signals")
            
        except Exception as e:
            print(f"❌ Scanner error: {e}")
    
    try:
        thread = threading.Thread(target=run_scanner)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'SELL scanner started. This will take 2-5 minutes.',
            'status': 'scanning'
        }), 202
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scan-sell/status', methods=['GET'])
def get_sell_scan_status():
    """Get SELL scanner status"""
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Query SELL signals today
        sell_signals = Signal.query.filter(
            Signal.action == 'SELL',
            Signal.exit_date == today
        ).all()
        
        # Group by reason
        by_reason = {}
        for sig in sell_signals:
            reason = sig.exit_reason or 'UNKNOWN'
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        return jsonify({
            'success': True,
            'date': today,
            'total_sell_signals': len(sell_signals),
            'by_reason': by_reason
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Then:**

```powershell
# Commit changes
git add backend_api.py
git commit -m "feat: Add /api/scan-sell endpoint"
git push origin main
```

---

### STEP 3: Update GitHub Actions Workflow (2 phút)

```powershell
cd C:\ai-advisor1

# 1. Backup old workflow
Copy-Item .github\workflows\hourly-sell-scanner.yml .github\workflows\hourly-sell-scanner.yml.backup

# 2. Copy new workflow
Copy-Item hourly-sell-scanner-api.yml .github\workflows\hourly-sell-scanner.yml -Force

# 3. Verify
Get-Content .github\workflows\hourly-sell-scanner.yml -Head 30

# 4. Push to production
git add .github\workflows\hourly-sell-scanner.yml
git commit -m "fix: Update SELL scanner to use backend API"
git push origin main
```

---

### STEP 4: Verify Deployment (5 phút)

#### A. Check Backend Deployed

```
1. Visit: https://dashboard.render.com
2. Click: ai-advisor1-backend
3. Check: Latest deploy successful
4. Check logs for: "✓ Added column: exit_reason" (migration)
```

#### B. Test API Endpoint

```powershell
# Test health
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/health"

# Test trigger SELL scanner
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell" -Method POST

# Wait 3 minutes...

# Check status
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status" | ConvertFrom-Json
```

**Expected output:**
```json
{
  "success": true,
  "date": "2026-02-05",
  "total_sell_signals": 26,
  "by_reason": {
    "SL": 2,
    "TP_PARTIAL": 3,
    "MA20_CONSECUTIVE": 20,
    "MA20_HIGH_VOLUME": 1
  }
}
```

#### C. Test GitHub Actions

```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Click: "Hourly SELL Signal Scanner - Backend API"
3. Click: "Run workflow" → main branch
4. Wait 5 minutes
5. Check logs show: "✅ Generated X SELL signals today"
```

---

## 🔍 TROUBLESHOOTING

### Issue 1: Scanner file not found on backend

**Error:** `ModuleNotFoundError: No module named 'sell_signal_scanner_v2'`

**Solution:**
```powershell
# Verify file pushed
git log --oneline -5 | findstr "SELL scanner"

# Re-push if needed
git add sell_signal_scanner_v2.py
git commit -m "fix: Ensure SELL scanner on backend"
git push origin main
```

---

### Issue 2: Database columns missing

**Error:** `no such column: exit_reason`

**Solution:** Backend auto-migrates on startup. If not working:

```python
# Add to backend_api.py after app initialization:
with app.app_context():
    db.engine.execute("""
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS exit_reason VARCHAR(50);
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS exit_date DATE;
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS profit_loss_pct FLOAT;
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS exit_quantity_pct FLOAT;
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS buy_signal_id INTEGER;
    ALTER TABLE signals ADD COLUMN IF NOT EXISTS volume_ratio FLOAT;
    """)
```

---

### Issue 3: No SELL signals generated

**Check backend logs:**
```
Render → ai-advisor1-backend → Logs
Look for:
  "⚠ No tickers" → No BUY signals in last 2 days
  "✓ Generated X SELL signals" → Success
```

**If "No tickers":**
```
1. Check BUY signals exist:
   GET /api/signals → Should show BUY signals with recent dates

2. If no recent BUY signals:
   POST /api/scan → Run BUY scanner first
   Wait 20-25 minutes
   Then POST /api/scan-sell
```

---

### Issue 4: Workflow fails

**Error:** `curl: (7) Failed to connect`

**Solution:** Backend sleeping. Workflow already includes wake-up step, but if fails:

```yaml
# Increase retries in workflow:
for i in {1..5}; do  # Was 3, now 5
  curl -s "${{ env.API_URL }}/signals" > /dev/null && break
  sleep 15  # Longer delay
done
```

---

## 📊 EXPECTED RESULTS

### First Run (After Deploy):

```
📊 SCAN RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before:       447 signals
After:        473 signals
New:          26 signals
SELL today:   26 signals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

By reason:
  SL: 2
  TP_PARTIAL: 3
  MA20_CONSECUTIVE: 20
  MA20_HIGH_VOLUME: 1

✅ Generated 26 SELL signals today
```

### Hourly Runs:

```
9:00 AM:  26 SELL signals
10:00 AM: 3 new SELL signals (market updates)
11:00 AM: 1 new SELL signal
1:00 PM:  5 new SELL signals
2:00 PM:  2 new SELL signals
```

---

## ✅ DEPLOYMENT CHECKLIST

**Backend:**
- [ ] sell_signal_scanner_v2.py pushed to main
- [ ] API endpoint /api/scan-sell added
- [ ] API endpoint /api/scan-sell/status added
- [ ] Backend deployed successfully
- [ ] Database migration ran (columns added)

**Workflow:**
- [ ] New workflow file pushed
- [ ] Workflow calls backend API (not local)
- [ ] Manual trigger successful
- [ ] SELL signals generated

**Verification:**
- [ ] API health check OK
- [ ] POST /api/scan-sell returns 202
- [ ] GET /api/scan-sell/status returns data
- [ ] GitHub Actions run successful
- [ ] SELL signals visible on website

---

## 🎯 BENEFITS OF NEW ARCHITECTURE

✅ **Correct data source** - Uses production PostgreSQL with real BUY signals
✅ **No local dependencies** - Scanner runs on backend, not GitHub Actions
✅ **Faster** - API call takes seconds, scan runs in background
✅ **Reliable** - Backend always has access to database
✅ **Scalable** - Can add more endpoints, features easily
✅ **Monitorable** - Check status via API anytime

---

## 📞 SUPPORT

**Files created:**
- `backend_sell_endpoint.py` - Code to add to backend
- `hourly-sell-scanner-api.yml` - Updated workflow
- `DEPLOY_SELL_SCANNER_CORRECT.md` - This guide

**Resources:**
- Backend: https://ai-advisor1-backend.onrender.com
- GitHub Actions: https://github.com/ngthson75-pixel/ai-advisor1/actions
- Render Dashboard: https://dashboard.render.com

**Contact:**
- Owner: Nguyễn Thanh Sơn
- Email: ngthson75@gmail.com
- Phone: +84938127666

---

## 🚀 READY TO DEPLOY

Follow STEP 1-4 above in order.

Total time: ~20 minutes

**After deployment, SELL scanner will:**
- Run every hour during trading (9 AM - 2 PM)
- Scan BUY signals from production database
- Generate SELL signals automatically
- Users see signals on website immediately

Good luck! 🍀
