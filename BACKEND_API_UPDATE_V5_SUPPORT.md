# BACKEND API UPDATE FOR V5 SUPPORT

**Purpose:** Backend cần xử lý bán từng phần (50%, 30%, 20%)  
**File:** backend_api.py  
**Impact:** POST /api/signals endpoint  

---

## 🎯 REQUIREMENTS

V5 scanner sẽ gửi SELL signals với `exit_quantity_pct`:
```json
{
  "ticker": "VCB",
  "action": "SELL",
  "strategy": "TAKE_PROFIT_1",
  "exit_quantity_pct": 50,       // ← NEW FIELD
  "buy_signal_code": "VCB-123"
}
```

Backend phải:
1. ✅ Nhận `exit_quantity_pct` field
2. ✅ Tìm BUY signal tương ứng
3. ✅ Update `position_pct` của BUY signal đúng
4. ✅ Set `status` của BUY signal (open/partial/closed)

---

## 📝 CURRENT CODE (backend_api.py)

**Location:** Lines 560-590 (POST /api/signals endpoint)

**Current logic:**
```python
@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    if request.method == 'POST':
        # ... create signal ...
        
        if signal.action == 'SELL':
            signal.status = 'closed'
            signal.position_pct = 0
            
            # Auto-update BUY (FIFO)
            buy_update_info = auto_update_buy_status(signal.ticker, session)
            # ...
```

**Problem:** Luôn set `position_pct = 0` → không support bán từng phần!

---

## ✅ UPDATED CODE

### Update 1: Accept exit_quantity_pct Field

**Line ~562:**
```python
@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    if request.method == 'POST':
        data = request.json
        
        # NEW: Get exit_quantity_pct from request
        exit_quantity_pct = data.get('exit_quantity_pct', 100)  # Default 100%
        
        signal = Signal(
            ticker=data['ticker'],
            action=data.get('action', 'BUY'),
            strategy=data.get('strategy', ''),
            entry_price=data.get('entry_price', 0),
            stop_loss=data.get('stop_loss', 0),
            take_profit=data.get('take_profit', 0),
            # ... other fields ...
        )
```

---

### Update 2: Update auto_update_buy_status Function

**Current (lines 614-670):**
```python
def auto_update_buy_status(ticker, session):
    """Tìm BUY signal cũ nhất → update status = 'closed'"""
    
    buy_signal = session.query(Signal).filter(
        Signal.ticker == ticker,
        Signal.action == 'BUY',
        Signal.status.in_(['open', 'partial'])
    ).order_by(Signal.date.asc()).first()
    
    if not buy_signal:
        return None
    
    buy_signal.status = 'closed'  # ← HARD-CODED!
    buy_signal.position_pct = 0   # ← HARD-CODED!
    
    session.commit()
    return {'buy_signal_code': buy_signal.signal_code}
```

**NEW (support partial selling):**
```python
def auto_update_buy_status(ticker, session, sell_pct=100):
    """
    Tìm BUY signal cũ nhất (FIFO) và update position_pct
    
    Args:
        ticker: Mã cổ phiếu
        session: DB session
        sell_pct: % bán (50, 30, 20, 100)
    
    Returns:
        dict with buy_signal_code and new position_pct
    """
    
    # Tìm BUY signal cũ nhất còn vị thế > 0
    buy_signal = session.query(Signal).filter(
        Signal.ticker == ticker,
        Signal.action == 'BUY',
        Signal.status.in_(['open', 'partial'])
    ).order_by(
        Signal.date.asc(),
        Signal.created_at.asc()
    ).first()
    
    if not buy_signal:
        print(f"⚠️ No open BUY signal for {ticker}")
        return None
    
    # Get current position
    current_pct = buy_signal.position_pct if buy_signal.position_pct is not None else 100
    
    # Calculate new position after selling
    new_pct = max(0, current_pct - sell_pct)
    
    # Determine new status
    if new_pct == 0:
        new_status = 'closed'
    elif new_pct < 100:
        new_status = 'partial'
    else:
        new_status = 'open'
    
    old_status = buy_signal.status or 'open'
    buy_code = buy_signal.signal_code or f"{buy_signal.ticker}-{buy_signal.id}"
    
    # Update BUY signal
    buy_signal.status = new_status
    buy_signal.position_pct = new_pct
    
    print(f"✅ BUY {buy_code}: {old_status} ({current_pct}%) → {new_status} ({new_pct}%)")
    
    session.commit()
    
    return {
        'buy_signal_code': buy_code,
        'old_status': old_status,
        'new_status': new_status,
        'old_position_pct': current_pct,
        'new_position_pct': new_pct,
        'sell_pct': sell_pct
    }
```

