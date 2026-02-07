# ============================================================
# FIX DAILY SCANNER WORKFLOWS
# ============================================================
# 
# This script:
# 1. Deletes duplicate daily-scan.yml
# 2. Updates daily-scanner.yml with 45-minute timeout
# 3. Commits and pushes changes
# 4. Provides verification steps
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "FIXING DAILY SCANNER WORKFLOWS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
cd C:\ai-advisor1

# Step 1: Check current workflows
Write-Host "📋 Current workflow files:" -ForegroundColor Yellow
Get-ChildItem .github\workflows\*.yml | Select-Object Name, Length | Format-Table -AutoSize
Write-Host ""

# Step 2: Delete duplicate
Write-Host "🗑️  Deleting duplicate: daily-scan.yml" -ForegroundColor Yellow
if (Test-Path .github\workflows\daily-scan.yml) {
    Remove-Item .github\workflows\daily-scan.yml
    Write-Host "   ✓ Deleted daily-scan.yml" -ForegroundColor Green
} else {
    Write-Host "   ℹ️ daily-scan.yml not found (already deleted?)" -ForegroundColor Gray
}
Write-Host ""

# Step 3: Backup current daily-scanner.yml
Write-Host "💾 Backing up current daily-scanner.yml" -ForegroundColor Yellow
if (Test-Path .github\workflows\daily-scanner.yml) {
    Copy-Item .github\workflows\daily-scanner.yml .github\workflows\daily-scanner.yml.backup
    Write-Host "   ✓ Backup created: daily-scanner.yml.backup" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ daily-scanner.yml not found!" -ForegroundColor Red
}
Write-Host ""

# Step 4: Download new workflow from outputs
Write-Host "📥 You need to:" -ForegroundColor Yellow
Write-Host "   1. Download: /mnt/user-data/outputs/daily-scanner-fixed.yml" -ForegroundColor White
Write-Host "   2. Save as: C:\ai-advisor1\.github\workflows\daily-scanner.yml" -ForegroundColor White
Write-Host "   3. (Replace existing file)" -ForegroundColor White
Write-Host ""

Write-Host "Press Enter after you've copied the file..." -ForegroundColor Cyan
Read-Host

# Step 5: Verify new file
Write-Host "🔍 Verifying new workflow file..." -ForegroundColor Yellow
if (Test-Path .github\workflows\daily-scanner.yml) {
    $content = Get-Content .github\workflows\daily-scanner.yml -Raw
    
    # Check for 45-minute timeout marker
    if ($content -match "for i in \{1\.\.90\}") {
        Write-Host "   ✓ New workflow detected (45-minute timeout)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ File exists but may not be updated" -ForegroundColor Yellow
        Write-Host "   Please verify you copied the new version" -ForegroundColor Yellow
    }
    
    $size = (Get-Item .github\workflows\daily-scanner.yml).Length
    Write-Host "   File size: $size bytes" -ForegroundColor Gray
} else {
    Write-Host "   ❌ daily-scanner.yml not found!" -ForegroundColor Red
    Write-Host "   Please copy the file and run this script again" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 6: Check final state
Write-Host "📋 Final workflow files:" -ForegroundColor Yellow
Get-ChildItem .github\workflows\*.yml | Select-Object Name, Length | Format-Table -AutoSize
Write-Host ""

Write-Host "Expected files:" -ForegroundColor Gray
Write-Host "  - ci-cd.yml (deploy workflow)" -ForegroundColor Gray
Write-Host "  - daily-scanner.yml (scanner with 45-min timeout)" -ForegroundColor Gray
Write-Host ""

# Step 7: Commit changes
Write-Host "📝 Committing changes..." -ForegroundColor Yellow
git add .github\workflows\

$status = git status --short .github\workflows\
if ($status) {
    Write-Host "   Changes to commit:" -ForegroundColor Gray
    Write-Host $status -ForegroundColor Gray
    Write-Host ""
    
    git commit -m "fix: Update daily-scanner timeout to 45min, remove duplicate workflow"
    Write-Host "   ✓ Changes committed" -ForegroundColor Green
} else {
    Write-Host "   ℹ️ No changes to commit" -ForegroundColor Gray
}
Write-Host ""

# Step 8: Push to GitHub
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "   This will NOT trigger deployment (workflow changes don't redeploy backend)" -ForegroundColor Gray
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Pushed successfully" -ForegroundColor Green
} else {
    Write-Host "   ❌ Push failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 9: Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ WORKFLOW FIX COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Changes made:" -ForegroundColor Yellow
Write-Host "  ✓ Deleted: daily-scan.yml (duplicate)" -ForegroundColor Green
Write-Host "  ✓ Updated: daily-scanner.yml (45-min timeout)" -ForegroundColor Green
Write-Host "  ✓ Committed and pushed to GitHub" -ForegroundColor Green
Write-Host ""
Write-Host "What's different:" -ForegroundColor Yellow
Write-Host "  • Timeout: 30 minutes → 45 minutes" -ForegroundColor White
Write-Host "  • Handles: 20-25 min scan + wake-up delays" -ForegroundColor White
Write-Host "  • Only 1 workflow (no duplicates)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Tomorrow at 9:00 AM: Workflow runs automatically" -ForegroundColor White
Write-Host "  2. Or test now: GitHub Actions → Daily Signal Scanner → Run workflow" -ForegroundColor White
Write-Host "  3. Should complete successfully (no timeout)" -ForegroundColor White
Write-Host ""
Write-Host "GitHub Actions: https://github.com/ngthson75-pixel/ai-advisor1/actions" -ForegroundColor Cyan
Write-Host ""
