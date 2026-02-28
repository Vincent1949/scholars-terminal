@echo off
title Scholar's Terminal Launcher
echo.
echo ============================================================
echo 📚 Starting Scholar's Terminal
echo ============================================================
echo.

:: Check if Ollama is running, start if needed
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

:: Start the File Watcher in background (minimized)
echo Starting file watcher...
start /min "Scholar's Terminal Watcher" cmd /c "cd /d D:\Claude\Projects\scholars-terminal && python file_watcher.py --interval 60"

:: Start the API in a new window
echo Starting API server...
start "Scholar's Terminal API" cmd /k "cd /d D:\Claude\Projects\scholars-terminal && python Scholars_api.py"

:: Wait a moment for API to initialize
timeout /t 5 /nobreak > nul

:: Start the frontend in a new window
echo Starting frontend...
start "Scholar's Terminal Frontend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend && npm run dev"

:: Wait for frontend to start
timeout /t 5 /nobreak > nul

:: Open browser
echo Opening browser...
start http://localhost:5173

echo.
echo ============================================================
echo 📚 Scholar's Terminal is running!
echo.
echo    Ollama:   http://localhost:11434
echo    API:      http://localhost:8000
echo    Frontend: http://localhost:5173
echo    Watcher:  Running (minimized)
echo.
echo    Close the terminal windows to stop the servers.
echo ============================================================
echo.
