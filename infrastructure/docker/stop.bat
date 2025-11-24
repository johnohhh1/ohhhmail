@echo off
echo.
echo ============================================================
echo  ChiliHead OpsManager v2.1 - Stopping All Services
echo ============================================================
echo.

REM Change to the docker directory
cd /d "%~dp0"

echo Stopping all services...
docker-compose down

echo.
echo ============================================================
echo  All services stopped
echo ============================================================
echo.
pause
