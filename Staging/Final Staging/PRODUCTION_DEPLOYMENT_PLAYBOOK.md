# 📋 PRODUCTION DEPLOYMENT PLAYBOOK

## 🎯 MỤC TIÊU

Deploy production **an toàn** vào **buổi tối** với kiểm soát chặt chẽ.

**Recommended Time:** 20:00-22:00 (8PM-10PM)  
**Duration:** ~30 minutes deploy + 1-2 hours monitoring  
**Required:** You hoặc team member available

---

## ⏰ DEPLOYMENT SCHEDULE

### **Thời gian khuyến nghị:**

| Time | Activity | Who |
|------|----------|-----|
| 19:30 | Pre-deployment prep | You |
| 20:00 | Start deployment | You + Team |
| 20:15 | Deployment complete | Monitor |
| 20:15-21:30 | Active monitoring | You |
| 21:30-22:00 | Final checks | You |

### **Tại sao buổi tối?**

✅ **Users ít nhất** - Ít người online, ít impact  
✅ **Có thời gian fix** - Nếu có bug, có thể fix ngay  
✅ **Không gấp rút** - Không pressure, làm việc cẩn thận  
✅ **Monitor đầy đủ** - 1-2 giờ để watch closely

---

## 📋 PRE-DEPLOYMENT CHECKLIST (19:00-19:30)

### **Code & Testing:**

- [ ] All code committed to staging branch
- [ ] Staging deployed and tested thoroughly
- [ ] Internal testing complete (you + team)
- [ ] No critical bugs found
- [ ] Performance acceptable on staging
- [ ] All features working as expected

### **Database:**

- [ ] Database migration script ready (if needed)
- [ ] Migration tested on staging database
- [ ] Backup plan prepared
- [ ] Rollback script ready

### **Infrastructure:**

- [ ] Backend health check passing on staging
- [ ] Frontend builds successfully
- [ ] All environment variables configured
- [ ] API keys valid and working

### **Documentation:**

- [ ] CHANGELOG.md updated
- [ ] Release notes prepared
- [ ] Version number decided
- [ ] Git tag planned

### **Team Coordination:**

- [ ] Team notified about deployment time
- [ ] On-call person identified (you or team member)
- [ ] Backup person available (optional)
- [ ] Communication channel ready (Telegram/Slack)

### **Personal Readiness:**

- [ ] Can dedicate 2 hours for monitoring
- [ ] Laptop/computer ready
- [ ] Good internet connection
- [ ] No other urgent tasks

---

## 🚀 DEPLOYMENT PROCESS (20:00-20:15)

### **Option 1: Scheduled Deployment (Recommended)**

```powershell
# Schedule for 20:00 (8PM)
.\schedule-production-deploy.ps1 "v2.1.0 - Feature improvements" -Time "20:00"

# Script will:
# 1. Validate time
# 2. Run pre-deployment checklist
# 3. Wait until 20:00
# 4. Alert you when ready
# 5. Require final confirmation
# 6. Execute deployment
```

### **Option 2: Manual Deployment**

```powershell
# Only deploy between 20:00-22:00
.\deploy-production.ps1 "v2.1.0 - Feature improvements"

# Script will:
# 1. Check current time
# 2. Warn if not evening
# 3. Require confirmation
# 4. Execute deployment
```

### **During Deployment:**

**DO:**
- ✅ Stay at computer
- ✅ Watch deployment logs
- ✅ Keep Render/Cloudflare dashboards open
- ✅ Have rollback command ready

**DON'T:**
- ❌ Leave computer
- ❌ Start other tasks
- ❌ Close terminal windows
- ❌ Panic if errors appear (follow playbook)

---

## 👀 POST-DEPLOYMENT MONITORING (20:15-22:00)

### **Immediate Checks (First 15 minutes):**

```powershell
# 1. Check backend health
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/health

# 2. Check frontend
# Visit: https://ai-advisor.vn
# Test: Login, core features

# 3. Check status
.\check-status.ps1 -Environment production

# 4. Check error logs
# Render: https://dashboard.render.com → Logs
# Cloudflare: https://dash.cloudflare.com → Analytics
```

**Expected:**
- ✅ Backend returns 200 OK
- ✅ Frontend loads in < 3 seconds
- ✅ No 500 errors in logs
- ✅ Core features work

**If issues detected:** Go to ROLLBACK section

### **Active Monitoring (20:15-21:30):**

**Every 15 minutes, check:**

| Time | Check | Action |
|------|-------|--------|
| 20:15 | Health endpoints | Log results |
| 20:30 | Error logs | Note any errors |
| 20:45 | User activity | Monitor traffic |
| 21:00 | Core features | Test manually |
| 21:15 | Performance | Check response times |
| 21:30 | Final check | All clear? |

**Tools:**

