# ========================================================================
# START LOCAL DEVELOPMENT (NO DOCKER)
# ========================================================================

Write-Host "🚀 AI Advisor - Local Development (Simplified)" -ForegroundColor Green
Write-Host ""

# Check if .env.local exists
if (-Not (Test-Path ".env.local")) {
    Write-Host "⚠️  .env.local not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Creating from template..." -ForegroundColor Cyan
    
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env.local
        Write-Host "✅ Created .env.local from .env.example" -ForegroundColor Green
        Write-Host ""
        Write-Host "📝 Please edit .env.local and add your:" -ForegroundColor Yellow
        Write-Host "   - OPENAI_API_KEY" -ForegroundColor White
        Write-Host ""
        Write-Host "Then run this script again." -ForegroundColor Yellow
        
        # Open in notepad
        $edit = Read-Host "Open .env.local now? (Y/n)"
        if ($edit -eq "" -or $edit -eq "Y" -or $edit -eq "y") {
            notepad .env.local
        }
        exit 0
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
        Write-Host "Please create .env.local manually" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "✅ Configuration loaded" -ForegroundColor Green
Write-Host ""

# Ask what to start
Write-Host "What do you want to start?" -ForegroundColor Cyan
Write-Host "  1. Frontend only (recommended)" -ForegroundColor White
Write-Host "  2. Backend only" -ForegroundColor White
Write-Host "  3. Both (requires 2 terminals)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Choose (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🎨 Starting Frontend..." -ForegroundColor Cyan
        Write-Host ""
        
        if (-Not (Test-Path "frontend")) {
            Write-Host "❌ frontend directory not found!" -ForegroundColor Red
            exit 1
        }
        
        Push-Location frontend
        
        # Check if node_modules exists
        if (-Not (Test-Path "node_modules")) {
            Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
            npm install
            Write-Host ""
        }
        
        Write-Host "✅ Starting dev server..." -ForegroundColor Green
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray
        Write-Host "Frontend running at: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray
        Write-Host ""
        
        npm run dev
        
        Pop-Location
    }
    
    "2" {
        Write-Host ""
        Write-Host "🔧 Starting Backend..." -ForegroundColor Cyan
        Write-Host ""
        
        # Check Python
        try {
            $pythonVersion = python --version 2>&1
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
        } catch {
            Write-Host "❌ Python not found!" -ForegroundColor Red
            exit 1
        }
        
        # Check requirements
        if (Test-Path "requirements.txt") {
            Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
            pip list | Select-String "flask|pytest" | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Installing requirements..." -ForegroundColor Yellow
                pip install -r requirements.txt --break-system-packages
            }
        }
        
        Write-Host ""
        Write-Host "✅ Starting API server..." -ForegroundColor Green
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray
        Write-Host "Backend running at: http://localhost:10000" -ForegroundColor Cyan
        Write-Host "Health check: http://localhost:10000/health" -ForegroundColor Gray
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray
        Write-Host ""
        
        python backend_api.py
    }
    
    "3" {
        Write-Host ""
        Write-Host "⚠️  Starting both requires 2 terminals" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Terminal 1 (this one):" -ForegroundColor Cyan
        Write-Host "  .\start-local-simple.ps1" -ForegroundColor White
        Write-Host "  Choose option 2 (Backend)" -ForegroundColor White
        Write-Host ""
        Write-Host "Terminal 2 (open new):" -ForegroundColor Cyan
        Write-Host "  cd C:\ai-advisor1" -ForegroundColor White
        Write-Host "  .\start-local-simple.ps1" -ForegroundColor White
        Write-Host "  Choose option 1 (Frontend)" -ForegroundColor White
        Write-Host ""
        
        $continue = Read-Host "Start backend now? (Y/n)"
        if ($continue -eq "" -or $continue -eq "Y" -or $continue -eq "y") {
            Write-Host ""
            Write-Host "🔧 Starting Backend..." -ForegroundColor Cyan
            python backend_api.py
        }
    }
    
    default {
        Write-Host ""
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}
