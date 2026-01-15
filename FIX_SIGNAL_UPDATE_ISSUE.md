# 🔍 FIX: TÍN HIỆU KHÔNG CẬP NHẬT

## ❌ **VẤN ĐỀ:**

**Tín hiệu không thay đổi hàng ngày** vì:
```
Button "Refresh" chỉ FETCH data cũ
KHÔNG quét tín hiệu mới
→ Tín hiệu ngày 13/1 vẫn hiển thị ngày 14/1 ❌
```

---

## 🔍 **CƠ CHẾ HIỆN TẠI:**

### **Luồng khi click "Refresh":**

```
1. Click "Refresh"
    ↓
2. Call: GET /api/signals
    ↓
3. Backend query database
    ↓
4. Return: Tín hiệu CŨ (từ 13/1/2026)
    ↓
5. Display: TCB, HPG, VHM, VCB (không đổi) ❌
```

**Thiếu:**
- ❌ Không quét tín hiệu mới
- ❌ Không có auto-scan hàng ngày
- ❌ Button "Refresh" chỉ fetch, không scan

---

## ✅ **3 GIẢI PHÁP:**

### **OPTION 1: Manual Scan (Immediate)**

**Mỗi ngày chạy lệnh này:**

```powershell
# Trigger scan:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST -UseBasicParsing

# Output:
# "signals_created": 4
# "message": "Quét hoàn tất! Tìm thấy 4 tín hiệu mới."

# Then refresh website
```

**Pros:**
- ✅ 0 setup time
- ✅ Free
- ✅ Control hoàn toàn

**Cons:**
- ⚠️ Phải nhớ chạy mỗi ngày
- ⚠️ Manual work

---

### **OPTION 2: GitHub Actions Auto-Scan (RECOMMENDED ⭐)**

**Setup tự động scan mỗi ngày lúc 6PM:**

#### **Bước 1: Tạo workflow file (5 phút)**

```powershell
cd C:\ai-advisor1

# Create directory:
mkdir -p .github\workflows

# Create file: .github\workflows\daily-scan.yml
# Copy content from attachment ⬆️
```

**File: `.github/workflows/daily-scan.yml`**
```yaml
name: Daily Signal Scan

on:
  schedule:
    # 6:00 PM Vietnam time (11:00 AM UTC)
    - cron: '0 11 * * *'
  workflow_dispatch: # Manual trigger

jobs:
  scan-signals:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Signal Scan
        run: |
          curl -X POST https://ai-advisor1-backend.onrender.com/api/scan
      
      - name: Wait for Scan
        run: sleep 180
      
      - name: Verify Signals
        run: |
          curl https://ai-advisor1-backend.onrender.com/api/signals
```

#### **Bước 2: Deploy (2 phút)**

```powershell
cd C:\ai-advisor1

git add .github/workflows/daily-scan.yml
git commit -m "Add: Auto-scan signals daily at 6PM"
git push origin main
```

#### **Bước 3: Enable in GitHub (3 phút)**

```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1
2. Tab: "Actions"
3. Click: "Daily Signal Scan"
4. Click: "Enable workflow"
5. Test: Click "Run workflow" → "Run workflow"
6. Wait 3 minutes
7. Check website for new signals ✅
```

**Pros:**
- ✅ **HOÀN TOÀN TỰ ĐỘNG**
- ✅ Free (GitHub Actions free tier: 2000 mins/month)
- ✅ Chạy mỗi ngày lúc 6PM
- ✅ Có thể manual trigger
- ✅ Logs để debug

**Cons:**
- ⚠️ Setup 10 phút
- ⚠️ Cần enable trên GitHub

**Cost:**
```
GitHub Actions free tier:
- 2000 minutes/month
- Each scan: ~3 minutes
- Daily scans: 3 min × 30 days = 90 mins/month
- Usage: 90/2000 = 4.5%

Cost: $0 ✅
```

---

### **OPTION 3: Add "Scan" Button to UI (Best UX)**

**Thêm button "Quét tín hiệu mới" vào frontend:**

```jsx
// In SignalsModule.jsx:

const [scanning, setScanning] = useState(false);

const handleScan = async () => {
  if (!confirm('Quét tín hiệu mới? Sẽ mất 2-3 phút.')) return;
  
  setScanning(true);
  try {
    const response = await fetch(`${API_BASE}/scan`, {
      method: 'POST'
    });
    const data = await response.json();
    
    if (data.success) {
      alert(`✅ Quét hoàn tất! Tìm thấy ${data.signals_created} tín hiệu mới.`);
      fetchSignals(); // Refresh list
    }
  } catch (error) {
    alert('Lỗi khi quét tín hiệu');
  } finally {
    setScanning(false);
  }
};

// UI:
<button onClick={handleScan} disabled={scanning}>
  {scanning ? '⏳ Đang quét...' : '🔍 Quét tín hiệu mới'}
</button>
```

