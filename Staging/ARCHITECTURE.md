# 🏗️ AI ADVISOR - ARCHITECTURE & WORKFLOW DIAGRAMS

## 📊 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB REPOSITORY                           │
│                   https://github.com/.../ai-advisor1                │
│                                                                     │
│  ┌──────────────────────┐              ┌──────────────────────┐   │
│  │   MAIN BRANCH        │              │  STAGING BRANCH      │   │
│  │   (Production)       │◄─────merge───│  (Testing)           │   │
│  │                      │              │                      │   │
│  │  - Stable code       │              │  - New features      │   │
│  │  - Real users        │              │  - Beta testing      │   │
│  │  - Auto-deploy       │              │  - Auto-deploy       │   │
│  └──────────────────────┘              └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
           │                                        │
           │ Push triggers deploy                   │ Push triggers deploy
           │                                        │
           ▼                                        ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   PRODUCTION BACKEND     │          │   STAGING BACKEND        │
│   Render (Starter)       │          │   Render (Free)          │
│   $7/month               │          │   $0/month               │
│                          │          │                          │
│  URL: ai-advisor1-       │          │  URL: ai-advisor1-       │
│       backend.           │          │       staging.           │
│       onrender.com       │          │       onrender.com       │
│                          │          │                          │
│  - Always online         │          │  - Sleeps after 15min    │
│  - Fast response         │          │  - Slower cold start     │
│  - 512MB RAM             │          │  - 512MB RAM             │
└──────────────────────────┘          └──────────────────────────┘
           │                                        │
           │ Database connection                    │ Database connection
           │                                        │
           ▼                                        ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   PRODUCTION DATABASE    │          │   STAGING DATABASE       │
│   Render PostgreSQL      │          │   Supabase (Free)        │
│   $7/month               │          │   $0/month               │
│                          │          │                          │
│  - 1GB storage           │          │  - 500MB storage         │
│  - Daily backups         │          │  - 2GB bandwidth/month   │
│  - Persistent data       │          │  - May reset on restart  │
└──────────────────────────┘          └──────────────────────────┘


           │                                        │
           │ API calls                              │ API calls
           │                                        │
           ▼                                        ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   PRODUCTION FRONTEND    │          │   STAGING FRONTEND       │
│   Cloudflare Pages       │          │   Cloudflare Pages       │
│   Free                   │          │   Free                   │
│                          │          │                          │
│  Domain: ai-advisor.vn   │          │  Domain: staging.        │
│                          │          │          ai-advisor.vn   │
│                          │          │                          │
│  - Global CDN            │          │  - Global CDN            │
│  - Auto SSL              │          │  - Auto SSL              │
│  - Unlimited bandwidth   │          │  - Unlimited bandwidth   │
└──────────────────────────┘          └──────────────────────────┘
           │                                        │
           │ Accessed by                            │ Accessed by
           │                                        │
           ▼                                        ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   PRODUCTION USERS       │          │   INTERNAL TEAM          │
