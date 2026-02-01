# 🚀 DEPLOYMENT GUIDE - Portfolio Manager v2.0

## 📋 PRE-DEPLOYMENT CHECKLIST

### **Files to Deploy:**
- [ ] `frontend/src/components/AIPortfolioManager.jsx` (NEW)
- [ ] `frontend/src/App.css` (ADD responsive CSS)
- [ ] `backend_api.py` (ADD price endpoint code)
- [ ] `scripts/update_portfolio_prices.py` (NEW)
- [ ] `requirements.txt` (verify vnstock dependency)

### **Environment Variables to Check:**
- [ ] OPENAI_API_KEY (backend)
- [ ] ANTHROPIC_API_KEY (if using Claude)

---

## 🔧 STEP 1: PREPARE LOCAL FILES

### **1.1: Update Frontend**

```bash
# Navigate to project root
cd C:\ai-advisor1

# Copy new AIPortfolioManager.jsx
# From: /home/claude/AIPortfolioManager.jsx
# To: frontend/src/components/AIPortfolioManager.jsx
```

### **1.2: Add Responsive CSS**

Open `frontend/src/App.css` and add at the end:

```css
/* Copy from portfolio-responsive.css */

/* Desktop: 2 columns side-by-side */
.portfolio-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 24px;
}

/* Mobile: stack vertically */
@media (max-width: 768px) {
  .portfolio-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .portfolio-section {
    order: 1;
  }
  
  .chat-section {
    order: 2;
  }
  
  .portfolio-section,
  .chat-section {
    padding: 16px;
  }
}

/* ... rest of responsive CSS ... */
```

### **1.3: Update Backend**

Open `backend_api.py` and add:

```python
# Add at the end of file, before if __name__ == '__main__':

# ============================================================================
# AUTO-FETCH STOCK PRICE ENDPOINT
# ============================================================================

@app.route('/api/stock/current-price', methods=['GET'])
def get_current_price():
    """Get current/latest EOD price for a stock"""
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({'success': False, 'error': 'Ticker required'}), 400
    
    ticker = ticker.upper()
    
    try:
        stock_api = Vnstock()
        stock = stock_api.stock(symbol=ticker, source='VCI')
        
        # Try intraday first
        try:
            intraday = stock.quote.intraday(symbol=ticker, page_size=1)
            if not intraday.empty:
                price = float(intraday['close'].iloc[-1])
                return jsonify({
                    'success': True,
                    'price': price,
                    'source': 'intraday',
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker
                })
        except:
            pass
        
        # Fallback to EOD
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        daily = stock.quote.history(symbol=ticker, start=yesterday, end=today)
        
        if not daily.empty:
            price = float(daily['close'].iloc[-1])
            return jsonify({
                'success': True,
                'price': price,
                'source': 'eod',
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker
            })
        
        return jsonify({
            'success': False,
            'error': f'No price data found for {ticker}',
            'ticker': ticker
        }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker
        }), 500
```

### **1.4: Add Auto-Update Script**

```bash
# Create scripts directory if not exists
mkdir -p scripts

# Copy update_portfolio_prices.py
# From: /home/claude/update_portfolio_prices.py
# To: scripts/update_portfolio_prices.py
```

### **1.5: Verify Dependencies**

Check `requirements.txt` includes:

```
vnstock>=3.3.0
```

---

## 🧪 STEP 2: LOCAL TESTING

### **2.1: Test Frontend Locally**

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

Test:
- [ ] Add stock (VCB, 100, 85000)
- [ ] Check auto-price fetching
- [ ] Check P/L calculation
- [ ] Check responsive layout (resize browser)
- [ ] Chat with AI
- [ ] Refresh - data persists

### **2.2: Test Backend Locally**

```bash
# Terminal 1: Run backend
cd C:\ai-advisor1
python backend_api.py

# Terminal 2: Test endpoints
# Price endpoint
curl http://localhost:10000/api/stock/current-price?ticker=VCB

# Chat endpoint
curl -X POST http://localhost:10000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Hello","portfolio":[]}'
```

Expected:
- [ ] Price endpoint returns price
- [ ] Chat endpoint returns AI response

---

