# 🚀 STAGING ENVIRONMENT SETUP GUIDE - AI ADVISOR MVP 2.0

## 📋 OVERVIEW

Hướng dẫn này sẽ giúp bạn setup staging environment hoàn chỉnh trong **60 phút**.

**Kết quả:**
- ✅ Staging environment độc lập
- ✅ Upload/sync files siêu dễ (1 lệnh)
- ✅ Test an toàn trước khi production
- ✅ Chi phí: $0 (staging miễn phí)

---

## 🎯 ARCHITECTURE

```
PRODUCTION                          STAGING
─────────────────────              ─────────────────────
Branch: main                       Branch: staging
Domain: ai-advisor.vn              Domain: staging.ai-advisor.vn
Backend: Render Starter ($7)      Backend: Render Free ($0)
Database: Render PostgreSQL ($7)  Database: Supabase Free ($0)
Users: All users (existing + new) Users: Internal only (you + team)
```

---

## 🛠️ SETUP STAGING ENVIRONMENT

### **PHASE 1: GIT SETUP (10 phút)**

#### **1.1. Tạo Staging Branch**

```powershell
cd C:\ai-advisor1

# Ensure you're on latest main
git checkout main
git pull origin main

# Create staging branch from main
git checkout -b staging

# Push staging branch
git push -u origin staging
```

✅ **Verify:**
```powershell
git branch -a
# Should show: staging (local) and remotes/origin/staging
```

#### **1.2. Setup Branch Protection (Optional)**

Visit: https://github.com/YOUR_USERNAME/ai-advisor1/settings/branches

**For `main` branch:**
- ✓ Require pull request reviews before merging
- ✓ Require status checks to pass
- ✓ Do not allow direct pushes

**For `staging` branch:**
- ✓ Allow direct pushes (for easy updates)

---

### **PHASE 2: BACKEND SETUP (15 phút)**

#### **2.1. Create Staging Backend on Render**

1. **Visit:** https://dashboard.render.com
2. **Click:** "New +" → "Web Service"
3. **Select:** `ai-advisor1` repository
4. **Configure:**

```yaml
Name: ai-advisor1-staging
Region: Singapore
Branch: staging  ⚠️ IMPORTANT!
Root Directory: (leave empty)
Runtime: Python 3
Build Command: pip install -r requirements.txt --break-system-packages
Start Command: gunicorn backend_api:app
Instance Type: Free  ⚠️ FREE TIER
```

5. **Environment Variables:**

**Set later** (after database setup)

6. **Click:** "Create Web Service"

**URL will be:** `https://ai-advisor1-staging.onrender.com`

#### **2.2. Create Staging Database on Supabase**

1. **Visit:** https://supabase.com
2. **Click:** "New project"
3. **Configure:**

```yaml
Organization: (your organization)
Name: ai-advisor-staging
Database Password: [create strong password - SAVE THIS!]
Region: Southeast Asia (Singapore)
Pricing Plan: Free
```

4. **Wait 2-3 minutes** for database to initialize

5. **Get Connection String:**
   - Click: Project Settings (gear icon)
   - Click: Database
   - Find: "Connection string" → "URI"
   - Copy the string (looks like):
   
```
postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```

#### **2.3. Configure Staging Backend Environment Variables**

Back to Render dashboard → `ai-advisor1-staging` → Environment

**Add these variables:**

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres.xxxxx:...@...supabase.com:5432/postgres
ENVIRONMENT=staging
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # Optional
TELEGRAM_CHAT_ID=your_telegram_chat_id      # Optional
```

**Click:** "Save Changes"

✅ Backend will auto-deploy (takes 3-5 minutes)

#### **2.4. Run Database Migration**

Wait for backend deployment to finish, then:

```powershell
# Test health
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/health

# Run migration to create tables
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/migrate -Method POST

