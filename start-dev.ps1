# Start both backend and frontend servers

Write-Host "🚀 Starting Backend and Frontend Servers..." -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "Starting Backend (FastAPI) on http://127.0.0.1:8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\backend'; .venv\Scripts\Activate.ps1; Write-Host '=== BACKEND SERVER ===' -ForegroundColor Green; Write-Host 'Running on: http://127.0.0.1:8001' -ForegroundColor Cyan; Write-Host 'API Docs: http://127.0.0.1:8001/docs' -ForegroundColor Cyan; Write-Host ''; uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend (Next.js) on http://localhost:3001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\frontend'; $env:PORT='3001'; Write-Host '=== FRONTEND SERVER ===' -ForegroundColor Green; Write-Host 'Running on: http://localhost:3001' -ForegroundColor Cyan; Write-Host ''; npm run dev"

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "✅ Both servers are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "=== Your Application URLs ===" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001" -ForegroundColor Yellow
Write-Host "Backend API: http://127.0.0.1:8001" -ForegroundColor Yellow
Write-Host "API Docs: http://127.0.0.1:8001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening frontend in browser..." -ForegroundColor Green
Start-Sleep -Seconds 3
Start-Process "http://localhost:3001"

