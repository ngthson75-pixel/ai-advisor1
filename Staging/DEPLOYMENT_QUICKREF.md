# 🚀 DEPLOYMENT QUICK REFERENCE

## 📦 ONE-COMMAND DEPLOYMENT

### **Deploy to Staging**
```powershell
.\deploy-staging.ps1 "Your commit message here"
```
⏱️ Time: 5-10 minutes

### **Deploy to Production**
```powershell
.\deploy-production.ps1 "Release message"
```
⏱️ Time: 15-20 minutes  
⚠️ Requires confirmation

### **Quick Sync Files**
```powershell
# Staging
.\sync-files.ps1 -Environment staging -Files "file.js","file.py"

# Production
.\sync-files.ps1 -Environment production -Files "file.js"
```
⏱️ Time: 2-3 minutes

### **Emergency Rollback**
```powershell
.\rollback-production.ps1 [optional-version-tag]
```
⏱️ Time: 3-5 minutes  
⚠️ Emergency use only

---

## 🌐 ENVIRONMENT URLS

**Staging:**
- Website: https://staging.ai-advisor.vn
- API: https://ai-advisor1-staging.onrender.com

**Production:**
- Website: https://ai-advisor.vn
- API: https://ai-advisor1-backend.onrender.com

---

## 📋 COMMON WORKFLOWS

### **Scenario 1: New Feature**
```powershell
# 1. Develop on feature branch
git checkout -b feature/my-feature

# 2. Test locally
npm run dev

# 3. Deploy to staging
git checkout staging
git merge feature/my-feature
.\deploy-staging.ps1 "Add my feature"

# 4. Test on staging
# Visit: https://staging.ai-advisor.vn

# 5. Deploy to production
.\deploy-production.ps1 "Release my feature"
```

### **Scenario 2: Quick Hotfix**
```powershell
# 1. Fix the bug in file.js

# 2. Deploy to staging
.\sync-files.ps1 -Environment staging -Files "file.js" -Message "Fix bug"

# 3. Test

# 4. Deploy to production
.\sync-files.ps1 -Environment production -Files "file.js" -Message "Fix bug"
```

### **Scenario 3: Weekly Release**
```powershell
# 1. Merge all features to staging
git checkout staging
git merge feature1
git merge feature2
.\deploy-staging.ps1 "Weekly update"

# 2. Internal testing (thorough)

# 3. Deploy to production
.\deploy-production.ps1 "v2.1.0 - Weekly release"
```

---

## 🔍 MONITORING

### **Check Health**
```powershell
# Staging
Invoke-WebRequest https://ai-advisor1-staging.onrender.com/health

# Production
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health
```

### **Check Deployment Status**
- Cloudflare Pages: https://dash.cloudflare.com
- Render Backend: https://dashboard.render.com

### **View Logs**
- Render: Dashboard → Service → Logs
- Browser: F12 → Console

---

## 🆘 EMERGENCY

### **Production Down**
```powershell
# 1. Check status
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health

# 2. Check deployment logs
# Visit: https://dashboard.render.com

# 3. Rollback if needed
.\rollback-production.ps1
```

### **Bad Deployment**
```powershell
# Immediately rollback
.\rollback-production.ps1

# Or rollback to specific version
.\rollback-production.ps1 "v2.0.5"
```

---

## 💡 TIPS

**Before Production Deploy:**
- ✅ Test thoroughly on staging
- ✅ Internal testing complete
- ✅ Check no critical bugs
- ✅ Database migration ready
- ✅ Have rollback plan

**Cost Optimization:**
- Staging: 100% FREE (Render Free + Supabase Free)
- Production: $14/month only

**Performance:**
- Staging may be slower (free tier sleeps)
- Production is always fast (paid tier)

---

## 📞 HELP

**Documentation:**
- Full Guide: `STAGING_SETUP_GUIDE.md`
- Troubleshooting: Ask Claude

**Dashboards:**
- Cloudflare: https://dash.cloudflare.com
- Render: https://dashboard.render.com
- Supabase: https://supabase.com/dashboard

**Contact:**
- Email: ngthson75@gmail.com
- Telegram: @your_telegram

---

**Setup Date:** [Fill when complete]  
**Last Updated:** 2026-01-24  
**Version:** 1.0
