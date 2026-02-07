# TEST SELL SCANNER MANUAL
# Purpose: Debug why no SELL signals generated

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "SELL SCANNER - MANUAL TEST & DEBUG" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check database exists
Write-Host "1. CHECK DATABASE" -ForegroundColor Yellow
if (Test-Path "signals.db") {
    Write-Host "   ✓ Database found: signals.db" -ForegroundColor Green
} else {
    Write-Host "   ✗ Database NOT found!" -ForegroundColor Red
    Write-Host "   Looking for database..." -ForegroundColor Yellow
    Get-ChildItem -Recurse -Filter "*.db" | Select-Object FullName
    exit 1
}

Write-Host ""

# 2. Check BUY signals in last 2 days
Write-Host "2. CHECK BUY SIGNALS (Last 2 days)" -ForegroundColor Yellow

$cutoff = (Get-Date).AddDays(-2).ToString("yyyy-MM-dd")
Write-Host "   Cutoff date: $cutoff" -ForegroundColor Cyan

$query = @"
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT ticker) as unique_tickers
FROM signals 
WHERE action = 'BUY' 
    AND date >= '$cutoff'
"@

$result = sqlite3 signals.db $query

Write-Host "   Result: $result" -ForegroundColor White

if ($result -match "0\|0") {
    Write-Host "   ✗ NO BUY signals found in last 2 days!" -ForegroundColor Red
    Write-Host "   → This is why SELL scanner found nothing" -ForegroundColor Yellow
    Write-Host ""
    
    # Check all BUY signals
    Write-Host "   Checking ALL BUY signals..." -ForegroundColor Yellow
    $allBuy = sqlite3 signals.db "SELECT COUNT(*), MAX(date) FROM signals WHERE action='BUY'"
    Write-Host "   Total BUY signals: $allBuy" -ForegroundColor White
    
    # Check latest date
    $latestDate = sqlite3 signals.db "SELECT MAX(date) FROM signals WHERE action='BUY'"
    Write-Host "   Latest BUY signal date: $latestDate" -ForegroundColor White
    
} else {
    Write-Host "   ✓ Found BUY signals!" -ForegroundColor Green
    
    # Show tickers
    Write-Host ""
    Write-Host "   Tickers with BUY signals:" -ForegroundColor Cyan
    $tickers = sqlite3 signals.db "SELECT DISTINCT ticker FROM signals WHERE action='BUY' AND date >= '$cutoff' ORDER BY ticker"
    $tickers -split "`n" | ForEach-Object {
        Write-Host "      - $_" -ForegroundColor White
    }
}

Write-Host ""

# 3. Check SELL signals exist
Write-Host "3. CHECK SELL SIGNALS" -ForegroundColor Yellow

$sellCount = sqlite3 signals.db "SELECT COUNT(*) FROM signals WHERE action='SELL'"
$sellToday = sqlite3 signals.db "SELECT COUNT(*) FROM signals WHERE action='SELL' AND exit_date='$(Get-Date -Format "yyyy-MM-dd")'"

Write-Host "   Total SELL signals: $sellCount" -ForegroundColor White
Write-Host "   SELL signals today: $sellToday" -ForegroundColor White

Write-Host ""

# 4. Check database columns
Write-Host "4. CHECK DATABASE SCHEMA" -ForegroundColor Yellow

$columns = sqlite3 signals.db "PRAGMA table_info(signals)" | ForEach-Object {
    if ($_ -match '\|([^|]+)\|') {
        $matches[1]
    }
}

$requiredCols = @('exit_reason', 'exit_date', 'profit_loss_pct', 'exit_quantity_pct', 'buy_signal_id', 'volume_ratio')

foreach ($col in $requiredCols) {
    if ($columns -contains $col) {
        Write-Host "   ✓ Column exists: $col" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Column missing: $col" -ForegroundColor Red
    }
}

Write-Host ""

# 5. Recommendation
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if ($result -match "0\|0") {
    Write-Host ""
    Write-Host "🔴 PROBLEM: No recent BUY signals" -ForegroundColor Red
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  1. Run BUY scanner first to generate fresh signals:" -ForegroundColor White
    Write-Host "     python scripts/daily_signal_scanner_eod.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. Test SELL scanner with older signals (increase days):" -ForegroundColor White
    Write-Host "     python sell_signal_scanner_v2.py --days 7" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Check when was last BUY signal generated:" -ForegroundColor White
    Write-Host "     Latest date: $latestDate" -ForegroundColor Cyan
    
} else {
    Write-Host ""
    Write-Host "✓ BUY signals found - Scanner should work!" -ForegroundColor Green
    Write-Host ""
    Write-Host "TRY RUNNING:" -ForegroundColor Yellow
    Write-Host "  python sell_signal_scanner_v2.py --days 2 --delay 2.0" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
