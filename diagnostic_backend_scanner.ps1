# DIAGNOSTIC: CHECK BACKEND SCANNER
# Kiểm tra xem backend scanner có hoạt động không

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DIAGNOSTIC: BACKEND SCANNER STATUS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

# Configuration
$PRODUCTION_API = "https://ai-advisor1-backend.onrender.com/api"
$STAGING_API = "https://ai-advisor1-staging.onrender.com/api"

function Test-Backend {
    param(
        [string]$Name,
        [string]$Url
    )
    
    Write-Host "Testing $Name..." -ForegroundColor Yellow
    Write-Host "URL: $Url" -ForegroundColor Gray
    Write-Host ""
    
    # Test 1: Health check
    Write-Host "  1. Health check:" -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -TimeoutSec 10 -UseBasicParsing
        $status = $response.StatusCode
        Write-Host "     Status: $status" -ForegroundColor Green
    } catch {
        Write-Host "     Status: FAILED" -ForegroundColor Red
        Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
    
    # Test 2: Get signals
    Write-Host "  2. Current signals:" -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri "$Url/signals" -TimeoutSec 10 -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        
        $count = $data.count
        Write-Host "     Total: $count signals" -ForegroundColor Cyan
        
        if ($data.signals -and $data.signals.Count -gt 0) {
            $latestDate = $data.signals[0].date
            Write-Host "     Latest: $latestDate" -ForegroundColor Cyan
            
            Write-Host ""
            Write-Host "     Top 5 signals:" -ForegroundColor Gray
            for ($i = 0; $i -lt [Math]::Min(5, $data.signals.Count); $i++) {
                $sig = $data.signals[$i]
                Write-Host "       $($i+1). $($sig.ticker) - $($sig.strategy) - $($sig.strength)%" -ForegroundColor Gray
            }
        } else {
            Write-Host "     No signals found!" -ForegroundColor Red
        }
    } catch {
        Write-Host "     FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
    
    # Test 3: Scan status
    Write-Host "  3. Scanner status:" -ForegroundColor White
    try {
        $response = Invoke-WebRequest -Uri "$Url/scan/status" -TimeoutSec 10 -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "     Last scan: $($data.last_scan)" -ForegroundColor Cyan
        Write-Host "     Signals count: $($data.signals_count)" -ForegroundColor Cyan
        Write-Host "     Status: $($data.status)" -ForegroundColor Cyan
    } catch {
        Write-Host "     FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
    
    Write-Host "-" * 80 -ForegroundColor Gray
    Write-Host ""
}

# Test Production
Test-Backend -Name "PRODUCTION" -Url $PRODUCTION_API

# Test Staging
Test-Backend -Name "STAGING" -Url $STAGING_API

# Summary
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

Write-Host "If signals are old or count is 0:" -ForegroundColor Yellow
Write-Host "  1. Backend scanner is NOT working" -ForegroundColor White
Write-Host "  2. Need to push local signals manually" -ForegroundColor White
Write-Host ""

Write-Host "To push local signals:" -ForegroundColor Yellow
Write-Host "  cd C:\ai-advisor1" -ForegroundColor Gray
Write-Host "  python push_local_signals.py" -ForegroundColor Gray
Write-Host ""

Write-Host "To check backend logs:" -ForegroundColor Yellow
Write-Host "  Visit: https://dashboard.render.com" -ForegroundColor Gray
Write-Host "  Service: ai-advisor1-backend" -ForegroundColor Gray
Write-Host "  Logs tab" -ForegroundColor Gray
Write-Host ""
