# Start Alex Orator Bot Docker services
# PowerShell script for Windows

Write-Host "Starting Alex Orator Bot Docker services..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "Error: docker-compose is not available." -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
Write-Host ""

# Start PostgreSQL
Write-Host "Starting PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check PostgreSQL status
$postgresStatus = docker-compose ps postgres | Select-String "Up"
if (-not $postgresStatus) {
    Write-Host "Error: PostgreSQL failed to start." -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker-compose logs postgres
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "PostgreSQL is running." -ForegroundColor Green

# Start Redis (optional)
Write-Host "Starting Redis..." -ForegroundColor Cyan
docker-compose up -d redis

# Wait for Redis to be ready
Write-Host "Waiting for Redis to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check Redis status
$redisStatus = docker-compose ps redis | Select-String "Up"
if (-not $redisStatus) {
    Write-Host "Warning: Redis failed to start. Continuing without Redis..." -ForegroundColor Yellow
} else {
    Write-Host "Redis is running." -ForegroundColor Green
}

Write-Host ""
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host ""

# Show services status
Write-Host "Services status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "PostgreSQL: localhost:5434" -ForegroundColor Cyan
Write-Host "Redis: localhost:6379" -ForegroundColor Cyan
Write-Host ""

Write-Host "You can now start the admin panel with:" -ForegroundColor Yellow
Write-Host "streamlit run admin_panel/admin_app.py" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to continue"
