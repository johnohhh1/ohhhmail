@echo off
REM ChiliHead OpsManager v2.1 - Windows Stop Script

echo ============================================================
echo ChiliHead OpsManager v2.1 - Stopping All Services
echo ============================================================
echo.

cd /d "%~dp0infrastructure\docker"

echo Stopping all services...
docker-compose down

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to stop services!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo All services stopped successfully!
echo ============================================================
echo.
pause