1. **Render Dashboard:**
   - URL: https://dashboard.render.com
   - Check: Logs, CPU, Memory
   - Look for: Errors, crashes, high usage

2. **Cloudflare Dashboard:**
   - URL: https://dash.cloudflare.com
   - Check: Traffic, errors
   - Look for: 500 errors, slow responses

3. **Production Website:**
   - URL: https://ai-advisor.vn
   - Test: Login, signals, portfolio, AI chat
   - Look for: Broken features, errors

### **Final Verification (21:30-22:00):**

- [ ] No critical errors in logs
- [ ] All core features working
- [ ] Performance acceptable
- [ ] No user complaints (if any users active)
- [ ] Database operations normal
- [ ] API response times good

**If all clear:**
```
✅ Deployment successful!
Send update to team
Note in deployment log
```

**If issues:**
```
⚠️  See ROLLBACK section
```

---

## 🚨 ROLLBACK PROCEDURE

### **When to rollback:**

- ❌ Critical feature broken
- ❌ Multiple 500 errors
- ❌ Database issues
- ❌ Users cannot login
- ❌ Performance severely degraded
- ❌ Data corruption detected

### **How to rollback:**

```powershell
# Immediate rollback to previous version
.\rollback-production.ps1

# Script will:
# 1. Confirm rollback intent
# 2. Revert to previous commit
# 3. Force push to production
# 4. Monitor rollback
```

**Timeline:**
- Decision: < 5 minutes
- Execution: 3-5 minutes
- Verification: 5-10 minutes
- **Total: ~15 minutes to stable state**

### **After rollback:**

1. **Communicate:**
   ```
   Send message to team:
   "Rolled back production to v2.0.5 due to [issue].
   Investigating. Will redeploy after fix."
   ```

2. **Investigate:**
   - Check staging - can you reproduce issue?
   - Review logs - what went wrong?
   - Test fix on staging

3. **Fix and redeploy:**
   - Fix issue on staging
   - Test thoroughly
   - Schedule new deployment (next evening)

---

## 📊 DEPLOYMENT LOG

Keep a simple log of all deployments:

| Date | Time | Version | Result | Issues | Notes |
|------|------|---------|--------|--------|-------|
| 2026-01-24 | 20:00 | v2.1.0 | ✅ Success | None | Smooth deploy |
| 2026-01-25 | 20:15 | v2.1.1 | ❌ Rolled back | API errors | Fixed next day |
| 2026-01-26 | 20:00 | v2.1.1 | ✅ Success | None | Retry successful |

**Store in:** `deployment_log.txt` or spreadsheet

---

## 🎯 SUCCESS CRITERIA

**Deployment is successful when:**

✅ All health checks pass  
✅ No critical errors in logs  
✅ Core features working  
✅ Performance acceptable  
✅ Monitored for 1.5 hours with no issues

**Then you can:**
- 🎉 Mark deployment as complete
- 📝 Update deployment log
- 💬 Notify team
- 😴 Relax!

---

## 💡 TIPS & BEST PRACTICES

### **DO:**

✅ **Always test on staging first** - No exceptions  
✅ **Deploy in evening** - 20:00-22:00 recommended  
✅ **Stay available for monitoring** - At least 1.5 hours  
✅ **Have rollback plan** - Know how to rollback quickly  
✅ **Document everything** - Keep deployment log  
✅ **Communicate with team** - Everyone knows what's happening

### **DON'T:**

❌ **Deploy on Friday evening** - No weekend support  
❌ **Deploy during business hours** - Too risky  
❌ **Deploy without testing** - Recipe for disaster  
❌ **Deploy multiple features at once** - Hard to debug  
❌ **Leave after deployment** - Monitor for issues  
❌ **Panic if issues occur** - Follow playbook

### **Weekly Deployment Schedule:**

**Recommended:**
- **Test on staging:** Monday-Thursday
- **Deploy to production:** Thursday or Friday evening
- **Monitor:** Friday evening + Saturday morning
- **Weekend:** Available for emergency fixes

**OR:**

- **Test on staging:** Monday-Wednesday  
- **Deploy to production:** Wednesday evening
- **Monitor:** Wednesday-Thursday
- **Rest of week:** Monitor stability

---

## 📞 EMERGENCY CONTACTS

**If deployment fails and you need help:**

1. **Check documentation:** This file
2. **Check logs:** Render + Cloudflare
3. **Try rollback:** `.\rollback-production.ps1`
4. **If still stuck:** Contact team member (if available)

**Keep calm and follow the playbook!** 🧘

---

## 📚 RELATED DOCUMENTS

- `DEPLOYMENT_QUICKREF.md` - Quick commands
- `TROUBLESHOOTING_GUIDE.md` - Debug issues
- `ARCHITECTURE.md` - System overview

---

**Last Updated:** 2026-01-24  
**Version:** 2.0 (Evening deployment focus)  
**Owner:** Nguyễn Thanh Sơn
