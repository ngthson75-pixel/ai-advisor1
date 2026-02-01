# 📘 STAGING VS PRODUCTION - CLARIFICATION

## 🎯 TÓM TẮT

Hệ thống có **2 môi trường riêng biệt** với mục đích khác nhau:

---

## 🧪 STAGING ENVIRONMENT

**Mục đích:** Môi trường test **nội bộ**

**Người dùng:**
- ✅ Bạn (founder)
- ✅ Team members (nếu có)
- ❌ KHÔNG cho external users
- ❌ KHÔNG cho beta testers

**Khi nào dùng:**
- Test features mới trước khi release
- Phát hiện bugs sớm
- Thử nghiệm không ảnh hưởng production
- Internal quality assurance

**URL:** https://staging.ai-advisor.vn

**Chi phí:** $0 (miễn phí 100%)

---

## 🌐 PRODUCTION ENVIRONMENT

**Mục đích:** Môi trường **live** cho tất cả users

**Người dùng:**
- ✅ Tất cả users (existing + new)
- ✅ Existing customers
- ✅ New signups
- ✅ Beta testers (nếu muốn test features mới)

**Đặc điểm:**
- Always online (24/7)
- Fast performance
- Stable và reliable
- Real data, real money

**URL:** https://ai-advisor.vn

**Chi phí:** $14/month

---

## 🔄 WORKFLOW

### **Development Flow:**

```
1. Develop locally
   ↓
2. Deploy to STAGING (internal testing)
   ↓
3. Test thoroughly (you + team)
   ↓
4. Fix bugs if found
   ↓
5. Deploy to PRODUCTION (evening, all users)
   ↓
6. Monitor for 1-2 hours
```

### **Correct Workflow:**

```
✅ Develop → Staging (you + team) → Production (evening, all users)
```

### **Deployment Timing:**

**Staging:** Anytime during work hours  
**Production:** **Evening only (20:00-22:00)** - Recommended

**Why evening?**
- ✅ Fewer users online → Less impact
- ✅ Time to monitor and fix issues
- ✅ Can rollback if needed
- ✅ Not rushed, more careful

---

## 💡 KHUYẾN NGHỊ

### **Staging: Internal Only**

Chỉ dùng cho:
- ✅ Bạn test features mới
- ✅ Team test trước release
- ✅ Quality assurance nội bộ
- ✅ Phát hiện bugs critical

**Deploy anytime:** During work hours OK

### **Production: All Users**

Cho tất cả:
- ✅ All existing users
- ✅ New signups
- ✅ Everyone gets same version

**Deploy timing:** **Evening only (20:00-22:00)**

### **Deployment Strategy:**

**Giai đoạn đầu (MVP 2.0):**
1. Test kỹ trên staging (nội bộ)
2. Schedule production deploy for evening
3. Deploy at 20:00-22:00
4. Monitor carefully for 1-2 hours
5. Collect user feedback from production

**Sau này (khi có nhiều users):**
1. Same process - test on staging
2. Deploy production in evening
3. Monitor more closely (more users = more impact)
4. Have faster rollback plan

---

## 📊 SO SÁNH

| Aspect | Staging | Production |
|--------|---------|------------|
| **Purpose** | Internal testing | Live service |
| **Users** | You + team | All users |
| **Data** | Test data | Real data |
| **Performance** | Slower (free tier) | Fast (paid) |
| **Uptime** | ~95% (can sleep) | 99.5%+ (always on) |
| **Cost** | $0 | $14/month |
| **URL** | staging.ai-advisor.vn | ai-advisor.vn |
| **Database** | Supabase Free | Render PostgreSQL |

---

## 🎯 EXAMPLE SCENARIOS

### **Scenario 1: New Feature - AI Coach Improvement**

