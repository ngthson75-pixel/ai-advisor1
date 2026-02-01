# 🛡️ DEPLOYMENT SAFETY & CONTROL GUIDE

## 🎯 DEPLOYMENT PHILOSOPHY

**Core Principles:**
1. ✅ **Manual Control** - No auto-deploy to production
2. ✅ **Evening Only** - Deploy 20:00-22:00 when traffic is low
3. ✅ **Always Monitor** - Stay available 1-2 hours after deploy
4. ✅ **Quick Rollback** - Can revert in 3-5 minutes if issues

---

## ⏰ DEPLOYMENT WINDOW

### **Recommended Times:**

| Day | Time | Status |
|-----|------|--------|
| Mon-Thu | 20:00-22:00 | ✅ **Best** |
| Tue-Thu | 20:00-22:00 | ✅ **Ideal** |
| Friday | 20:00-22:00 | ⚠️ **Risky** (no weekend support) |
| Sat-Sun | Any time | ❌ **Avoid** (weekend emergency) |
| Mon-Fri | 09:00-17:00 | ❌ **Never** (business hours) |

### **Why Evening Deployment?**

✅ **Fewer active users** - Less impact if issues occur  
✅ **Time to monitor** - Can watch for 1-2 hours  
✅ **Can rollback** - Enough time to fix before next day  
✅ **Less pressure** - Not rushed, more careful  
✅ **Team available** - Can coordinate with team if needed

---

## 🔐 MANUAL APPROVAL PROCESS

### **Three-Level Safety:**

```
Level 1: Pre-deployment Checklist
   ↓
Level 2: Scheduled Deployment (wait until evening)
   ↓
Level 3: Final Confirmation (you approve)
   ↓
Deploy
```

### **Level 1: Pre-deployment Checklist**

**Run before scheduling:**

```powershell
# Check current status
.\check-status.ps1 -Environment staging

# Verify staging is healthy
# - All features working
# - No critical bugs
# - Performance good
```

**Checklist:**
- [ ] Tested on staging
- [ ] All features work
- [ ] No critical bugs
- [ ] Team notified
- [ ] Can monitor 1-2 hours
- [ ] Rollback plan ready

### **Level 2: Scheduled Deployment**

```powershell
# Schedule for 20:00
.\schedule-production-deploy.ps1 "v2.1.0 - Release" -Time "20:00"

# What happens:
# 1. Pre-checks run
# 2. Countdown starts
# 3. Alert at deployment time
# 4. Requires your confirmation
```

### **Level 3: Final Confirmation**

**At 20:00, script asks:**
```
Type 'DEPLOY NOW' to proceed: _
```

**Only YOU or authorized team member can type this.**

No auto-deploy, no scripts can bypass this.

---

## 🚨 DEPLOYMENT SAFETY CHECKS

### **Automated Pre-flight Checks:**

```powershell
# These run automatically before deployment:

1. ✓ Git status clean
2. ✓ Staging branch exists
3. ✓ All changes committed
4. ✓ Current time check (evening?)
5. ✓ Backend health check
6. ✓ Frontend build test
```

### **Manual Verification Required:**

**You must verify:**
- [ ] Staging tested thoroughly
- [ ] No known bugs
- [ ] Database migration ready (if needed)
- [ ] Can dedicate 1-2 hours for monitoring
- [ ] Team knows about deployment

---

## 📊 POST-DEPLOYMENT MONITORING

### **Required Monitoring (20:15-21:30):**

**Every 15 minutes:**

```powershell
# Health check
Invoke-WebRequest https://ai-advisor.vn/api/health

# Expected: 200 OK
# If 500: Check logs immediately
```

**Dashboards to watch:**

1. **Render (Backend):**
   - URL: https://dashboard.render.com
   - Watch: Error logs, CPU usage
   
2. **Cloudflare (Frontend):**
   - URL: https://dash.cloudflare.com
   - Watch: Traffic, error rate

