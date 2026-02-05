# SELL SCANNER - QUICK DEPLOY GUIDE

**Version:** 2.0  
**Date:** 2026-02-05  

---

## ⚡ QUICK START (5 PHÚT)

### 1. Copy files
```powershell
cd C:\ai-advisor1

# Scanner
Copy-Item sell_signal_scanner_v2_production.py sell_signal_scanner_v2.py -Force

# Workflow
New-Item -ItemType Directory -Force -Path .github\workflows
Copy-Item hourly-sell-scanner.yml .github\workflows\hourly-sell-scanner.yml -Force
```

### 2. Push to staging
```powershell
git add sell_signal_scanner_v2.py .github\workflows\hourly-sell-scanner.yml
git commit -m "feat: Add hourly SELL scanner + GitHub Actions"
git push origin staging
```

### 3. Test on GitHub
```
GitHub → Actions → Hourly SELL Signal Scanner
→ Run workflow → Select: staging → Run
```

### 4. Deploy to production
```powershell
git checkout main
git merge staging
git push origin main
```

---

## 📅 SCHEDULE

**Scan times (Vietnam):**
- 🕘 9:00 AM
- 🕙 10:00 AM
- 🕚 11:00 AM
- 🕐 1:00 PM
- 🕑 2:00 PM

**Days:** Monday-Friday only

**Frequency:** 5 times/day, ~100 times/month

---

## 📊 EXPECTED OUTPUT

```
✓ Scanning 78 tickers...
🟢 VCB - TP_PARTIAL - +8.14%
🔴 HPG - MA20_CONSECUTIVE - -3.64%
✓ Generated 26 SELL signals

New signals: 26
```

---

## 🔍 VERIFY

```powershell
# Check signals
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/signals

# Check workflow
# GitHub → Actions → See runs
```

---

## 🐛 TROUBLESHOOTING

**Workflow not showing?**
```powershell
git add .github\workflows\hourly-sell-scanner.yml
git commit -m "ci: Add workflow"
git push origin staging
```

**Scanner fails?**
→ Check logs: GitHub → Actions → Latest run

**No signals?**
→ Normal if market doesn't trigger conditions

---

## 📁 FILES

All files in `/mnt/user-data/outputs/`:
1. `sell_signal_scanner_v2_production.py` - Scanner
2. `hourly-sell-scanner.yml` - Workflow
3. `DEPLOY_SELL_SCANNER_GUIDE.md` - Full guide
4. `SELL_SCANNER_QUICK_DEPLOY.md` - This file

---

**Ready!** Follow steps 1-4 above. 🚀
