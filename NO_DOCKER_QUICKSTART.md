# ⚡ QUICK START - NO DOCKER NEEDED

## 🎯 3 BƯỚC ĐƠN GIẢN (5 phút)

### **BƯỚC 1: Setup Environment (1 phút)**

```powershell
cd C:\ai-advisor1

# Copy environment template
Copy-Item .env.example .env.local

# Edit và thêm OPENAI_API_KEY
notepad .env.local
```

Thêm vào file:
```bash
OPENAI_API_KEY=sk-... (your ChatGPT key)
DATABASE_URL=sqlite:///local_signals.db
FLASK_ENV=development
```

---

### **BƯỚC 2: Start Development (2 phút)**

**Option A: Chỉ Frontend (Đơn giản nhất)**

```powershell
cd C:\ai-advisor1\frontend
npm install  # First time only
npm run dev

# ✅ Open: http://localhost:5173
```

**Option B: Frontend + Backend**

Terminal 1 (Backend):
```powershell
cd C:\ai-advisor1
pip install -r requirements.txt --break-system-packages
python backend_api.py

# ✅ Running at: http://localhost:10000
```

Terminal 2 (Frontend):
```powershell
cd C:\ai-advisor1\frontend
npm run dev

# ✅ Open: http://localhost:5173
```

---

### **BƯỚC 3: Test và Deploy (2 phút)**

```powershell
cd C:\ai-advisor1

# Test (optional)
pytest tests/ -v -m "not slow"

# Commit
git add .
git commit -m "feat: my changes"

# Deploy to staging
git push origin staging

# ✅ Check GitHub Actions:
# https://github.com/ngthson75-pixel/ai-advisor1/actions
```

---

## ✅ HOÀN THÀNH!

**Bạn đã có:**
- ✅ Local development (no Docker)
- ✅ Fast iteration (2-5 min)
- ✅ Auto-test & deploy (CI/CD)

**So với trước:**
- Old: 30-60 phút per bug
- New: 2-5 phút per bug
- **10-20x FASTER!** 🚀

---

## 📋 DAILY WORKFLOW

```powershell
# Morning: Start dev
cd C:\ai-advisor1\frontend
npm run dev

# Develop: Make changes
# → Code changes auto-reload
# → No manual refresh needed

# Before lunch: Test
cd C:\ai-advisor1
pytest tests/ -v

# Afternoon: Deploy
git add .
git commit -m "feat: feature X"
git push origin staging

# End of day: Check results
# → GitHub Actions auto-tested
# → Deployed to staging if pass
# → Check: https://staging.ai-advisor.vn
```

---

## 🆘 TROUBLESHOOTING

**Frontend won't start?**
```powershell
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Backend errors?**
```powershell
pip install -r requirements.txt --break-system-packages
# Check .env.local exists
python backend_api.py
```

**Tests fail?**
```powershell
# Install test deps
pip install pytest pytest-flask --break-system-packages

# Run again
pytest tests/ -v
```

---

## 💡 TIPS

**Tip 1: Use SQLite (Simple)**
```bash
# In .env.local:
DATABASE_URL=sqlite:///local_signals.db
# → Auto-creates local file
# → No PostgreSQL needed
```

**Tip 2: Test Before Push**
```powershell
# Quick test (1 min)
pytest tests/ -v -m "not slow"

# Full test (on GitHub after push)
git push → GitHub Actions runs all tests
```

**Tip 3: Skip Backend**
```powershell
# Frontend can connect to production API
# Just start frontend:
npm run dev

# Frontend → Production backend
# Faster development!
```

---

## 🎯 NEXT STEPS

1. ✅ Start frontend: `npm run dev`
2. ✅ Make changes
3. ✅ Test: `pytest tests/ -v`
4. ✅ Push: `git push origin staging`
5. ✅ Profit! 🎉

**You don't need Docker at all!**

---

**Version:** 2.0 (No Docker)  
**Last Updated:** 2026-02-01