3. **Production Site:**
   - URL: https://ai-advisor.vn
   - Test: Login, signals, AI chat

### **Monitoring Checklist:**

| Time | Action | Expected | If Failed |
|------|--------|----------|-----------|
| 20:15 | Health check | 200 OK | Check logs |
| 20:30 | Test features | All work | Rollback |
| 20:45 | Check logs | No errors | Investigate |
| 21:00 | User activity | Normal | Monitor |
| 21:15 | Performance | < 3s | Optimize |
| 21:30 | Final check | All clear | Done! |

---

## 🔄 ROLLBACK PROCEDURES

### **When to Rollback:**

Rollback immediately if:
- ❌ Critical feature broken
- ❌ Users cannot login
- ❌ Multiple 500 errors
- ❌ Database corruption
- ❌ Severe performance degradation

### **How to Rollback:**

```powershell
# Immediate rollback (3-5 minutes)
.\rollback-production.ps1

# What it does:
# 1. Reverts to previous commit
# 2. Force pushes to production
# 3. Auto-deploys previous version
# 4. Monitors rollback success
```

### **After Rollback:**

1. **Notify team:**
   ```
   "Rolled back production to v2.0.5 due to [issue].
   Will investigate and redeploy tomorrow evening."
   ```

2. **Investigate on staging:**
   - Reproduce the issue
   - Fix the bug
   - Test thoroughly

3. **Redeploy next evening:**
   - Fix verified on staging
   - Schedule for next day 20:00

---

## 📋 DEPLOYMENT WORKFLOW

### **Complete End-to-End Process:**

**Day 1-3: Development**
```
Monday: Develop features
Tuesday: Continue development  
Wednesday: Test on staging
```

**Day 4: Deployment Day**

**19:30 - Pre-deployment:**
```powershell
# 1. Final staging check
.\check-status.ps1 -Environment staging

# 2. Verify all checklist items
# 3. Prepare for monitoring

# 4. Schedule deployment
.\schedule-production-deploy.ps1 "v2.1.0 - Weekly release" -Time "20:00"
```

**19:30-20:00 - Waiting:**
```
- Review deployment plan
- Have rollback command ready
- Open monitoring dashboards
- Clear your schedule for 1-2 hours
```

**20:00 - Deployment:**
```
⏰ Script alerts: "Ready to deploy!"
You type: "DEPLOY NOW"
Script executes deployment (15 min)
```

**20:15-21:30 - Active Monitoring:**
```
Every 15 mins:
- Check health endpoints
- Review error logs
- Test core features
- Monitor performance
```

**21:30 - Final Verification:**
```
✅ All checks pass → Success!
❌ Issues found → Rollback

Send update to team
Document in deployment log
```

---

## 🛠️ EMERGENCY PROCEDURES

### **Scenario 1: Critical Bug During Business Hours**

```
15:00 - Bug discovered
15:15 - Fix on staging
15:30 - Test fix
16:00 - Schedule evening deployment
20:00 - Deploy fix
```

**DO NOT deploy immediately unless:**
- Site is completely down
- Security vulnerability
- Data corruption in progress

### **Scenario 2: Production Down**

```powershell
# Immediate actions:
1. Check status
.\check-status.ps1 -Environment production

2. Check Render/Cloudflare dashboards

3. If deployment-related:
.\rollback-production.ps1

4. If infrastructure issue:
- Contact Render support
- Check status pages
```

### **Scenario 3: Deployment Stuck**

```
If deployment doesn't complete in 30 mins:

1. Check Render/Cloudflare build logs
2. Check for errors
3. If stuck, cancel and retry
4. If repeated failures, investigate locally
```

---

## 📝 DEPLOYMENT LOG

**Keep track of every deployment:**

```
Date: 2026-01-24
Time: 20:00
Version: v2.1.0
Changes: Improved AI Coach
Result: ✅ Success
Issues: None
Downtime: 0 minutes
Monitoring: 1.5 hours
Notes: Smooth deployment
```