# Verify
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/signals
# Should return: {"success":true,"signals":[]}
```

✅ **Backend staging is ready!**

---

### **PHASE 3: FRONTEND SETUP (15 phút)**

#### **3.1. Update Frontend Environment Config**

Create/update: `frontend/.env.staging`

```env
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
VITE_APP_NAME=AI Advisor [STAGING]
```

Create/update: `frontend/.env.production`

```env
VITE_API_URL=https://ai-advisor1-backend.onrender.com/api
VITE_ENVIRONMENT=production
VITE_APP_NAME=AI Advisor
```

#### **3.2. Create Staging Frontend on Cloudflare Pages**

1. **Visit:** https://dash.cloudflare.com
2. **Click:** "Workers & Pages"
3. **Click:** "Create application" → "Pages" tab
4. **Click:** "Connect to Git"
5. **Select:** `ai-advisor1` repository
6. **Click:** "Begin setup"
7. **Configure:**

```yaml
Project name: ai-advisor-staging
Production branch: staging  ⚠️ IMPORTANT!

Build configuration:
Framework preset: None
Root directory: frontend
Build command: npm install && npm run build
Build output directory: dist
```

8. **Environment Variables:**

```
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
```

9. **Click:** "Save and Deploy"

**Temporary URL will be:** `https://ai-advisor-staging.pages.dev`

#### **3.3. Setup Custom Domain (Optional)**

**If you want staging.ai-advisor.vn:**

1. **In Cloudflare Pages** → `ai-advisor-staging` project
2. **Click:** "Custom domains" tab
3. **Click:** "Set up a custom domain"
4. **Enter:** `staging.ai-advisor.vn`
5. **Click:** "Continue"
6. **Cloudflare** will auto-create DNS record
7. **Wait 2-5 minutes** for DNS propagation

✅ **Frontend staging is ready!**

---

### **PHASE 4: TESTING STAGING (10 phút)**

#### **4.1. Test Staging Website**

Visit: `https://staging.ai-advisor.vn` (or `.pages.dev`)

**Checklist:**
- [ ] Homepage loads
- [ ] Login/signup works
- [ ] Tab "Tín hiệu mua bán" accessible
- [ ] Tab "Quản trị đầu tư" accessible
- [ ] AI features respond (may be slow on Render free tier)
- [ ] No console errors (F12)

#### **4.2. Test Staging API**

```powershell
# Health check
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/health
# Response: {"status":"healthy"}

# Get signals (empty initially)
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/signals
# Response: {"success":true,"signals":[]}

# Test portfolio
$body = @{user_id=1; ticker="VCB"; quantity=100; price=85000} | ConvertTo-Json
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/portfolio -Method POST -Body $body -ContentType "application/json"
# Response: {"success":true}
```

✅ **Staging environment is fully functional!**

---

## 🚀 DAILY WORKFLOW

### **Scenario 1: Develop New Feature**

```powershell
# 1. Create feature branch from staging
git checkout staging
git pull origin staging
git checkout -b feature/new-ai-signal

# 2. Develop & test locally
# ... make changes ...
npm run dev  # Test frontend
python backend_api.py  # Test backend

# 3. Commit and push to staging
git add .
git commit -m "feat: Add new AI signal feature"
git checkout staging
git merge feature/new-ai-signal
git push origin staging

# 4. Wait 5-10 mins for auto-deploy
# 5. Test on https://staging.ai-advisor.vn

# 6. If OK, deploy to production
.\deploy-production.ps1 "Release new AI signal feature"
```

### **Scenario 2: Quick Hotfix**

```powershell
# Fix a bug in a single file
# Example: Fix bug in frontend/src/components/SignalsModule.jsx

# Quick sync to staging
.\sync-files.ps1 -Environment staging -Files "frontend/src/components/SignalsModule.jsx" -Message "Fix signals display bug"

# Wait 5 mins, test on staging
# If OK, sync to production
.\sync-files.ps1 -Environment production -Files "frontend/src/components/SignalsModule.jsx" -Message "Fix signals display bug"
```

### **Scenario 3: Full Deployment**

```powershell
# Deploy all changes to staging
.\deploy-staging.ps1 "Weekly update: new features and bug fixes"

# Wait 10 mins, test thoroughly

# Deploy to production
.\deploy-production.ps1 "v2.1.0 - Weekly release"
```

---

## 📋 DEPLOYMENT SCRIPTS USAGE

### **Script 1: `deploy-staging.ps1`**

