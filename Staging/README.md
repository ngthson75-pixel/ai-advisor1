# 🚀 AI ADVISOR STAGING SYSTEM - COMPLETE PACKAGE

## 📦 PACKAGE CONTENTS

Đây là bộ công cụ hoàn chỉnh để setup và quản lý staging environment cho AI Advisor MVP 2.0.

### **📋 DOCUMENTATION**

1. **STAGING_SETUP_GUIDE.md** - Hướng dẫn setup đầy đủ từ đầu (60 phút)
2. **DEPLOYMENT_QUICKREF.md** - Tham khảo nhanh các lệnh thường dùng
3. **README.md** (file này) - Tổng quan và quick start

### **🛠️ DEPLOYMENT SCRIPTS**

4. **setup-staging.ps1** - Tự động setup staging environment
5. **deploy-staging.ps1** - Deploy lên staging (1 lệnh)
6. **deploy-production.ps1** - Deploy lên production (với approval)
7. **sync-files.ps1** - Sync files nhanh giữa environments
8. **rollback-production.ps1** - Rollback khi có vấn đề
9. **check-status.ps1** - Kiểm tra health của environments

### **⚙️ CONFIGURATION**

10. **.gitignore** - Git ignore phù hợp cho project

---

## ⚡ QUICK START (5 PHÚT)

### **BƯỚC 1: Copy files vào project**

```powershell
# Copy tất cả files vào project root
cd C:\ai-advisor1
# Copy các file .ps1, .md, .gitignore vào đây
```

### **BƯỚC 2: Chạy auto setup**

```powershell
.\setup-staging.ps1
```

**Script này sẽ:**
- ✅ Tạo staging branch
- ✅ Configure git
- ✅ Hướng dẫn các bước tiếp theo

### **BƯỚC 3: Làm theo hướng dẫn**

Script sẽ hiển thị 6 bước manual cần làm:
1. Create Render staging backend
2. Create Supabase staging database
3. Configure environment variables
4. Run database migration
5. Create Cloudflare Pages staging
6. Setup custom domain (optional)

**Chi tiết:** Xem `STAGING_SETUP_GUIDE.md`

### **BƯỚC 4: Test deployment**

```powershell
# Check status
.\check-status.ps1 -Environment staging

# Deploy to staging
.\deploy-staging.ps1 "First staging deploy"

# Visit: https://staging.ai-advisor.vn
```

---

## 🎯 DAILY USAGE

### **Deploy Changes to Staging (Anytime)**

```powershell
.\deploy-staging.ps1 "Your commit message"
```

⏱️ **Time:** 5-10 minutes  
✅ **Safe:** Auto-deploys to staging only  
🕐 **When:** Anytime during work hours

### **Quick Fix Single File**

```powershell
.\sync-files.ps1 -Environment staging -Files "file.js" -Message "Fix bug"
```

⏱️ **Time:** 2-3 minutes  
✅ **Fast:** Syncs specific files only

### **Deploy to Production (Evening Only!)**

**Option 1: Scheduled Deployment (Recommended)**
```powershell
.\schedule-production-deploy.ps1 "v2.1.0 - Release message" -Time "20:00"
```

⏱️ **Time:** Waits until 20:00, then deploys (15-20 min)  
⚠️ **Control:** Manual approval required at deployment time  
🌙 **When:** Evening only (20:00-22:00 recommended)

**Option 2: Immediate Deployment (Evening)**
```powershell
.\deploy-production.ps1 "v2.1.0 - Release message"
```

⏱️ **Time:** 15-20 minutes  
⚠️ **Safe:** Requires 2 confirmations + evening time check  
🌙 **When:** Only deploy 20:00-22:00

### **Emergency Rollback**

```powershell
.\rollback-production.ps1
```

⏱️ **Time:** 3-5 minutes  
🚨 **Emergency:** Use when production has critical issues

### **Check Status**

```powershell
.\check-status.ps1 -Environment all
```

