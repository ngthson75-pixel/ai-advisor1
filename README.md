# AI Advisor MVP

MVP hoàn chỉnh với AI Decision Support cho investors. Sử dụng AI để phân tích chứng khoán real-time.

## 🚀 Features

### ✅ Đã hoàn thành
- **AI Decision Engine**: Tín hiệu MUA/BÁN với AI analysis
- **AI Risk Shield**: Phân tích rủi ro thị trường real-time
- **AI Discipline Coach**: Coaching hành vi đầu tư
- **Backend API**: Next.js API routes với Chatgpt 4o
- **Frontend**: React components với TypeScript

### 🎯 Công nghệ

- **Framework**: Next.js 14 + React 18 + TypeScript
- **AI**: Chatgpt 4o mini
- **Styling**: CSS Modules
- **Deploy**: Render

## 📦 Setup Local

### 1. Install dependencies

```bash
npm install
```

### 2. Setup Environment Variables

Tạo file `.env.local`:

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Lấy API key**: https://console.anthropic.com/

### 3. Run development server

```bash
npm run dev
```

Mở [http://localhost:3000](http://localhost:3000)

## 🚀 Deploy lên Vercel (RECOMMENDED)

### Option 1: Deploy từ GitHub (Easiest)

1. **Push code lên GitHub**:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/ai-advisor-mvp.git
git push -u origin main
```

2. **Deploy trên Vercel**:
- Vào https://vercel.com
- Click "New Project"
- Import GitHub repo
- Add environment variable: `ANTHROPIC_API_KEY`
- Click "Deploy"

✅ Done! Vercel sẽ tự động:
- Build project
- Deploy production
- Cấp domain: `your-project.vercel.app`
- Auto-deploy mỗi khi push code mới

### Option 2: Deploy từ CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Set env variable
vercel env add ANTHROPIC_API_KEY

# Production deploy
vercel --prod
```

## 🌐 Deploy lên Netlify

### Option 1: Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Init
netlify init

# Set build command: npm run build
# Set publish directory: .next

# Deploy
netlify deploy --prod

# Add env variable
netlify env:set ANTHROPIC_API_KEY your_api_key_here
```

### Option 2: Netlify Dashboard

1. Vào https://app.netlify.com
2. "New site from Git"
3. Connect GitHub repo
4. Build settings:
   - Build command: `npm run build`
   - Publish directory: `.next`
5. Environment variables:
   - `ANTHROPIC_API_KEY`: your_api_key
6. Deploy

## 💰 Chi phí

### Anthropic API Costs
- **Free tier**: $5 credit
- **Claude Sonnet 4**: ~$3 per million input tokens
- **Estimated cost**: ~$0.01-0.05 per request
- **For 100 beta users**: ~$20-50/month (nếu mỗi user 5-10 requests/day)

### Hosting Costs
- **Vercel**: Free tier đủ cho MVP (100GB bandwidth)
- **Netlify**: Free tier đủ cho MVP (100GB bandwidth)

### Total MVP Cost
- **Development**: Free (using this code)
- **API**: ~$50/month cho 100 active users
- **Hosting**: Free
- **Domain** (optional): ~$12/year

**→ Tổng: ~$50-100/month cho MVP với 100 beta users**

## 📊 Limits & Scaling

### Current MVP Limits
- ✅ **Users**: 100-200 concurrent users OK
- ✅ **Requests**: ~1000 requests/day trong free tier
- ✅ **API Rate Limit**: 50 requests/min (Claude API)

### Khi cần scale (>500 users)
1. Upgrade Anthropic API tier
2. Add caching layer (Redis) để giảm API calls
3. Add user authentication (NextAuth.js)
4. Move sang paid hosting plan

## 🧪 Testing

### Test AI endpoints locally

```bash
# Test signals API
curl -X POST http://localhost:3000/api/signals \
  -H "Content-Type: application/json" \
  -d '{"analysisType": "all"}'

# Test risk analysis
curl http://localhost:3000/api/risk-analysis

# Test discipline coach
curl -X POST http://localhost:3000/api/discipline-coach \
  -H "Content-Type: application/json" \
  -d '{"userMessage": "Tôi sợ quá, có nên bán không?"}'
```

## 📝 Để thu thập feedback từ investors

### 1. Share link MVP
- Domain: `ai-advisor-mvp.vercel.app`
- Or custom domain: `mvp.ai-advisor.vn`

### 2. Tạo feedback form (Google Forms)
Questions:
- Tính năng nào bạn thích nhất?
- AI analysis có hữu ích không?
- Bạn có sẵn sàng trả 299k/tháng?
- Còn thiếu tính năng gì?
- Đánh giá UI/UX: 1-10

### 3. Track metrics
Nếu add Google Analytics:
```javascript
// pages/_app.tsx
import Script from 'next/script'

export default function App({ Component, pageProps }) {
  return (
    <>
      <Script
        src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"
        strategy="afterInteractive"
      />
      <Script id="google-analytics" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-XXXXXXXXXX');
        `}
      </Script>
      <Component {...pageProps} />
    </>
  )
}
```

## 🔒 Security Notes

### Environment Variables
- ⚠️ **NEVER** commit `.env.local` to git
- ✅ API key chỉ dùng server-side (API routes)
- ✅ Frontend không bao giờ access API key

### Rate Limiting
Current MVP không có rate limiting. Nếu cần:

```typescript
// pages/api/signals.ts
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
})
```

## 🐛 Troubleshooting

### "API key not found"
→ Check `.env.local` có đúng key không
→ Restart dev server: `npm run dev`

### "Module not found"
→ `npm install`

### Deploy fails on Vercel
→ Check build logs
→ Ensure Node version >= 18 in `package.json`

### AI responses are slow
→ Normal, Claude API takes 2-5 seconds
→ Consider adding loading indicators
→ Add caching for repeated queries

## 📞 Support

- **Technical issues**: Check logs trong Vercel/Netlify dashboard
- **API issues**: https://docs.anthropic.com
- **Questions**: [Your contact]

## 📈 Next Steps

### Để chuyển từ MVP → Production:

1. **User Authentication**
   - Add NextAuth.js
   - Google/Email login
   - User sessions

2. **Database**
   - Supabase (Postgres + Auth)
   - Save user portfolios
   - Track signal history

3. **Real Stock Data**
   - VNDirect API integration
   - Real-time price updates
   - Historical data

4. **Payment**
   - Stripe integration
   - Subscription management
   - 299k/month pricing

5. **Mobile App**
   - React Native
   - Push notifications
   - Offline support

**Budget for Production**: $10K-15K + $500-1000/month operational cost

---

## 🎉 You're ready to demo!

1. ✅ Deploy lên Vercel
2. ✅ Share link với investors
3. ✅ Collect feedback
4. ✅ Iterate dựa trên feedback
5. ✅ Raise seed round 🚀

Good luck! 🍀
