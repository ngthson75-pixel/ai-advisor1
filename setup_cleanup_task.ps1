# ============================================================================
# AUTOMATED SIGNAL CLEANUP - WINDOWS TASK SCHEDULER SETUP
# ============================================================================
# Owner: Nguyễn Thanh Sơn
# Email: ngthson75@gmail.com
#
# This script creates a Windows Scheduled Task to run signal cleanup daily
# ============================================================================

# Configuration
$ScriptPath = "C:\ai-advisor1\signal_cleanup.py"
$PythonPath = "python"  # Adjust if Python is not in PATH
$LogPath = "C:\ai-advisor1\logs\cleanup.log"
$TaskName = "AI-Advisor-Cleanup"

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "✅ Created logs directory: $LogDir"
}

Write-Host "=" * 70
Write-Host "🤖 AI ADVISOR - AUTOMATED CLEANUP SETUP"
Write-Host "=" * 70

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "`n⚠️  Task '$TaskName' already exists!"
    $Response = Read-Host "Do you want to replace it? (y/n)"
    if ($Response -ne 'y') {
        Write-Host "❌ Cancelled"
        exit
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ Removed old task"
}

# Create task action (what to run)
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "$ScriptPath --aggressive" `
    -WorkingDirectory "C:\ai-advisor1"

# Create task trigger (when to run)
# Run daily at 2:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00"

# Create task settings
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -DontStopOnIdleEnd

# Create task principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Daily cleanup of old AI Advisor trading signals" | Out-Null

Write-Host "`n✅ Scheduled task created successfully!"
Write-Host "`nTask details:"
Write-Host "  Name: $TaskName"
Write-Host "  Schedule: Daily at 2:00 AM"
Write-Host "  Command: $PythonPath $ScriptPath --aggressive"
Write-Host "  Log: $LogPath"

# Test the task
Write-Host "`n" + ("-" * 70)
Write-Host "🧪 Testing cleanup (dry run)..."
Write-Host ("-" * 70)

& $PythonPath $ScriptPath --dry-run

Write-Host "`n" + ("=" * 70)
Write-Host "✅ SETUP COMPLETE"
Write-Host ("=" * 70)
Write-Host "`nThe cleanup task will run automatically every day at 2:00 AM."
Write-Host "`nManual commands:"
Write-Host "  Test (dry run):  python signal_cleanup.py --dry-run"
Write-Host "  Run cleanup:     python signal_cleanup.py"
Write-Host "  Aggressive:      python signal_cleanup.py --aggressive"
Write-Host "  Stats only:      python signal_cleanup.py --stats-only"
Write-Host "`nTask management:"
Write-Host "  View task:       Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Run now:         Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Disable task:    Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Remove task:     Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ("=" * 70)
