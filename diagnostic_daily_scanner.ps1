# 🔍 COMPREHENSIVE DIAGNOSTIC - DAILY SCANNER ISSUE
# Why signals aren't auto-updating daily?

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🔍 AI ADVISOR - DAILY SCANNER DIAGNOSTIC" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

cd C:\ai-advisor1

# ==============================================================================
# ISSUE ANALYSIS
# ==============================================================================

Write-Host "📋 KNOWN ISSUES FROM PROJECT DOCS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "From LOCAL_DEV_CICD_SUMMARY.md:" -ForegroundColor White
Write-Host "  ❌ Daily auto-scan NOT configured" -ForegroundColor Red
Write-Host "  ❌ Signals not updating automatically" -ForegroundColor Red
Write-Host "  ❌ Manual trigger required: POST /api/scan" -ForegroundColor Red
Write-Host "  ⚠️  Production shows old signals (20-21/1/2026)" -ForegroundColor Yellow
Write-Host "  📁 File ready: daily-scanner.yml (pending activation)" -ForegroundColor Gray
Write-Host ""

# ==============================================================================
# CHECK 1: GITHUB WORKFLOWS DIRECTORY
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 1: GitHub Workflows Directory Structure" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

if (Test-Path ".github\workflows") {
    Write-Host "✅ .github\workflows directory EXISTS" -ForegroundColor Green
    Write-Host ""
    Write-Host "Files in .github\workflows:" -ForegroundColor Yellow
    Get-ChildItem ".github\workflows" -File | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  📄 $($_.Name) - $size KB - Modified: $($_.LastWriteTime)" -ForegroundColor White
    }
    Write-Host ""
} else {
    Write-Host "❌ .github\workflows directory NOT FOUND!" -ForegroundColor Red
    Write-Host "   Creating directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path ".github\workflows" -Force
    Write-Host ""
}

# ==============================================================================
# CHECK 2: DAILY SCANNER WORKFLOW FILE
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 2: Daily Scanner Workflow File" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

$scannerFile = ".github\workflows\daily-scanner.yml"

if (Test-Path $scannerFile) {
    Write-Host "✅ daily-scanner.yml EXISTS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "File details:" -ForegroundColor Yellow
    $file = Get-Item $scannerFile
    Write-Host "  Size: $([math]::Round($file.Length / 1KB, 2)) KB" -ForegroundColor White
    Write-Host "  Modified: $($file.LastWriteTime)" -ForegroundColor White
    Write-Host ""
    Write-Host "File content (first 50 lines):" -ForegroundColor Yellow
    Get-Content $scannerFile -TotalCount 50 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
} else {
    Write-Host "❌ daily-scanner.yml NOT FOUND!" -ForegroundColor Red
    Write-Host ""
    Write-Host "This file SHOULD exist according to project docs!" -ForegroundColor Yellow
    Write-Host "File path: $scannerFile" -ForegroundColor Gray
    Write-Host ""
}

# ==============================================================================
# CHECK 3: GITHUB ACTIONS STATUS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 3: GitHub Actions Status Check" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "GitHub Actions Status:" -ForegroundColor Yellow
Write-Host "  Repository: https://github.com/ngthson75-pixel/ai-advisor1" -ForegroundColor White
Write-Host "  Actions URL: https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  MANUAL CHECK REQUIRED:" -ForegroundColor Yellow
Write-Host "  1. Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor White
Write-Host "  2. Look for workflow: 'Daily Signal Scanner'" -ForegroundColor White
Write-Host "  3. Check if it's:" -ForegroundColor White
Write-Host "     a) Listed but disabled" -ForegroundColor Gray
Write-Host "     b) Listed and enabled but never run" -ForegroundColor Gray
Write-Host "     c) Not listed at all" -ForegroundColor Gray
Write-Host ""

# ==============================================================================
# CHECK 4: SCANNER SCRIPT EXISTS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 4: Scanner Script Availability" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

$scannerScript = "scripts\daily_signal_scanner_eod.py"

