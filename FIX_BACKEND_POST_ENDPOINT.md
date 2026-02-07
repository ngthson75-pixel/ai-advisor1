# 🔧 FIX BACKEND - ADD POST /api/signals ENDPOINT

## ❌ CURRENT ISSUE

```
Backend only has: GET /api/signals (line 390)
Push script needs: POST /api/signals
Result: HTTP 405 Method Not Allowed
```

---

## ✅ SOLUTION - UPDATE backend_api.py

### **STEP 1: Locate the endpoint (Line 390)**

```powershell
cd C:\ai-advisor1

# Open file
code backend_api.py
# Or: notepad backend_api.py
```

**Find line 390:**
```python
@app.route('/api/signals', methods=['GET'])  ← LINE 390
def get_signals():
```

---

### **STEP 2: Replace the endpoint (Lines 390-425)**

**DELETE these lines (390-425):**
```python
@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get all signals"""
    session = Session()
    try:
        signals = session.query(Signal).order_by(Signal.created_at.desc()).all()
        
        signals_data = []
        for s in signals:
            signals_data.append({
                'id': s.id,
                'ticker': s.ticker,
                'code': s.ticker,
                'strategy': s.strategy,
                'entry_price': s.entry_price,
                'stop_loss': s.stop_loss,
                'take_profit': s.take_profit,
                'risk_reward': s.risk_reward,
                'strength': s.strength or 0,
                'stock_type': s.stock_type,
                'rsi': s.rsi,
                'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                'action': s.action,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        
        return jsonify({
            'success': True,
            'signals': signals_data,
            'count': len(signals_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
```

**REPLACE WITH:**
```python
@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    """Get all signals (GET) or create new signal (POST)"""
    
    if request.method == 'GET':
        # Original GET functionality
        session = Session()
        try:
            signals = session.query(Signal).order_by(Signal.created_at.desc()).all()
            
            signals_data = []
            for s in signals:
                signals_data.append({
                    'id': s.id,
                    'ticker': s.ticker,
                    'code': s.ticker,
                    'strategy': s.strategy,
                    'entry_price': s.entry_price,
                    'stop_loss': s.stop_loss,
                    'take_profit': s.take_profit,
                    'risk_reward': s.risk_reward,
                    'strength': s.strength or 0,
                    'stock_type': s.stock_type,
                    'rsi': s.rsi,
                    'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                    'action': s.action,
                    'created_at': s.created_at.isoformat() if s.created_at else None
                })
            
            return jsonify({
                'success': True,
                'signals': signals_data,
                'count': len(signals_data)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()
    
    elif request.method == 'POST':
        # NEW: Create signal functionality
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['ticker', 'entry_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        session = Session()
        try:
            # Create new signal
            signal = Signal(
                ticker=data['ticker'],
                strategy=data.get('strategy'),
                entry_price=data['entry_price'],
                stop_loss=data.get('stop_loss'),
                take_profit=data.get('take_profit'),
                risk_reward=data.get('risk_reward'),
                strength=data.get('strength'),
                stock_type=data.get('stock_type'),
                rsi=data.get('rsi'),
                date=data.get('date'),
                action=data.get('action', 'BUY')
            )
            
            session.add(signal)
            session.commit()
            
            return jsonify({
                'success': True,
                'id': signal.id,
                'ticker': signal.ticker,
                'message': 'Signal created successfully'
            }), 201
            
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()
```

---

### **STEP 3: Save and deploy**

```powershell
cd C:\ai-advisor1

# Test locally (optional)
python backend_api.py
# Should start without errors

# Commit
git add backend_api.py
git commit -m "feat: Add POST /api/signals endpoint for push script"

# Deploy
git push origin main
```

---

### **STEP 4: Wait for Render deployment**

```
1. Visit: https://dashboard.render.com
2. Service: ai-advisor1-backend
3. Events tab: Wait for "Deploy succeeded"
4. Duration: 3-5 minutes
```

---

### **STEP 5: Test POST endpoint**

```powershell
# Test POST request
$body = @{
    ticker = "TEST"
    entry_price = 10000
    strategy = "PULLBACK"
    date = "2026-01-30"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals" `
  -Method POST `
  -Body $body `
  -ContentType "application/json" `
  -UseBasicParsing

# Should return: 201 Created
# {"success":true,"id":...,"ticker":"TEST","message":"Signal created successfully"}
```

---

### **STEP 6: Push local signals again**

```powershell
cd C:\ai-advisor1

# Run push script
python push_local_signals.py

# Expected:
# ✓ Success: 132/132
# ✗ Failed: 0/132
```

---

## 📋 WHAT CHANGED

### **Before:**
```python
@app.route('/api/signals', methods=['GET'])  ← Only GET
def get_signals():
    # Only read signals
```

### **After:**
```python
@app.route('/api/signals', methods=['GET', 'POST'])  ← GET + POST
def signals_endpoint():
    if request.method == 'GET':
        # Read signals (same as before)
    elif request.method == 'POST':
        # Create signal (NEW!)
```

---

## ✅ VERIFICATION

### **Test GET (should still work):**
```powershell
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals
# Should return signals as before
```

### **Test POST (new feature):**
```powershell
$body = '{"ticker":"VCB","entry_price":85000}' | ConvertTo-Json
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals" -Method POST -Body $body -ContentType "application/json"
# Should return 201 with success message
```

---

## 🎯 COMPLETE WORKFLOW AFTER FIX

```powershell
# 1. Edit backend_api.py (add POST support)
code backend_api.py

# 2. Deploy
git add backend_api.py
git commit -m "feat: Add POST /api/signals"
git push origin main

# 3. Wait for deployment (5 min)

# 4. Push local signals
python push_local_signals.py
# Choose: 1 (Production)
# Result: ✓ 132/132 success!

# 5. Verify website
# Browser: https://ai-advisor.vn
# Ctrl + Shift + R
# Should see: 132 signals dated 2026-01-30
```

---

## 🆘 TROUBLESHOOTING

### **Still 405 after deployment:**
```
1. Check deployment finished
2. Hard refresh Render page
3. Check logs for errors
4. Try curl test
```

### **500 error after POST:**
```
1. Check Render logs
2. Verify database connection
3. Check Signal model matches data
```

### **Deployment fails:**
```
1. Check syntax errors
2. Verify indentation (Python)
3. Check Render logs
4. Rollback if needed
```

---

**TOTAL TIME:** 10-15 minutes (including deployment)

**DIFFICULTY:** Easy (copy-paste replacement)

**FILES TO CHANGE:** 1 (backend_api.py only)

---

**NEXT:** After fixing, run `python push_local_signals.py` again! 🚀
