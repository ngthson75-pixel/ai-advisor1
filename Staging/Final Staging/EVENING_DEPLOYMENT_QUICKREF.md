# ⚡ EVENING DEPLOYMENT - QUICK REFERENCE

## 🎯 ONE-PAGE CHEAT SHEET

### **Deployment Rule:**
```
Production deploys ONLY 20:00-22:00 (8PM-10PM)
Manual approval REQUIRED
NO auto-deploy
```

---

## ⏰ TODAY'S DEPLOYMENT SCHEDULE

**Preferred Days:** Tuesday, Wednesday, Thursday  
**Time:** 20:00-22:00  
**Duration:** 15 min deploy + 1.5 hours monitoring

---

## 🚀 HOW TO DEPLOY

### **Step 1: Test on Staging (Anytime)**

```powershell
.\deploy-staging.ps1 "Your changes"
# Test thoroughly
```

### **Step 2: Schedule Evening Deployment**

```powershell
.\schedule-production-deploy.ps1 "v2.1.0 - Release" -Time "20:00"
```

**What happens:**
- ✅ Pre-flight checks run
- ⏳ Waits until 20:00
- 🔔 Alerts you at deployment time
- 🔐 Requires your confirmation: "DEPLOY NOW"

### **Step 3: Monitor (20:15-21:30)**

**Every 15 minutes:**
```powershell
Invoke-WebRequest https://ai-advisor.vn/api/health
# Should return: 200 OK
```

**Check:**
- Render logs (errors?)
- Cloudflare analytics (traffic OK?)
- Test features (working?)

### **Step 4: Verify or Rollback**

**If all good:**
```
✅ Update deployment log
✅ Notify team
✅ Done!
```

**If issues:**
```powershell
.\rollback-production.ps1
# Reverts in 3-5 minutes
```

---

## 📋 PRE-DEPLOYMENT CHECKLIST

Quick checklist before scheduling:

- [ ] Tested on staging
- [ ] No critical bugs
- [ ] Can monitor 1-2 hours
- [ ] Rollback plan ready
- [ ] Team notified

**All checked?** → Schedule deployment

---

## ⚠️ SAFETY RULES

1. ✅ **ONLY evening** (20:00-22:00)
2. ✅ **Manual approval** required
3. ✅ **Must monitor** 1.5 hours
4. ✅ **Can rollback** quickly
5. ❌ **NO Friday** deployments
6. ❌ **NO business hours** (9-5)
7. ❌ **NO auto-deploy**

---

## 🔄 ROLLBACK (If Needed)

```powershell
.\rollback-production.ps1

# Takes 3-5 minutes
# Reverts to previous version
# Automatically deploys old code
```

**Rollback when:**
- Critical bug
- Features broken
- Users cannot login
- Multiple errors

---

## 📞 COMMANDS

### **Staging (Anytime)**
```powershell
.\deploy-staging.ps1 "message"
```

### **Production (Evening Only)**
```powershell
# Scheduled
.\schedule-production-deploy.ps1 "v2.1.0" -Time "20:00"

# Manual (if already evening)
.\deploy-production.ps1 "v2.1.0"
```

### **Status Check**
```powershell
.\check-status.ps1 -Environment all
```

### **Emergency Rollback**
```powershell
.\rollback-production.ps1
```

---

## 🎯 QUICK DECISION TREE

```
Is it evening (20:00-22:00)?
├─ NO → Wait or schedule for evening
└─ YES → Continue ↓

Tested on staging?
├─ NO → Test first!
└─ YES → Continue ↓

Can monitor 1-2 hours?
├─ NO → Schedule different time
└─ YES → Continue ↓

Rollback plan ready?
├─ NO → Prepare rollback command
└─ YES → ✅ DEPLOY!
```

---

## 💡 PRO TIPS

**Best deployment day:** Wednesday evening  
**Worst deployment day:** Friday evening  
**Best deployment time:** 20:00  
**Monitor until:** 21:30 minimum

**Never deploy when:**
- ❌ Tired
- ❌ Friday evening
- ❌ Business hours
- ❌ Without testing

**Always:**
- ✅ Test on staging first
- ✅ Have rollback ready
- ✅ Monitor full time
- ✅ Document results

---

## 📊 MONITORING CHECKLIST

| Time | Action | Pass? |
|------|--------|-------|
| 20:15 | Health check | ☐ |
| 20:30 | Test features | ☐ |
| 20:45 | Check logs | ☐ |
| 21:00 | Monitor traffic | ☐ |
| 21:15 | Performance test | ☐ |
| 21:30 | Final verification | ☐ |

**All checked?** → ✅ Success!

---

## 🔗 DOCUMENTATION

**Detailed guides:**
- `DEPLOYMENT_SAFETY_GUIDE.md` - Complete safety procedures
- `PRODUCTION_DEPLOYMENT_PLAYBOOK.md` - Full playbook
- `DEPLOYMENT_QUICKREF.md` - Command reference

**This is the quick version.** See full guides for details.

---

**Remember:** You are in control. No auto-deploy. You decide when.

**Deploy smart, deploy safe!** 🚀
