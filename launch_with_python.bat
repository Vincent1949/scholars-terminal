@echo off
echo ========================================
echo  Scholar's Terminal v3.0 - Multi-DB
echo  PYTHON HTTP SERVER MODE
echo ========================================
echo.
echo This workaround uses Python HTTP server
echo to bypass Windows blocking Node.js
echo.

REM Check if dist folder exists
if not exist "D:\Claude\Projects\scholars-terminal\frontend\dist" (
    echo Building frontend for first time...
    cd D:\Claude\Projects\scholars-terminal\frontend
    call npm run build
    echo.
    echo Build complete!
    echo.
)

echo Starting Scholar's Terminal...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8080
echo.

REM Start backend
start "Scholar's Terminal - Backend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && uvicorn Scholars_api:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

REM Start Python HTTP server for frontend
start "Scholar's Terminal - Frontend (Python)" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\dist && python -m http.server 8080"

timeout /t 2 /nobreak >nul

echo Opening browser...
start http://127.0.0.1:8080

echo.
echo ========================================
echo Scholar's Terminal is now running!
echo.
echo IMPORTANT: If you change the React code,
echo you must rebuild with: npm run build
echo.
echo Backend: Check terminal window
echo Frontend: Python HTTP server on 8080
echo.
echo To rebuild after code changes:
echo   cd frontend
echo   npm run build
echo.
echo Press any key to close launcher...
pause >nul
