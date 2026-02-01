# 🚀 LOCAL DEVELOPMENT (NO DOCKER)

## ⚡ QUICK START

### Backend (Python trực tiếp)

```powershell
cd C:\ai-advisor1

# 1. Install dependencies
pip install -r requirements.txt --break-system-packages

# 2. Setup environment
Copy-Item .env.example .env
notepad .env

# Điền:
# OPENAI_API_KEY=sk-... (your ChatGPT API key)
# DATABASE_URL=sqlite:///signals.db (local SQLite)

# 3. Run backend
python backend_api.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:10000
 * Debug mode: on
```

**Test:**
```powershell
# Mở browser: http://localhost:10000/health
# Hoặc:
curl http://localhost:10000/health
```

---

### Frontend (React)

**Terminal mới:**
```powershell
cd C:\ai-advisor1\frontend

# 1. Install dependencies (one time)
npm install

# 2. Run dev server
npm run dev
```

**Expected output:**
```
  VITE v4.3.9  ready in 241 ms
  ➜  Local:   http://localhost:5173/
```

**Test:**
- Mở browser: http://localhost:5173

---

## 🧪 TESTING

### Backend Tests (Không cần Docker)

```powershell
cd C:\ai-advisor1

# Run tests
python -m pytest tests/ -v

# Với coverage
python -m pytest tests/ -v --cov=. --cov-report=html
```

### Frontend Tests

```powershell
cd C:\ai-advisor1\frontend

# Run tests
npm run test

# Với coverage
npm run test:coverage
```

---

## 🗄️ DATABASE

### SQLite Local (Không cần PostgreSQL)

Backend tự động dùng SQLite file:

```
C:\ai-advisor1\signals.db
```

**Tạo tables:**
```powershell
# Backend tự động tạo khi start lần đầu
python backend_api.py

# Hoặc trigger migration:
curl -X POST http://localhost:10000/api/migrate
```

**View database:**
```powershell
# Download DB Browser for SQLite (free)
# https://sqlitebrowser.org/

# Mở file signals.db
```

---

## 🔧 TROUBLESHOOTING

### Backend không start

**Lỗi: Module not found**
```powershell
pip install -r requirements.txt --break-system-packages
```

**Lỗi: Port 10000 already in use**
```powershell
# Tìm process
netstat -ano | findstr :10000

# Kill process
taskkill /PID <pid> /F
```

### Frontend không start

**Lỗi: npm not found**
```powershell
# Install Node.js từ https://nodejs.org
```

**Lỗi: Port 5173 already in use**
```powershell
# Sửa port trong vite.config.js:
# server: { port: 5174 }
```

---

## 📊 SO SÁNH: DOCKER vs NO DOCKER

| Feature | With Docker | No Docker |
|---------|-------------|-----------|
| Setup time | 10 phút | 2 phút |
| RAM usage | 2-4GB | 500MB |
| Windows requirement | Win 10 Pro 22H2+ | Bất kỳ |
| Backend | PostgreSQL | SQLite |
| Speed | Chậm hơn | Nhanh hơn |
| Production-like | 95% | 85% |

**Kết luận:** No Docker **tốt hơn** cho development!

---

## ✅ ADVANTAGES NO DOCKER

1. ✅ **Nhanh hơn** - Không qua layer ảo hóa
2. ✅ **Đơn giản hơn** - Ít bước setup
3. ✅ **Ít RAM hơn** - Không overhead Docker
4. ✅ **Debug dễ hơn** - Breakpoint trực tiếp
5. ✅ **Không cần nâng cấp Windows**

---

## 🎯 RECOMMENDED WORKFLOW

### Development:

```powershell
# Terminal 1: Backend
cd C:\ai-advisor1
python backend_api.py

# Terminal 2: Frontend
cd C:\ai-advisor1\frontend
npm run dev

# Terminal 3: Tests
cd C:\ai-advisor1
python -m pytest tests/ -v --watch
```

### Before Deploy:

```powershell
# 1. Run all tests
python -m pytest tests/ -v
cd frontend && npm run test

# 2. Build frontend
npm run build

# 3. Commit & push
git add .
git commit -m "feat: new feature"
git push origin staging

# 4. CI/CD auto-test & deploy
```

---

## 💡 PRO TIPS

### Faster Testing:

```powershell
# Chỉ test fast tests
python -m pytest tests/ -v -m "not slow"
```

### Auto-reload Backend:

```powershell
# Install watchdog
pip install watchdog --break-system-packages

# Run với auto-reload (nếu backend support)
# Hoặc dùng nodemon-like tool cho Python
```

### Multiple Environments:

```env
# .env.local (development)
DATABASE_URL=sqlite:///signals.db
OPENAI_API_KEY=sk-dev-...

# .env.staging (staging)
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-staging-...
```

---

## 🚀 BOTTOM LINE

**Bạn KHÔNG CẦN Docker!**

Local development hoạt động hoàn hảo với:
- ✅ Python trực tiếp
- ✅ SQLite local
- ✅ Vite dev server

**CI/CD vẫn dùng Docker** (trên GitHub Actions) → Production vẫn đúng!

---

**Last Updated:** 2026-01-31  
**For:** Windows users without Docker Desktop