if (Test-Path $scannerScript) {
    Write-Host "✅ Scanner script EXISTS: $scannerScript" -ForegroundColor Green
    $scriptFile = Get-Item $scannerScript
    Write-Host "  Size: $([math]::Round($scriptFile.Length / 1KB, 2)) KB" -ForegroundColor White
    Write-Host "  Modified: $($scriptFile.LastWriteTime)" -ForegroundColor White
} else {
    Write-Host "❌ Scanner script NOT FOUND: $scannerScript" -ForegroundColor Red
}
Write-Host ""

# ==============================================================================
# CHECK 5: BACKEND API SCAN ENDPOINT
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 5: Backend /api/scan Endpoint" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "Testing production backend..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "  ✅ Production backend: ONLINE" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Production backend: OFFLINE" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing staging backend..." -ForegroundColor Yellow
try {
    $healthStaging = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "  ✅ Staging backend: ONLINE" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Staging backend: OFFLINE" -ForegroundColor Red
}
Write-Host ""

# ==============================================================================
# CHECK 6: CURRENT SIGNALS STATUS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 6: Current Signals Status" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "Production Signals:" -ForegroundColor Yellow
try {
    $prodStatus = Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan/status" -UseBasicParsing
    $prodJson = $prodStatus.Content | ConvertFrom-Json
    Write-Host "  Last scan: $($prodJson.last_scan)" -ForegroundColor White
    Write-Host "  Signals today: $($prodJson.signals_count)" -ForegroundColor $(if($prodJson.signals_count -gt 0){"Green"}else{"Red"})
    Write-Host "  Total signals: $($prodJson.total_signals)" -ForegroundColor White
    Write-Host "  Status: $($prodJson.status)" -ForegroundColor $(if($prodJson.status -eq "complete"){"Green"}else{"Yellow"})
    
    $lastScanDate = [DateTime]::Parse($prodJson.last_scan)
    $daysSince = ([DateTime]::Now - $lastScanDate).Days
    Write-Host "  Days since last scan: $daysSince" -ForegroundColor $(if($daysSince -eq 0){"Green"}elseif($daysSince -le 3){"Yellow"}else{"Red"})
} catch {
    Write-Host "  ❌ Cannot get production signals status" -ForegroundColor Red
}
Write-Host ""

Write-Host "Staging Signals:" -ForegroundColor Yellow
try {
    $stageStatus = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/scan/status" -UseBasicParsing
    $stageJson = $stageStatus.Content | ConvertFrom-Json
    Write-Host "  Last scan: $($stageJson.last_scan)" -ForegroundColor White
    Write-Host "  Signals today: $($stageJson.signals_count)" -ForegroundColor $(if($stageJson.signals_count -gt 0){"Green"}else{"Red"})
    Write-Host "  Total signals: $($stageJson.total_signals)" -ForegroundColor White
} catch {
    Write-Host "  ❌ Cannot get staging signals status" -ForegroundColor Red
}
Write-Host ""

# ==============================================================================
# CHECK 7: GIT REPO STATUS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "CHECK 7: Git Repository Status" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "Current branch:" -ForegroundColor Yellow
git branch --show-current

Write-Host ""
Write-Host "Recent commits:" -ForegroundColor Yellow
git log --oneline -5

Write-Host ""
Write-Host "Remote branches:" -ForegroundColor Yellow
git branch -r

Write-Host ""

# ==============================================================================
# ROOT CAUSE ANALYSIS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🎯 ROOT CAUSE ANALYSIS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "POSSIBLE CAUSES FOR DAILY SCANNER NOT WORKING:" -ForegroundColor Yellow
Write-Host ""

$causes = @(
    @{
        num = "1"
        issue = "daily-scanner.yml file NOT in repository"
        check = "Check 2 result"
        fix = "Create and push daily-scanner.yml to .github/workflows/"
    },
    @{
        num = "2"
        issue = "daily-scanner.yml exists but NOT pushed to GitHub"
        check = "Check if file in local only or in remote"
        fix = "git add .github/workflows/daily-scanner.yml && git push"
    },
    @{
        num = "3"
        issue = "Workflow exists but DISABLED in GitHub Actions"
        check = "GitHub Actions UI - workflow list"
        fix = "Enable workflow in GitHub Actions settings"
    },
    @{
        num = "4"
        issue = "Workflow enabled but CRON schedule wrong"
        check = "daily-scanner.yml schedule: cron line"
        fix = "Correct cron syntax (e.g., '0 2 * * *' for 9AM Vietnam)"
    },
    @{
        num = "5"
        issue = "Workflow running but FAILING silently"
        check = "GitHub Actions logs for errors"
        fix = "Debug workflow errors from logs"
    },
    @{
        num = "6"
        issue = "GitHub Actions NOT enabled for repository"
        check = "Repo Settings > Actions > General"
        fix = "Enable GitHub Actions in repository settings"
    }
)

