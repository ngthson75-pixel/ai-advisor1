# CHECK SIGNALS IN DATABASE
# Quick script to see what dates have signals

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CHECK LOCAL SIGNALS DATABASE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

cd C:\ai-advisor1

# Check if database exists
if (-not (Test-Path "signals.db")) {
    Write-Host "❌ signals.db not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Database should be at: C:\ai-advisor1\signals.db" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run scanner first:" -ForegroundColor Yellow
    Write-Host "  cd C:\ai-advisor1\scripts" -ForegroundColor Gray
    Write-Host "  python daily_signal_scanner_eod.py" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✓ Database found: signals.db" -ForegroundColor Green
Write-Host ""

# Method 1: Using Python (recommended)
Write-Host "Checking dates in database..." -ForegroundColor Yellow
Write-Host ""

try {
    $output = python -c @"
import sqlite3
conn = sqlite3.connect('signals.db')
cursor = conn.cursor()

# Get dates with signal counts
cursor.execute('''
    SELECT date, COUNT(*) as count
    FROM signals
    GROUP BY date
    ORDER BY date DESC
''')

dates = cursor.fetchall()
conn.close()

if not dates:
    print('NO_SIGNALS')
else:
    for date, count in dates:
        print(f'{date}:{count}')
"@

    if ($output -eq "NO_SIGNALS") {
        Write-Host "❌ No signals in database!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Run scanner first:" -ForegroundColor Yellow
        Write-Host "  cd C:\ai-advisor1\scripts" -ForegroundColor Gray
        Write-Host "  python daily_signal_scanner_eod.py" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "Available dates:" -ForegroundColor Green
        Write-Host ""
        
        $totalSignals = 0
        $latestDate = $null
        
        foreach ($line in $output) {
            $parts = $line -split ':'
            $date = $parts[0]
            $count = [int]$parts[1]
            
            if ($null -eq $latestDate) {
                $latestDate = $date
            }
            
            $totalSignals += $count
            
            if ($date -eq $latestDate) {
                Write-Host "  📅 $date - $count signals" -ForegroundColor Cyan -NoNewline
                Write-Host " ← LATEST" -ForegroundColor Yellow
            } else {
                Write-Host "  📅 $date - $count signals" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        Write-Host "Total signals across all dates: $totalSignals" -ForegroundColor White
        Write-Host ""
        
        # Show recommendation
        Write-Host "-" * 80 -ForegroundColor Gray
        Write-Host ""
        Write-Host "RECOMMENDATION:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Latest signals: $latestDate ($($output[0] -split ':')[1] signals)" -ForegroundColor White
        Write-Host ""
        Write-Host "  To push these to production:" -ForegroundColor Yellow
        Write-Host "    python push_local_signals.py" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  The script will auto-select the latest date ($latestDate)" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host "❌ Error checking database: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try using SQLite directly:" -ForegroundColor Yellow
    Write-Host "  sqlite3 signals.db 'SELECT date, COUNT(*) FROM signals GROUP BY date ORDER BY date DESC;'" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