---

### Update 3: Call auto_update_buy_status with sell_pct

**Line ~575 (in POST /api/signals):**
```python
if request.method == 'POST':
    data = request.json
    
    # Get exit_quantity_pct
    exit_quantity_pct = data.get('exit_quantity_pct', 100)
    
    # ... create signal ...
    
    if signal.action == 'SELL':
        signal.status = 'closed'
        signal.position_pct = 0
        
        # NEW: Pass sell_pct to auto_update function
        buy_update_info = auto_update_buy_status(
            signal.ticker, 
            session,
            sell_pct=exit_quantity_pct  # ← Pass the % here
        )
        
        if buy_update_info:
            signal.buy_signal_code = buy_update_info['buy_signal_code']
            
            # Log for debugging
            print(f"📊 SELL {signal.ticker}:")
            print(f"   Sell: {exit_quantity_pct}%")
            print(f"   BUY {buy_update_info['buy_signal_code']}: " +
                  f"{buy_update_info['old_position_pct']}% → {buy_update_info['new_position_pct']}%")
```

---

## 📝 COMPLETE UPDATED FUNCTION

**Replace entire auto_update_buy_status function:**

```python
def auto_update_buy_status(ticker, session, sell_pct=100):
    """
    Auto-update BUY signal position when SELL signal created (V5 support)
    
    Logic:
      - Tìm BUY signal cũ nhất (FIFO) còn vị thế > 0
      - Giảm position_pct theo sell_pct
      - Update status: open → partial → closed
    
    Examples:
      current=100%, sell=50% → new=50%, status=partial
      current=50%, sell=30% → new=20%, status=partial
      current=20%, sell=20% → new=0%, status=closed
    
    Args:
        ticker (str): Stock ticker
        session: SQLAlchemy session
        sell_pct (int): Percentage to sell (default 100)
    
    Returns:
        dict: {
            'buy_signal_code': str,
            'old_status': str,
            'new_status': str,
            'old_position_pct': int,
            'new_position_pct': int,
            'sell_pct': int
        } or None if no BUY signal found
    """
    try:
        # Tìm BUY signal cũ nhất còn vị thế (FIFO)
        buy_signal = session.query(Signal).filter(
            Signal.ticker == ticker,
            Signal.action == 'BUY',
            Signal.status.in_(['open', 'partial'])
        ).order_by(
            Signal.date.asc(),
            Signal.created_at.asc()
        ).first()
        
        if not buy_signal:
            # Try fallback: BUY signals without status (old data)
            buy_signal = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.action == 'BUY',
                Signal.status == None
            ).order_by(
                Signal.date.asc(),
                Signal.created_at.asc()
            ).first()
            
            if not buy_signal:
                print(f"⚠️ No open BUY signal found for {ticker}")
                return None
        
        # Get current state
        current_pct = buy_signal.position_pct if buy_signal.position_pct is not None else 100
        old_status = buy_signal.status or 'open'
        buy_code = buy_signal.signal_code or f"{buy_signal.ticker}-{buy_signal.id}"
        
        # Calculate new position
        new_pct = max(0, current_pct - sell_pct)
        
        # Determine new status
        if new_pct == 0:
            new_status = 'closed'
        elif new_pct < 100:
            new_status = 'partial'
        else:
            new_status = 'open'
        
        # Update BUY signal via ORM
        buy_signal.status = new_status
        buy_signal.position_pct = new_pct
        
        # Log
        print(f"✅ BUY {buy_code}: {old_status} ({current_pct}%) → {new_status} ({new_pct}%) [sold {sell_pct}%]")
        
        return {
            'buy_signal_code': buy_code,
            'old_status': old_status,
            'new_status': new_status,
            'old_position_pct': current_pct,
            'new_position_pct': new_pct,
            'sell_pct': sell_pct
        }
        
    except Exception as e:
        print(f"❌ Error in auto_update_buy_status for {ticker}: {e}")
        return None
```

