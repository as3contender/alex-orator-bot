# Stop Alex Orator Bot Docker services
# PowerShell script for Windows

Write-Host "Stopping Alex Orator Bot Docker services..." -ForegroundColor Yellow

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running." -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Stopping all services..." -ForegroundColor Yellow
Write-Host ""

# Stop all services
docker-compose down

# Check if services are stopped
$runningServices = docker-compose ps | Select-String "Up"
if (-not $runningServices) {
    Write-Host "All services stopped successfully." -ForegroundColor Green
} else {
    Write-Host "Some services are still running." -ForegroundColor Yellow
    docker-compose ps
}

Write-Host ""
Write-Host "Services status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "All Docker services have been stopped." -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to continue"