```powershell
# Monday-Wednesday: Develop & test on staging
# 1. Develop locally
# ... code changes ...

# 2. Deploy to staging (anytime)
.\deploy-staging.ps1 "Improve AI Coach"

# 3. Test yourself + team
# Visit: https://staging.ai-advisor.vn
# Test all edge cases
# Make sure it works perfectly

# Wednesday evening: Deploy to production
# 4. Schedule deployment for 20:00
.\schedule-production-deploy.ps1 "v2.1.0 - Improved AI Coach" -Time "20:00"

# Script will wait until 20:00, then deploy

# 5. Monitor 20:00-21:30
# Check logs, test features, watch for errors

# ✅ Success!
```

### **Scenario 2: Urgent Hotfix**

```powershell
# Critical bug found at 15:00 (3PM)

# 1. Fix immediately on staging
.\sync-files.ps1 -Environment staging -Files "backend_api.py" -Message "Fix critical bug"

# 2. Test on staging (15 mins)

# 3. Schedule evening deployment
.\schedule-production-deploy.ps1 "v2.0.6 - Critical bugfix" -Time "20:00"

# 4. Wait until evening (safer than immediate deploy)
# 5. Deploy at 20:00
# 6. Monitor

# Note: Only deploy immediately if truly emergency
# Otherwise, wait for evening window
```

### **Scenario 3: Weekly Release**

```powershell
# Monday: Start development
# Tuesday-Wednesday: Develop features
# Thursday: Test on staging

# Thursday 19:30: Pre-deployment prep
# - Final tests
# - Check staging thoroughly
# - Prepare rollback plan

# Thursday 20:00: Production deployment
.\schedule-production-deploy.ps1 "v2.2.0 - Weekly release" -Time "20:00"

# Thursday 20:00-21:30: Active monitoring
# - Every 15 mins: check health
# - Watch logs
# - Test features

# Thursday 21:30: Final verification
# ✅ All good → Done!
# ❌ Issues → Rollback and fix tomorrow

# Friday: Normal operation, monitor stability
```

---

## ✅ BEST PRACTICES

### **Staging:**

1. ✅ Test mọi feature trước khi production
2. ✅ Tự test kỹ (hoặc với team)
3. ✅ Dùng test data, không dùng real data
4. ✅ Có thể thử nghiệm mạo hiểm
5. ✅ Deploy anytime during work hours

### **Production:**

1. ✅ **Chỉ deploy buổi tối (20:00-22:00)**
2. ✅ Luôn test kỹ trên staging trước
3. ✅ Monitor carefully sau deploy (1-2 giờ)
4. ✅ Có rollback plan sẵn sàng
5. ✅ Backup database trước major changes
6. ✅ Có thể theo dõi và xử lý nếu có vấn đề

### **Deployment Timing:**

1. ✅ **Best:** Thứ 3-5 tối (Tue-Thu evening)
2. ⚠️ **Acceptable:** Thứ 2 tối (Mon evening)
3. ❌ **Avoid:** Thứ 6 tối (Fri evening) - No weekend support
4. ❌ **Never:** Business hours (9AM-5PM) - Too risky

### **Weekly Routine:**

**Recommended schedule:**
```
Monday:    Develop features
Tuesday:   Continue development
Wednesday: Test on staging
Thursday:  Deploy to production (evening)
Friday:    Monitor stability, fix if needed
Weekend:   Rest (unless emergency)
```

---

## 🎓 TÓM LẠI

**Staging:**
- Nội bộ only (you + team)
- Test trước khi release
- Free, có thể không stable
- Your QA environment
- **Deploy anytime**

**Production:**
- Tất cả users
- Live service  
- Paid, fast, stable
- Your real product
- **Deploy ONLY evening (20:00-22:00)**

**Key Points:**
- ✅ No beta testing needed
- ✅ Staging = internal testing only
- ✅ Production = deploy in evening with manual approval
- ✅ Always monitor 1-2 hours after deploy

---

**Last Updated:** 2026-01-24  
**Version:** 1.1 (Updated with clarification)
