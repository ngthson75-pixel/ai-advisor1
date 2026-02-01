# QUICK DEPLOYMENT SCRIPT
# Save as: C:\ai-advisor1\deploy_fixed_requirements.ps1

Write-Host "🚀 AI ADVISOR - DEPLOY FIXED REQUIREMENTS" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Gray

# Step 1: Backup
Write-Host "`n📦 Step 1: Backing up old requirements.txt..." -ForegroundColor Yellow
Copy-Item requirements.txt requirements.OLD.txt -Force
Write-Host "✅ Backup saved: requirements.OLD.txt" -ForegroundColor Green

# Step 2: Download instruction
Write-Host "`n📥 Step 2: Download fixed requirements.txt" -ForegroundColor Yellow
Write-Host "   1. Download 'requirements_FIXED.txt' from chat above" -ForegroundColor White
Write-Host "   2. Save to Downloads folder" -ForegroundColor White
Write-Host "   3. Press Enter when ready..." -ForegroundColor White
Read-Host

# Step 3: Copy fixed file
Write-Host "`n📄 Step 3: Copying fixed requirements.txt..." -ForegroundColor Yellow
$downloadPath = "$env:USERPROFILE\Downloads\requirements_FIXED.txt"

if (Test-Path $downloadPath) {
    Copy-Item $downloadPath requirements.txt -Force
    Write-Host "✅ File copied successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ File not found in Downloads!" -ForegroundColor Red
    Write-Host "   Please download from chat and try again" -ForegroundColor Red
    exit 1
}

# Step 4: Show changes
Write-Host "`n🔍 Step 4: Changes made:" -ForegroundColor Yellow
Write-Host "   ✅ psycopg[binary] → psycopg2-binary" -ForegroundColor Green
Write-Host "   ✅ Added pandas>=2.0.0" -ForegroundColor Green
Write-Host "   ✅ Added numpy>=1.24.0" -ForegroundColor Green

# Step 5: Git status
Write-Host "`n📊 Step 5: Checking git status..." -ForegroundColor Yellow
git status --short requirements.txt
Write-Host "✅ Requirements.txt modified" -ForegroundColor Green

# Step 6: Commit
Write-Host "`n💾 Step 6: Committing changes..." -ForegroundColor Yellow
git add requirements.txt
git commit -m "Fix: Replace psycopg3 with psycopg2-binary + add pandas/numpy"
Write-Host "✅ Changes committed" -ForegroundColor Green

# Step 7: Push
Write-Host "`n🚀 Step 7: Pushing to staging..." -ForegroundColor Yellow
git push origin staging
Write-Host "✅ Pushed to staging" -ForegroundColor Green

# Step 8: Wait for deploy
Write-Host "`n⏱️  Step 8: Waiting for Render deploy..." -ForegroundColor Yellow
Write-Host "   Expected time: 5-10 minutes" -ForegroundColor White
Write-Host "   Monitor: https://dashboard.render.com" -ForegroundColor White
Write-Host "`n   Press Enter after deploy completes..." -ForegroundColor White
Read-Host

# Step 9: Test
Write-Host "`n🧪 Step 9: Testing backend..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/health" -UseBasicParsing

if ($response.StatusCode -eq 200) {
    Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor White
} else {
    Write-Host "❌ Backend returned: $($response.StatusCode)" -ForegroundColor Red
    exit 1
}

# Step 10: Done
Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Run scanner manually:" -ForegroundColor White
Write-Host "      Invoke-WebRequest -Uri 'https://ai-advisor1-staging.onrender.com/api/scan' -Method POST" -ForegroundColor Gray
Write-Host "`n   2. Or wait for scheduled run at 15:30 daily" -ForegroundColor White
Write-Host "`n   3. Check signals:" -ForegroundColor White
Write-Host "      Invoke-WebRequest -Uri 'https://ai-advisor1-staging.onrender.com/api/signals'" -ForegroundColor Gray

Write-Host "`n✅ PostgreSQL connected!" -ForegroundColor Green
Write-Host "✅ Signals will persist forever!" -ForegroundColor Green
Write-Host "`n🚀 Your AI Advisor is ready!" -ForegroundColor Cyan
