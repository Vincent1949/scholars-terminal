@echo off
echo ========================================
echo  Scholar's Terminal v3.0 - FINAL FIX
echo ========================================
echo.

REM Check if build exists
if not exist "D:\Claude\Projects\scholars-terminal\frontend\dist" (
    echo [1/4] Building frontend...
    cd D:\Claude\Projects\scholars-terminal\frontend
    call npm run build
    if errorlevel 1 (
        echo ERROR: Build failed!
        pause
        exit /b 1
    )
    echo.
)

echo [2/4] Starting backend (simplified API, port 8000)...
start "Backend API - Port 8000" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && python Scholars_api_simple.py"

timeout /t 4 /nobreak >nul

echo [3/4] Trying frontend on high port (49152)...
start "Frontend - Port 49152" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\dist && python -m http.server 49152"

timeout /t 2 /nobreak >nul

echo [4/4] Opening browser...
start http://localhost:49152

echo.
echo ========================================
echo Scholar's Terminal Running!
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:49152
echo.
echo If port 49152 fails, manually run:
echo   cd frontend\dist
echo   python -m http.server 50000
echo   Then open: http://localhost:50000
echo.
echo ========================================
pause
