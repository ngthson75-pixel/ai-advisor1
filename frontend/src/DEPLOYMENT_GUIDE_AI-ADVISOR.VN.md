# 🚀 DEPLOYMENT GUIDE - AI-ADVISOR.VN

**Deploy frontend to Cloudflare Pages with custom domain**  
**Keep backend on Render (no changes needed)**

---

## 📋 OVERVIEW

### **Current Setup:**
```
❌ Frontend: Netlify (paused)
✅ Backend: Render (working)
✅ Domain: ai-advisor.vn (registered at Mat Bao)
```

### **New Setup:**
```
✅ Frontend: Cloudflare Pages → ai-advisor.vn
✅ Backend: Render → ai-advisor1-backend.onrender.com
✅ Architecture: Separated frontend/backend (best practice)
```

---

## 🎯 DEPLOYMENT STEPS

### **STEP 1: Add Domain to Cloudflare** (15 minutes)

#### **1.1 Create Cloudflare Account**

```
1. Go to: https://dash.cloudflare.com/sign-up
2. Sign up with email
3. Verify email
4. Login
```

#### **1.2 Add Site**

```
1. Click "Add a Site"
2. Enter: ai-advisor.vn
3. Select plan: Free
4. Click "Continue"
5. Cloudflare will scan DNS records
6. Click "Continue"
```

#### **1.3 Copy Nameservers**

```
Cloudflare will show 2 nameservers like:
- alex.ns.cloudflare.com
- uma.ns.cloudflare.com

⚠️ COPY THESE! You'll need them next.
```

---

### **STEP 2: Update Nameservers at Mat Bao** (5 minutes)

#### **2.1 Login to Mat Bao**

```
1. Go to: https://manage.matbao.net
2. Login with your credentials
3. Find: ai-advisor.vn in domain list
4. Click to manage
```

#### **2.2 Change Nameservers**

```
1. Find "Quản lý DNS" or "Nameservers"
2. Change from Mat Bao nameservers to:
   - Nameserver 1: alex.ns.cloudflare.com (example)
   - Nameserver 2: uma.ns.cloudflare.com (example)
   ⚠️ Use YOUR nameservers from Cloudflare!
3. Save changes
4. Wait 2-24 hours for propagation
   (Usually takes 2-4 hours)
```

#### **2.3 Verify DNS Propagation**

```
Check status at:
https://www.whatsmydns.net/#NS/ai-advisor.vn

When you see Cloudflare nameservers worldwide → Ready!
```

---

### **STEP 3: Deploy Frontend to Cloudflare Pages** (20 minutes)

#### **3.1 Create Cloudflare Pages Project**

```
1. Go to: https://pages.cloudflare.com
2. Login (same Cloudflare account)
3. Click "Create a project"
4. Click "Connect to Git"
5. Authorize Cloudflare to access GitHub
6. Select repository: ai-advisor1
```

#### **3.2 Configure Build Settings**

```
Project name: ai-advisor-frontend (or any name)
Production branch: main

Build settings:
- Framework preset: None (or Vite if available)
- Build command: npm run build
- Build output directory: dist
- Root directory: frontend (if your React app is in /frontend)

Environment variables: (if needed)
- VITE_API_URL: https://ai-advisor1-backend.onrender.com/api
```

#### **3.3 Deploy**

```
Click "Save and Deploy"

Wait 3-5 minutes for build...

✅ You'll get a URL like:
   ai-advisor-frontend.pages.dev
```

---

### **STEP 4: Add Custom Domain** (10 minutes)

#### **4.1 Add ai-advisor.vn**

```
In Cloudflare Pages project:
1. Go to: Custom domains
2. Click "Set up a custom domain"
3. Enter: ai-advisor.vn
4. Click "Continue"
5. Cloudflare auto-configures DNS
6. Wait 2-5 minutes for SSL
```

#### **4.2 Add www subdomain (Optional)**

```
1. Click "Set up a custom domain" again
2. Enter: www.ai-advisor.vn
3. Click "Continue"
4. This will redirect www → ai-advisor.vn
```

#### **4.3 Verify SSL**

```
Wait 5-10 minutes, then visit:
https://ai-advisor.vn

✅ Should see your frontend with green lock 🔒
```

---

### **STEP 5: Update Frontend Code** (15 minutes)

#### **5.1 Create Config File**

```bash
cd C:\ai-advisor1\frontend\src

# Create config.js
notepad config.js
```

**Paste this:**

```javascript
const config = {
  API_BASE_URL: import.meta.env.PROD 
    ? 'https://ai-advisor1-backend.onrender.com/api'
    : 'http://localhost:10000/api',
  
  FRONTEND_URL: import.meta.env.PROD
    ? 'https://ai-advisor.vn'
    : 'http://localhost:5173',
};

export default config;
```

**Save and close.**

#### **5.2 Create API Service**

```bash
mkdir services
cd services
notepad api.js
```

**Paste the api.js content I provided above**

#### **5.3 Update Components to Use Config**

**Example - Update any component that calls API:**

```javascript
// OLD:
const response = await fetch('https://some-old-url.com/api/signals');

// NEW:
import config from '../config';
const response = await fetch(`${config.API_BASE_URL}/signals`);
```

**Or use the API service:**

```javascript
import { signalsAPI } from '../services/api';

// Get signals
const data = await signalsAPI.getAll();

// Get by strategy
const pullbackSignals = await signalsAPI.getByStrategy('PULLBACK');
```