---

## 🧪 TESTING

### Test 1: Bán 50% @ TP1

```powershell
$body = @{
    ticker = "VCB"
    action = "SELL"
    strategy = "TAKE_PROFIT_1"
    entry_price = 68000
    stop_loss = 64600
    take_profit = 73400
    exit_quantity_pct = 50
    buy_signal_code = "VCB-123"
    date = "2026-02-19"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:10000/api/signals" `
    -Method POST -Body $body -ContentType "application/json"
```

**Expected backend log:**
```
✅ BUY VCB-123: open (100%) → partial (50%) [sold 50%]
```

**Verify:**
```powershell
$r = Invoke-RestMethod -Uri "http://localhost:10000/api/signals"
$r.signals | Where-Object { $_.signal_code -eq "VCB-123" } | 
    Select ticker, status, position_pct
```

**Expected:**
```
ticker status  position_pct
------ ------  ------------
VCB    partial 50
```

---

### Test 2: Bán 30% @ TP2 (từ 50% còn lại)

```powershell
$body = @{
    ticker = "VCB"
    action = "SELL"
    strategy = "TAKE_PROFIT_2"
    exit_quantity_pct = 30
    buy_signal_code = "VCB-123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:10000/api/signals" `
    -Method POST -Body $body -ContentType "application/json"
```

**Expected:**
```
✅ BUY VCB-123: partial (50%) → partial (20%) [sold 30%]
```

**Verify:**
```
ticker status  position_pct
------ ------  ------------
VCB    partial 20
```

---

### Test 3: Bán 20% cuối @ Trailing Stop

```powershell
$body = @{
    ticker = "VCB"
    action = "SELL"
    strategy = "TRAILING_STOP"
    exit_quantity_pct = 20
    buy_signal_code = "VCB-123"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:10000/api/signals" `
    -Method POST -Body $body -ContentType "application/json"
```

**Expected:**
```
✅ BUY VCB-123: partial (20%) → closed (0%) [sold 20%]
```

**Verify:**
```
ticker status position_pct
------ ------ ------------
VCB    closed 0
```

---

## ✅ DEPLOYMENT

### Step 1: Update backend_api.py

```python
# Replace auto_update_buy_status function (lines 614-670)
# with the new version above
```

### Step 2: Test locally

```powershell
cd C:\ai-advisor1
python backend_api.py

# In another terminal, run tests above
```

### Step 3: Deploy to staging

```powershell
git add backend_api.py
git commit -m "feat: Support V5 partial selling (exit_quantity_pct)"
git push origin staging
```

### Step 4: Test staging

```powershell
# Use staging URL in tests
# https://ai-advisor1-staging.onrender.com/api/signals
```

### Step 5: Deploy to production

```powershell
git checkout main
git merge staging
git push origin main
```

---

## 🔍 VERIFICATION CHECKLIST

After deployment, verify:

- [ ] POST /api/signals accepts `exit_quantity_pct` field
- [ ] Bán 50% → BUY signal position_pct = 50
- [ ] Bán 30% từ 50% → position_pct = 20
- [ ] Bán 20% từ 20% → position_pct = 0, status = closed
- [ ] Bán 100% → position_pct = 0, status = closed (normal)
- [ ] Backend log shows correct calculations
- [ ] No errors in Render logs

---

## 🆘 TROUBLESHOOTING

### Issue: position_pct not updating

**Check:**
```python
# In auto_update_buy_status, verify:
buy_signal.position_pct = new_pct  # ORM update
session.commit()  # Must commit!
```

### Issue: Negative position_pct

**Add validation:**
```python
new_pct = max(0, current_pct - sell_pct)  # Ensure >= 0
```

### Issue: Multiple BUY signals matched

**Verify FIFO order:**
```python
.order_by(Signal.date.asc(), Signal.created_at.asc())  # Oldest first
```

---

**READY TO UPDATE BACKEND!** 🚀

Apply changes to backend_api.py and test!
