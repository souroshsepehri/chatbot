# PowerShell script to run production mode locally
# This mimics exactly what runs on the server

param(
    [switch]$SkipBuild = $false,
    [switch]$SkipMigrate = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Production Mode (Local)" -ForegroundColor Green
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# 1. Load environment variables from .env.production files
Write-Host "📋 Loading production environment variables..." -ForegroundColor Cyan

$BackendEnvPath = Join-Path $ProjectRoot "apps\backend\.env.production"
$FrontendEnvPath = Join-Path $ProjectRoot "apps\frontend\.env.production.local"

# Check if production env files exist, if not, use .env files
if (-not (Test-Path $BackendEnvPath)) {
    $BackendEnvPath = Join-Path $ProjectRoot "apps\backend\.env"
    Write-Host "⚠️  .env.production not found, using .env" -ForegroundColor Yellow
}

if (-not (Test-Path $FrontendEnvPath)) {
    $FrontendEnvPath = Join-Path $ProjectRoot "apps\frontend\.env.local"
    Write-Host "⚠️  .env.production.local not found, using .env.local" -ForegroundColor Yellow
}

# Load backend env
if (Test-Path $BackendEnvPath) {
    Get-Content $BackendEnvPath | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "✅ Backend env loaded from: $BackendEnvPath" -ForegroundColor Green
} else {
    Write-Host "❌ Backend .env file not found at: $BackendEnvPath" -ForegroundColor Red
    exit 1
}

# Load frontend env
if (Test-Path $FrontendEnvPath) {
    Get-Content $FrontendEnvPath | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "✅ Frontend env loaded from: $FrontendEnvPath" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend .env file not found, using defaults" -ForegroundColor Yellow
}

Write-Host ""

# 2. Database Migration
if (-not $SkipMigrate) {
    Write-Host "🗄️  Running database migrations..." -ForegroundColor Cyan
    Set-Location (Join-Path $ProjectRoot "apps\backend")
    
    # Check if venv exists
    $venvPath = Join-Path (Get-Location) "venv"
    if (Test-Path $venvPath) {
        & "$venvPath\Scripts\Activate.ps1"
        $pythonCmd = "$venvPath\Scripts\python.exe"
    } else {
        $pythonCmd = "python"
        Write-Host "⚠️  Virtual environment not found, using system Python" -ForegroundColor Yellow
    }
    
    & $pythonCmd -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Migration failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Migrations completed" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping migrations (--SkipMigrate)" -ForegroundColor Yellow
    Write-Host ""
}

# 3. Build Frontend
if (-not $SkipBuild) {
    Write-Host "🏗️  Building frontend..." -ForegroundColor Cyan
    Set-Location (Join-Path $ProjectRoot "apps\frontend")
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Build
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Frontend built successfully" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping frontend build (--SkipBuild)" -ForegroundColor Yellow
    Write-Host ""
}

# 4. Start with PM2
Write-Host "🚀 Starting services with PM2..." -ForegroundColor Cyan
Set-Location $ProjectRoot

# Check if PM2 is installed
$pm2Check = Get-Command pm2 -ErrorAction SilentlyContinue
if (-not $pm2Check) {
    Write-Host "❌ PM2 is not installed. Install it with: npm install -g pm2" -ForegroundColor Red
    exit 1
}

# Create logs directory
$logsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Stop existing processes
Write-Host "🛑 Stopping existing PM2 processes..." -ForegroundColor Yellow
pm2 stop all 2>$null
pm2 delete all 2>$null

# Start with PM2
pm2 start pm2.ecosystem.config.js

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start PM2 services!" -ForegroundColor Red
    exit 1
}

# Show status
Write-Host ""
Write-Host "📊 PM2 Status:" -ForegroundColor Cyan
pm2 status

Write-Host ""
Write-Host "✅ Production mode started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Services:" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Gray
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   pm2 logs              - View all logs" -ForegroundColor Gray
Write-Host "   pm2 logs chatbot-backend   - View backend logs" -ForegroundColor Gray
Write-Host "   pm2 logs chatbot-frontend  - View frontend logs" -ForegroundColor Gray
Write-Host "   pm2 stop all          - Stop all services" -ForegroundColor Gray
Write-Host "   pm2 restart all       - Restart all services" -ForegroundColor Gray
Write-Host ""