**Pros:**
- ✅ User có thể scan bất kỳ lúc nào
- ✅ Clear UX
- ✅ Immediate feedback

**Cons:**
- ⚠️ Cần update frontend
- ⚠️ Users có thể abuse (spam scan)

---

## 🎯 **KHUYẾN NGHỊ:**

### **NGẮN HẠN (Bây giờ):**
**→ OPTION 1: Manual Scan**
```powershell
# Mỗi sáng (hoặc 6PM):
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST -UseBasicParsing
```

### **DÀI HẠN (Setup 1 lần):**
**→ OPTION 2: GitHub Actions**
- Setup 1 lần (10 phút)
- Tự động mãi mãi
- Free
- Chạy mỗi ngày 6PM

### **TỐI ƯU (Nếu có thời gian):**
**→ OPTION 2 + OPTION 3**
- GitHub Actions: Auto-scan hàng ngày
- UI Button: User có thể scan thêm nếu muốn

---

## 📊 **SO SÁNH:**

| Feature | Manual | GitHub Actions | UI Button |
|---------|--------|----------------|-----------|
| **Setup time** | 0 | 10 mins | 30 mins |
| **Cost** | $0 | $0 | $0 |
| **Auto daily** | ❌ | ✅ | ❌ |
| **Manual trigger** | ✅ | ✅ | ✅ |
| **User friendly** | ❌ | ⚠️ | ✅ |
| **Maintenance** | Daily | None | None |

---

## 🚀 **DEPLOY GITHUB ACTIONS (10 PHÚT):**

### **BƯỚC 1: Create Workflow File (5 phút)**

```powershell
cd C:\ai-advisor1

# Create directory:
New-Item -Path ".github\workflows" -ItemType Directory -Force

# Download daily-scan.yml from attachment ⬆️
# Save to: .github\workflows\daily-scan.yml
```

---

### **BƯỚC 2: Push to GitHub (2 phút)**

```powershell
cd C:\ai-advisor1

git add .github/workflows/daily-scan.yml
git commit -m "Add: Daily auto-scan at 6PM Vietnam time"
git push origin main
```

---

### **BƯỚC 3: Enable & Test (3 phút)**

```
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions

2. Click: "Daily Signal Scan" workflow

3. Click: "Enable workflow" (if needed)

4. Test manually:
   - Click: "Run workflow" dropdown
   - Select: "Branch: main"
   - Click: "Run workflow" button

5. Watch workflow run (~3 minutes)

6. Check logs:
   - ✅ "Scan triggered successfully!"
   - ✅ "Signals verified: 4 signals found"

7. Refresh website:
   - Should see NEW signals with TODAY's date ✅
```

---

## 🔍 **VERIFY AUTO-SCAN WORKS:**

### **After setup, check daily:**

```
Morning (7AM):
1. Visit: https://ai-advisor.vn
2. Check "Tín hiệu giao dịch"
3. Ngày: Should be TODAY ✅

Or check GitHub Actions:
1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Should see: "Daily Signal Scan" ran at 6:00 PM yesterday
3. Status: ✅ Success
```

---

## 🐛 **TROUBLESHOOTING:**

### **Issue: GitHub Actions not running**

**Check 1: Is workflow enabled?**
```
GitHub → Actions → Daily Signal Scan → Enable workflow
```

**Check 2: Is schedule correct?**
```yaml
cron: '0 11 * * *'  # 11:00 AM UTC = 6:00 PM Vietnam
```

**Check 3: Manual test**
```
Actions → Daily Signal Scan → Run workflow
Check logs for errors
```

---

### **Issue: Scan runs but no new signals**

**Possible causes:**
1. Backend scan logic issues
2. No stocks meet criteria today
3. Database reset (Render ephemeral storage)

**Debug:**
```powershell
# Check backend logs:
# Render dashboard → ai-advisor1-backend → Logs

# Manual scan test:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST -UseBasicParsing

# Check response:
# Should show: "signals_created": X
```

---

### **Issue: Signals show wrong date**

**Check timezone:**
```python
# In backend_api.py:
# Make sure timezone is correct:
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')  # Uses server timezone

# Or force Vietnam timezone:
import pytz
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
today = datetime.now(vn_tz).strftime('%Y-%m-%d')
```

---

## ⏰ **SCHEDULE DETAILS:**

### **Current schedule:**
```yaml
cron: '0 11 * * *'
```

**Means:**
- Minute: 0
- Hour: 11 (UTC)
- Day: * (every day)
- Month: * (every month)
- Weekday: * (every day of week)