⏱️ **Time:** 10 seconds  
ℹ️ **Info:** Health check for both environments

---

## 📊 ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────┐
│         PRODUCTION (ai-advisor.vn)      │
│                                         │
│  Branch: main                           │
│  Backend: Render Starter ($7/month)    │
│  Database: Render PostgreSQL ($7)      │
│  Domain: ai-advisor.vn                  │
│  Users: ALL USERS (existing + new)     │
└─────────────────────────────────────────┘
                    ↑
                    │ Deploy after internal testing
                    │
┌─────────────────────────────────────────┐
│      STAGING (staging.ai-advisor.vn)    │
│                                         │
│  Branch: staging                        │
│  Backend: Render Free ($0/month)       │
│  Database: Supabase Free ($0)          │
│  Domain: staging.ai-advisor.vn          │
│  Users: INTERNAL ONLY (you + team)     │
└─────────────────────────────────────────┘
```

**Total Cost:** $14/month (staging FREE!)

**Key Features:**
- ✅ Staging for internal testing (you + team)
- ✅ Production for all users
- ✅ **Controlled evening deployment (20:00-22:00)**
- ✅ **Manual approval required** - no auto-deploy
- ✅ Emergency rollback capability
- ✅ Full monitoring & safety checks

---

## 🔄 WORKFLOW EXAMPLES

### **Example 1: New Feature Development**

```powershell
# 1. Create feature branch
git checkout staging
git pull origin staging
git checkout -b feature/new-ai-coach

# 2. Develop locally
# ... code changes ...

# 3. Test locally
npm run dev
python backend_api.py

# 4. Deploy to staging
git checkout staging
git merge feature/new-ai-coach
.\deploy-staging.ps1 "Add new AI coach feature"

# 5. Wait 10 mins, test on staging
# Visit: https://staging.ai-advisor.vn

# 6. Internal testing (you + team)
# Test all features thoroughly
# Check for bugs, performance issues

# 7. When ready, deploy to production
.\deploy-production.ps1 "v2.1.0 - Add new AI coach"
```

### **Example 2: Hotfix**

```powershell
# 1. Fix bug in backend_api.py
# ... make fix ...

# 2. Deploy to staging immediately
.\sync-files.ps1 -Environment staging -Files "backend_api.py" -Message "Fix critical bug"

# 3. Test (2 mins)

# 4. Deploy to production
.\sync-files.ps1 -Environment production -Files "backend_api.py" -Message "Fix critical bug"
```

### **Example 3: Weekly Release**

```powershell
# Monday: Merge all features to staging
git checkout staging
git merge feature1
git merge feature2
git merge feature3
.\deploy-staging.ps1 "Weekly update - features 1, 2, 3"

# Tuesday-Friday: Internal testing
# Test thoroughly on staging
# Fix bugs if found

# Saturday: Final verification
.\check-status.ps1 -Environment staging
# Verify all features work perfectly

# Sunday: Deploy to production (all users)
.\deploy-production.ps1 "v2.1.0 - Weekly release"
```

---

## 💡 BEST PRACTICES

### **✅ DO**

- ✅ Always test on staging first (internal testing)
- ✅ Test thoroughly before production deploy
- ✅ Use meaningful commit messages
- ✅ Run `check-status.ps1` before deploying
- ✅ Have rollback plan ready
- ✅ Monitor deployments (Render + Cloudflare dashboards)

### **❌ DON'T**

- ❌ Deploy to production without staging test
- ❌ Push directly to main branch
- ❌ Deploy on Friday evening (no weekend support)
- ❌ Deploy multiple features at once (hard to rollback)
- ❌ Skip internal testing on staging
- ❌ Forget to backup database before major changes

---

## 🎓 LEARNING RESOURCES

### **For Beginners:**

1. **Start here:** `DEPLOYMENT_QUICKREF.md`
2. **Setup:** `STAGING_SETUP_GUIDE.md`
3. **Practice:** Deploy to staging multiple times

### **For Advanced:**

1. **Customize scripts:** Edit `.ps1` files
2. **Setup CI/CD:** GitHub Actions
3. **Add monitoring:** Sentry, LogRocket
4. **Optimize costs:** Review hosting options

---

## 📞 SUPPORT

### **Issues & Questions:**

- **Documentation:** Read `STAGING_SETUP_GUIDE.md`
- **Quick answers:** `DEPLOYMENT_QUICKREF.md`
- **Check status:** `.\check-status.ps1`

### **Dashboards:**

- **Cloudflare:** https://dash.cloudflare.com
- **Render:** https://dashboard.render.com
- **Supabase:** https://supabase.com/dashboard
- **GitHub:** https://github.com/ngthson75-pixel/ai-advisor1

### **Contact:**

- **Email:** ngthson75@gmail.com
- **Telegram:** @your_telegram

---

## 🚨 EMERGENCY PROCEDURES

### **Production Down**

```powershell
# 1. Check status
.\check-status.ps1 -Environment production

