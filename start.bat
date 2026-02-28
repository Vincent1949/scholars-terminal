@echo off
echo ========================================
echo  Scholar's Terminal - Complete Startup
echo ========================================
echo.

echo Starting File Watcher...
start "Scholar's Terminal - File Watcher" cmd /k "cd /d D:\Claude\Projects\scholars-terminal && python file_watcher.py"

timeout /t 3 /nobreak > nul

echo Starting Backend Server...
start "Scholar's Terminal - Backend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && uvicorn Scholars_api:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5 /nobreak > nul

echo Starting Frontend...
start "Scholar's Terminal - Frontend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend && npm run dev"

echo.
echo ========================================
echo  Scholar's Terminal Started!
echo ========================================
echo.
echo File Watcher:  Monitoring D:\Books and D:\GitHub
echo Backend API:   http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo Frontend UI:   http://localhost:5173
echo.
echo Three windows opened:
echo   1. File Watcher  (indexes new books/code)
echo   2. Backend API   (FastAPI + ChromaDB)
echo   3. Frontend UI   (React interface)
echo.
echo Press any key to close this launcher window...
pause > nul
