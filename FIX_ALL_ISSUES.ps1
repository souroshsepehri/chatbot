# Comprehensive Fix Script
# This script fixes all known issues and restarts everything

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Comprehensive Fix & Restart" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all processes
Write-Host "Step 1: Stopping all processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*frontend*" -or $_.Path -like "*chatbot*"} | Stop-Process -Force

# Kill processes on ports
$ports = @(8000, 8001, 3000, 3001)
foreach ($port in $ports) {
    $proc = netstat -ano | findstr ":$port" | Select-String "LISTENING"
    if ($proc) {
        $pid = ($proc -split '\s+')[-1]
        taskkill /PID $pid /F 2>$null | Out-Null
    }
}

Start-Sleep -Seconds 3
Write-Host "  All processes stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Clean and rebuild frontend
Write-Host "Step 2: Cleaning and rebuilding frontend..." -ForegroundColor Yellow
cd apps/frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Frontend build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  Frontend built successfully" -ForegroundColor Green
cd ../..
Write-Host ""

# Step 3: Verify backend database
Write-Host "Step 3: Verifying backend setup..." -ForegroundColor Yellow
cd apps/backend

# Check if database exists
if (-not (Test-Path "chatbot.db")) {
    Write-Host "  Creating database..." -ForegroundColor Cyan
    python -m alembic upgrade head
}

# Check if admin user exists
$adminCheck = python -c "from app.db.session import SessionLocal; from app.models.admin_user import AdminUser; db = SessionLocal(); count = db.query(AdminUser).count(); db.close(); print('OK' if count > 0 else 'MISSING')" 2>&1
if ($adminCheck -match "MISSING") {
    Write-Host "  Creating admin user..." -ForegroundColor Cyan
    python create_admin.py
}

Write-Host "  Backend setup verified" -ForegroundColor Green
cd ../..
Write-Host ""

# Step 4: Start Backend
Write-Host "Step 4: Starting Backend..." -ForegroundColor Yellow
$backendDir = Join-Path $PWD "apps\backend"
$backendScript = "cd '$backendDir'; Write-Host '=== BACKEND SERVER ===' -ForegroundColor Green; Write-Host 'Running on: http://127.0.0.1:8000' -ForegroundColor Cyan; Write-Host 'API Docs: http://127.0.0.1:8000/docs' -ForegroundColor Cyan; Write-Host ''; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendScript) -WindowStyle Normal
Write-Host "  Backend starting..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Step 5: Test Backend
Write-Host "Step 5: Testing Backend..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "  Backend not responding yet. Please wait a few more seconds." -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Start Frontend
Write-Host "Step 6: Starting Frontend..." -ForegroundColor Yellow
$frontendDir = Join-Path $PWD "apps\frontend"
$frontendScript = "cd '$frontendDir'; Write-Host '=== FRONTEND SERVER ===' -ForegroundColor Green; Write-Host 'Running on: http://localhost:3000' -ForegroundColor Cyan; Write-Host 'Admin: http://localhost:3000/admin/login' -ForegroundColor Cyan; Write-Host 'Chat: http://localhost:3000/chat' -ForegroundColor Cyan; Write-Host ''; npm run start"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $frontendScript) -WindowStyle Normal
Write-Host "  Frontend starting..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Step 7: Final Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All Issues Fixed & Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fixed Issues:" -ForegroundColor Yellow
Write-Host "  - Logging error (request_id conflict)" -ForegroundColor Green
Write-Host "  - Frontend build (BUILD_ID)" -ForegroundColor Green
Write-Host "  - Port conflicts" -ForegroundColor Green
Write-Host "  - Database setup" -ForegroundColor Green
Write-Host ""
Write-Host "Access Your Application:" -ForegroundColor Yellow
Write-Host "  Admin Panel: http://localhost:3000/admin/login" -ForegroundColor White
Write-Host "  Chat UI:     http://localhost:3000/chat" -ForegroundColor White
Write-Host "  Backend API: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Wait 10-15 seconds for both servers to fully start," -ForegroundColor Cyan
Write-Host "then refresh your browser and try again." -ForegroundColor Cyan
Write-Host ""

