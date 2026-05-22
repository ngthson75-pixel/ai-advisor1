# MONITOR SELL SCANNER PROGRESS
# Check every 30s for up to 15 minutes

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "MONITORING SELL SCANNER PROGRESS" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$maxChecks = 30  # 30 checks * 30s = 15 minutes
$checkInterval = 30  # seconds

Write-Host "Will check every $checkInterval seconds for up to $($maxChecks * $checkInterval / 60) minutes...`n" -ForegroundColor Yellow

for ($i = 1; $i -le $maxChecks; $i++) {
    $elapsed = ($i - 1) * $checkInterval / 60
    Write-Host "[Check $i/$maxChecks - ${elapsed} min] Checking status..." -ForegroundColor Gray
    
    try {
        $status = Invoke-RestMethod -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status" -ErrorAction Stop
        
        $sellCount = $status.total_sell_signals
        $stopLoss = $status.breakdown.stop_loss
        $takeProfit = $status.breakdown.take_profit
        
        Write-Host "  Total SELL signals: $sellCount" -ForegroundColor White
        if ($sellCount -gt 0) {
            Write-Host "    🔴 Stop Loss: $stopLoss" -ForegroundColor Red
            Write-Host "    🟢 Take Profit: $takeProfit" -ForegroundColor Green
        }
        
        # If we have new signals, likely done
        if ($sellCount -gt 0) {
            Write-Host "`n✅ NEW SELL SIGNALS DETECTED!" -ForegroundColor Green
            Write-Host "Scanner completed successfully!`n" -ForegroundColor Green
            
            # Show breakdown by reason
            if ($status.by_reason) {
                Write-Host "Breakdown by reason:" -ForegroundColor Cyan
                $status.by_reason.PSObject.Properties | ForEach-Object {
                    Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor White
                }
            }
            
            break
        }
        
        # Check if stuck
        if ($i -ge 20 -and $sellCount -eq 0) {
            Write-Host "`n⚠️  WARNING: 10+ minutes elapsed, no signals yet" -ForegroundColor Yellow
            Write-Host "Scanner may be:" -ForegroundColor Yellow
            Write-Host "  - Still running (checking many tickers)" -ForegroundColor Yellow
            Write-Host "  - No BUY signals hit SL/TP today" -ForegroundColor Yellow
            Write-Host "  - Stuck (check Render logs)`n" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "  ❌ Error checking status: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Don't sleep on last check
    if ($i -lt $maxChecks) {
        Start-Sleep -Seconds $checkInterval
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "MONITORING COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Final status check
Write-Host "Final status:" -ForegroundColor Cyan
$finalStatus = Invoke-RestMethod -Uri "https://ai-advisor1-backend.onrender.com/api/scan-sell/status"
$finalStatus | ConvertTo-Json -Depth 3

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Check Render logs for details: https://dashboard.render.com/web/srv-d578436mcj7s738ak8vg/logs" -ForegroundColor White
Write-Host "  2. View SELL signals in frontend: https://ai-advisor.vn" -ForegroundColor White
Write-Host "  3. Manual trigger: Invoke-RestMethod -Uri 'https://ai-advisor1-backend.onrender.com/api/scan-sell' -Method POST -ContentType 'application/json' -Body '{\"days\": 7}'" -ForegroundColor Gray
