# ============================================================================
# SCHEDULE PRODUCTION DEPLOYMENT - AI ADVISOR
# ============================================================================
# Usage: .\schedule-production-deploy.ps1 "release message" -Time "20:30"
# 
# Deploy production vào buổi tối với kiểm soát chặt chẽ:
# - Recommended: 20:00-22:00 (8PM-10PM)
# - Manual approval required
# - Full monitoring checklist
# - Easy rollback if needed
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ReleaseMessage,
    
    [Parameter(Mandatory=$false)]
    [string]$Time = "20:00",  # Default 8PM
    
    [Parameter(Mandatory=$false)]
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📅 SCHEDULE PRODUCTION DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STEP 1: Validate time
# ============================================================================

Write-Host "⏰ Step 1: Validate deployment time..." -ForegroundColor Yellow
Write-Host ""

try {
    $targetHour = [int]$Time.Split(':')[0]
    $targetMinute = [int]$Time.Split(':')[1]
    
    # Create target datetime
    $targetTime = Get-Date -Hour $targetHour -Minute $targetMinute -Second 0
    
    # If time has passed today, schedule for tomorrow
    if ((Get-Date) -gt $targetTime) {
        $targetTime = $targetTime.AddDays(1)
    }
    
    Write-Host "Scheduled time: $($targetTime.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Invalid time format!" -ForegroundColor Red
    Write-Host "Use format: HH:mm (e.g., '20:30' for 8:30 PM)" -ForegroundColor Yellow
    exit 1
}

# Check if evening hours (recommended)
$recommendedStart = 20
$recommendedEnd = 22

if ($targetHour -lt $recommendedStart -or $targetHour -gt $recommendedEnd) {
    Write-Host "⚠️  WARNING: Deployment outside recommended hours!" -ForegroundColor Yellow
    Write-Host "   Recommended: 20:00-22:00 (8PM-10PM)" -ForegroundColor White
    Write-Host "   Scheduled: $Time" -ForegroundColor White
    Write-Host ""
    
    $proceed = Read-Host "Continue with this time? (yes/no)"
    if ($proceed -ne "yes") {
        Write-Host "❌ Cancelled" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "✅ Time validated" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 2: Pre-deployment checklist
# ============================================================================

Write-Host "📋 Step 2: Pre-deployment checklist..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Before scheduling, confirm:" -ForegroundColor Cyan
Write-Host ""

$checklist = @(
    "Tested thoroughly on staging",
    "Internal testing complete",
    "No critical bugs found",
    "Database migration ready (if needed)",
    "Rollback plan prepared",
    "Can monitor deployment (available during/after deploy)",
    "Team notified about deployment"
)

$allConfirmed = $true

foreach ($item in $checklist) {
    $response = Read-Host "  ✓ $item ? (y/n)"
    if ($response -ne "y") {
        Write-Host "    ❌ Not confirmed: $item" -ForegroundColor Red
        $allConfirmed = $false
    }
}

Write-Host ""

if (-not $allConfirmed) {
    Write-Host "❌ Pre-deployment checklist incomplete!" -ForegroundColor Red
    Write-Host "   Please complete all items before scheduling" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Pre-deployment checklist complete" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 3: Confirm schedule
# ============================================================================

Write-Host "📅 Step 3: Confirm schedule..." -ForegroundColor Yellow
Write-Host ""

$waitTime = ($targetTime - (Get-Date))
$waitMinutes = [math]::Round($waitTime.TotalMinutes)

Write-Host "Deployment scheduled for:" -ForegroundColor Cyan
Write-Host "  Time: $($targetTime.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor White
Write-Host "  Waiting: $waitMinutes minutes" -ForegroundColor White
Write-Host ""
Write-Host "Release: $ReleaseMessage" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "Confirm schedule? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "❌ Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# ============================================================================
# STEP 4: Wait until scheduled time
# ============================================================================

Write-Host "⏳ Step 4: Waiting for scheduled time..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Scheduled: $($targetTime.ToString('HH:mm'))" -ForegroundColor Cyan
Write-Host "Current:   $(Get-Date -Format 'HH:mm')" -ForegroundColor White
Write-Host ""
Write-Host "💡 You can cancel anytime with Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Countdown loop
while ((Get-Date) -lt $targetTime) {
    $remaining = ($targetTime - (Get-Date))
    $hours = [math]::Floor($remaining.TotalHours)
    $minutes = $remaining.Minutes
    $seconds = $remaining.Seconds
    
    Write-Host -NoNewline "`r⏰ Time remaining: $hours h $minutes m $seconds s     "
    
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host ""
Write-Host "✅ Scheduled time reached!" -ForegroundColor Green
Write-Host ""

# Play alert sound (Windows)
[console]::beep(800, 300)
[console]::beep(800, 300)
[console]::beep(800, 300)

# ============================================================================
# STEP 5: Final confirmation before deploy
# ============================================================================

Write-Host "========================================" -ForegroundColor Red
Write-Host "⚠️  READY TO DEPLOY" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

Write-Host "Release: $ReleaseMessage" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'HH:mm')" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will deploy to PRODUCTION now!" -ForegroundColor Red
Write-Host ""

$finalConfirm = Read-Host "Type 'DEPLOY NOW' to proceed"
if ($finalConfirm -ne "DEPLOY NOW") {
    Write-Host "❌ Deployment cancelled at final confirmation" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# ============================================================================
# STEP 6: Execute deployment
# ============================================================================

Write-Host "🚀 Step 6: Executing deployment..." -ForegroundColor Yellow
Write-Host ""

# Call the main production deployment script
$deployParams = @{
    ReleaseMessage = $ReleaseMessage
}

if ($Version) {
    $deployParams.Version = $Version
}

Write-Host "Calling deploy-production.ps1..." -ForegroundColor White
Write-Host ""

# Execute the actual deployment
& .\deploy-production.ps1 @deployParams

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT INITIATED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "⚠️  IMPORTANT: Monitor deployment!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Monitor for 15-30 minutes" -ForegroundColor White
Write-Host "  2. Check error logs" -ForegroundColor White
Write-Host "  3. Test production site" -ForegroundColor White
Write-Host "  4. Watch user reports" -ForegroundColor White
Write-Host ""
Write-Host "If issues occur:" -ForegroundColor Yellow
Write-Host "  .\rollback-production.ps1" -ForegroundColor Red
Write-Host ""
