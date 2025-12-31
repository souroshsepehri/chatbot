# Quick script to start backend in dev mode (port 8001)
Write-Host "Starting Backend Server (Dev Mode - Port 8001)..." -ForegroundColor Green
Write-Host ""

# Check and kill any process using port 8001
Write-Host "Checking port 8001..." -ForegroundColor Yellow
$connections = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        if ($pid -gt 0) {
            Write-Host "Killing existing process $pid on port 8001..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    Write-Host "✅ Port 8001 is now free" -ForegroundColor Green
    Write-Host ""
}

cd apps\backend

# Activate virtual environment if it exists
if (Test-Path .venv\Scripts\Activate.ps1) {
    .\.venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== BACKEND SERVER (Dev Mode) ===" -ForegroundColor Green
Write-Host "Running on: http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "API Docs: http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host "Health: http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

