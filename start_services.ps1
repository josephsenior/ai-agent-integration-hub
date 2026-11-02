# Start Backend and Frontend Services
# Run this in PowerShell

Write-Host "=== Starting AI Agent Integration Hub ===" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "Starting Backend (FastAPI)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\GIGABYTE\Desktop\Portfolio\agent_integration_hub"
    & ".\\.venv\Scripts\python.exe" -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
}

# Start Frontend
Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\GIGABYTE\Desktop\Portfolio\agent_integration_hub\frontend-nextjs"
    npm run dev
}

Write-Host ""
Write-Host "Services starting in background..." -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Wait a bit for services to start
Start-Sleep -Seconds 8

# Check status
Write-Host "Checking service status..." -ForegroundColor Yellow
try {
    $backend = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "⏳ Backend is still starting..." -ForegroundColor Yellow
}

try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ Frontend is running!" -ForegroundColor Green
} catch {
    Write-Host "⏳ Frontend is still starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To view logs, run:" -ForegroundColor Gray
Write-Host "  Receive-Job -Id $($backendJob.Id)" -ForegroundColor Gray
Write-Host "  Receive-Job -Id $($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services, run:" -ForegroundColor Gray
Write-Host "  Stop-Job -Id $($backendJob.Id), $($frontendJob.Id); Remove-Job -Id $($backendJob.Id), $($frontendJob.Id)" -ForegroundColor Gray

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job -Id $backendJob.Id, $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id, $frontendJob.Id -ErrorAction SilentlyContinue
    Write-Host "`nServices stopped." -ForegroundColor Yellow
}
