# ✅ STAGING SETUP CHECKLIST

## 📋 SETUP PROGRESS TRACKER

**Started:** [DATE]  
**Completed:** [DATE]  
**Status:** 🔄 In Progress | ✅ Complete

---

## PHASE 1: PREPARATION (Day 1)

### **Git Setup**
- [ ] Git installed and configured
- [ ] In correct project directory
- [ ] Remote repository configured
- [ ] All changes committed

### **Prerequisites**
- [ ] GitHub account ready
- [ ] Render account created (https://render.com)
- [ ] Supabase account created (https://supabase.com)
- [ ] Cloudflare account ready (https://cloudflare.com)
- [ ] Gemini API key obtained

### **Files Setup**
- [ ] All `.ps1` scripts in project root
- [ ] All `.md` documentation in project root
- [ ] `.gitignore` file in project root
- [ ] Scripts executable (`Set-ExecutionPolicy RemoteSigned`)

---

## PHASE 2: GIT CONFIGURATION (10 minutes)

### **Branch Setup**
- [ ] Ran `.\setup-staging.ps1` successfully
- [ ] Staging branch created
- [ ] Staging branch pushed to GitHub
- [ ] Verified branch on GitHub
- [ ] Main branch protected (optional)

**Staging Branch URL:**
```
https://github.com/YOUR_USERNAME/ai-advisor1/tree/staging
```

---

## PHASE 3: BACKEND STAGING (15 minutes)

### **Render Web Service**
- [ ] Visited https://dashboard.render.com
- [ ] Created new Web Service
- [ ] Connected GitHub repository
- [ ] Configured settings:
  - Name: `ai-advisor1-staging`
  - Region: Singapore
  - Branch: `staging` ⚠️
  - Runtime: Python 3
  - Build: `pip install -r requirements.txt --break-system-packages`
  - Start: `gunicorn backend_api:app`
  - Instance Type: Free ⚠️
- [ ] Service created successfully

**Staging Backend URL:**
```
https://ai-advisor1-staging.onrender.com
```

### **Supabase Database**
- [ ] Visited https://supabase.com
- [ ] Created new project
- [ ] Configured settings:
  - Name: `ai-advisor-staging`
  - Region: Southeast Asia (Singapore)
  - Plan: Free ⚠️
- [ ] Saved database password securely
- [ ] Copied DATABASE_URL (Connection string)
- [ ] Database initialized

**Database URL (keep secret!):**
```
postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
```

### **Environment Variables**
- [ ] Added `GEMINI_API_KEY` to Render
- [ ] Added `DATABASE_URL` to Render
- [ ] Added `ENVIRONMENT=staging` to Render
- [ ] Saved environment variables
- [ ] Backend redeployed automatically

### **Database Migration**
- [ ] Waited for backend deployment
- [ ] Ran migration command:
  ```powershell
  Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/migrate -Method POST
  ```
- [ ] Verified tables created:
  ```powershell
  Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/signals
  ```
- [ ] Response: `{"success":true,"signals":[]}`

---

## PHASE 4: FRONTEND STAGING (15 minutes)

### **Frontend Configuration**
- [ ] Created `frontend/.env.staging`:
  ```env
  VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
  VITE_ENVIRONMENT=staging
  ```
- [ ] Verified `frontend/.env.production` exists

### **Cloudflare Pages**
- [ ] Visited https://dash.cloudflare.com
- [ ] Clicked Workers & Pages
- [ ] Created new Pages project
- [ ] Connected GitHub repository
- [ ] Configured settings:
  - Project name: `ai-advisor-staging`
  - Production branch: `staging` ⚠️
  - Root directory: `frontend`
  - Build command: `npm install && npm run build`
  - Output directory: `dist`
- [ ] Added environment variables:
  - `VITE_API_URL`
  - `VITE_ENVIRONMENT`
- [ ] Deployment started

**Temporary URL:**
```
https://ai-advisor-staging.pages.dev
```

### **Custom Domain (Optional)**
- [ ] In Cloudflare Pages → Custom domains
- [ ] Added `staging.ai-advisor.vn`
- [ ] DNS record auto-created
- [ ] Waited for DNS propagation (2-5 mins)
- [ ] Verified custom domain works

**Custom Domain URL:**
```
https://staging.ai-advisor.vn
```

---

## PHASE 5: TESTING (10 minutes)

### **Backend Health Check**
- [ ] Tested health endpoint:
  ```powershell
  Invoke-WebRequest https://ai-advisor1-staging.onrender.com/health
  ```
- [ ] Response: `{"status":"healthy"}`

### **API Endpoints**
- [ ] Tested signals endpoint:
  ```powershell
  Invoke-WebRequest https://ai-advisor1-staging.onrender.com/api/signals
  ```
- [ ] Response: `{"success":true,"signals":[]}`

### **Frontend Website**
- [ ] Visited staging website
- [ ] Homepage loaded
- [ ] Login/signup works
- [ ] Tab "Tín hiệu mua bán" accessible
- [ ] Tab "Quản trị đầu tư" accessible
- [ ] AI features respond
- [ ] No console errors (F12)
- [ ] Mobile responsive

### **Status Check Script**
- [ ] Ran `.\check-status.ps1 -Environment staging`
- [ ] All checks passed

---

## PHASE 6: DEPLOYMENT TEST (5 minutes)

### **First Deployment**
- [ ] Ran `.\deploy-staging.ps1 "Initial staging deployment"`
- [ ] Deployment completed successfully
- [ ] Waited 10 minutes
- [ ] Tested website again
- [ ] All features working

### **Quick Sync Test**
- [ ] Made small change to a file
- [ ] Ran `.\sync-files.ps1 -Environment staging -Files "file.js"`
- [ ] Sync completed
- [ ] Change reflected on staging

---

## PHASE 7: INTERNAL TESTING PREPARATION

### **Testing Checklist Setup**
- [ ] Created testing checklist (functional, UI, performance, security)
- [ ] Prepared bug tracking system (spreadsheet or tool)
- [ ] Setup monitoring tools
- [ ] Documented test scenarios

### **Team Coordination (if applicable)**
- [ ] Assigned testing responsibilities
- [ ] Setup communication channel (Telegram/Slack)
- [ ] Scheduled testing timeline
- [ ] Defined critical paths to test

### **Testing Timeline**
- [ ] Quick test procedures ready (1-2 hours)
- [ ] Thorough test procedures ready (1-3 days)
- [ ] Weekly test procedures ready (3-7 days)

### **Success Criteria Defined**
- [ ] All core features must work
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Ready for production deployment

---

## PRODUCTION SETUP (For Reference)

### **Production Backend**
- [ ] Render service: `ai-advisor1-backend`
- [ ] Branch: `main`
- [ ] Instance Type: Starter ($7/month)
- [ ] Database: Render PostgreSQL ($7/month)

### **Production Frontend**
- [ ] Cloudflare Pages: `ai-advisor`
- [ ] Branch: `main`
- [ ] Domain: `ai-advisor.vn`

---

## DEPLOYMENT WORKFLOW CHECKLIST

### **Before Each Deploy**
- [ ] All changes committed
- [ ] Tested locally
- [ ] Meaningful commit message
- [ ] Know what features are being deployed

### **Deploy to Staging**
- [ ] Run `.\deploy-staging.ps1 "Message"`
- [ ] Wait 10 minutes
- [ ] Test thoroughly
- [ ] No critical bugs

### **Deploy to Production**
- [ ] Tested on staging ✅
- [ ] Internal testing complete ✅
- [ ] No critical bugs ✅
- [ ] Database migration ready (if needed)
- [ ] Run `.\deploy-production.ps1 "Message"`
- [ ] Confirm twice (type "DEPLOY" then "CONFIRM")
- [ ] Monitor deployment
- [ ] Test production

---

## TROUBLESHOOTING CHECKLIST

### **If Staging Backend Not Working**
- [ ] Check Render logs
- [ ] Verify environment variables set
- [ ] Run migration again
- [ ] Check Supabase status
- [ ] Restart Render service

### **If Frontend Not Updating**
- [ ] Clear browser cache (Ctrl+Shift+R)
- [ ] Check Cloudflare Pages deployment
- [ ] Verify correct branch deployed
- [ ] Try incognito mode
- [ ] Wait 5 minutes for cache

### **If Deployment Fails**
- [ ] Check git status
- [ ] Check error message
- [ ] Verify files committed
- [ ] Check network connection
- [ ] Try again

---

## SUCCESS CRITERIA

**Setup is complete when:**

✅ Staging backend responds  
✅ Staging frontend loads  
✅ Can deploy with 1 command  
✅ Status check passes  
✅ All features work on staging  
✅ Ready for internal testing

---

## NOTES & ISSUES

**Date:** [DATE]  
**Issue:** [DESCRIPTION]  
**Solution:** [WHAT WORKED]

---

**Date:** [DATE]  
**Issue:** [DESCRIPTION]  
**Solution:** [WHAT WORKED]

---

## COMPLETION

**Setup completed:** [DATE]  
**Total time:** [HOURS]  
**Ready for production:** ✅ YES | ❌ NO  
**Next steps:** [WHAT'S NEXT]

---

**Congratulations! 🎉**

You've successfully setup staging environment!

**Next:** Start internal testing, then deploy to production (all users)!
