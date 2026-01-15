# DEPLOY PORTFOLIO V2 - AUTOMATED SCRIPT
# Run this in PowerShell from C:\ai-advisor1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY PORTFOLIO V2 WITH CASH + P&L  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check current directory
$currentDir = Get-Location
if ($currentDir.Path -notlike "*ai-advisor1*") {
    Write-Host "ERROR: Please run this script from C:\ai-advisor1" -ForegroundColor Red
    Write-Host "Current directory: $currentDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/5] Checking for AIPortfolioManager_v2.jsx..." -ForegroundColor Yellow

# Check if v2 file exists
if (-not (Test-Path "AIPortfolioManager_v2.jsx")) {
    Write-Host "ERROR: AIPortfolioManager_v2.jsx not found!" -ForegroundColor Red
    Write-Host "" 
    Write-Host "Please download the file first:" -ForegroundColor Yellow
    Write-Host "1. Click the download link above" -ForegroundColor White
    Write-Host "2. Save to: C:\ai-advisor1\AIPortfolioManager_v2.jsx" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "  Found! Size: $((Get-Item AIPortfolioManager_v2.jsx).Length) bytes" -ForegroundColor Green

Write-Host "[2/5] Backing up current file..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "frontend\src\components\AIPortfolioManager.jsx" "frontend\src\components\AIPortfolioManager_BACKUP_$timestamp.jsx" -ErrorAction SilentlyContinue
Write-Host "  Backup created: AIPortfolioManager_BACKUP_$timestamp.jsx" -ForegroundColor Green

Write-Host "[3/5] Replacing with new version..." -ForegroundColor Yellow
Copy-Item "AIPortfolioManager_v2.jsx" "frontend\src\components\AIPortfolioManager.jsx" -Force
Write-Host "  File replaced!" -ForegroundColor Green

Write-Host "[4/5] Verifying new file..." -ForegroundColor Yellow
$content = Get-Content "frontend\src\components\AIPortfolioManager.jsx" -Raw
if ($content -match "Tiền mặt" -and $content -match "cash_amount") {
    Write-Host "  Verification PASSED! Cash feature detected." -ForegroundColor Green
} else {
    Write-Host "  WARNING: File may not contain Cash feature!" -ForegroundColor Yellow
}

Write-Host "[5/5] Git operations..." -ForegroundColor Yellow

# Git status
Write-Host "  Checking git status..." -ForegroundColor Gray
git status --short

# Add file
Write-Host "  Adding file to git..." -ForegroundColor Gray
git add frontend/src/components/AIPortfolioManager.jsx

# Commit
Write-Host "  Creating commit..." -ForegroundColor Gray
git commit -m "Update: Add Cash position and P&L display (automated)"

# Push
Write-Host "  Pushing to GitHub..." -ForegroundColor Gray
git push origin main

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT INITIATED!                " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 10 minutes for Cloudflare to deploy" -ForegroundColor White
Write-Host "2. Visit: https://ai-advisor.vn" -ForegroundColor White
Write-Host "3. Press: Ctrl+Shift+R (clear cache)" -ForegroundColor White
Write-Host "4. Tab: 'Quản trị đầu tư bằng AI'" -ForegroundColor White
Write-Host "5. Look for: '💵 Tiền mặt' section" -ForegroundColor White
Write-Host ""
Write-Host "If you see Cash section → SUCCESS! ✅" -ForegroundColor Green
Write-Host ""

# Cleanup
Write-Host "Cleanup old files? (Y/N)" -ForegroundColor Yellow
$cleanup = Read-Host
if ($cleanup -eq "Y" -or $cleanup -eq "y") {
    Remove-Item "AIPortfolioManager_v2.jsx" -ErrorAction SilentlyContinue
    Remove-Item "backend_api_v3_COMPLETE.py" -ErrorAction SilentlyContinue
    Remove-Item "QUICK_FIX_GUIDE.md" -ErrorAction SilentlyContinue
    Write-Host "Cleanup completed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Script completed! 🎉" -ForegroundColor Cyan
