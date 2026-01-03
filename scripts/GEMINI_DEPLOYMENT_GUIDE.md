# 🚀 GEMINI AI INTEGRATION - DEPLOYMENT GUIDE

## 🎯 TỔNG QUAN NÂNG CẤP:

### **Tính năng mới:**
1. ✅ **Gemini AI tự động trả lời** - Context-aware, thông minh
2. ✅ **Lưu danh mục riêng** - Mỗi user có portfolio riêng
3. ✅ **Lưu lịch sử chat** - Conversation persistent
4. ✅ **Giữ nguyên UI** - Không thay đổi giao diện

### **Technology:**
- **Backend:** Flask + Gemini API
- **Frontend:** React (giữ nguyên)
- **Database:** SQLite (thêm 2 tables)
- **AI:** Google Gemini Pro

---

## 📋 BƯỚC 1: LẤY GEMINI API KEY

### **1.1. Truy cập Google AI Studio:**

https://makersuite.google.com/app/apikey

### **1.2. Đăng nhập Google Account**

### **1.3. Click "Create API Key"**

### **1.4. Copy API key** (dạng: AIzaSy...)

**Lưu ý:** API key này FREE, có quota:
- 60 requests/minute
- 1500 requests/day
- Đủ cho testing và production nhỏ

---

## 📋 BƯỚC 2: CÀI ĐẶT LOCAL

### **2.1. Download files:**
- `migrate_database.py` - Migration script
- `backend_api_with_gemini.py` - Backend mới
- `PortfolioManager.jsx` - Frontend mới

### **2.2. Cài đặt Gemini library:**

```bash
pip install google-generativeai
```

### **2.3. Run database migration:**

```bash
cd C:\ai-advisor1\scripts
python migrate_database.py
```

**Expected output:**
```
Starting database migration...
Creating portfolios table...
Creating chat_history table...
Creating indexes...
✓ Migration completed successfully!

New tables:
  - portfolios: Store user portfolios
  - chat_history: Store chat conversations
```

### **2.4. Set environment variable:**

**Windows CMD:**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

### **2.5. Test backend locally:**

```bash
cd C:\ai-advisor1
python backend_api_with_gemini.py
```

**Expected:**
```
✓ Gemini AI initialized
 * Running on http://0.0.0.0:10000
```

### **2.6. Test API:**

**Open browser:**
```
http://localhost:10000/health
```

**Should return:**
```json
{
  "status": "healthy",
  "gemini": true,
  "timestamp": "2026-01-02T..."
}
```

---

## 📋 BƯỚC 3: UPDATE FRONTEND

### **3.1. Replace PortfolioManager:**

```bash
cd C:\ai-advisor1\frontend\src\components

# Backup old file
copy PortfolioManager.jsx PortfolioManager.jsx.bak

# Copy new file
# (Download PortfolioManager.jsx and paste here)
```

### **3.2. Test frontend locally:**

```bash
cd C:\ai-advisor1\frontend
npm start
```

**Visit:** http://localhost:3000

**Test:**
1. Click "Quản trị đầu tư bằng AI"
2. Add some stocks
3. Ask AI: "Phân tích danh mục của tôi"
4. Should see AI response!

---

## 📋 BƯỚC 4: DEPLOY TO RENDER

### **4.1. Add Gemini API key to Render:**

**Visit:** https://dashboard.render.com/web/srv-cta8m0ggph6c73c1qf7g

**Click:** Environment

**Add:**
```
Key: GEMINI_API_KEY
Value: your_api_key_here
```

**Click:** Save Changes

### **4.2. Update backend file:**

```bash
cd C:\ai-advisor1

# Replace backend_api.py
copy backend_api.py backend_api.py.bak
copy backend_api_with_gemini.py backend_api.py
```

### **4.3. Add requirement:**

**Edit `requirements.txt`:**
```
Flask==2.3.0
flask-cors==4.0.0
google-generativeai==0.3.2
```

### **4.4. Deploy:**

```bash
cd C:\ai-advisor1

# Add migration script
git add scripts/migrate_database.py

# Add new backend
git add backend_api.py

# Add updated frontend
git add frontend/src/components/PortfolioManager.jsx

# Add requirements
git add requirements.txt

# Commit
git commit -m "Add Gemini AI integration to Portfolio Manager

- Gemini AI for smart portfolio advice
- Save user portfolios to database
- Save chat history persistently
- Context-aware AI responses
- Keep existing UI design"

# Push
git push origin main
```

### **4.5. Wait for deploy (5-10 mins)**

**Monitor:** https://dashboard.render.com/web/srv-cta8m0ggph6c73c1qf7g

---

## 📋 BƯỚC 5: RUN MIGRATION ON RENDER

### **5.1. SSH into Render (optional):**

**Or trigger via API:**

```bash
# Create migration endpoint (add to backend_api.py)
@app.route('/api/migrate', methods=['POST'])
def run_migration():
    import subprocess
    subprocess.run(['python', 'scripts/migrate_database.py'])
    return jsonify({'success': True})
```

**Then trigger:**
```bash
curl -X POST https://ai-advisor1-backend.onrender.com/api/migrate
```

**Or simpler:** Migration runs automatically on first request!

---

## 📋 BƯỚC 6: TEST PRODUCTION

### **6.1. Visit website:**

