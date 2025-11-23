@echo off
REM ChiliHead OpsManager v2.1 - Windows Setup Script

echo ============================================================
echo ChiliHead OpsManager v2.1 - Initial Setup
echo ============================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Python is not installed (optional for local development)
) else (
    echo [OK] Python is installed
)
echo.

REM Navigate to docker directory
cd /d "%~dp0infrastructure\docker"

REM Setup .env file
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo [INFO] .env file created!
    echo Please edit it with your configuration...
    echo.
    notepad .env
) else (
    echo [OK] .env file already exists
)

echo.
echo ============================================================
echo Setup Ollama Models
echo ============================================================
echo.
echo This will download AI models (may take 10-30 minutes)
echo.
set /p SETUP_MODELS="Download Ollama models now? (y/n): "

if /i "%SETUP_MODELS%"=="y" (
    echo.
    echo Starting infrastructure to download models...
    docker-compose up -d ollama

    echo Waiting for Ollama to be ready...
    timeout /t 10 /nobreak >nul

    echo Downloading models...
    docker exec chilihead-ollama ollama pull llama3.2:8b-instruct
    docker exec chilihead-ollama ollama pull llama3.2-vision:11b
    docker exec chilihead-ollama ollama pull qwen:110b

    echo.
    echo [OK] Models downloaded!
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Review/edit .env file if needed
echo   2. Run start.bat to start all services
echo   3. Access Open-WebUI at http://localhost:3000
echo.
echo For more help, see README.md or QUICK_START.md
echo.
pause
