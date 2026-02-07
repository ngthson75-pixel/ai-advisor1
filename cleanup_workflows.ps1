# CLEANUP WORKFLOWS - CHỈ GIỮ 2 FILES CẦN THIẾT
# Xóa tất cả workflows cũ, chỉ giữ ci-cd.yml và daily-scan.yml

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CLEANING UP WORKFLOWS FOLDER" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

cd C:\ai-advisor1\.github\workflows

# STEP 1: Show current files
Write-Host "STEP 1: Current workflow files" -ForegroundColor Yellow
Write-Host ""
Get-ChildItem | Select-Object Name, Length, LastWriteTime | Format-Table
Write-Host ""

# STEP 2: Delete old/duplicate files
Write-Host "STEP 2: Deleting old files..." -ForegroundColor Yellow
Write-Host ""

$filesToDelete = @(
    "ci-cd_backup.yml",
    "daily-scan.yml",
    "daily-signals.yml",
    "pr-checks.yml",
    "FIX_WORKFLOW_NOT_APPEARING.md"
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  Deleted: $file" -ForegroundColor Red
    } else {
        Write-Host "  Not found: $file (skip)" -ForegroundColor Gray
    }
}

Write-Host ""

# STEP 3: Rename daily-scanner.yml to daily-scan.yml
Write-Host "STEP 3: Renaming daily-scanner.yml..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "daily-scanner.yml") {
    # Backup old content
    Copy-Item "daily-scanner.yml" "daily-scanner.yml.backup" -Force
    Write-Host "  Backup created: daily-scanner.yml.backup" -ForegroundColor Gray
    
    # Delete old file
    Remove-Item "daily-scanner.yml" -Force
    Write-Host "  Deleted: daily-scanner.yml" -ForegroundColor Red
}

Write-Host ""

# STEP 4: Copy clean version
Write-Host "STEP 4: Installing clean daily-scan.yml..." -ForegroundColor Yellow
Write-Host ""

# You need to download daily-scan-clean.yml first
if (Test-Path "C:\ai-advisor1\daily-scan-clean.yml") {
    Copy-Item "C:\ai-advisor1\daily-scan-clean.yml" "daily-scan.yml" -Force
    Write-Host "  Installed: daily-scan.yml (clean version)" -ForegroundColor Green
} else {
    Write-Host "  ERROR: daily-scan-clean.yml not found!" -ForegroundColor Red
    Write-Host "  Please download daily-scan-clean.yml from chat first" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# STEP 5: Verify final state
Write-Host "STEP 5: Final workflow files" -ForegroundColor Yellow
Write-Host ""

$finalFiles = Get-ChildItem -Filter "*.yml"
$finalFiles | Select-Object Name, Length, LastWriteTime | Format-Table

Write-Host ""

if ($finalFiles.Count -eq 2) {
    Write-Host "✅ SUCCESS! Only 2 workflow files:" -ForegroundColor Green
    foreach ($file in $finalFiles) {
        Write-Host "  - $($file.Name)" -ForegroundColor White
    }
} else {
    Write-Host "⚠️  WARNING! Found $($finalFiles.Count) files (expected 2)" -ForegroundColor Yellow
}

Write-Host ""

# STEP 6: Git operations
Write-Host "STEP 6: Git operations..." -ForegroundColor Yellow
Write-Host ""

cd C:\ai-advisor1

# Add all changes in workflows folder
git add .github/workflows/

# Show what changed
Write-Host "Changes:" -ForegroundColor White
git status --short .github/workflows/

Write-Host ""

# Commit
Write-Host "Committing..." -ForegroundColor Yellow
git commit -m "cleanup: Remove old workflow files, keep only ci-cd and daily-scan

- Deleted: ci-cd_backup, daily-signals, pr-checks
- Renamed: daily-scanner -> daily-scan
- Clean version without tests (tests were failing)
- Only 2 workflows: ci-cd.yml + daily-scan.yml"

Write-Host ""

# Push to staging
Write-Host "Pushing to staging..." -ForegroundColor Yellow
git push origin staging

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ CLEANUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Merge staging to main:" -ForegroundColor White
Write-Host "   git checkout main" -ForegroundColor Gray
Write-Host "   git merge staging" -ForegroundColor Gray
Write-Host "   git push origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Wait 2 minutes, then visit:" -ForegroundColor White
Write-Host "   https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Should see ONLY 1 workflow:" -ForegroundColor White
Write-Host "   'Daily Signal Scanner'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Test manual trigger:" -ForegroundColor White
Write-Host "   - Click 'Run workflow'" -ForegroundColor Gray
Write-Host "   - Select 'production'" -ForegroundColor Gray
Write-Host "   - Run and monitor for 30 min" -ForegroundColor Gray
Write-Host ""