**Vietnam time:**
- 11:00 AM UTC = 6:00 PM Vietnam (UTC+7)

**To change schedule:**
```yaml
# 8:00 PM Vietnam (1:00 PM UTC):
cron: '0 13 * * *'

# 6:00 AM Vietnam (11:00 PM UTC previous day):
cron: '0 23 * * *'

# Weekdays only (Mon-Fri):
cron: '0 11 * * 1-5'
```

---

## 📝 **WORKFLOW EXPLANATION:**

```yaml
name: Daily Signal Scan

on:
  schedule:
    - cron: '0 11 * * *'  # Run daily at 6PM Vietnam
  workflow_dispatch:       # Allow manual trigger

jobs:
  scan-signals:
    runs-on: ubuntu-latest  # Free GitHub runner
    
    steps:
      # Step 1: Trigger scan
      - name: Trigger Signal Scan
        run: |
          curl -X POST https://ai-advisor1-backend.onrender.com/api/scan
      
      # Step 2: Wait for completion
      - name: Wait for Scan to Complete
        run: sleep 180  # 3 minutes
      
      # Step 3: Verify signals created
      - name: Verify Signals
        run: |
          curl https://ai-advisor1-backend.onrender.com/api/signals
```

**What it does:**
1. ✅ Runs at 6PM Vietnam daily (automatic)
2. ✅ Calls `/api/scan` to create new signals
3. ✅ Waits 3 minutes for scan to complete
4. ✅ Verifies signals were created
5. ✅ Shows success/failure in logs

---

## 💡 **BEST PRACTICES:**

### **For production:**

1. **Add notifications:**
```yaml
- name: Notify on Failure
  if: failure()
  run: |
    # Send email/Telegram notification
    curl -X POST https://api.telegram.org/bot${{ secrets.BOT_TOKEN }}/sendMessage \
      -d chat_id=${{ secrets.CHAT_ID }} \
      -d text="❌ Daily scan failed!"
```

2. **Add retry logic:**
```yaml
- name: Trigger Scan with Retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    command: |
      curl -X POST https://ai-advisor1-backend.onrender.com/api/scan
```

3. **Monitor execution:**
```
GitHub → Actions → Daily Signal Scan
Check "Last run" daily
```

---

## ✅ **CHECKLIST:**

### **Setup:**
- [ ] Create `.github/workflows/daily-scan.yml`
- [ ] Push to GitHub
- [ ] Enable workflow in GitHub Actions
- [ ] Manual test run
- [ ] Verify signals created

### **Daily monitoring:**
- [ ] Check GitHub Actions ran at 6PM
- [ ] Verify new signals on website
- [ ] Check signal date is TODAY

### **If issues:**
- [ ] Check GitHub Actions logs
- [ ] Manual scan test
- [ ] Check backend logs on Render

---

## 🎉 **EXPECTED RESULTS:**

### **Before setup:**
```
Ngày 13/1: Signals A, B, C, D
Ngày 14/1: STILL Signals A, B, C, D ❌
Ngày 15/1: STILL Signals A, B, C, D ❌
```

### **After setup:**
```
Ngày 13/1 6PM: Scan runs → Signals A, B, C, D
Ngày 14/1 6PM: Scan runs → Signals E, F, G, H ✅
Ngày 15/1 6PM: Scan runs → Signals I, J, K, L ✅
```

---

## 📞 **QUICK COMMANDS:**

```powershell
# Manual scan (immediate):
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST -UseBasicParsing

# Setup auto-scan:
cd C:\ai-advisor1
mkdir .github\workflows
# Create daily-scan.yml
git add .github\workflows\daily-scan.yml
git commit -m "Add: Auto-scan daily"
git push origin main

# Test workflow:
# GitHub → Actions → Daily Signal Scan → Run workflow

# Check signals:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals | Select-Object Content
```

---

## 🎯 **SUMMARY:**

**Problem:**
- Tín hiệu không cập nhật hàng ngày
- Button "Refresh" chỉ fetch, không scan

**Solution (Recommended):**
- GitHub Actions auto-scan mỗi ngày 6PM
- 10 phút setup
- Free forever
- Tự động hoàn toàn

**Alternative:**
- Manual scan mỗi ngày (0 setup, manual work)
- UI button (30 phút setup, best UX)

**Deploy now:**
```powershell
cd C:\ai-advisor1
# Create .github/workflows/daily-scan.yml
git add .github/workflows/daily-scan.yml
git commit -m "Add: Auto-scan"
git push origin main
# Enable on GitHub
```

---

**Setup ngay để tín hiệu tự động cập nhật mỗi ngày!** 🚀
