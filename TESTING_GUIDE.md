# 🧪 AI ADVISOR - LOCAL DEVELOPMENT & TESTING GUIDE

## 📋 TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Running Tests](#running-tests)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Troubleshooting](#troubleshooting)

---

## ✅ PREREQUISITES

### Required Software

- ✅ **Docker Desktop** (for local database)
  - Download: https://www.docker.com/products/docker-desktop
  - Version: 20.10+
  
- ✅ **Python 3.10+**
  - Download: https://www.python.org/downloads/
  
- ✅ **Node.js 18+**
  - Download: https://nodejs.org/
  
- ✅ **Git**
  - Download: https://git-scm.com/downloads

### Required Accounts

- ✅ **Gemini API Key** (for AI features)
  - Get: https://makersuite.google.com/app/apikey
  
- ✅ **GitHub Account** (for CI/CD)
  - Already have: https://github.com/ngthson75-pixel/ai-advisor1

---

## 🚀 LOCAL DEVELOPMENT SETUP

### Step 1: Clone Repository

```powershell
cd C:\
git clone https://github.com/ngthson75-pixel/ai-advisor1.git
cd ai-advisor1
```

### Step 2: Setup Environment Variables

```powershell
# Copy example env file
Copy-Item .env.local.example .env.local

# Edit .env.local and fill in your values
notepad .env.local
```

**Required variables:**
```bash
GEMINI_API_KEY=your-actual-gemini-api-key
DATABASE_URL=postgresql://aiadvisor:dev123456@localhost:5432/aiadvisor_dev
```

### Step 3: Start Local Services

```powershell
# Start Docker services (database + backend)
.\start-local.ps1
```

This will:
- ✅ Start PostgreSQL database (port 5432)
- ✅ Start Redis cache (port 6379)  
- ✅ Start Backend API (port 10000)
- ✅ Run database migrations
- ✅ Insert sample data

**Expected output:**
```
🚀 Starting AI Advisor Local Development...
✅ Docker is running
🏗️  Starting services...
✅ All services are healthy!

📍 Services:
  🔹 Backend API:    http://localhost:10000
  🔹 Database:       localhost:5432
  🔹 Redis Cache:    localhost:6379

🧪 Quick Tests:
  curl http://localhost:10000/health
  curl http://localhost:10000/api/signals
```

### Step 4: Start Frontend (Separate Terminal)

```powershell
# Open new terminal
cd C:\ai-advisor1\frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Expected output:**
```
  VITE v4.3.9  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 5: Test Local Setup

**Open browser:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:10000/health

**Test API endpoints:**
```powershell
# Health check
Invoke-WebRequest http://localhost:10000/health

# Get signals
Invoke-WebRequest http://localhost:10000/api/signals

# Get portfolio
Invoke-WebRequest "http://localhost:10000/api/portfolio?user_id=1"
```

---

## 🧪 RUNNING TESTS

### Backend Tests

#### Run All Tests

```powershell
# From project root
.\run-tests.ps1
```

#### Run Specific Test Types

```powershell
# Unit tests only
.\run-tests.ps1 -Type unit

# Integration tests only  
.\run-tests.ps1 -Type integration

# API tests only
.\run-tests.ps1 -Type api

# Fast tests (exclude slow)
.\run-tests.ps1 -Type fast
```

#### Run with Coverage

```powershell
# Generate coverage report
.\run-tests.ps1 -Coverage

# View HTML report
Start-Process htmlcov/index.html
```

#### Run Specific Test File

```powershell
python -m pytest tests/test_api.py -v
```

#### Run Specific Test Function

```powershell
python -m pytest tests/test_api.py::TestSignalsEndpoint::test_get_signals_success -v
```

### Frontend Tests

```powershell
cd frontend

# Run tests once
npm run test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# View coverage report
Start-Process coverage/index.html
```

### Manual Testing Checklist

Before deploying, manually test:

- [ ] Frontend loads at http://localhost:5173
- [ ] Login/signup works
- [ ] Signals tab displays data
- [ ] Portfolio tab works (add/delete stocks)
- [ ] AI chat responds
- [ ] No console errors (F12)
- [ ] Mobile responsive (resize browser)

---

## ⚙️ CI/CD PIPELINE

### GitHub Actions Workflows

Our CI/CD has **2 workflows**:

#### 1. **Pull Request Checks** (`.github/workflows/pr-checks.yml`)

**Trigger:** When PR is opened/updated

**What it does:**
- ✅ Run fast tests (unit + integration)
- ✅ Build check (ensure no compile errors)
- ✅ Comment on PR with results

**Duration:** ~3-5 minutes

**Use case:** Quick feedback on PRs before merge

---

#### 2. **Full CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)

**Trigger:** Push to `main` or `staging` branch

**Jobs:**

**Job 1: Backend Tests**
- Install Python dependencies
- Setup test database (PostgreSQL)
- Run pytest with coverage
- Upload coverage to Codecov

**Job 2: Frontend Tests**
- Install Node dependencies
- Run Vitest tests
- Build check
- Upload coverage

**Job 3: Code Quality**
- Black formatting check
- Flake8 linting
- ESLint (frontend)

**Job 4: Security Scan**
- Trivy vulnerability scanner
- Upload SARIF results

**Job 5: Deploy Staging** (auto on `staging` branch)
- Deploy backend to Render
- Deploy frontend to Cloudflare Pages
- Health checks
- Notify success/failure