│                          │          │                          │
│  - All users             │          │  - You (founder)         │
│  - Existing customers    │          │  - Team members          │
│  - New signups           │          │  - Internal testing only │
└──────────────────────────┘          └──────────────────────────┘
```

---

## 🔄 DEPLOYMENT WORKFLOW

### **DEVELOPMENT → STAGING → PRODUCTION**

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT PHASE                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1. Develop new feature
                              │    on feature branch
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Feature Branch     │
                    │  feature/my-feature │
                    └─────────────────────┘
                              │
                              │ 2. Test locally
                              │    npm run dev
                              │    python backend_api.py
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Local Testing      │
                    │  ✓ Frontend works   │
                    │  ✓ Backend works    │
                    │  ✓ No errors        │
                    └─────────────────────┘
                              │
                              │ 3. Merge to staging
                              │    git merge
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       STAGING PHASE                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Staging Branch     │
                    │  .\deploy-staging   │
                    └─────────────────────┘
                              │
                              │ 4. Auto-deploy (5-10 mins)
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Staging Website    │
                    │  staging.ai-advisor │
                    │  .vn                │
                    └─────────────────────┘
                              │
                              │ 5. Internal testing (you + team)
                              │    Thorough testing
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Testing Complete   │
                    │  ✓ All features OK  │
                    │  ✓ No critical bugs │
                    │  ✓ Ready to release │
                    └─────────────────────┘
                              │
                              │ 6. Deploy to production
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION PHASE                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Deploy Production  │
                    │  .\deploy-production│
                    │  Requires: DEPLOY   │
                    │  Requires: CONFIRM  │
                    └─────────────────────┘
                              │
                              │ 7. Merge staging → main
                              │    Auto-deploy (10-15 mins)
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Production Website │
                    │  ai-advisor.vn      │
                    └─────────────────────┘
                              │
                              │ 8. Monitor
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Health Check       │
                    │  .\check-status     │
                    │  ✓ Backend healthy  │
                    │  ✓ Frontend healthy │
                    └─────────────────────┘
                              │
                              │ 9. Success!
                              │
                              ▼
                    ┌─────────────────────┐
                    │  All Users          │
                    │  Using new feature  │
                    │  (existing + new)   │
                    └─────────────────────┘
```

---

## 🔥 HOTFIX WORKFLOW

```
┌─────────────────┐
│  Bug Detected   │
│  in Production  │
└─────────────────┘
         │
         │ 1. Fix locally
         │
         ▼
┌─────────────────┐
│  Make Fix       │
│  in file.js     │
└─────────────────┘
         │
         │ 2. Quick sync to staging
         │    .\sync-files staging
         │
         ▼
┌─────────────────┐
│  Test Staging   │
│  (2 mins)       │
└─────────────────┘
         │
         │ 3. If OK
         │
         ▼
┌─────────────────┐
│  Quick sync to  │
│  production     │
│  .\sync-files   │
│  production     │
└─────────────────┘
         │
         │ 4. Monitor
         │
         ▼
┌─────────────────┐
│  Bug Fixed!     │
│  (Total: 5 mins)│
└─────────────────┘
```

---

## 🚨 ROLLBACK WORKFLOW

```
┌─────────────────┐
│  Bad Deploy     │
│  Production     │
│  broken!        │
└─────────────────┘
         │
         │ 1. Immediate action
         │
         ▼
┌─────────────────┐
│  Run Rollback   │
│  .\rollback-    │
│  production     │
│  Type: ROLLBACK │
└─────────────────┘
         │
         │ 2. Revert to previous
         │
         ▼
┌─────────────────┐
│  Force Push     │
│  Type: FORCE    │
└─────────────────┘
         │
         │ 3. Wait (3-5 mins)
         │
         ▼
┌─────────────────┐
│  Production     │
│  Restored!      │
└─────────────────┘
         │
         │ 4. Fix bug on staging
         │
         ▼
┌─────────────────┐
│  Fix & Test     │
│  on Staging     │
└─────────────────┘
         │
         │ 5. Re-deploy properly
         │
         ▼
┌─────────────────┐
│  Production     │
│  Fixed!         │
└─────────────────┘
```

---

## 📁 FILE STRUCTURE

```
ai-advisor1/
│
├── .git/                           # Git repository
│   ├── hooks/
│   └── ...
│
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── SignalsModule.jsx
│   │   │   └── AIPortfolioManager.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env.staging               # Staging environment
│   ├── .env.production            # Production environment
│   ├── package.json
│   ├── vite.config.js
│   └── dist/                      # Build output
│
├── backend/                       # Python backend (optional structure)
│   ├── backend_api.py
│   ├── telegram_notifier.py
│   ├── requirements.txt
│   └── ...
│
├── scripts/                       # Utility scripts
│   ├── deploy-staging.ps1         # 🚀 Deploy to staging
│   ├── deploy-production.ps1      # 🚀 Deploy to production
│   ├── sync-files.ps1             # 📦 Quick sync files
│   ├── rollback-production.ps1    # 🔙 Rollback
│   ├── check-status.ps1           # 🔍 Health check
│   └── setup-staging.ps1          # ⚙️ Auto setup
│
├── docs/                          # Documentation
│   ├── STAGING_SETUP_GUIDE.md     # Full setup guide
│   ├── DEPLOYMENT_QUICKREF.md     # Quick reference
│   ├── SETUP_CHECKLIST.md         # Progress tracker
│   ├── ARCHITECTURE.md            # This file
│   └── README.md                  # Main readme
│
├── .gitignore                     # Git ignore rules
├── .env.example                   # Environment template
├── README.md                      # Project readme
└── package.json                   # Root package.json
```

