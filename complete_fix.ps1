# COMPLETE FIX - GIT PUSH + WORKFLOW SETUP
# Fixes git issue and pushes daily-scanner.yml

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "FIXING GIT PUSH + SETTING UP DAILY SCANNER" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

cd C:\ai-advisor1

# STEP 1: Check git status
Write-Host "STEP 1: Checking Git status..." -ForegroundColor Yellow
Write-Host ""

git status --short

Write-Host ""

# STEP 2: Pull remote changes
Write-Host "STEP 2: Pulling remote changes..." -ForegroundColor Yellow
Write-Host ""

try {
    git pull origin main
    Write-Host "  Successfully pulled" -ForegroundColor Green
} catch {
    Write-Host "  Pull had issues, continuing..." -ForegroundColor Yellow
}

Write-Host ""

# STEP 3: Check if daily-scanner.yml exists
Write-Host "STEP 3: Checking daily-scanner.yml..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".github\workflows\daily-scanner.yml") {
    Write-Host "  File EXISTS" -ForegroundColor Green
} else {
    Write-Host "  File NOT found!" -ForegroundColor Red
    Write-Host "  Please download daily-scanner.yml from chat" -ForegroundColor Yellow
    Write-Host "  And place in .github\workflows\ directory" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Exiting..." -ForegroundColor Red
    exit 1
}

Write-Host ""

# STEP 4: Add file to Git
Write-Host "STEP 4: Adding to Git..." -ForegroundColor Yellow
Write-Host ""

git add .github/workflows/daily-scanner.yml

$status = git status --short
Write-Host "Git status: $status" -ForegroundColor White

Write-Host ""

# STEP 5: Commit
Write-Host "STEP 5: Committing..." -ForegroundColor Yellow
Write-Host ""

git commit -m "feat: Add daily signal scanner workflow

- Auto-scan 343 stocks daily at 15:30 Vietnam time
- Schedule: cron 30 8 * * * (08:30 UTC)
- Manual trigger enabled via workflow_dispatch
- Monitors progress for 30 minutes
- Supports both production and staging environments"

Write-Host ""

# STEP 6: Push to GitHub
Write-Host "STEP 6: Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""

$pushed = $false
$attempt = 1

while (-not $pushed -and $attempt -le 3) {
    Write-Host "  Attempt $attempt..." -ForegroundColor White
    
    try {
        git push origin main
        $pushed = $true
        Write-Host "  Successfully pushed!" -ForegroundColor Green
    } catch {
        Write-Host "  Push failed, pulling and retrying..." -ForegroundColor Yellow
        git pull origin main --rebase
        $attempt++
    }
}

if (-not $pushed) {
    Write-Host ""
    Write-Host "  Push failed after 3 attempts" -ForegroundColor Red
    Write-Host "  You may need to resolve conflicts manually" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# STEP 7: Verify
Write-Host "STEP 7: Verification..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  Check if file in Git:" -ForegroundColor White
$inGit = git ls-files .github/workflows/daily-scanner.yml
if ($inGit) {
    Write-Host "    File tracked by Git" -ForegroundColor Green
} else {
    Write-Host "    File NOT tracked" -ForegroundColor Red
}

Write-Host ""
Write-Host "  Last 3 commits:" -ForegroundColor White
git log --oneline -3

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Visit GitHub Actions (wait 2 minutes):" -ForegroundColor White
Write-Host "   https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Look for workflow:" -ForegroundColor White
Write-Host "   'Daily Signal Scanner' in left sidebar" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Test manual trigger:" -ForegroundColor White
Write-Host "   - Click workflow name" -ForegroundColor Gray
Write-Host "   - Click 'Run workflow' button" -ForegroundColor Gray
Write-Host "   - Select 'production'" -ForegroundColor Gray
Write-Host "   - Click 'Run workflow'" -ForegroundColor Gray
Write-Host "   - Watch logs for 30 minutes" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Verify results after 30 min:" -ForegroundColor White

Write-Host ""
Write-Host "Run this command:" -ForegroundColor Yellow
Write-Host 'Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan/status"' -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected: 136 signals, today's date" -ForegroundColor Green
Write-Host ""

Write-Host "DONE! Daily auto-scan will run at 15:30 Vietnam time!" -ForegroundColor Green
Write-Host ""
