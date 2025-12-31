# PowerShell script to run all tests

$ErrorActionPreference = "Stop"

Write-Host "🧪 Running all tests..." -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

# Run pytest with quiet mode
pytest -q

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Tests failed!" -ForegroundColor Red
    exit 1
}



