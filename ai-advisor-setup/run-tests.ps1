# ========================================================================
# RUN TESTS - AI ADVISOR
# ========================================================================

param(
    [string]$Type = "all",  # all, unit, integration, api, slow
    [switch]$Coverage,
    [switch]$Verbose
)

Write-Host "🧪 Running AI Advisor Tests..." -ForegroundColor Green
Write-Host ""

# Check if in correct directory
if (-Not (Test-Path "tests")) {
    Write-Host "❌ Error: tests directory not found!" -ForegroundColor Red
    Write-Host "Make sure you're in the project root directory." -ForegroundColor Yellow
    exit 1
}

# Check if pytest is installed
try {
    $pytestVersion = python -m pytest --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pytest not found"
    }
} catch {
    Write-Host "❌ pytest not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install with:" -ForegroundColor Yellow
    Write-Host "  pip install pytest pytest-cov pytest-flask --break-system-packages" -ForegroundColor White
    exit 1
}

# Build pytest command
$pytestCmd = "python -m pytest tests/"

# Add test type filter
switch ($Type) {
    "unit" {
        $pytestCmd += " -m 'unit'"
        Write-Host "📋 Running: Unit Tests Only" -ForegroundColor Cyan
    }
    "integration" {
        $pytestCmd += " -m 'integration'"
        Write-Host "📋 Running: Integration Tests Only" -ForegroundColor Cyan
    }
    "api" {
        $pytestCmd += " -m 'api'"
        Write-Host "📋 Running: API Tests Only" -ForegroundColor Cyan
    }
    "slow" {
        $pytestCmd += " -m 'slow'"
        Write-Host "📋 Running: Slow Tests" -ForegroundColor Cyan
    }
    "fast" {
        $pytestCmd += " -m 'not slow'"
        Write-Host "📋 Running: Fast Tests (excluding slow)" -ForegroundColor Cyan
    }
    "all" {
        Write-Host "📋 Running: All Tests" -ForegroundColor Cyan
    }
}

# Add coverage
if ($Coverage) {
    $pytestCmd += " --cov=. --cov-report=html --cov-report=term-missing"
    Write-Host "📊 Coverage: Enabled" -ForegroundColor Cyan
}

# Add verbosity
if ($Verbose) {
    $pytestCmd += " -vv"
    Write-Host "🔍 Verbose: Enabled" -ForegroundColor Cyan
} else {
    $pytestCmd += " -v"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray

# Run tests
Invoke-Expression $pytestCmd

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Gray

# Summary
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
    
    if ($Coverage) {
        Write-Host ""
        Write-Host "📊 Coverage report generated:" -ForegroundColor Cyan
        Write-Host "  htmlcov/index.html" -ForegroundColor White
        Write-Host ""
        Write-Host "Open coverage report:" -ForegroundColor Cyan
        Write-Host "  Start-Process htmlcov/index.html" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ SOME TESTS FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Review the output above for details." -ForegroundColor Yellow
}

Write-Host ""

# Usage examples
if ($exitCode -ne 0) {
    Write-Host "💡 Tip: Run specific test types:" -ForegroundColor Yellow
    Write-Host "  .\run-tests.ps1 -Type unit" -ForegroundColor Gray
    Write-Host "  .\run-tests.ps1 -Type integration" -ForegroundColor Gray
    Write-Host "  .\run-tests.ps1 -Type fast" -ForegroundColor Gray
    Write-Host "  .\run-tests.ps1 -Coverage" -ForegroundColor Gray
    Write-Host ""
}

exit $exitCode
