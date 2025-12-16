# ⚡ AI ADVISOR 1 - GEMINI VERSION - QUICKSTART

## 🎉 ĐIỂM MỚI

✅ **Migrate sang Google Gemini 2.0 Flash**
- FREE tier: 1,500 requests/day
- Nhanh hơn Claude
- Chi phí $0 cho MVP (100-200 users)
- Quality vẫn rất tốt (⭐⭐⭐⭐)

✅ **VIP Registration Popup** (giữ nguyên)
✅ **3 AI Features** (giữ nguyên)

---

## 🔑 LẤY GEMINI API KEY (2 PHÚT)

### Bước 1: Vào Google AI Studio

https://aistudio.google.com/apikey

### Bước 2: Tạo API Key

1. Click **"Get API key"**
2. Click **"Create API key"**
3. Chọn project (hoặc tạo mới)
4. Copy API key (dạng: `AIzaSy...`)

**FREE TIER:**
- 1,500 requests/day
- 1M tokens/day  
- Rate limit: 15 req/min
- Không cần credit card! ✅

---

## 🚀 DEPLOY LÊN NETLIFY (5 PHÚT)

### Bước 1: Update local project

```powershell
cd C:\ai-advisor1

# Update package.json
# Đổi "@anthropic-ai/sdk" thành "@google/generative-ai": "^0.21.0"

# Tạo .env.local
echo GEMINI_API_KEY=AIzaSy... > .env.local
```

### Bước 2: Push lên GitHub

```powershell
git add .
git commit -m "Migrate to Gemini 2.0 Flash"
git push origin main
```

### Bước 3: Update Netlify

1. Vào https://app.netlify.com
2. Site **ai-advisor11**
3. **Site settings** → **Environment variables**
4. **Xóa** `ANTHROPIC_API_KEY`
5. **Add new**:
   - Key: `GEMINI_API_KEY`
   - Value: `AIzaSy...` (API key từ Google)
6. **Save**

### Bước 4: Trigger Redeploy

1. **Deploys** tab
2. Click **"Trigger deploy"** → **"Deploy site"**
3. Đợi 2-3 phút
4. **Done!** ✅

---

## 💰 CHI PHÍ

### Phase 1: MVP (0-200 users)
- Gemini: **$0/tháng** (FREE tier)
- Netlify: **$0/tháng**
- **TOTAL: $0** ✨

### Phase 2: Beta (200-1000 users)  
- Gemini: **$20-50/tháng** (nếu vượt free tier)
- Netlify: **$0**
- **TOTAL: $20-50/tháng**

### So với Claude:
- Claude: $270/tháng cho 100 users
- Gemini: $0/tháng cho 100 users
- **TIẾT KIỆM: 100%** 💰

---

## 🎯 TEST

https://ai-advisor11.netlify.app

1. Tab "Tín hiệu AI" → Thấy badge "Powered by Google Gemini 2.0 Flash"
2. AI analysis nhanh hơn (1-2 giây vs 3-4 giây)
3. Quality vẫn rất tốt
4. VIP popup vẫn hoạt động

---

## 📊 GEMINI vs CLAUDE

| Feature | Gemini 2.0 | Claude Sonnet 4 |
|---------|-----------|-----------------|
| **Cost (100 users)** | $0 | $270 |
| **Speed** | 1-2s | 3-4s |
| **Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Free tier** | 1.5M tokens/day | $5 one-time |
| **Vietnamese** | Tốt | Tốt |

---

## ✅ DONE!

Deploy và demo ngay! 🚀

**Domain**: https://ai-advisor11.netlify.app
**Cost**: $0/tháng
**Users**: 100-200

Perfect cho MVP fundraising! 💰
