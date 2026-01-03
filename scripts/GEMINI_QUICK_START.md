# ⚡ GEMINI AI - QUICK START (5 PHÚT)

## 🎯 TÍNH NĂNG MỚI:

✅ Gemini AI trả lời tự động  
✅ Lưu danh mục riêng từng user  
✅ Lưu lịch sử chat  
✅ Giữ nguyên giao diện  

---

## 🚀 CÀI ĐẶT (5 BƯỚC):

### **STEP 1: Lấy Gemini API Key (1 phút)**

1. Visit: https://makersuite.google.com/app/apikey
2. Login Google
3. Click "Create API Key"
4. Copy key (AIzaSy...)

**FREE, không cần credit card!**

---

### **STEP 2: Cài đặt (1 phút)**

```bash
# Install Gemini
pip install google-generativeai

# Download 3 files:
# - migrate_database.py
# - backend_api_with_gemini.py
# - PortfolioManager.jsx
```

---

### **STEP 3: Migration (30 giây)**

```bash
cd C:\ai-advisor1\scripts
python migrate_database.py
```

**Output:**
```
✓ Migration completed successfully!
New tables:
  - portfolios
  - chat_history
```

---

### **STEP 4: Deploy (2 phút)**

#### **4.1. Add API key to Render:**

https://dashboard.render.com/web/srv-cta8m0ggph6c73c1qf7g

→ Environment → Add:
```
GEMINI_API_KEY = your_key_here
```

#### **4.2. Update files:**

```bash
cd C:\ai-advisor1

# Replace backend
copy backend_api_with_gemini.py backend_api.py

# Replace frontend component
copy PortfolioManager.jsx frontend\src\components\PortfolioManager.jsx

# Add to requirements.txt:
echo google-generativeai==0.3.2 >> requirements.txt
```

#### **4.3. Deploy:**

```bash
git add .
git commit -m "Add Gemini AI to Portfolio Manager"
git push origin main
```

---

### **STEP 5: Test (30 giây)**

**Visit:** https://ai-advisor.vn

1. Login
2. Click "Quản trị đầu tư bằng AI"
3. Add stock: VCB, 100, 85000
4. Ask AI: "Phân tích danh mục của tôi"
5. See AI response! ✅

---

## ✅ CHECKLIST:

- [ ] Get Gemini API key (FREE)
- [ ] `pip install google-generativeai`
- [ ] Run `migrate_database.py`
- [ ] Add GEMINI_API_KEY to Render
- [ ] Replace backend & frontend files
- [ ] Add to requirements.txt
- [ ] `git push`
- [ ] Test on website

---

## 🎯 KẾT QUẢ:

**Before:**
- Danh mục không lưu
- Chat không lưu
- Không có AI

**After:**
- ✅ Danh mục lưu vĩnh viễn
- ✅ Chat history persistent
- ✅ Gemini AI trả lời thông minh
- ✅ Context-aware advice

---

## 💡 EXAMPLE CONVERSATION:

**User:** "Phân tích danh mục của tôi"

**AI:** "Danh mục của bạn:
- VCB: 100 CP @ 85,000 VND
- MBB: 200 CP @ 24,500 VND

Phân tích:
1. Tập trung ngành ngân hàng (100%)
2. Đa dạng hóa thấp
3. Rủi ro: Nếu ngành này giảm → cả danh mục giảm

Khuyến nghị:
- Thêm công nghệ (FPT)
- Thêm bất động sản (VHM)
- Tỷ lệ: 40% bank, 30% tech, 30% real estate"

---

## 🐛 NẾU CÓ LỖI:

### **Gemini not working:**

```bash
# Check health
curl https://ai-advisor1-backend.onrender.com/health
```

**Should return:** `{"gemini": true}`

**If false:**
- Check GEMINI_API_KEY in Render
- Restart Render service

### **Portfolio not saving:**

```bash
# Run migration again
python scripts/migrate_database.py
```

---

## 📋 FILES CẦN DOWNLOAD:

1. **migrate_database.py** → Run migration
2. **backend_api_with_gemini.py** → Replace backend_api.py
3. **PortfolioManager.jsx** → Replace frontend component

---

## ⏱️ TIMELINE:

```
00:00 - Get API key (1 min)
00:01 - Install library (30s)
00:02 - Run migration (30s)
00:03 - Update Render env (1 min)
00:04 - Deploy code (1 min)
00:09 - Wait for deploy (5 mins)
00:14 - Test on website (1 min)
00:15 - DONE! ✅
```

---

## 🎉 SUCCESS!

**Bạn có:**
- ✅ AI Advisor powered by Gemini
- ✅ Persistent portfolios
- ✅ Chat history
- ✅ Smart recommendations

**Users có:**
- ✅ Personal portfolio manager
- ✅ AI investment advisor
- ✅ 24/7 support
- ✅ Professional experience

---

**TOTAL TIME: 15 PHÚT**

**COST: FREE (Gemini API free tier)**

**RESULT: PROFESSIONAL AI PORTFOLIO MANAGER! 🚀**