**Job 6: Deploy Production** (manual approval on `main` branch)
- Requires environment approval
- Deploy to production
- Comprehensive health checks
- Create deployment summary

**Job 7: Post-Deployment Tests**
- Smoke tests on production
- Performance checks
- Final verification

**Total Duration:** ~10-15 minutes (full pipeline)

---

### Deployment Workflow

#### Deploy to Staging

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, test locally
# ...

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# Create PR to staging
# → PR checks run automatically

# Merge PR to staging
# → Full CI/CD runs
# → Auto-deploy to staging

# Test on staging: https://staging.ai-advisor.vn
```

#### Deploy to Production

```bash
# After testing on staging
git checkout main
git merge staging

# Push to main
git push origin main

# → Full CI/CD runs
# → Manual approval required (GitHub UI)
# → Deploy to production after approval

# Verify production: https://ai-advisor.vn
```

---

### GitHub Secrets Required

Setup these secrets in GitHub:
- Settings → Secrets and variables → Actions → New repository secret

**Required secrets:**

```
GEMINI_API_KEY=sk-...
RENDER_STAGING_HOOK=srv-xxx/deploy/xxx
RENDER_PRODUCTION_HOOK=srv-yyy/deploy/yyy
```

**How to get Render deploy hooks:**
1. Go to Render Dashboard
2. Select service (ai-advisor1-backend)
3. Settings → Deploy Hook
4. Copy webhook URL
5. Add to GitHub secrets

---

## 🐛 TROUBLESHOOTING

### Docker Issues

**Problem:** Docker not starting
```powershell
# Check Docker status
docker info

# If error: Start Docker Desktop manually
```

**Problem:** Port already in use
```powershell
# Find process using port 10000
netstat -ano | findstr :10000

# Kill process
taskkill /PID <pid> /F

# Or use different port in .env.local
```

### Database Issues

**Problem:** Database connection failed
```powershell
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d
```

**Problem:** Tables not created
```powershell
# Run migration manually
Invoke-WebRequest http://localhost:10000/api/migrate -Method POST

# Or exec into database
docker-compose exec postgres psql -U aiadvisor -d aiadvisor_dev

# Check tables
\dt
```

### Test Failures

**Problem:** Tests fail with "Module not found"
```powershell
# Reinstall dependencies
pip install -r requirements.txt --break-system-packages
cd frontend && npm ci
```

**Problem:** Tests pass locally but fail in CI
- Check Python/Node versions match
- Check environment variables are set in GitHub secrets
- Check test database credentials

### CI/CD Issues

**Problem:** GitHub Actions workflow not triggering
- Check workflow file syntax (YAML)
- Ensure pushed to correct branch
- Check GitHub Actions is enabled (Settings → Actions)

**Problem:** Deployment fails
- Check Render service is running
- Verify deploy webhook URL
- Check build logs in Render dashboard
- Verify environment variables in Render

---

## 📊 QUICK REFERENCE

### Common Commands

```powershell
# Local Development
.\start-local.ps1              # Start all services
docker-compose down            # Stop services
docker-compose logs -f backend # View logs

# Testing
.\run-tests.ps1                # Run all tests
.\run-tests.ps1 -Coverage      # With coverage
.\run-tests.ps1 -Type fast     # Fast tests only

# Frontend
cd frontend
npm run dev                    # Start dev server
npm run build                  # Build for production
npm run test                   # Run tests

# Database
docker-compose exec postgres psql -U aiadvisor -d aiadvisor_dev
\dt                            # List tables
\d signals                     # Describe table
SELECT COUNT(*) FROM signals;  # Query
```

### Useful URLs

**Local:**
- Frontend: http://localhost:5173
- Backend: http://localhost:10000
- Database: localhost:5432 (user: aiadvisor, password: dev123456)

**Staging:**
- Frontend: https://staging.ai-advisor.vn
- Backend: https://ai-advisor1-staging.onrender.com

**Production:**
- Frontend: https://ai-advisor.vn
- Backend: https://ai-advisor1-backend.onrender.com

**Dashboards:**
- GitHub Actions: https://github.com/ngthson75-pixel/ai-advisor1/actions
- Render: https://dashboard.render.com
- Cloudflare: https://dash.cloudflare.com

---

## 🎯 BEST PRACTICES

1. **Always test locally before pushing**
   ```powershell
   .\run-tests.ps1
   # Only push if tests pass
   ```

2. **Write tests for new features**
   - Backend: Add to `tests/test_api.py`
   - Frontend: Add to `frontend/src/components/__tests__/`

3. **Use staging before production**
   - Test on staging first
   - Get approval from team
   - Then deploy to production

4. **Monitor after deployment**
   - Check health endpoints
   - Watch error logs
   - Monitor user reports

5. **Keep dependencies updated**
   ```powershell
   pip list --outdated
   npm outdated
   ```

---

## ✅ SUCCESS METRICS

After setup, you should have:

- ✅ Local development running smoothly
- ✅ All tests passing
- ✅ CI/CD pipeline green
- ✅ Zero manual deploy steps
- ✅ Fast development cycle (no waiting for deploys)

**Time saved:**
- Before: 30-60 minutes per bug fix (deploy + test cycle)
- After: 2-5 minutes (test locally + auto-deploy)

**Result: 10-20x faster development! 🚀**

---

## 📞 SUPPORT

If you encounter issues:

1. Check this guide
2. Review error logs
3. Search GitHub Issues
4. Ask team for help

**Last Updated:** 2026-01-31
**Version:** 1.0
