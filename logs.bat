@echo off
REM ChiliHead OpsManager v2.1 - View Logs

echo ============================================================
echo ChiliHead OpsManager v2.1 - Service Logs
echo ============================================================
echo.
echo Select a service to view logs:
echo.
echo   1. AUBS (orchestrator)
echo   2. Dolphin Server
echo   3. Dolphin Worker GPU
echo   4. Dolphin Worker CPU
echo   5. Email Ingestion
echo   6. Open-WebUI
echo   7. Ollama
echo   8. PostgreSQL
echo   9. Redis
echo   10. All services
echo   0. Exit
echo.

set /p CHOICE="Enter choice (1-10): "

cd /d "%~dp0infrastructure\docker"

if "%CHOICE%"=="1" (
    docker-compose logs -f aubs
) else if "%CHOICE%"=="2" (
    docker-compose logs -f dolphin-server
) else if "%CHOICE%"=="3" (
    docker-compose logs -f dolphin-worker-gpu
) else if "%CHOICE%"=="4" (
    docker-compose logs -f dolphin-worker-cpu
) else if "%CHOICE%"=="5" (
    docker-compose logs -f email-ingestion
) else if "%CHOICE%"=="6" (
    docker-compose logs -f open-webui
) else if "%CHOICE%"=="7" (
    docker-compose logs -f ollama
) else if "%CHOICE%"=="8" (
    docker-compose logs -f postgres
) else if "%CHOICE%"=="9" (
    docker-compose logs -f redis
) else if "%CHOICE%"=="10" (
    docker-compose logs -f
) else if "%CHOICE%"=="0" (
    exit /b 0
) else (
    echo Invalid choice!
    pause
)
