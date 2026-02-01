# ========================================================================
# START LOCAL DEVELOPMENT ENVIRONMENT
# ========================================================================

Write-Host "🚀 Starting AI Advisor Local Development..." -ForegroundColor Green

# Check if .env.local exists
if (-Not (Test-Path ".env.local")) {
    Write-Host "❌ .env.local not found!" -ForegroundColor Red
    Write-Host "📝 Please copy .env.local.example to .env.local and fill in your values" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run this command:" -ForegroundColor Cyan
    Write-Host "  Copy-Item .env.local.example .env.local" -ForegroundColor White
    exit 1
}

# Load environment variables
Write-Host "📁 Loading environment variables..." -ForegroundColor Cyan
Get-Content .env.local | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Check Docker
Write-Host "🐳 Checking Docker..." -ForegroundColor Cyan
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green

# Start services
Write-Host ""
Write-Host "🏗️  Starting services..." -ForegroundColor Cyan
docker-compose up -d

# Wait for services to be healthy
Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan

$maxRetries = 30
$retryCount = 0
$allHealthy = $false

while ($retryCount -lt $maxRetries -and -not $allHealthy) {
    $retryCount++
    
    # Check PostgreSQL
    $pgHealthy = docker-compose exec -T postgres pg_isready -U aiadvisor 2>&1
    
    # Check Backend
    try {
        $backendHealthy = Invoke-RestMethod -Uri "http://localhost:10000/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    } catch {
        $backendHealthy = $null
    }
    
    if ($pgHealthy -match "accepting connections" -and $backendHealthy) {
        $allHealthy = $true
        break
    }
    
    Write-Host "  Retry $retryCount/$maxRetries..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

Write-Host ""
if ($allHealthy) {
    Write-Host "✅ All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "🎉 AI ADVISOR LOCAL ENVIRONMENT READY!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📍 Services:" -ForegroundColor White
    Write-Host "  🔹 Backend API:    http://localhost:10000" -ForegroundColor White
    Write-Host "  🔹 Database:       localhost:5432" -ForegroundColor White
    Write-Host "  🔹 Redis Cache:    localhost:6379" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Quick Tests:" -ForegroundColor White
    Write-Host "  curl http://localhost:10000/health" -ForegroundColor Gray
    Write-Host "  curl http://localhost:10000/api/signals" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 View Logs:" -ForegroundColor White
    Write-Host "  docker-compose logs -f backend" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🛑 Stop Services:" -ForegroundColor White
    Write-Host "  docker-compose down" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Next Step: Start Frontend" -ForegroundColor Yellow
    Write-Host "  cd frontend" -ForegroundColor Gray
    Write-Host "  npm run dev" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "❌ Services failed to start!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs" -ForegroundColor Gray
    exit 1
}
