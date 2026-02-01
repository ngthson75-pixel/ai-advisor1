# FIX FRONTEND API URL - POINT TO STAGING BACKEND
# Problem: Frontend points to production backend
# Solution: Change to staging backend URL

Write-Host "=== FIXING FRONTEND API URL ===" -ForegroundColor Cyan
Write-Host ""

cd C:\ai-advisor1\frontend\src\components

# Backup
Write-Host "1. Creating backups..." -ForegroundColor Yellow
Copy-Item AIPortfolioManager.jsx AIPortfolioManager.jsx.BACKUP -Force
if (Test-Path SignalsModule.jsx) {
    Copy-Item SignalsModule.jsx SignalsModule.jsx.BACKUP -Force
}
Write-Host "   ✅ Backups created" -ForegroundColor Green

# Show current URLs
Write-Host "`n2. Current API URLs:" -ForegroundColor Yellow
Get-Content AIPortfolioManager.jsx | Select-String "API_BASE" | Select-Object -First 3

# Fix AIPortfolioManager.jsx
Write-Host "`n3. Fixing AIPortfolioManager.jsx..." -ForegroundColor Yellow

# Read file
$content = Get-Content AIPortfolioManager.jsx -Raw

# Replace production URL with staging URL
$content = $content -replace 'https://ai-advisor1-backend\.onrender\.com/api', 'https://ai-advisor1-staging.onrender.com/api'

# Save
$content | Set-Content AIPortfolioManager.jsx -NoNewline

Write-Host "   ✅ Fixed AIPortfolioManager.jsx" -ForegroundColor Green

# Fix SignalsModule.jsx if exists
if (Test-Path SignalsModule.jsx) {
    Write-Host "`n4. Fixing SignalsModule.jsx..." -ForegroundColor Yellow
    
    $content2 = Get-Content SignalsModule.jsx -Raw
    $content2 = $content2 -replace 'https://ai-advisor1-backend\.onrender\.com/api', 'https://ai-advisor1-staging.onrender.com/api'
    $content2 | Set-Content SignalsModule.jsx -NoNewline
    
    Write-Host "   ✅ Fixed SignalsModule.jsx" -ForegroundColor Green
}

# Verify changes
Write-Host "`n5. Verifying changes:" -ForegroundColor Yellow
Write-Host "   New API URLs:" -ForegroundColor White
Get-Content AIPortfolioManager.jsx | Select-String "https://ai-advisor1-staging" | Select-Object -First 3

# Git status
Write-Host "`n6. Git status:" -ForegroundColor Yellow
cd C:\ai-advisor1
git status --short

# Commit
Write-Host "`n7. Committing changes..." -ForegroundColor Yellow
git add frontend/src/components/AIPortfolioManager.jsx
if (Test-Path frontend/src/components/SignalsModule.jsx.BACKUP) {
    git add frontend/src/components/SignalsModule.jsx
}

git commit -m "Fix: Frontend API URL point to staging backend"

Write-Host "   ✅ Changes committed" -ForegroundColor Green

# Push
Write-Host "`n8. Pushing to staging..." -ForegroundColor Yellow
git push origin staging

Write-Host "   ✅ Pushed to staging" -ForegroundColor Green

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "✅ FRONTEND API URL FIXED!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`nChanges:" -ForegroundColor Cyan
Write-Host "  OLD: https://ai-advisor1-backend.onrender.com/api (production)" -ForegroundColor Red
Write-Host "  NEW: https://ai-advisor1-staging.onrender.com/api (staging)" -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Wait 5-10 min for Cloudflare Pages deploy" -ForegroundColor White
Write-Host "  2. Refresh frontend staging" -ForegroundColor White
Write-Host "  3. Should now connect to staging backend!" -ForegroundColor White
