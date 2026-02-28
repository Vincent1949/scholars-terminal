@echo off
echo ========================================
echo  Scholar's Terminal - Backend Only
echo ========================================
echo.

:: Check if Ollama is running
echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama...
    start /min "Ollama Service" cmd /c "ollama serve"
    echo Waiting for Ollama to initialize...
    timeout /t 10 /nobreak > nul
) else (
    echo Ollama is already running
)

cd /d D:\Claude\Projects\scholars-terminal

echo.
echo Starting Backend Server...
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Ollama:       http://localhost:11434
echo.

python Scholars_api.py

pause
