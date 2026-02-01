# 📦 INSTALLATION CHECKLIST

## ✅ FILES TO COPY TO YOUR PROJECT

Copy all files below from `/home/claude/` (or download folder) to your project `C:\ai-advisor1\`

---

## 📁 ROOT DIRECTORY FILES

Copy to `C:\ai-advisor1\`:

- [x] `docker-compose.yml` - Docker services configuration
- [x] `Dockerfile.dev` - Development Docker image
- [x] `.env.local.example` - Environment variables template
- [x] `init.sql` - Database initialization script
- [x] `pytest.ini` - Pytest configuration
- [x] `start-local.ps1` - Script to start local dev environment
- [x] `run-tests.ps1` - Script to run tests
- [x] `TESTING_GUIDE.md` - Complete testing documentation

---

## 🧪 TESTS DIRECTORY

Create directory: `C:\ai-advisor1\tests\`

Copy to `C:\ai-advisor1\tests\`:

- [x] `conftest.py` - Pytest fixtures and configuration
- [x] `test_api.py` - Backend API tests
- [x] `test_database.py` - Database integration tests

---

## 🎨 FRONTEND FILES

Copy to `C:\ai-advisor1\frontend\`:

- [x] `package.json` (from `frontend-package.json`) - Update dependencies
- [x] `vite.config.test.js` - Vitest configuration (merge with existing vite.config.js)

Create directory: `C:\ai-advisor1\frontend\src\`

Copy to `C:\ai-advisor1\frontend\src\`:

- [x] `setupTests.js` - Frontend test setup

Create directory: `C:\ai-advisor1\frontend\src\components\__tests__\`

Copy to `C:\ai-advisor1\frontend\src\components\__tests__\`:

- [x] `SignalsModule.test.jsx` - SignalsModule component tests
- [x] `AIPortfolioManager.test.jsx` - AIPortfolioManager tests

---

## ⚙️ GITHUB ACTIONS

Create directory: `C:\ai-advisor1\.github\workflows\`

Copy to `C:\ai-advisor1\.github\workflows\`:

- [x] `ci-cd.yml` - Main CI/CD pipeline
- [x] `pr-checks.yml` - Pull request checks

---

## 🚀 SETUP STEPS

### Step 1: Copy Files

```powershell
# Assuming files are downloaded to C:\Downloads\ai-advisor-setup\

cd C:\ai-advisor1

# Copy root files
Copy-Item C:\Downloads\ai-advisor-setup\*.yml .
Copy-Item C:\Downloads\ai-advisor-setup\*.ps1 .
Copy-Item C:\Downloads\ai-advisor-setup\*.sql .
Copy-Item C:\Downloads\ai-advisor-setup\*.ini .
Copy-Item C:\Downloads\ai-advisor-setup\Dockerfile.dev .
Copy-Item C:\Downloads\ai-advisor-setup\.env.local.example .

# Copy tests
mkdir tests -Force
Copy-Item C:\Downloads\ai-advisor-setup\tests\* .\tests\

# Copy frontend files
Copy-Item C:\Downloads\ai-advisor-setup\frontend-package.json .\frontend\package.json
Copy-Item C:\Downloads\ai-advisor-setup\frontend-tests\* .\frontend\src\ -Recurse

# Copy GitHub workflows
mkdir .github\workflows -Force
Copy-Item C:\Downloads\ai-advisor-setup\.github\workflows\* .\.github\workflows\
```

### Step 2: Setup Environment

```powershell
# Copy and edit environment file
Copy-Item .env.local.example .env.local
notepad .env.local
# Fill in your GEMINI_API_KEY
```

### Step 3: Install Dependencies

```powershell
# Backend: Install test dependencies
pip install pytest pytest-cov pytest-flask pytest-mock --break-system-packages

# Frontend: Update dependencies
cd frontend
npm install
cd ..
```

### Step 4: Setup GitHub Secrets

1. Go to: https://github.com/ngthson75-pixel/ai-advisor1/settings/secrets/actions
2. Click "New repository secret"
3. Add these secrets:

```
GEMINI_API_KEY=your-actual-key
RENDER_STAGING_HOOK=https://api.render.com/deploy/srv-xxx
RENDER_PRODUCTION_HOOK=https://api.render.com/deploy/srv-yyy
```

### Step 5: Test Local Setup

```powershell
# Start local environment
.\start-local.ps1

# In another terminal: Run tests
.\run-tests.ps1

# In another terminal: Start frontend
cd frontend
npm run dev
```

### Step 6: Commit and Push

```powershell
# Add all files
git add .

# Commit
git commit -m "feat: add local development and CI/CD pipeline"

# Push to staging first
git checkout -b staging
git push origin staging

# Watch GitHub Actions run
# → https://github.com/ngthson75-pixel/ai-advisor1/actions
```

---

## ✅ VERIFICATION CHECKLIST

After setup, verify:

**Local Development:**
- [ ] `docker-compose up` works
- [ ] Backend runs at http://localhost:10000
- [ ] Frontend runs at http://localhost:5173
- [ ] Health check passes: `curl http://localhost:10000/health`

**Testing:**
- [ ] `.\run-tests.ps1` passes
- [ ] Backend tests pass (pytest)
- [ ] Frontend tests pass (vitest)
- [ ] Coverage reports generate

**CI/CD:**
- [ ] GitHub Actions workflows exist
- [ ] Secrets are configured
- [ ] Push to staging triggers deployment
- [ ] All jobs pass (green checkmarks)

**Final Check:**
- [ ] Read TESTING_GUIDE.md completely
- [ ] Understand workflow
- [ ] Can run local dev without issues
- [ ] Tests pass both locally and in CI

---

## 🆘 TROUBLESHOOTING

### Docker Issues

**Can't start Docker:**
```powershell
# Make sure Docker Desktop is running
# Check: docker info
```

**Port conflicts:**
```powershell
# Change ports in docker-compose.yml if needed
# Default ports: 5432 (postgres), 10000 (backend), 6379 (redis)
```

### Test Issues

**Tests fail:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --break-system-packages
cd frontend && npm ci
```

**Import errors:**
```powershell
# Make sure you're in project root
cd C:\ai-advisor1
.\run-tests.ps1
```

### CI/CD Issues

**Workflows don't trigger:**
- Check .github/workflows/ files exist
- Ensure YAML syntax is correct
- Push to main or staging branch

**Deploy fails:**
- Check GitHub secrets are set
- Verify Render webhook URLs
- Check Render service is running

---

## 📞 NEXT STEPS

1. ✅ Complete this checklist
2. ✅ Read TESTING_GUIDE.md
3. ✅ Test locally
4. ✅ Push to staging
5. ✅ Verify CI/CD works
6. ✅ Start developing!

---

**Setup Date:** 2026-01-31
**Version:** 1.0
**Estimated Time:** 30-45 minutes
