# Kill any process using port 8001
Write-Host "Checking for processes on port 8001..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $pids) {
        if ($pid -gt 0) {
            Write-Host "Killing process $pid on port 8001..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    Write-Host "✅ Port 8001 is now free" -ForegroundColor Green
} else {
    Write-Host "✅ Port 8001 is already free" -ForegroundColor Green
}