#### **5.4 Update package.json (if needed)**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

---

### **STEP 6: Push Changes and Redeploy** (5 minutes)

```bash
cd C:\ai-advisor1

# Add new files
git add frontend/src/config.js
git add frontend/src/services/api.js

# Commit
git commit -m "Add config for ai-advisor.vn domain"

# Push
git push origin main
```

**Cloudflare Pages will auto-deploy!**

Wait 3-5 minutes, then check: https://ai-advisor.vn

---

## ✅ VERIFICATION CHECKLIST

### **DNS & Domain:**

- [ ] Nameservers updated at Mat Bao
- [ ] DNS propagated (check whatsmydns.net)
- [ ] ai-advisor.vn resolves to Cloudflare

### **Cloudflare Pages:**

- [ ] Frontend deployed successfully
- [ ] Build completed without errors
- [ ] Custom domain added
- [ ] SSL certificate active (🔒)

### **Frontend:**

- [ ] https://ai-advisor.vn loads
- [ ] All pages work
- [ ] API calls work
- [ ] No console errors

### **Backend:**

- [ ] Render backend still works
- [ ] https://ai-advisor1-backend.onrender.com/health returns healthy
- [ ] CORS allows ai-advisor.vn

---

## 🔧 UPDATE BACKEND CORS (Important!)

### **In backend_api.py:**

```python
from flask_cors import CORS

app = Flask(__name__)

# Update CORS to allow new domain
CORS(app, origins=[
    'https://ai-advisor.vn',
    'https://www.ai-advisor.vn',
    'http://localhost:5173',  # Local dev
    'http://localhost:3000',   # Alternative dev port
])
```

**Then redeploy backend:**

```bash
git add backend_api.py
git commit -m "Update CORS for ai-advisor.vn"
git push origin main
```

**Render will auto-redeploy.**

---

## 🎯 EXPECTED RESULTS

### **After completion:**

```
✅ https://ai-advisor.vn - Your frontend (Cloudflare Pages)
✅ https://ai-advisor1-backend.onrender.com - Backend API (Render)
✅ SSL enabled (green lock)
✅ Fast loading (Cloudflare CDN)
✅ No more pausing (unlimited bandwidth)
✅ Professional domain
```

---

## 📊 ARCHITECTURE DIAGRAM

```
User Browser
    ↓
https://ai-advisor.vn (Cloudflare Pages)
    ↓ API Calls
https://ai-advisor1-backend.onrender.com/api (Render)
    ↓
SQLite Database (on Render)
```

---

## 🚨 TROUBLESHOOTING

### **Issue: Domain not resolving**

```
✅ Check nameservers at Mat Bao
✅ Wait 2-24 hours for DNS propagation
✅ Clear browser cache (Ctrl+Shift+Delete)
✅ Check: https://www.whatsmydns.net
```

### **Issue: SSL not working**

```
✅ Wait 10-15 minutes after adding domain
✅ Check Cloudflare SSL/TLS settings
✅ Set to "Full" or "Full (strict)"
✅ Clear browser cache
```

### **Issue: API calls failing**

```
✅ Check backend CORS settings
✅ Verify API_BASE_URL in config.js
✅ Check browser console for errors
✅ Test backend health: /health endpoint
```

### **Issue: Build fails on Cloudflare**

```
✅ Check build command: npm run build
✅ Check output directory: dist
✅ Check root directory setting
✅ Check build logs for errors
```

---

## 💰 COSTS

```
Domain (ai-advisor.vn):
- Mat Bao: ~350k VND/year ✅ Already paid

Frontend Hosting:
- Cloudflare Pages: FREE
- Unlimited bandwidth
- Unlimited requests

Backend Hosting:
- Render Free: Currently FREE
- Upgrade to $7/month when needed

Total Current: 350k VND/year (domain only!)
Total with Backend Pro: 350k + 84k*12 = 1.4M VND/year
```

---

## 🎊 BENEFITS

```
✅ Professional domain (ai-advisor.vn)
✅ Unlimited bandwidth (no more pausing!)
✅ Fast global CDN (Cloudflare)
✅ Auto SSL certificate
✅ Separated frontend/backend (best practice)
✅ Easy to scale
✅ Keep using GitHub + Render
✅ Minimal code changes
```

---

## 📞 SUPPORT RESOURCES

**Cloudflare:**
- Docs: https://developers.cloudflare.com/pages
- Community: https://community.cloudflare.com
- Status: https://www.cloudflarestatus.com

**Mat Bao:**
- Support: https://matbao.net/lien-he
- KB: https://matbao.net/kb

**Render:**
- Docs: https://render.com/docs
- Status: https://status.render.com

---

## ✅ FINAL CHECKLIST

**Before starting:**

- [ ] Domain ai-advisor.vn registered at Mat Bao ✅
- [ ] GitHub repo ready
- [ ] Backend running on Render
- [ ] Frontend code ready

**After completion:**

- [ ] Domain points to Cloudflare
- [ ] Frontend deployed to Cloudflare Pages
- [ ] Custom domain configured
- [ ] SSL enabled
- [ ] Backend CORS updated
- [ ] API calls working
- [ ] https://ai-advisor.vn loads perfectly

---

**READY TO DEPLOY! 🚀**

**Estimated Total Time: 60-90 minutes**

*Last Updated: December 24, 2025*
