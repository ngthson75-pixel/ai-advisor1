#!/usr/bin/env pwsh
# ============================================================================
# ENABLE DAILY SCANNER WORKFLOW - AUTOMATED SETUP
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🤖 DAILY SCANNER WORKFLOW SETUP" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check we're in correct directory
if (-not (Test-Path "backend_api.py")) {
    Write-Host "❌ Error: Not in ai-advisor1 directory!" -ForegroundColor Red
    Write-Host "Please run: cd C:\ai-advisor1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Confirmed in ai-advisor1 directory" -ForegroundColor Green
Write-Host ""

# Step 1: Create workflows directory
Write-Host "📁 Step 1: Creating .github/workflows directory..." -ForegroundColor Yellow

if (-not (Test-Path ".github")) {
    New-Item -ItemType Directory -Path ".github" | Out-Null
    Write-Host "  ✓ Created .github/" -ForegroundColor Green
}

if (-not (Test-Path ".github\workflows")) {
    New-Item -ItemType Directory -Path ".github\workflows" | Out-Null
    Write-Host "  ✓ Created .github/workflows/" -ForegroundColor Green
} else {
    Write-Host "  ✓ .github/workflows/ already exists" -ForegroundColor Green
}

Write-Host ""

# Step 2: Check if workflow file exists
Write-Host "📄 Step 2: Checking workflow file..." -ForegroundColor Yellow

$workflowFile = ".github\workflows\daily-scanner.yml"

if (Test-Path $workflowFile) {
    Write-Host "  ⚠️  Workflow file already exists" -ForegroundColor Yellow
    Write-Host "  📍 Location: $workflowFile" -ForegroundColor Cyan
    
    $replace = Read-Host "  Replace with new version? (y/n)"
    if ($replace -ne "y") {
        Write-Host "  ✓ Keeping existing file" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ⚠️  Please download daily-scanner.yml from outputs ⬆️" -ForegroundColor Yellow
        Write-Host "  📍 Save to: $PWD\$workflowFile" -ForegroundColor Cyan
        Write-Host ""
        Read-Host "  Press Enter after saving file..."
        
        if (Test-Path $workflowFile) {
            Write-Host "  ✓ Workflow file ready" -ForegroundColor Green
        } else {
            Write-Host "  ❌ File not found!" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "  ⚠️  Workflow file not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  📥 Please download daily-scanner.yml from outputs ⬆️" -ForegroundColor Yellow
    Write-Host "  📍 Save to: $PWD\$workflowFile" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "  Press Enter after saving file..."
    
    if (Test-Path $workflowFile) {
        Write-Host "  ✓ Workflow file ready" -ForegroundColor Green
    } else {
        Write-Host "  ❌ File not found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Step 3: Verify workflow content
Write-Host "🔍 Step 3: Verifying workflow content..." -ForegroundColor Yellow

$content = Get-Content $workflowFile -Raw

if ($content -match "name: Daily Signal Scanner") {
    Write-Host "  ✓ Workflow name: OK" -ForegroundColor Green
} else {
    Write-Host "  ❌ Invalid workflow file!" -ForegroundColor Red
    exit 1
}

if ($content -match "cron: '\d+ \d+ \* \* \*'") {
    Write-Host "  ✓ Schedule (cron): Found" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  No schedule found (manual trigger only)" -ForegroundColor Yellow
}

if ($content -match "workflow_dispatch") {
    Write-Host "  ✓ Manual trigger: Enabled" -ForegroundColor Green
}

Write-Host ""

# Step 4: Git status
Write-Host "📊 Step 4: Checking git status..." -ForegroundColor Yellow

git add $workflowFile

$status = git status --short $workflowFile

if ($status) {
    Write-Host "  ✓ File staged for commit" -ForegroundColor Green
    Write-Host "  📝 Status: $status" -ForegroundColor Cyan
} else {
    Write-Host "  ℹ️  No changes to commit" -ForegroundColor Cyan
}

Write-Host ""

# Step 5: Commit
Write-Host "💾 Step 5: Committing workflow..." -ForegroundColor Yellow

$hasChanges = git diff --cached --quiet $workflowFile
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat: Add daily signal scanner workflow" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Committed successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Commit failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ℹ️  No changes to commit (file unchanged)" -ForegroundColor Cyan
}

Write-Host ""

# Step 6: Push
Write-Host "🚀 Step 6: Pushing to GitHub..." -ForegroundColor Yellow

Write-Host "  📤 Pushing to origin main..." -ForegroundColor Cyan

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Pushed successfully!" -ForegroundColor Green
} else {
    Write-Host "  ❌ Push failed!" -ForegroundColor Red
    Write-Host "  💡 Run manually: git push origin main" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "✅ WORKFLOW SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 7: Next steps
Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Enable workflow on GitHub:" -ForegroundColor Cyan
Write-Host "   - Visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions" -ForegroundColor White
Write-Host "   - Click: 'Daily Signal Scanner'" -ForegroundColor White
Write-Host "   - Click: 'Enable workflow' (if disabled)" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  Test manual trigger:" -ForegroundColor Cyan
Write-Host "   - Same page: Actions tab" -ForegroundColor White
Write-Host "   - Click: 'Run workflow' button" -ForegroundColor White
Write-Host "   - Select: Branch 'main', Environment 'production'" -ForegroundColor White
Write-Host "   - Click: 'Run workflow'" -ForegroundColor White
Write-Host "   - Wait: ~5 minutes" -ForegroundColor White
Write-Host "   - Check: Green ✓ = Success!" -ForegroundColor White
Write-Host ""

Write-Host "3️⃣  Verify automatic scheduling:" -ForegroundColor Cyan
Write-Host "   - Schedule: 9:00 AM Vietnam daily" -ForegroundColor White
Write-Host "   - Next run: Tomorrow at 9:00 AM" -ForegroundColor White
Write-Host "   - Check: Actions tab for scheduled runs" -ForegroundColor White
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📖 Full documentation: SETUP_DAILY_SCANNER.md" -ForegroundColor Cyan
Write-Host ""

# Open GitHub Actions page
$openGitHub = Read-Host "🌐 Open GitHub Actions page now? (y/n)"
if ($openGitHub -eq "y") {
    # Try to get GitHub repo URL
    $remoteUrl = git remote get-url origin 2>$null
    if ($remoteUrl) {
        # Convert SSH to HTTPS if needed
        $httpsUrl = $remoteUrl -replace 'git@github.com:', 'https://github.com/'
        $httpsUrl = $httpsUrl -replace '\.git$', ''
        $actionsUrl = "$httpsUrl/actions"
        
        Write-Host "  Opening: $actionsUrl" -ForegroundColor Cyan
        Start-Process $actionsUrl
    } else {
        Write-Host "  ⚠️  Could not determine GitHub URL" -ForegroundColor Yellow
        Write-Host "  📍 Manually visit: https://github.com/YOUR_USERNAME/ai-advisor1/actions" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "🚀 All done! Daily scanner will run automatically at 9 AM!" -ForegroundColor Green
Write-Host ""
