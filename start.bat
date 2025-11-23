@echo off
REM ChiliHead OpsManager v2.1 - Windows Startup Script

echo ============================================================
echo ChiliHead OpsManager v2.1 - Starting All Services
echo ============================================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Navigate to docker directory
cd /d "%~dp0infrastructure\docker"

REM Check if .env exists
if not exist ".env" (
    echo [WARN] .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env with your API keys and passwords!
    echo Opening .env file for editing...
    notepad .env
    echo.
    echo Press any key when you're done editing .env...
    pause >nul
)

echo [INFO] Starting all services with Docker Compose...
echo.

docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Services Starting...
echo ============================================================
echo.

REM Wait a moment for services to initialize
timeout /t 5 /nobreak >nul

echo Checking service status...
docker-compose ps

echo.
echo ============================================================
echo ChiliHead OpsManager Services:
echo ============================================================
echo.
echo Open-WebUI:        http://localhost:3000
echo Dolphin Scheduler: http://localhost:12345
echo AUBS API:          http://localhost:5000
echo UI-TARS:           http://localhost:8080 (embedded in Open-WebUI)
echo Grafana:           http://localhost:3001 (if monitoring enabled)
echo.
echo ============================================================
echo.
echo To view logs: docker-compose logs -f [service-name]
echo To stop: docker-compose down
echo.
echo Press any key to open Open-WebUI in your browser...
pause >nul

start http://localhost:3000

echo.
echo Services are running!
echo.
pause