foreach ($cause in $causes) {
    Write-Host "Cause $($cause.num): $($cause.issue)" -ForegroundColor Red
    Write-Host "  Check: $($cause.check)" -ForegroundColor Yellow
    Write-Host "  Fix: $($cause.fix)" -ForegroundColor Green
    Write-Host ""
}

# ==============================================================================
# RECOMMENDED ACTIONS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ RECOMMENDED ACTIONS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "ACTION 1: Check if daily-scanner.yml is in Git" -ForegroundColor Yellow
Write-Host "  Run: git ls-files .github/workflows/" -ForegroundColor White
Write-Host ""

Write-Host "ACTION 2: Check GitHub Actions enabled" -ForegroundColor Yellow
Write-Host "  Visit: https://github.com/ngthson75-pixel/ai-advisor1/settings/actions" -ForegroundColor White
Write-Host "  Ensure: 'Allow all actions and reusable workflows' is selected" -ForegroundColor Gray
Write-Host ""

Write-Host "ACTION 3: Check workflow runs" -ForegroundColor Yellow
Write-Host "  Visit: https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor White
Write-Host "  Look for: 'Daily Signal Scanner' workflow" -ForegroundColor Gray
Write-Host "  Check: Last run time and status" -ForegroundColor Gray
Write-Host ""

Write-Host "ACTION 4: Manual trigger test" -ForegroundColor Yellow
Write-Host "  If workflow has 'workflow_dispatch', trigger manually" -ForegroundColor White
Write-Host "  GitHub Actions > Daily Signal Scanner > Run workflow" -ForegroundColor Gray
Write-Host ""

Write-Host "ACTION 5: Create/Fix workflow if missing" -ForegroundColor Yellow
Write-Host "  I can create the correct daily-scanner.yml file" -ForegroundColor White
Write-Host "  With proper cron schedule: 15:30 Vietnam = 08:30 UTC" -ForegroundColor Gray
Write-Host ""

# ==============================================================================
# NEXT STEPS
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📋 NEXT STEPS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "STEP 1: Check if daily-scanner.yml is tracked by Git" -ForegroundColor Yellow
Write-Host "  Command:" -ForegroundColor White
Write-Host "  git ls-files .github/workflows/daily-scanner.yml" -ForegroundColor Gray
Write-Host ""

Write-Host "STEP 2: If file NOT in Git, check if it exists locally" -ForegroundColor Yellow
Write-Host "  Result from Check 2 above" -ForegroundColor White
Write-Host ""

Write-Host "STEP 3: Visit GitHub Actions page" -ForegroundColor Yellow
Write-Host "  https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor White
Write-Host "  Screenshot and send to me!" -ForegroundColor Green
Write-Host ""

Write-Host "STEP 4: Based on findings, I will:" -ForegroundColor Yellow
Write-Host "  a) Create proper daily-scanner.yml if missing" -ForegroundColor White
Write-Host "  b) Fix cron schedule if wrong" -ForegroundColor White
Write-Host "  c) Debug workflow errors if failing" -ForegroundColor White
Write-Host "  d) Enable GitHub Actions if disabled" -ForegroundColor White
Write-Host ""

# ==============================================================================
# SUMMARY
# ==============================================================================

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "Run these commands and send me results:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. git ls-files .github/workflows/" -ForegroundColor White
Write-Host "  2. Visit https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor White
Write-Host "  3. Screenshot GitHub Actions page" -ForegroundColor White
Write-Host ""

Write-Host "Then I will create/fix the daily scanner workflow!" -ForegroundColor Green
Write-Host ""

Write-Host "=" * 80 -ForegroundColor Cyan