## 📤 STEP 3: COMMIT & PUSH

### **3.1: Git Add**

```bash
cd C:\ai-advisor1

# Check what changed
git status

# Add modified files
git add frontend/src/components/AIPortfolioManager.jsx
git add frontend/src/App.css
git add backend_api.py
git add scripts/update_portfolio_prices.py

# Check again
git status
```

### **3.2: Commit**

```bash
git commit -m "✅ Portfolio Manager v2.0: Auto EOD price + ChatGPT-4o + Responsive

Features:
- Auto-fetch current price from VNStock
- Tiền mặt field
- Remove manual 'Giá hiện tại' input
- Responsive layout (mobile: stack vertically)
- Remove '(Gemini)' text
- Update subtitle
- Daily auto-update script
- Backend price endpoint

Technical:
- Frontend: AIPortfolioManager.jsx rewrite
- Backend: /api/stock/current-price endpoint
- Script: update_portfolio_prices.py
- CSS: Responsive breakpoints @768px
"
```

### **3.3: Push**

```bash
git push origin main
```

Expected output:
```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 15.2 KiB | 1.5 MiB/s, done.
Total 8 (delta 4), reused 0 (delta 0)
To https://github.com/ngthson75-pixel/ai-advisor1.git
   abc1234..def5678  main -> main
```

---

## ⏳ STEP 4: WAIT FOR DEPLOYMENT

### **4.1: Monitor Render (Backend)**

1. Visit: https://dashboard.render.com
2. Click: `ai-advisor1-backend`
3. Click: "Events" tab

Expected timeline:
```
[17:35:01] Build started
[17:35:15] Installing dependencies...
[17:36:00] Build successful
[17:36:15] Deploying...
[17:36:45] Live
```

⏱️ Total time: ~5-7 minutes

### **4.2: Monitor Cloudflare Pages (Frontend)**

1. Visit: https://dash.cloudflare.com
2. Workers & Pages → `ai-advisor`
3. Click latest deployment

Expected timeline:
```
[17:35:10] Initializing build environment
[17:35:30] Cloning repository
[17:35:45] Installing dependencies
[17:37:00] Building application
[17:38:00] Deploying to Cloudflare network
[17:38:30] Success
```

⏱️ Total time: ~8-10 minutes

### **4.3: Check Deploy Status**

```bash
# Check backend
curl https://ai-advisor1-backend.onrender.com/health

# Expected: {"status":"healthy"}

# Check price endpoint
curl https://ai-advisor1-backend.onrender.com/api/stock/current-price?ticker=VCB

# Expected: {"success":true,"price":96500,...}
```

---

## ✅ STEP 5: POST-DEPLOYMENT VERIFICATION

### **5.1: Clear Browser Cache**

```
Method 1: Hard refresh
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)

Method 2: Clear cache
F12 → Application → Storage → Clear site data

Method 3: Incognito
Ctrl + Shift + N
```

### **5.2: Test Production**

Visit: https://ai-advisor.vn

#### **Test 1: UI Verification**
- [ ] Subtitle: "Hãy chia sẻ danh mục..."
- [ ] No "(Gemini)" text
- [ ] "Tiền mặt" field visible
- [ ] No "Giá hiện tại" input
- [ ] Responsive on mobile (use F12 → Device Toolbar)

#### **Test 2: Functionality**
- [ ] Add VCB → Auto-price fetches
- [ ] P/L calculates correctly
- [ ] Chat works (ChatGPT-4o responds)
- [ ] Refresh → Data persists
- [ ] Delete stock works

#### **Test 3: Mobile (Real Device)**
- [ ] Open on phone: https://ai-advisor.vn
- [ ] Portfolio section on TOP
- [ ] Chat section BELOW
- [ ] Touch-friendly buttons
- [ ] No horizontal scroll

### **5.3: Monitor Logs**

**Render logs:**
```
Dashboard → ai-advisor1-backend → Logs

Look for:
✅ "POST /api/stock/current-price" 200
✅ "POST /api/chat" 200
❌ Any 500 errors
```

**Browser console:**
```
F12 → Console

Look for:
✅ "Portfolio loaded: X positions"
✅ "Fetched VCB price: 96500"
❌ Any red errors
```

