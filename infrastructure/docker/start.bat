@echo off
echo.
echo ============================================================
echo  ChiliHead OpsManager v2.1 - Starting All Services
echo ============================================================
echo.

REM Change to the docker directory
cd /d "%~dp0"

echo [1/3] Pulling latest images...
docker-compose pull

echo.
echo [2/3] Starting all services...
docker-compose up -d

echo.
echo [3/3] Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================
echo  ChiliHead OpsManager v2.1 - READY
echo ============================================================
echo.
echo  Open-WebUI:     http://localhost:3040
echo  Email Client:   http://localhost:3040 (Emails tab)
echo  AUBS Chat:      http://localhost:3040 (Chat tab)
echo  Settings:       http://localhost:3040 (Settings tab)
echo.
echo  UI-TARS Debug:  http://localhost:8080
echo  Dolphin Admin:  http://localhost:12345
echo.
echo ============================================================
echo.
echo Checking service status...
docker-compose ps
echo.
echo To view logs: docker-compose logs -f [service-name]
echo To stop all:  stop.bat
echo.
pause
