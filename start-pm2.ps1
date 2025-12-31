# PowerShell script to start PM2 services
# Run from project root directory

Write-Host "🚀 Starting Chatbot Services with PM2..." -ForegroundColor Green

# Check if PM2 is installed
$pm2Check = Get-Command pm2 -ErrorAction SilentlyContinue
if (-not $pm2Check) {
    Write-Host "❌ PM2 is not installed. Install it with: npm install -g pm2" -ForegroundColor Red
    exit 1
}

# Check if frontend is built
$frontendBuild = Join-Path $PSScriptRoot "apps\frontend\.next"
if (-not (Test-Path $frontendBuild)) {
    Write-Host "⚠️  Frontend build not found. Building frontend..." -ForegroundColor Yellow
    Set-Location (Join-Path $PSScriptRoot "apps\frontend")
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    Set-Location $PSScriptRoot
    Write-Host "✅ Frontend built successfully!" -ForegroundColor Green
}

# Check if backend venv exists
$backendVenv = Join-Path $PSScriptRoot "apps\backend\venv"
if (-not (Test-Path $backendVenv)) {
    Write-Host "⚠️  Backend virtual environment not found. Creating..." -ForegroundColor Yellow
    Set-Location (Join-Path $PSScriptRoot "apps\backend")
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    deactivate
    Set-Location $PSScriptRoot
    Write-Host "✅ Backend virtual environment created!" -ForegroundColor Green
}

# Create logs directory
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Stop existing processes
Write-Host "🛑 Stopping existing PM2 processes..." -ForegroundColor Yellow
pm2 stop all 2>$null
pm2 delete all 2>$null

# Start with PM2
Write-Host "▶️  Starting services with PM2..." -ForegroundColor Green
pm2 start pm2.ecosystem.config.js

# Show status
Write-Host "`n📊 PM2 Status:" -ForegroundColor Cyan
pm2 status

Write-Host "`n✅ Services started! Use 'pm2 logs' to view logs" -ForegroundColor Green
Write-Host "   Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Gray



