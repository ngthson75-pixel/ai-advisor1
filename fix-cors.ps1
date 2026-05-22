# Fix CORS in backend_api.py for ai-advisor.vn

$backendFile = "C:\ai-advisor1\backend_api.py"

# Read file content
$content = Get-Content $backendFile -Raw

# Old CORS config
$oldCORS = @"
app = Flask(__name__)
CORS(app)
"@

# New CORS config
$newCORS = @"
app = Flask(__name__)

# CORS Configuration - Allow production + staging + local
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://ai-advisor.vn",
            "https://www.ai-advisor.vn",
            "https://ai-advisor-staging.pages.dev",
            "http://localhost:5173",
            "http://localhost:3000"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
"@

# Replace
if ($content -match [regex]::Escape($oldCORS)) {
    $newContent = $content -replace [regex]::Escape($oldCORS), $newCORS
    
    # Write back with UTF-8 encoding (no BOM)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($backendFile, $newContent, $utf8NoBom)
    
    Write-Host "✅ CORS fixed in backend_api.py" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. git add backend_api.py"
    Write-Host "2. git commit -m 'fix: Add CORS for production domain'"
    Write-Host "3. git push origin main"
} else {
    Write-Host "❌ Could not find CORS(app) to replace" -ForegroundColor Red
    Write-Host "Please edit manually in VS Code" -ForegroundColor Yellow
}
