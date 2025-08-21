@echo off
echo Starting Alex Orator Bot Docker services...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: docker-compose is not available.
    pause
    exit /b 1
)

echo.
echo Starting services...
echo.

REM Start PostgreSQL
echo Starting PostgreSQL...
docker-compose up -d postgres

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Check PostgreSQL status
docker-compose ps postgres | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo Error: PostgreSQL failed to start.
    echo Checking logs...
    docker-compose logs postgres
    pause
    exit /b 1
)

echo PostgreSQL is running.

REM Start Redis (optional)
echo Starting Redis...
docker-compose up -d redis

REM Wait for Redis to be ready
echo Waiting for Redis to be ready...
timeout /t 5 /nobreak >nul

REM Check Redis status
docker-compose ps redis | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo Warning: Redis failed to start. Continuing without Redis...
) else (
    echo Redis is running.
)

echo.
echo All services started successfully!
echo.
echo Services status:
docker-compose ps

echo.
echo PostgreSQL: localhost:5434
echo Redis: localhost:6379
echo.
echo You can now start the admin panel with: streamlit run admin_panel/admin_app.py
echo.
pause
