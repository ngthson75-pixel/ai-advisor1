# 🚀 HƯỚNG DẪN DEPLOY AI ADVISOR MVP

## 📋 Chuẩn bị

### 1. Tạo Anthropic API Key (MIỄN PHÍ $5 credit)

1. Vào https://console.anthropic.com/
2. Sign up (dùng email)
3. Vào "API Keys"
4. Click "Create Key"
5. Copy key (dạng: `sk-ant-api03-xxxx`)
6. **Lưu key này lại** - cần dùng lúc deploy

**Chi phí ước tính:**
- Free tier: $5 credit (đủ test)
- Sau đó: ~$50/tháng cho 100 users

---

## ⚡ CÁCH 1: DEPLOY LÊN VERCEL (KHUYẾN NGHỊ)

### Bước 1: Tạo GitHub Repository

```bash
# Trong folder ai-advisor-mvp
git init
git add .
git commit -m "Initial commit - AI Advisor MVP"

# Tạo repo mới trên GitHub
# Vào github.com → New Repository → Tên: ai-advisor-mvp

# Push code lên
git remote add origin https://github.com/YOUR_USERNAME/ai-advisor-mvp.git
git branch -M main
git push -u origin main
```

### Bước 2: Deploy trên Vercel

1. **Vào https://vercel.com**
2. Click **"Sign Up"** (dùng GitHub account)
3. Click **"New Project"**
4. **Import Git Repository**:
   - Select `ai-advisor-mvp` repo
   - Click "Import"

5. **Configure Project**:
   - Framework Preset: **Next.js** (auto-detect)
   - Root Directory: `./`
   - Build Command: `npm run build` (auto)
   - Output Directory: `.next` (auto)

6. **Environment Variables** (QUAN TRỌNG):
   - Click "Add Environment Variable"
   - Name: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-api03-xxxxx` (paste key từ bước 1)

7. Click **"Deploy"** ✨

### Bước 3: Đợi Deploy (1-2 phút)

Vercel sẽ:
- ✅ Install dependencies
- ✅ Build Next.js app
- ✅ Deploy to production
- ✅ Cấp domain: `https://ai-advisor-mvp-xxxxx.vercel.app`

### Bước 4: Test MVP

1. Click vào domain Vercel vừa tạo
2. Đợi 3-5 giây để AI load data
3. Test 3 tabs:
   - 🎯 Tín hiệu AI (MUA/BÁN)
   - 🛡️ Risk Shield
   - 🧠 Discipline Coach

**✅ DONE! MVP đã sẵn sàng để demo với investors!**

---

## 🌐 CÁCH 2: DEPLOY LÊN NETLIFY

### Bước 1: Cài Netlify CLI

```bash
npm install -g netlify-cli
```

### Bước 2: Login & Deploy

```bash
# Login vào Netlify
netlify login

# Trong folder ai-advisor-mvp
netlify init

# Chọn:
# → Create & configure a new site
# → Team: Your team
# → Site name: ai-advisor-mvp (hoặc tên khác)
# → Build command: npm run build
# → Publish directory: .next

# Deploy
netlify deploy --prod
```

### Bước 3: Add Environment Variable

```bash
netlify env:set ANTHROPIC_API_KEY sk-ant-api03-xxxxx
```

### Bước 4: Redeploy để apply env var

```bash
netlify deploy --prod
```

**✅ Domain: https://ai-advisor-mvp.netlify.app**

---

## 🎯 SAU KHI DEPLOY THÀNH CÔNG

### 1. Share với Investors

**Link demo**: Gửi domain Vercel/Netlify

**Email template**:
```
Subject: [Demo] AI Advisor MVP - AI-powered Investment Assistant

Xin chào [Investor Name],

Tôi đã hoàn thiện MVP cho AI Advisor - trợ lý đầu tư được hỗ trợ bởi Claude AI.

🔗 Demo link: https://ai-advisor-mvp-xxxxx.vercel.app

Features:
✅ AI Decision Engine: Tín hiệu MUA/BÁN real-time
✅ AI Risk Shield: Cảnh báo rủi ro thị trường
✅ AI Discipline Coach: Coaching hành vi đầu tư

Tôi rất mong nhận được feedback từ anh/chị về:
- Tính năng AI có hữu ích không?
- UI/UX có dễ dùng không?
- Giá 299k/tháng có hợp lý không?

Thanks,
Sơn Nguyễn
```

### 2. Setup Feedback Form

**Google Forms link**: https://forms.google.com

Questions:
1. Tính năng nào bạn thích nhất? (Multiple choice)
   - AI Decision Engine
   - AI Risk Shield
   - Discipline Coach
   
2. AI analysis có hữu ích không? (Scale 1-10)

