@echo off
REM ChiliHead OpsManager v2.1 - Check Status

echo ============================================================
echo ChiliHead OpsManager v2.1 - System Status
echo ============================================================
echo.

cd /d "%~dp0infrastructure\docker"

echo Checking Docker service status...
echo.

docker-compose ps

echo.
echo ============================================================
echo Service Health Checks
echo ============================================================
echo.

echo Checking AUBS...
curl -s http://localhost:5000/health >nul 2>&1
if errorlevel 1 (
    echo [X] AUBS: Not responding
) else (
    echo [OK] AUBS: Running at http://localhost:5000
)

echo Checking Open-WebUI...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [X] Open-WebUI: Not responding
) else (
    echo [OK] Open-WebUI: Running at http://localhost:3000
)

echo Checking Dolphin...
curl -s http://localhost:12345/dolphinscheduler/health >nul 2>&1
if errorlevel 1 (
    echo [X] Dolphin: Not responding
) else (
    echo [OK] Dolphin: Running at http://localhost:12345
)

echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [X] Ollama: Not responding
) else (
    echo [OK] Ollama: Running at http://localhost:11434
)

echo.
echo ============================================================
echo.
pause