# 2. Check dashboards
# Render: https://dashboard.render.com
# Cloudflare: https://dash.cloudflare.com

# 3. Rollback if needed
.\rollback-production.ps1

# 4. Monitor
.\check-status.ps1 -Environment production

# 5. Fix bug on staging
# 6. Re-deploy after testing
```

### **Staging Issues**

```powershell
# Staging issues don't affect production!
# Take your time to debug

# 1. Check logs
# Render: Dashboard → Logs
# Browser: F12 → Console

# 2. Redeploy
.\deploy-staging.ps1 "Fix issue"

# 3. If still broken, restore from main
git checkout staging
git reset --hard origin/main
git push origin staging --force
```

---

## 📈 METRICS TO TRACK

### **Deployment Success:**

- Time from commit to live (Target: < 15 min)
- Deployment failure rate (Target: < 5%)
- Rollback frequency (Target: < 1/month)

### **Testing Quality:**

- Internal testing coverage (Target: 100% features tested)
- Critical bugs found in staging (Good: Find before production)
- Staging test thoroughness (Target: All edge cases covered)

### **Performance:**

- Staging uptime (expect ~95% on free tier)
- Production uptime (target: >99.5%)
- API response time (target: < 3s)

---

## 🎉 SUCCESS CRITERIA

**You're successful when:**

✅ Can deploy to staging in < 5 minutes  
✅ Can deploy to production safely  
✅ Zero downtime deployments  
✅ Thorough internal testing before production  
✅ Can rollback in emergency  
✅ Sleeping well (no production fires!) 😴

---

## 🔄 VERSION HISTORY

- **v1.0 (2026-01-24):** Initial release
  - All deployment scripts
  - Complete documentation
  - Auto setup

---

## 📝 NEXT STEPS

### **After Setup:**

1. ✅ Run `.\setup-staging.ps1`
2. ✅ Follow manual setup steps
3. ✅ Deploy to staging: `.\deploy-staging.ps1 "Initial deploy"`
4. ✅ Test thoroughly on staging (internal)
5. ✅ When ready, deploy to production (all users)
6. ✅ Monitor production! 🚀

### **Week 2-4:**

1. Develop new features
2. Test on staging (you + team)
3. Deploy to production when ready
4. Monitor metrics and user feedback

### **Month 2+:**

1. Consider paid Render for staging (always-on)
2. Consider PostgreSQL for staging (persistent data)
3. Setup CI/CD automation
4. Scale infrastructure as users grow

---

## 🌟 CONCLUSION

**You now have:**

- ✅ Complete staging environment (FREE)
- ✅ One-command deployment
- ✅ Safe production releases
- ✅ Emergency rollback
- ✅ Professional workflow

**Total cost:** $14/month  
**Setup time:** 60 minutes  
**Deploy time:** 5-10 minutes  
**Peace of mind:** Priceless 😌

---

**Happy deploying! 🚀**

*Questions? Check `STAGING_SETUP_GUIDE.md` or `DEPLOYMENT_QUICKREF.md`*
