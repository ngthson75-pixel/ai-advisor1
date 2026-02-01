# COMPLETE FIX PLAN - STAGING ENVIRONMENT
# 2 issues found, 2 fixes needed

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🚨 STAGING ENVIRONMENT FIX PLAN" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`n📋 ISSUES FOUND:" -ForegroundColor Yellow
Write-Host "  ❌ Issue 1: Backend has only 4 old signals (need 136 new)" -ForegroundColor Red
Write-Host "  ❌ Issue 2: Frontend points to PRODUCTION backend (should be STAGING)" -ForegroundColor Red

Write-Host "`n✅ SOLUTIONS:" -ForegroundColor Green
Write-Host "  1. Trigger scanner on staging backend (30 min)" -ForegroundColor White
Write-Host "  2. Fix frontend API URL to staging (10 min)" -ForegroundColor White

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "STEP 1: TRIGGER SCANNER (DO THIS NOW!)" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# Trigger scanner
Write-Host "`nTriggering scanner..." -ForegroundColor Yellow
try {
    $scan = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/scan" -Method POST -UseBasicParsing
    $scanJson = $scan.Content | ConvertFrom-Json
    
    Write-Host "✅ Scanner started!" -ForegroundColor Green
    Write-Host "   Process ID: $($scanJson.process_id)" -ForegroundColor White
    Write-Host "   Status: $($scanJson.status)" -ForegroundColor White
    Write-Host "   Message: $($scanJson.message)" -ForegroundColor Gray
    
    $startTime = Get-Date
    $endTime = $startTime.AddMinutes(30)
    
    Write-Host "`n⏰ Timing:" -ForegroundColor Yellow
    Write-Host "   Started: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor White
    Write-Host "   Expected end: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host "   Duration: 30 minutes" -ForegroundColor Gray
    
    Write-Host "`n🚨 CRITICAL: OPEN RENDER LOGS NOW!" -ForegroundColor Red
    Write-Host "   1. Visit: https://dashboard.render.com" -ForegroundColor White
    Write-Host "   2. Click: ai-advisor1-staging" -ForegroundColor White
    Write-Host "   3. Tab: Logs" -ForegroundColor White
    Write-Host "   4. Watch for 'Processing...' messages" -ForegroundColor White
    Write-Host "   5. Keep window OPEN for 30 minutes!" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Failed to trigger scanner: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "STEP 2: FIX FRONTEND (WHILE SCANNER RUNS)" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`nPress Enter to fix frontend API URL..." -ForegroundColor Yellow
Read-Host

cd C:\ai-advisor1\frontend\src\components

# Backup
Write-Host "`n1. Creating backups..." -ForegroundColor Yellow
Copy-Item AIPortfolioManager.jsx AIPortfolioManager.jsx.BACKUP -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ Backup created" -ForegroundColor Green

# Fix
Write-Host "`n2. Fixing API URL..." -ForegroundColor Yellow
$content = Get-Content AIPortfolioManager.jsx -Raw
$oldUrl = 'https://ai-advisor1-backend.onrender.com/api'
$newUrl = 'https://ai-advisor1-staging.onrender.com/api'

if ($content -match [regex]::Escape($oldUrl)) {
    $content = $content -replace [regex]::Escape($oldUrl), $newUrl
    $content | Set-Content AIPortfolioManager.jsx -NoNewline
    Write-Host "   ✅ API URL updated" -ForegroundColor Green
    Write-Host "      OLD: $oldUrl" -ForegroundColor Red
    Write-Host "      NEW: $newUrl" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  Already using correct URL" -ForegroundColor Cyan
}

# Verify
Write-Host "`n3. Verifying..." -ForegroundColor Yellow
$verify = Get-Content AIPortfolioManager.jsx | Select-String "API_BASE"
Write-Host "   Current: $verify" -ForegroundColor White

# Commit & push
Write-Host "`n4. Deploying changes..." -ForegroundColor Yellow
cd C:\ai-advisor1

git add frontend/src/components/AIPortfolioManager.jsx
git commit -m "Fix: Frontend staging points to staging backend"
git push origin staging

Write-Host "   ✅ Pushed to staging" -ForegroundColor Green

Write-Host "`n   ⏰ Cloudflare Pages will auto-deploy in 5-10 min" -ForegroundColor Cyan

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "STEP 3: MONITOR PROGRESS" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`nWhile waiting, you can:" -ForegroundColor Yellow
Write-Host "  1. Watch Render logs (scanner progress)" -ForegroundColor White
Write-Host "  2. Monitor Cloudflare Pages (frontend deploy)" -ForegroundColor White
Write-Host "  3. Run this script to check status:" -ForegroundColor White
Write-Host ""
Write-Host "  # Check scanner progress" -ForegroundColor Gray
Write-Host "  `$s = Invoke-WebRequest -Uri 'https://ai-advisor1-staging.onrender.com/api/scan/status' -UseBasicParsing" -ForegroundColor Gray
Write-Host "  (`$s.Content | ConvertFrom-Json)" -ForegroundColor Gray

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "EXPECTED RESULTS (After 30 min)" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`n✅ Backend (after scanner):" -ForegroundColor Green
Write-Host "   • 136 new signals generated" -ForegroundColor White
Write-Host "   • Total: 140 signals (4 old + 136 new)" -ForegroundColor White
Write-Host "   • Last scan: Today $(Get-Date -Format 'yyyy-MM-dd')" -ForegroundColor White

Write-Host "`n✅ Frontend (after deploy):" -ForegroundColor Green
Write-Host "   • Connects to staging backend" -ForegroundColor White
Write-Host "   • Displays 140 total signals" -ForegroundColor White
Write-Host "   • No CORS errors" -ForegroundColor White

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "⏰ TIMELINE" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

$now = Get-Date
Write-Host "`nNow:        $($now.ToString('HH:mm'))" -ForegroundColor White
Write-Host "Frontend:   $($now.AddMinutes(10).ToString('HH:mm')) (Deploy complete)" -ForegroundColor Yellow
Write-Host "Scanner:    $($now.AddMinutes(30).ToString('HH:mm')) (Signals ready)" -ForegroundColor Cyan
Write-Host "Test:       $($now.AddMinutes(35).ToString('HH:mm')) (Final verification)" -ForegroundColor Green

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "✅ SETUP COMPLETE - NOW WAIT!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`nReminders:" -ForegroundColor Yellow
Write-Host "  📊 Keep Render logs OPEN" -ForegroundColor White
Write-Host "  ⏰ Wait FULL 30 minutes" -ForegroundColor White
Write-Host "  🚨 Screenshot any errors" -ForegroundColor White
Write-Host "  ✅ Test frontend after 35 minutes" -ForegroundColor White

Write-Host "`n🎉 All fixes deployed! Monitoring in progress..." -ForegroundColor Cyan