---

## 🌐 NETWORK FLOW

```
┌──────────────┐
│   Browser    │
│              │
│ User visits  │
│ ai-advisor   │
│ .vn          │
└──────────────┘
       │
       │ DNS lookup
       │
       ▼
┌──────────────┐
│  Cloudflare  │
│     DNS      │
│              │
│ Points to    │
│ Pages        │
└──────────────┘
       │
       │ Route traffic
       │
       ▼
┌──────────────┐
│  Cloudflare  │
│    Pages     │
│     CDN      │
│              │
│ Serve static │
│ files        │
└──────────────┘
       │
       │ Load HTML/CSS/JS
       │
       ▼
┌──────────────┐
│   Browser    │
│  Executes    │
│     JS       │
└──────────────┘
       │
       │ API calls
       │ fetch('/api/signals')
       │
       ▼
┌──────────────┐
│    Render    │
│   Backend    │
│              │
│ Process      │
│ request      │
└──────────────┘
       │
       │ Database query
       │
       ▼
┌──────────────┐
│  PostgreSQL  │
│   Database   │
│              │
│ Return data  │
└──────────────┘
       │
       │ Send response
       │
       ▼
┌──────────────┐
│   Browser    │
│  Display     │
│  signals     │
└──────────────┘
```

---

## 💾 DATA FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    SIGNAL DETECTION                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1. Scanner runs
                           │    (cron job or manual)
                           │
                           ▼
                 ┌─────────────────┐
                 │  VNStock API    │
                 │  Fetch data     │
                 └─────────────────┘
                           │
                           │ 2. Stock data
                           │
                           ▼
                 ┌─────────────────┐
                 │  Signal Logic   │
                 │  - MACD         │
                 │  - RSI          │
                 │  - Volume       │
                 └─────────────────┘
                           │
                           │ 3. Detected signals
                           │
                           ▼
                 ┌─────────────────┐
                 │  Validation     │
                 │  - Price check  │
                 │  - R/R ratio    │
                 │  - Quality      │
                 └─────────────────┘
                           │
                           │ 4. Valid signals
                           │
                           ▼
                 ┌─────────────────┐
                 │  Database       │
                 │  Save signal    │
                 └─────────────────┘
                           │
                           │ 5. Notify admin
                           │
                           ▼
                 ┌─────────────────┐
                 │  Telegram       │
                 │  Send alert     │
                 └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ 1. User visits
                           │
                           ▼
                 ┌─────────────────┐
                 │  Frontend       │
                 │  Load page      │
                 └─────────────────┘
                           │
                           │ 2. API call
                           │    GET /api/signals
                           │
                           ▼
                 ┌─────────────────┐
                 │  Backend        │
                 │  Query database │
                 └─────────────────┘
                           │
                           │ 3. Return signals
                           │
                           ▼
                 ┌─────────────────┐
                 │  Frontend       │
                 │  Display        │
                 │  signals        │
                 └─────────────────┘
                           │
                           │ 4. User asks AI
                           │
                           ▼
                 ┌─────────────────┐
                 │  AI Coach       │
                 │  Gemini API     │
                 └─────────────────┘
                           │
                           │ 5. AI response
                           │
                           ▼
                 ┌─────────────────┐
                 │  Frontend       │
                 │  Display        │
                 │  advice         │
                 └─────────────────┘
```

---

## 🔒 SECURITY LAYERS

```
┌─────────────────────────────────────────────────────────────┐
│                       SECURITY STACK                        │
└─────────────────────────────────────────────────────────────┘