---

## 🔧 STEP 6: SETUP CRON JOB (Optional - for later)

### **6.1: Create Render Cron Job**

1. Render Dashboard → ai-advisor1-backend
2. Settings → Add Cron Job
3. Configure:
   ```
   Name: Daily Portfolio Price Update
   Schedule: 0 17 * * 1-5
   Command: python scripts/update_portfolio_prices.py
   ```
4. Save

This runs Mon-Fri at 5PM (after market close)

### **6.2: Test Cron Job Manually**

```bash
# SSH to Render (if possible) or run locally to verify
python scripts/update_portfolio_prices.py

# Expected output:
# ✅ Updated X portfolio entries
```

### **6.3: Monitor Cron Job**

Check Render logs next day after 5PM to verify it ran.

---

## 🐛 STEP 7: TROUBLESHOOTING

### **Issue 1: Frontend shows old version**

**Symptoms:**
- Still see "(Gemini)" text
- Old subtitle
- Old layout

**Fix:**
```
1. Check Cloudflare Pages deploy succeeded
2. Hard refresh: Ctrl + Shift + R
3. Clear all cookies/cache
4. Try incognito: Ctrl + Shift + N
5. Wait 5 more minutes (CDN cache)
```

### **Issue 2: Price fetch fails**

**Symptoms:**
- Error: "Cannot fetch current price"
- Stock added but currentPrice = entryPrice

**Fix:**
```
1. Check Render backend logs
2. Verify vnstock dependency installed
3. Test endpoint:
   curl https://ai-advisor1-backend.onrender.com/api/stock/current-price?ticker=VCB
4. Check error message
```

### **Issue 3: ChatGPT-4o not responding**

**Symptoms:**
- Chat loading forever
- Error: "Backend response failed"

**Fix:**
```
1. Check OPENAI_API_KEY in Render env variables
2. Check Render logs for errors
3. Verify /api/chat endpoint works:
   curl -X POST https://ai-advisor1-backend.onrender.com/api/chat \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","message":"Hello","portfolio":[]}'
```

### **Issue 4: Responsive not working**

**Symptoms:**
- Mobile still shows 2 columns
- Horizontal scroll on mobile

**Fix:**
```
1. Check App.css deployed
2. Verify CSS media queries:
   F12 → Sources → App.css → search "@media"
3. Force refresh CSS:
   Ctrl + F5
```

---

## 📊 STEP 8: SUCCESS VERIFICATION

### **Final Checklist:**

#### Frontend:
- [ ] Subtitle updated
- [ ] No "(Gemini)" text
- [ ] "Tiền mặt" field present
- [ ] Auto-price fetching works
- [ ] Responsive layout works
- [ ] Mobile tested

#### Backend:
- [ ] /health endpoint: 200 OK
- [ ] /api/stock/current-price: working
- [ ] /api/chat: ChatGPT-4o responding
- [ ] Data persisting correctly

#### Production:
- [ ] https://ai-advisor.vn accessible
- [ ] All features working
- [ ] No console errors
- [ ] Performance acceptable (<3s load)

---

## 🎉 DEPLOYMENT COMPLETE!

```
✅ Frontend deployed to Cloudflare Pages
✅ Backend deployed to Render
✅ All features verified
✅ Mobile responsive
✅ ChatGPT-4o integration working
✅ Auto-price fetching functional

Total deployment time: ~20-30 minutes
```

---

## 📝 POST-DEPLOYMENT NOTES

**Deployed by:** _________________
**Deployment date:** _________________
**Version:** 2.0
**Git commit:** _________________

**Issues encountered:**
_______________________________________________
_______________________________________________

**Performance metrics:**
- Load time: _______ seconds
- Price fetch: _______ seconds
- Chat response: _______ seconds

**Next steps:**
- [ ] Monitor user feedback
- [ ] Track error logs
- [ ] Setup cron job (if not done)
- [ ] Consider PostgreSQL migration (for data persistence)

---

**Need help?**
- Check: TROUBLESHOOTING_GUIDE.md
- Check: TESTING_CHECKLIST.md
- Render logs: https://dashboard.render.com
- Cloudflare logs: https://dash.cloudflare.com
