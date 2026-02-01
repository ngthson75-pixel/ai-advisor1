# 🚀 AI ADVISOR - LOCAL DEVELOPMENT (NO DOCKER)

## ✅ SIMPLIFIED SETUP - Windows bất kỳ version nào

Không cần Docker Desktop! Workflow đơn giản hơn.

---

## 📋 PREREQUISITES

- ✅ Python 3.10+ (có rồi)
- ✅ Node.js 18+ (có rồi)
- ✅ Git (có rồi)
- ❌ Docker (KHÔNG CẦN!)

---

## 🎯 LOCAL DEVELOPMENT WORKFLOW

### **1. Frontend Development**

```powershell
cd C:\ai-advisor1\frontend

# Install dependencies (first time)
npm install

# Start dev server
npm run dev

# Open: http://localhost:5173
```

**Features:**
- ✅ Hot reload (code changes → auto refresh)
- ✅ Fast (Vite dev server)
- ✅ Connect to production API

---

### **2. Backend Development** (Optional)

Nếu cần test backend locally:

```powershell
cd C:\ai-advisor1

# Create .env.local
Copy-Item .env.example .env.local
notepad .env.local

# Add:
# OPENAI_API_KEY=your-key
# DATABASE_URL=sqlite:///local_signals.db

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Run backend
python backend_api.py

# Open: http://localhost:10000/health
```

**Database:**
- Uses **SQLite** (local file - no PostgreSQL needed)
- Auto-creates `local_signals.db`
- Simple, no setup required

---

### **3. Testing**

#### **Frontend Tests**

```powershell
cd C:\ai-advisor1\frontend

# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Watch mode (auto re-run on changes)
npm run test:watch
```

#### **Backend Tests**

```powershell
cd C:\ai-advisor1

# Run all tests
pytest tests/ -v

# Run fast tests only
pytest tests/ -v -m "not slow"

# With coverage
pytest tests/ -v --cov=. --cov-report=html
```

---

## 🔄 DEVELOPMENT CYCLE

```
1. Make changes
   ↓
2. Test locally
   - Frontend: npm run dev (manual check)
   - Backend: pytest tests/
   ↓
3. Commit
   git add .
   git commit -m "feat: my feature"
   ↓
4. Push to staging
   git push origin staging
   ↓
5. GitHub Actions runs:
   - Automated tests (all)
   - Deploy if pass
   ↓
6. Check staging site:
   https://staging.ai-advisor.vn
   ↓
7. If OK → Deploy production
   git checkout main
   git merge staging
   git push origin main
```

**Time saved:**
- Old: 30-60 min per bug (manual deploy + test)
- New: 2-5 min (test local + auto-deploy)
- **10-20x faster!**

---

## 🧪 TESTING STRATEGY

### **Before Push (Local):**

```powershell
# Quick smoke tests
cd C:\ai-advisor1

# 1. Backend tests (2 min)
pytest tests/ -v -m "not slow"

# 2. Frontend dev check (1 min)
cd frontend
npm run dev
# Manual check: http://localhost:5173

# 3. Frontend build test (30 sec)
npm run build
# Verify: dist/ folder created
```

### **After Push (CI/CD):**

GitHub Actions automatically:
- ✅ Run ALL tests (backend + frontend)
- ✅ Check code quality
- ✅ Deploy if tests pass
- ✅ Health checks

**You just wait 5-10 min and check results!**

---

## 📊 WHAT ABOUT DATABASE?

### **For Development:**

**Option A: SQLite (Simple)**
```powershell
# In .env.local:
DATABASE_URL=sqlite:///local_signals.db

# Auto-creates file
# No setup needed
```

**Option B: Production Database (Easy)**
```powershell
# In .env.local:
DATABASE_URL=<your-production-database-url>

# Test against real data
# No local database needed
```

**Option C: Supabase Free (Best)**
```powershell
# Create free Supabase project
# Get connection string
# In .env.local:
DATABASE_URL=postgresql://...@aws-0-...supabase.co:5432/postgres
```

**Recommend: Option A (SQLite) for local dev**

---

## 🎯 CI/CD WITHOUT LOCAL DOCKER

GitHub Actions provides:
- ✅ Ubuntu containers (free)
- ✅ PostgreSQL service (for tests)
- ✅ All dependencies installed
- ✅ Same environment every time

**Your workflow:**
```powershell
# Local: Quick tests
pytest tests/ -v -m "not slow"  # 1-2 min

# Push: Full tests on GitHub
git push origin staging  # GitHub runs ALL tests

# Result: Same confidence, no Docker needed!
```

---

## 📁 PROJECT STRUCTURE

```
C:\ai-advisor1\
├── frontend/               # React app
│   ├── src/
│   ├── package.json
│   └── npm run dev        # ← Start here
│
├── backend_api.py          # Flask API
├── requirements.txt
├── python backend_api.py  # ← Or start here
│
├── tests/                  # Backend tests
│   ├── test_api.py
│   └── pytest tests/      # ← Run tests
│
├── .env.local             # Local config
├── .env.example           # Template
│
└── .github/workflows/     # CI/CD
    └── ci-cd.yml          # Auto-test & deploy
```

---

## 🔧 CONFIGURATION FILES

### **.env.local** (Create this)

```bash
# API Keys
OPENAI_API_KEY=sk-...

# Database (choose one)
DATABASE_URL=sqlite:///local_signals.db              # Simple
# DATABASE_URL=postgresql://...@supabase.co/postgres  # Cloud

# Flask
FLASK_ENV=development
FLASK_DEBUG=1

# CORS
ALLOWED_ORIGINS=http://localhost:5173
```

### **pytest.ini** (Already created)

```ini
[pytest]
testpaths = tests
addopts = -v --tb=short
```

---

## ✅ VERIFICATION

After setup:

```powershell
# 1. Frontend works
cd C:\ai-advisor1\frontend
npm run dev
# Visit: http://localhost:5173

# 2. Backend works (optional)
cd C:\ai-advisor1
python backend_api.py
# Visit: http://localhost:10000/health

# 3. Tests work
pytest tests/ -v
# Should see: X passed

# 4. CI/CD configured
git push origin staging
# Check: https://github.com/.../actions
```

---

## 🎉 YOU'RE READY!

**You now have:**
- ✅ Fast local development (no Docker)
- ✅ Automated testing (GitHub Actions)
- ✅ Auto-deploy (CI/CD)
- ✅ Simple workflow

**Time saved: 80-90%**

**Cost: $0** (all free tiers)

---

## 🆘 TROUBLESHOOTING

### **Port already in use**

```powershell
# Frontend (5173)
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Backend (10000)
netstat -ano | findstr :10000
taskkill /PID <PID> /F
```

### **Module not found**

```powershell
# Backend
pip install -r requirements.txt --break-system-packages

# Frontend
cd frontend && npm ci
```

### **Database errors**

```powershell
# Check .env.local exists
Test-Path .env.local

# Check DATABASE_URL set
Get-Content .env.local | Select-String DATABASE_URL

# For SQLite: Just delete file and restart
Remove-Item local_signals.db -Force
python backend_api.py
```

---

## 📞 NEXT STEPS

1. ✅ Read this guide (done!)
2. ✅ Setup .env.local
3. ✅ Test frontend: `npm run dev`
4. ✅ Test backend: `pytest tests/`
5. ✅ Push to staging: `git push origin staging`
6. ✅ Watch GitHub Actions
7. ✅ Celebrate! 🎊

---

**Last Updated:** 2026-02-01  
**Version:** 2.0 (No Docker Required)