3. Bạn có sẵn sàng trả 299k/tháng? (Yes/No/Maybe)

4. Còn thiếu tính năng gì? (Text)

5. Đánh giá UI/UX (Scale 1-10)

### 3. Track Metrics (Optional)

Nếu muốn track user behavior, add Google Analytics:

1. Tạo GA4 property: https://analytics.google.com
2. Get Measurement ID: `G-XXXXXXXXXX`
3. Update `pages/_app.tsx` (xem README)
4. Redeploy

---

## 🔧 TROUBLESHOOTING

### ❌ Problem: "API key not found"

**Fix**:
1. Check Vercel/Netlify dashboard
2. Settings → Environment Variables
3. Ensure `ANTHROPIC_API_KEY` tồn tại
4. Redeploy

### ❌ Problem: Deploy fails

**Fix Vercel**:
```bash
# Check logs
vercel logs

# Common fixes:
# 1. Node version - ensure >= 18
# 2. Build command - should be "npm run build"
# 3. Install command - should be "npm install"
```

**Fix Netlify**:
```bash
# Check logs in Netlify dashboard
# Go to: Site → Deploys → Click on failed deploy → View logs

# Common fixes same as Vercel
```

### ❌ Problem: AI responses are slow

**Normal!** Claude API takes 2-5 seconds per request.

**Solutions**:
- MVP: Accept the delay (users understand it's AI)
- Production: Add caching, loading animations

### ❌ Problem: Too many API requests → exceeded free tier

**Solutions**:
1. Add rate limiting (xem README)
2. Upgrade Anthropic plan
3. Add caching layer (Redis)

---

## 💰 CHI PHÍ THỰC TẾ

### Month 1 (Testing với 10-20 users)
- Hosting: **FREE** (Vercel/Netlify free tier)
- API: **~$5** (trong $5 free credit)
- Domain (optional): **$12/năm**
- **Total: ~$0-1/month**

### Month 2-3 (Beta với 50-100 users)
- Hosting: **FREE** (still trong free tier)
- API: **~$30-50** (sau khi hết free credit)
- **Total: ~$30-50/month**

### Production (>500 users)
- Hosting: **$20-40/month** (Vercel Pro)
- API: **$200-500/month** (depends on usage)
- Database: **$25/month** (Supabase Pro)
- **Total: ~$250-600/month**

---

## 📞 CẦN HỖ TRỢ?

### Vercel Support
- Docs: https://vercel.com/docs
- Community: https://github.com/vercel/next.js/discussions

### Netlify Support
- Docs: https://docs.netlify.com
- Support: https://answers.netlify.com

### Anthropic API Support
- Docs: https://docs.anthropic.com
- Discord: https://discord.gg/anthropic

---

## ✅ CHECKLIST TRƯỚC KHI DEMO

- [ ] MVP deployed successfully
- [ ] AI responses working (test all 3 tabs)
- [ ] Domain looks professional (not too random)
- [ ] Mobile responsive (test on phone)
- [ ] Feedback form ready
- [ ] Investor email list prepared
- [ ] Slide deck updated with demo link

**🚀 You're ready to pitch!**

---

## 🎬 VIDEO DEMO SCRIPT (2 phút)

**[0:00-0:15] Intro**
"Xin chào, tôi là Sơn. Đây là AI Advisor - trợ lý AI giúp nhà đầu tư duy trì kỷ luật và tăng lợi nhuận."

**[0:15-0:45] Tab 1: AI Signals**
"Tab đầu tiên là AI Decision Engine. Claude AI phân tích real-time và đưa ra tín hiệu MUA/BÁN với xác suất thành công, stop loss, take profit. Ví dụ đây là tín hiệu mua MBB với score 70/100..."

**[0:45-1:15] Tab 2: Risk Shield**
"Tab thứ hai là Risk Shield. AI theo dõi thị trường 24/7 và cảnh báo khi có rủi ro. Ví dụ hôm nay thị trường rơi 2.8%, AI khuyến nghị STOP TRADING MODE để tránh quyết định cảm xúc..."

**[1:15-1:45] Tab 3: Discipline Coach**
"Tab thứ ba là Discipline Coach. Khi bạn hỏi 'tôi sợ quá có nên bán không', AI nhận diện cảm xúc PANIC và can thiệp. AI cũng track hành vi - nếu bạn mua đuổi 8 lần/tháng, AI sẽ cảnh báo..."

**[1:45-2:00] Call to Action**
"Đây mới là MVP với 100 beta users. Mục tiêu là 50K users trong 24 tháng với model freemium. Rất mong được feedback từ anh/chị!"

---

**Good luck with your pitch! 🍀💰🚀**
