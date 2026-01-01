# PowerShell script to verify deployment readiness

$ErrorActionPreference = "Stop"

Write-Host "🔍 Running deployment health checks..." -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$Errors = 0

# 1. Check required environment variables
Write-Host "📋 Checking environment variables..." -ForegroundColor Cyan
Write-Host ""

# Backend env
$BackendEnv = Join-Path $ProjectRoot "apps\backend\.env"
if (-not (Test-Path $BackendEnv)) {
    Write-Host "⚠️  Backend .env not found at $BackendEnv" -ForegroundColor Yellow
    Write-Host "   Create it from .env.example"
    $Errors++
} else {
    Write-Host "✓ Backend .env exists" -ForegroundColor Green
    
    # Check required vars
    $RequiredVars = @("DATABASE_URL", "OPENAI_API_KEY", "SESSION_SECRET", "FRONTEND_ORIGIN")
    foreach ($var in $RequiredVars) {
        $content = Get-Content $BackendEnv | Where-Object { $_ -match "^${var}=" }
        if (-not $content -or $content -match "^${var}=$") {
            Write-Host "✗ Missing or empty: $var" -ForegroundColor Red
            $Errors++
        } else {
            Write-Host "✓ $var is set" -ForegroundColor Green
        }
    }
}

# Frontend env
$FrontendEnv = Join-Path $ProjectRoot "apps\frontend\.env.local"
if (-not (Test-Path $FrontendEnv)) {
    Write-Host "⚠️  Frontend .env.local not found (optional for local dev)" -ForegroundColor Yellow
} else {
    Write-Host "✓ Frontend .env.local exists" -ForegroundColor Green
}

Write-Host ""

# 2. Check frontend build
Write-Host "📦 Checking frontend build..." -ForegroundColor Cyan
$FrontendBuild = Join-Path $ProjectRoot "apps\frontend\.next"
if (-not (Test-Path $FrontendBuild)) {
    Write-Host "⚠️  Frontend build not found" -ForegroundColor Yellow
    Write-Host "   Run: cd apps/frontend && npm run build"
    $Errors++
} else {
    Write-Host "✓ Frontend build exists" -ForegroundColor Green
}
Write-Host ""

# 3. Check backend dependencies
Write-Host "🐍 Checking backend dependencies..." -ForegroundColor Cyan
$BackendVenv = Join-Path $ProjectRoot "apps\backend\venv"
if (-not (Test-Path $BackendVenv)) {
    Write-Host "⚠️  Backend virtual environment not found" -ForegroundColor Yellow
    Write-Host "   Run: cd apps/backend && python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt"
    $Errors++
} else {
    Write-Host "✓ Backend virtual environment exists" -ForegroundColor Green
}
Write-Host ""

# 4. Check PM2 ecosystem file
Write-Host "⚙️  Checking PM2 configuration..." -ForegroundColor Cyan
$Pm2Config = Join-Path $ProjectRoot "pm2.ecosystem.config.js"
if (-not (Test-Path $Pm2Config)) {
    Write-Host "✗ pm2.ecosystem.config.js not found" -ForegroundColor Red
    $Errors++
} else {
    Write-Host "✓ PM2 ecosystem file exists" -ForegroundColor Green
}
Write-Host ""

# 5. Health check (if backend is running)
Write-Host "🏥 Checking backend health..." -ForegroundColor Cyan
$BackendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "http://localhost:8000" }

try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend health check passed" -ForegroundColor Green
        
        # Check components
        try {
            $compResponse = Invoke-WebRequest -Uri "$BackendUrl/health/components" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($compResponse.StatusCode -eq 200) {
                Write-Host "✓ Backend components health check passed" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Backend components health check failed" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Backend components health check failed" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "⚠️  Backend not responding at $BackendUrl" -ForegroundColor Yellow
    Write-Host "   Start backend: cd apps/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
}
Write-Host ""

# Summary
if ($Errors -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Found $Errors issue(s)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix the issues above before deploying."
    exit 1
}





