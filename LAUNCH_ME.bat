@echo off
echo ========================================
echo  Scholar's Terminal v3.0
echo  Simplified Launcher (Port 9000)
echo ========================================
echo.

REM Check if dist folder exists
if not exist "D:\Claude\Projects\scholars-terminal\frontend\dist" (
    echo [1/4] Building frontend for first time...
    cd D:\Claude\Projects\scholars-terminal\frontend
    call npm run build
    if errorlevel 1 (
        echo ERROR: Build failed!
        pause
        exit /b 1
    )
    echo Build complete!
    echo.
)

echo [2/4] Starting backend API (simplified, no research scanner)...
start "Backend API" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && python Scholars_api_simple.py"

timeout /t 3 /nobreak >nul

echo [3/4] Starting frontend server on port 9000...
start "Frontend Server" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\dist && python -m http.server 9000"

timeout /t 2 /nobreak >nul

echo [4/4] Opening browser...
start http://localhost:9000

echo.
echo ========================================
echo Scholar's Terminal is running!
echo.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:9000
echo.
echo Close this window anytime.
echo Press CTRL+C in the other windows to stop.
echo ========================================
echo.
pause