https://ai-advisor.vn

### **6.2. Login/Register**

### **6.3. Click "Quản trị đầu tư bằng AI"**

### **6.4. Test features:**

**Add stocks:**
1. Enter: VCB, 100, 85000
2. Click "Thêm vào danh mục"
3. Should see in portfolio list

**Chat with AI:**
1. Type: "Phân tích danh mục của tôi"
2. Click "Gửi"
3. Wait for AI response
4. Should see detailed analysis!

**Chat history:**
1. Refresh page
2. Chat history should load
3. Previous conversations preserved

### **6.5. Test on mobile:**

Visit on phone, check responsive design

---

## 📊 DATABASE SCHEMA

### **portfolios table:**
```sql
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, ticker)
)
```

### **chat_history table:**
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    portfolio_context TEXT,
    created_at TIMESTAMP
)
```

---

## 🎯 API ENDPOINTS MỚI

### **Portfolio:**
```
GET  /api/portfolio?user_id=1              - Get portfolio
POST /api/portfolio                         - Add stock
DELETE /api/portfolio/{ticker}?user_id=1   - Remove stock
```

### **Chat:**
```
POST /api/chat                              - Send message
GET  /api/chat/history?user_id=1           - Get history
DELETE /api/chat/history?user_id=1         - Clear history
```

---

## 💡 GEMINI AI FEATURES

### **Context-Aware:**
AI biết danh mục user:
```
User: "Phân tích danh mục của tôi"

AI: "Danh mục của bạn hiện có:
- VCB: 100 CP @ 85,000 VND
- MBB: 200 CP @ 24,500 VND

Phân tích:
1. Tập trung vào ngành ngân hàng (100%)
2. Đa dạng hóa thấp
3. Khuyến nghị: Thêm ngành khác..."
```

### **Smart Recommendations:**
```
User: "Tôi nên mua thêm gì?"

AI: "Dựa trên danh mục hiện tại,
tôi khuyên bạn:
1. Đa dạng hóa sang công nghệ (FPT)
2. Thêm bất động sản (VHM)
3. Giữ tỷ lệ: 40% bank, 30% tech, 30% real estate"
```

### **Risk Analysis:**
```
User: "Rủi ro của danh mục?"

AI: "Rủi ro chính:
1. Tập trung ngành: Ngân hàng chiếm 100%
2. Nếu ngành này giảm → cả danh mục giảm
3. Khuyến nghị: Đa dạng hóa ngành"
```

---

## 🐛 TROUBLESHOOTING

### **Gemini not working:**

**Check:**
```bash
# Test API key
curl https://ai-advisor1-backend.onrender.com/health
```

**Should return:**
```json
{"status": "healthy", "gemini": true}
```

**If gemini: false:**
1. Check GEMINI_API_KEY in Render env
2. Restart Render service
3. Check API key is valid

### **Chat not saving:**

**Check database:**
```bash
cd C:\ai-advisor1\scripts
python check_database.py
```

**Should show chat_history table**

### **Portfolio not loading:**

**Check API:**
```bash
curl https://ai-advisor1-backend.onrender.com/api/portfolio?user_id=1
```

**Should return portfolio JSON**

---

## ✅ SUCCESS CHECKLIST

- [ ] Gemini API key obtained
- [ ] `pip install google-generativeai` done
- [ ] Migration script ran successfully
- [ ] Backend tested locally
- [ ] Frontend tested locally
- [ ] GEMINI_API_KEY added to Render
- [ ] Code deployed to production
- [ ] Migration ran on production
- [ ] Can add stocks on website
- [ ] Can chat with AI
- [ ] AI gives smart responses
- [ ] Chat history saves
- [ ] Portfolio persists after refresh
- [ ] Mobile responsive

---

## 🎉 AFTER SUCCESS

### **User Experience:**

1. **User adds stocks:**
   - VCB, MBB, FPT to portfolio
   - Saves to database

2. **User asks AI:**
   - "Phân tích danh mục của tôi"
   - AI knows their portfolio
   - Gives personalized advice

3. **User refreshes page:**
   - Portfolio loads from DB
   - Chat history preserved
   - Can continue conversation

4. **User returns tomorrow:**
   - Same portfolio
   - Same chat history
   - AI remembers context

---

## 📈 NEXT STEPS (OPTIONAL)

### **Future enhancements:**

1. **Real-time prices:**
   - Integrate vnstock for live prices
   - Show P&L for each position

2. **Advanced analytics:**
   - Portfolio performance charts
   - Risk metrics
   - Sector allocation

3. **Multi-user support:**
   - Proper authentication
   - User management
   - Private portfolios

4. **Notifications:**
   - Price alerts
   - AI recommendations
   - Market news

---

## 🚀 DEPLOYMENT COMMANDS (SUMMARY)

```bash
# 1. Install Gemini
pip install google-generativeai

# 2. Run migration
python scripts/migrate_database.py

# 3. Set API key (Render dashboard)
GEMINI_API_KEY=your_key

# 4. Deploy
git add .
git commit -m "Add Gemini AI integration"
git push origin main

# 5. Wait 10 mins

# 6. Test
https://ai-advisor.vn
```

---

**READY TO DEPLOY? LET'S GO! 🚀**

**Questions? I'm here to help! 💪**