**Purpose:** Deploy changes to staging

**Usage:**
```powershell
.\deploy-staging.ps1 "Your commit message"
```

**What it does:**
1. ✓ Switches to staging branch
2. ✓ Pulls latest changes
3. ✓ Commits your changes
4. ✓ Pushes to GitHub
5. ✓ Auto-deploys to staging
6. ✓ Checks health

**Example:**
```powershell
.\deploy-staging.ps1 "Add risk alert feature"
```

### **Script 2: `deploy-production.ps1`**

**Purpose:** Deploy staging → production

**Usage:**
```powershell
.\deploy-production.ps1 "Release message" [-Version "v1.2.0"]
```

**What it does:**
1. ✓ Asks for confirmation (type "DEPLOY")
2. ✓ Verifies tests passed
3. ✓ Creates git tag
4. ✓ Merges staging → main
5. ✓ Asks final confirmation (type "CONFIRM")
6. ✓ Pushes to production
7. ✓ Monitors deployment

**Example:**
```powershell
.\deploy-production.ps1 "v2.1.0 release with new features"
```

### **Script 3: `sync-files.ps1`**

**Purpose:** Quick sync specific files

**Usage:**
```powershell
.\sync-files.ps1 -Environment staging -Files "file1.js","file2.py"
.\sync-files.ps1 -Environment production -Files "file.js"
```

**What it does:**
1. ✓ Verifies files exist
2. ✓ Switches to target branch
3. ✓ Commits & pushes
4. ✓ Returns to your branch
5. ✓ Monitors deployment

**Example:**
```powershell
# Fix bug in single file
.\sync-files.ps1 -Environment staging -Files "backend_api.py" -Message "Fix API bug"
```

### **Script 4: `rollback-production.ps1`**

**Purpose:** Emergency rollback

**Usage:**
```powershell
.\rollback-production.ps1 [version_tag]
```

**What it does:**
1. ✓ Asks for confirmation (type "ROLLBACK")
2. ✓ Reverts to previous version
3. ✓ Force pushes to production
4. ✓ Monitors rollback

**Example:**
```powershell
# Rollback to previous commit
.\rollback-production.ps1

# Rollback to specific version
.\rollback-production.ps1 "v2.0.5"
```

---

## 🧪 INTERNAL TESTING WORKFLOW

### **Purpose của Staging Environment**

Staging là môi trường test **nội bộ** cho bạn và team:
- ✅ Giống production nhất có thể
- ✅ Test features mới trước khi release
- ✅ Phát hiện bugs sớm
- ✅ Không ảnh hưởng users nếu có vấn đề

### **Internal Testing Process**

#### **1. Prepare Staging**

```powershell
# Deploy latest to staging
.\deploy-staging.ps1 "Prepare for internal testing"

# Verify all features work
# Visit: https://staging.ai-advisor.vn
```

#### **2. Testing Checklist**

**Functional Testing:**
- [ ] All 3 core features work (Decision, Risk, Coach)
- [ ] Portfolio management functions correctly
- [ ] Signal generation working
- [ ] AI responses quality
- [ ] Data persists correctly

**UI/UX Testing:**
- [ ] All pages load correctly
- [ ] Mobile responsive
- [ ] No visual bugs
- [ ] User flow smooth

**Performance Testing:**
- [ ] Page load time < 3s
- [ ] API response time acceptable
- [ ] No memory leaks
- [ ] Database queries optimized

**Security Testing:**
- [ ] No API keys exposed
- [ ] CORS configured correctly
- [ ] Input validation working
- [ ] No XSS vulnerabilities

#### **3. Bug Tracking**

**Use simple tracking method:**

| Bug | Severity | Status | Fix |
|-----|----------|--------|-----|
| Login error | High | Fixed | v1.1.1 |
| Slow loading | Medium | In Progress | - |

#### **4. Testing Timeline**

**Quick Test (1-2 hours):**
- Small changes, hotfixes
- Basic functionality check
- Deploy to production same day

**Thorough Test (1-3 days):**
- New features
- Major changes
- Full testing checklist
- Deploy after verification