Layer 1: Network (Cloudflare)
┌─────────────────────────────────────┐
│ ✓ DDoS protection                   │
│ ✓ SSL/TLS encryption                │
│ ✓ WAF (Web Application Firewall)   │
│ ✓ Rate limiting                     │
└─────────────────────────────────────┘
               │
               ▼
Layer 2: Application (Frontend)
┌─────────────────────────────────────┐
│ ✓ HTTPS only                        │
│ ✓ No API keys in frontend           │
│ ✓ Input validation                  │
│ ✓ XSS protection                    │
└─────────────────────────────────────┘
               │
               ▼
Layer 3: API (Backend)
┌─────────────────────────────────────┐
│ ✓ CORS configuration                │
│ ✓ Request validation                │
│ ✓ Rate limiting                     │
│ ✓ Error handling                    │
└─────────────────────────────────────┘
               │
               ▼
Layer 4: Database
┌─────────────────────────────────────┐
│ ✓ Encrypted connections             │
│ ✓ SQL injection prevention          │
│ ✓ Regular backups                   │
│ ✓ Access control                    │
└─────────────────────────────────────┘
               │
               ▼
Layer 5: Secrets Management
┌─────────────────────────────────────┐
│ ✓ Environment variables             │
│ ✓ No secrets in git                 │
│ ✓ API keys rotation                 │
│ ✓ Secure credential storage         │
└─────────────────────────────────────┘
```

---

## 💰 COST BREAKDOWN

```
┌─────────────────────────────────────────────────────────┐
│              MONTHLY COST COMPARISON                    │
└─────────────────────────────────────────────────────────┘

STAGING ENVIRONMENT (FREE)
┌──────────────────────────┬────────┬──────┐
│ Service                  │ Plan   │ Cost │
├──────────────────────────┼────────┼──────┤
│ Cloudflare Pages         │ Free   │ $0   │
│ Render Backend           │ Free   │ $0   │
│ Supabase Database        │ Free   │ $0   │
│ Custom Domain (CF)       │ Free   │ $0   │
├──────────────────────────┼────────┼──────┤
│ TOTAL STAGING            │        │ $0   │
└──────────────────────────┴────────┴──────┘

PRODUCTION ENVIRONMENT
┌──────────────────────────┬────────┬──────┐
│ Service                  │ Plan   │ Cost │
├──────────────────────────┼────────┼──────┤
│ Cloudflare Pages         │ Free   │ $0   │
│ Render Backend           │ Starter│ $7   │
│ Render PostgreSQL        │ Starter│ $7   │
│ Custom Domain (CF)       │ Free   │ $0   │
├──────────────────────────┼────────┼──────┤
│ TOTAL PRODUCTION         │        │ $14  │
└──────────────────────────┴────────┴──────┘

TOTAL MONTHLY COST: $14
SAVINGS vs PAID STAGING: $50-100/month
```

---

## ⚡ PERFORMANCE METRICS

```
┌─────────────────────────────────────────────────────────┐
│                 EXPECTED PERFORMANCE                    │
└─────────────────────────────────────────────────────────┘

STAGING (Free Tier)
├── Backend Response Time: 100-500ms (warm)
│                         5-10s (cold start)
├── Frontend Load Time:   1-2s
├── Database Query Time:  50-200ms
├── Uptime:              ~95% (sleeps after 15min)
└── Concurrent Users:    50-100

PRODUCTION (Paid Tier)
├── Backend Response Time: 50-200ms (always warm)
├── Frontend Load Time:   1-2s
├── Database Query Time:  20-100ms
├── Uptime:              >99.5%
└── Concurrent Users:    500-1000

DEPLOYMENT TIME
├── Staging Deploy:      5-10 minutes
├── Production Deploy:   10-15 minutes
├── Quick Sync:          2-3 minutes
└── Rollback:           3-5 minutes
```

---

**Last Updated:** 2026-01-24  
**Version:** 1.0  
**Maintained By:** AI Advisor Team