**Template:**

```
Date: [YYYY-MM-DD]
Time: [HH:MM]
Version: [vX.X.X]
Changes: [Brief description]
Result: [✅ Success / ❌ Rolled back]
Issues: [None / List issues]
Downtime: [X minutes]
Monitoring: [X hours]
Notes: [Additional notes]
```

**Store in:** `deployment_log.txt` or spreadsheet

---

## ✅ SUCCESS CRITERIA

**Deployment is successful when:**

✅ All health checks pass  
✅ No critical errors in logs (15 min check)  
✅ Core features working (30 min check)  
✅ Performance acceptable (< 3s)  
✅ No user complaints  
✅ Monitored for 1.5 hours without issues

**Then you can:**
- 🎉 Mark as complete
- 📝 Update deployment log
- 💬 Notify team
- 😴 Rest easy

---

## 💡 TIPS & BEST PRACTICES

### **Before Deployment:**

1. ✅ **Test extensively on staging** - No shortcuts
2. ✅ **Clear your schedule** - Block 2 hours
3. ✅ **Notify team** - Everyone knows
4. ✅ **Prepare rollback** - Know the command
5. ✅ **Have backup plan** - What if fails?

### **During Deployment:**

1. ✅ **Stay focused** - No distractions
2. ✅ **Monitor actively** - Don't assume it's fine
3. ✅ **Take notes** - Document what happens
4. ✅ **Be patient** - Don't rush monitoring
5. ✅ **Trust the process** - Follow checklist

### **After Deployment:**

1. ✅ **Complete monitoring** - Full 1.5 hours
2. ✅ **Document results** - Update deployment log
3. ✅ **Communicate** - Update team
4. ✅ **Learn** - What can improve?
5. ✅ **Celebrate** - Successful deploy!

---

## 🚫 COMMON MISTAKES TO AVOID

### **DON'T:**

❌ **Deploy during business hours** - Too risky  
❌ **Deploy on Friday evening** - No weekend support  
❌ **Deploy without testing** - Recipe for disaster  
❌ **Leave after deployment** - Must monitor  
❌ **Deploy multiple features** - Hard to debug  
❌ **Skip monitoring** - Might miss issues  
❌ **Auto-deploy production** - Always manual  
❌ **Deploy when tired** - Need to be sharp

### **DO:**

✅ **Deploy Tuesday-Thursday evening** - Best days  
✅ **Test thoroughly first** - On staging  
✅ **Monitor for 1.5 hours** - Don't rush  
✅ **Have rollback ready** - Just in case  
✅ **Deploy one feature** - Easier to debug  
✅ **Stay available** - For full monitoring  
✅ **Manual approval only** - You control it  
✅ **Deploy when fresh** - Sharp mind needed

---

## 📞 SUPPORT & ESCALATION

### **If You Need Help:**

1. **Check documentation:** This guide
2. **Check logs:** Render + Cloudflare
3. **Try rollback:** If deployment issue
4. **Contact team:** If available
5. **Stay calm:** Follow the process

### **Emergency Contacts:**

- **You:** [Your phone]
- **Team member 1:** [If applicable]
- **Render support:** https://render.com/support
- **Cloudflare support:** https://dash.cloudflare.com/support

---

## 🎓 SUMMARY

**Remember:**

1. 🌙 **Deploy evenings only (20:00-22:00)**
2. 🔐 **Manual approval required**
3. 📋 **Follow pre-deployment checklist**
4. 👀 **Monitor for 1.5 hours minimum**
5. 🔄 **Can rollback in 3-5 minutes**
6. 🛡️ **Safety over speed**

**You are in control.** No script will auto-deploy.  
**You make the final decision.** Every time.

---

**Stay safe, deploy smart!** 🚀

**Version:** 2.0  
**Last Updated:** 2026-01-24  
**Owner:** Nguyễn Thanh Sơn