**Weekly Test (3-7 days):**
- Multiple features
- Weekly releases
- Comprehensive testing
- Monitor for edge cases

#### **5. Team Coordination (if applicable)**

If you have team members:

```
Testing Assignments:
- You: Core features, backend
- Team member 1: Frontend, UI/UX
- Team member 2: Mobile, edge cases
```

**Communication:**
- Telegram/Slack for quick updates
- Daily standup (5 mins)
- Bug tracking sheet

---

## 🔄 SYNC STRATEGY

### **When to Sync What**

**Small changes (1-3 files):**
```powershell
.\sync-files.ps1 -Environment staging -Files "file.js"
# Fast: < 2 minutes
```

**Medium changes (feature/bug fix):**
```powershell
.\deploy-staging.ps1 "Feature X"
# Medium: 5-10 minutes
```

**Large changes (weekly release):**
```powershell
.\deploy-staging.ps1 "Weekly update"
# Test thoroughly
.\deploy-production.ps1 "v2.1.0"
# Slow but safe: 15-20 minutes
```

---

## 💰 COST BREAKDOWN

### **Total Monthly Cost: $14**

| Service | Environment | Plan | Cost |
|---------|-------------|------|------|
| Cloudflare Pages | Staging | Free | $0 |
| Cloudflare Pages | Production | Free | $0 |
| Render Backend | Staging | Free | $0 |
| Render Backend | Production | Starter | $7 |
| Supabase DB | Staging | Free | $0 |
| Render PostgreSQL | Production | Starter | $7 |
| **TOTAL** | | | **$14** |

**Savings:** $50-100/month compared to paid staging

---

## 🚨 TROUBLESHOOTING

### **Issue: Staging Backend Sleeps**

**Symptom:** API slow to respond first time

**Cause:** Render Free tier sleeps after 15 min

**Solution:**
```powershell
# Wake it up
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/health

# Or: Setup Cron job to ping every 14 mins (optional)
```

### **Issue: Database Reset on Staging**

**Symptom:** Data disappears

**Cause:** Supabase free tier limits

**Solution:**
```powershell
# Re-run migration
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/migrate -Method POST

# This is expected on free tier
# For production, use paid database
```

### **Issue: Frontend Shows Old Version**

**Symptom:** Changes not visible

**Solution:**
```powershell
# 1. Clear browser cache
Ctrl + Shift + R

# 2. Wait 5 mins for Cloudflare cache

# 3. Check deployment
# Visit: https://dash.cloudflare.com
# Check: Latest deployment matches git commit
```

### **Issue: Merge Conflict**

**Symptom:** Git merge fails

**Solution:**
```powershell
# 1. Check conflicts
git status

# 2. Resolve manually
# Edit conflicted files
# Remove <<<<<<, ======, >>>>>> markers

# 3. Commit resolution
git add .
git commit -m "Resolve merge conflict"
git push origin staging
```

---

## ✅ CHECKLIST: STAGING READY

**Backend Staging:**
- [ ] Render web service created
- [ ] Branch set to `staging`
- [ ] Environment variables configured
- [ ] Database migration run
- [ ] API health check passes

**Frontend Staging:**
- [ ] Cloudflare Pages project created
- [ ] Branch set to `staging`
- [ ] Environment variables configured
- [ ] Custom domain working (optional)
- [ ] Website loads correctly

**Scripts Installed:**
- [ ] `deploy-staging.ps1` in project root
- [ ] `deploy-production.ps1` in project root
- [ ] `sync-files.ps1` in project root
- [ ] `rollback-production.ps1` in project root

**Testing:**
- [ ] Can deploy to staging
- [ ] Can sync single file
- [ ] Internal testing workflow ready
- [ ] Monitoring setup

---

## 🎉 YOU'RE READY!

**You now have:**
- ✅ Staging environment (100% free)
- ✅ Production environment ($14/month)
- ✅ One-command deployment
- ✅ Safe testing workflow
- ✅ Emergency rollback

**Next steps:**
1. Deploy current code to staging
2. Test thoroughly (internal)
3. Fix any bugs found
4. When ready, deploy to production (all users)!
5. Monitor and iterate

🚀 **Happy deploying!**
