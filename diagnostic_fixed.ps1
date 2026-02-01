# DIAGNOSTIC - DAILY SCANNER ISSUE
# Fixed version without syntax errors

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DAILY SCANNER DIAGNOSTIC" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

cd C:\ai-advisor1

# CHECK 1: Git files
Write-Host "CHECK 1: Files in Git repo" -ForegroundColor Yellow
Write-Host ""
git ls-files .github/workflows/

Write-Host ""

# CHECK 2: daily-scanner.yml status
Write-Host "CHECK 2: daily-scanner.yml status" -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".github\workflows\daily-scanner.yml") {
    Write-Host "  File EXISTS locally" -ForegroundColor Green
    
    $inGit = git ls-files .github/workflows/daily-scanner.yml
    if ($inGit) {
        Write-Host "  File TRACKED by Git" -ForegroundColor Green
    } else {
        Write-Host "  File NOT tracked by Git" -ForegroundColor Red
    }
} else {
    Write-Host "  File NOT found locally" -ForegroundColor Red
}

Write-Host ""

# CHECK 3: Backend status
Write-Host "CHECK 3: Backend status" -ForegroundColor Yellow
Write-Host ""

try {
    $status = Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan/status" -UseBasicParsing
    $json = $status.Content | ConvertFrom-Json
    
    Write-Host "  Last scan: $($json.last_scan)" -ForegroundColor White
    Write-Host "  Signals count: $($json.signals_count)" -ForegroundColor White
    Write-Host "  Total signals: $($json.total_signals)" -ForegroundColor White
    
} catch {
    Write-Host "  ERROR: Cannot connect to backend" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DIAGNOSTIC COMPLETE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. If file NOT in Git: Add and commit" -ForegroundColor White
Write-Host "2. If Git push rejected: Pull first then push" -ForegroundColor White
Write-Host "3. Visit GitHub Actions to verify workflow" -ForegroundColor White
Write-Host ""
