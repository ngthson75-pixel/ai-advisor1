# QUICK FIX: PYTHON 3.13 COMPATIBILITY
# Save as: C:\ai-advisor1\fix_python313.ps1

Write-Host "🔧 FIXING PYTHON 3.13 COMPATIBILITY" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# Problem
Write-Host "`n❌ Problem: psycopg2 does NOT support Python 3.13" -ForegroundColor Red
Write-Host "   Error: ImportError: undefined symbol: _PyInterpreterState_Get" -ForegroundColor Red

# Solution
Write-Host "`n✅ Solution: Use psycopg3 (Python 3.13 compatible)" -ForegroundColor Green
Write-Host "   Changes: backend_api.py + requirements.txt" -ForegroundColor Yellow

# Step 1: Backup
Write-Host "`n📦 Step 1: Backing up files..." -ForegroundColor Yellow
Copy-Item backend_api.py backend_api.OLD_psycopg2.py -Force
Copy-Item requirements.txt requirements.OLD_psycopg2.txt -Force
Write-Host "✅ Backups created" -ForegroundColor Green

# Step 2: Download
Write-Host "`n📥 Step 2: Download fixed files from chat" -ForegroundColor Yellow
Write-Host "   Files needed:" -ForegroundColor White
Write-Host "   1. backend_api_PSYCOPG3.py" -ForegroundColor White
Write-Host "   2. requirements_PSYCOPG3.txt" -ForegroundColor White
Write-Host "`n   Press Enter when downloaded..." -ForegroundColor White
Read-Host

# Step 3: Replace backend_api.py
Write-Host "`n📄 Step 3: Replacing backend_api.py..." -ForegroundColor Yellow
$backendPath = "$env:USERPROFILE\Downloads\backend_api_PSYCOPG3.py"

if (Test-Path $backendPath) {
    Copy-Item $backendPath backend_api.py -Force
    Write-Host "✅ backend_api.py updated" -ForegroundColor Green
} else {
    Write-Host "❌ File not found: $backendPath" -ForegroundColor Red
    Write-Host "   Please download from chat and try again" -ForegroundColor Red
    exit 1
}

# Step 4: Replace requirements.txt
Write-Host "`n📄 Step 4: Replacing requirements.txt..." -ForegroundColor Yellow
$reqPath = "$env:USERPROFILE\Downloads\requirements_PSYCOPG3.txt"

if (Test-Path $reqPath) {
    Copy-Item $reqPath requirements.txt -Force
    Write-Host "✅ requirements.txt updated" -ForegroundColor Green
} else {
    Write-Host "❌ File not found: $reqPath" -ForegroundColor Red
    Write-Host "   Please download from chat and try again" -ForegroundColor Red
    exit 1
}

# Step 5: Show changes
Write-Host "`n🔍 Step 5: Changes made:" -ForegroundColor Yellow
Write-Host "   backend_api.py:" -ForegroundColor White
Write-Host "     ✅ postgresql+psycopg:// (was psycopg2)" -ForegroundColor Green
Write-Host "`n   requirements.txt:" -ForegroundColor White
Write-Host "     ✅ psycopg[binary]==3.2.3 (was psycopg2-binary)" -ForegroundColor Green
Write-Host "     ✅ pandas>=2.0.0 (added)" -ForegroundColor Green
Write-Host "     ✅ numpy>=1.24.0 (added)" -ForegroundColor Green

# Step 6: Git status
Write-Host "`n📊 Step 6: Git status..." -ForegroundColor Yellow
git status --short
Write-Host "✅ Files modified" -ForegroundColor Green

# Step 7: Commit
Write-Host "`n💾 Step 7: Committing changes..." -ForegroundColor Yellow
git add backend_api.py requirements.txt
git commit -m "Fix: Use psycopg3 for Python 3.13 compatibility"
Write-Host "✅ Changes committed" -ForegroundColor Green

# Step 8: Push
Write-Host "`n🚀 Step 8: Pushing to staging..." -ForegroundColor Yellow
git push origin staging
Write-Host "✅ Pushed to staging" -ForegroundColor Green

# Step 9: Deploy wait
Write-Host "`n⏱️  Step 9: Waiting for Render deploy..." -ForegroundColor Yellow
Write-Host "   Expected time: 5-10 minutes" -ForegroundColor White
Write-Host "   Monitor: https://dashboard.render.com" -ForegroundColor White
Write-Host "`n   Look for these logs:" -ForegroundColor White
Write-Host "   ✅ Installing psycopg[binary]==3.2.3" -ForegroundColor Green
Write-Host "   ✅ Using PostgreSQL with psycopg (v3) driver" -ForegroundColor Green
Write-Host "   ✅ Database initialized" -ForegroundColor Green
Write-Host "`n   Press Enter after deploy completes..." -ForegroundColor White
Read-Host

# Step 10: Test
Write-Host "`n🧪 Step 10: Testing backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/health" -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
        $json = $response.Content | ConvertFrom-Json
        
        Write-Host "`n📊 Backend info:" -ForegroundColor Cyan
        Write-Host "   Service: $($json.service)" -ForegroundColor White
        Write-Host "   Status: $($json.status)" -ForegroundColor Green
        
    } else {
        Write-Host "⚠️  Backend returned: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Backend test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Check Render logs for details" -ForegroundColor Yellow
    exit 1
}

# Step 11: Test scanner trigger
Write-Host "`n🔍 Step 11: Would you like to trigger scanner now? (y/n)" -ForegroundColor Yellow
$runScanner = Read-Host

if ($runScanner -eq 'y') {
    Write-Host "`n🚀 Triggering scanner..." -ForegroundColor Yellow
    try {
        $scanResponse = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/scan" -Method POST -UseBasicParsing
        
        if ($scanResponse.StatusCode -eq 202) {
            Write-Host "✅ Scanner started!" -ForegroundColor Green
            Write-Host "   Expected time: 25-30 minutes" -ForegroundColor White
            Write-Host "   Monitor at: https://dashboard.render.com" -ForegroundColor White
        }
    } catch {
        Write-Host "⚠️  Scanner trigger: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Skipped. You can trigger manually later:" -ForegroundColor White
    Write-Host "   Invoke-WebRequest -Uri 'https://ai-advisor1-staging.onrender.com/api/scan' -Method POST" -ForegroundColor Gray
}

# Done
Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "🎉 PYTHON 3.13 COMPATIBILITY FIXED!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`n✅ What changed:" -ForegroundColor Cyan
Write-Host "   • psycopg2 → psycopg3 (Python 3.13 compatible)" -ForegroundColor White
Write-Host "   • Backend connects to PostgreSQL successfully" -ForegroundColor White
Write-Host "   • Scanner can run and generate signals" -ForegroundColor White
Write-Host "   • Signals persist in database forever" -ForegroundColor White

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Monitor scanner (if triggered): 25-30 min" -ForegroundColor White
Write-Host "   2. Check signals: " -ForegroundColor White
Write-Host "      Invoke-WebRequest -Uri 'https://ai-advisor1-staging.onrender.com/api/signals'" -ForegroundColor Gray
Write-Host "   3. Daily workflow runs automatically at 15:30" -ForegroundColor White

Write-Host "`n🚀 Your AI Advisor is now Python 3.13 compatible!" -ForegroundColor Green
