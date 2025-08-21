@echo off
echo Stopping Alex Orator Bot Docker services...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running.
    pause
    exit /b 1
)

echo.
echo Stopping all services...
echo.

REM Stop all services
docker-compose down

REM Check if services are stopped
docker-compose ps | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo All services stopped successfully.
) else (
    echo Some services are still running.
    docker-compose ps
)

echo.
echo Services status:
docker-compose ps

echo.
echo All Docker services have been stopped.
echo.
pause
