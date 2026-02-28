@echo off
echo ========================================
echo  Scholar's Terminal - Quick Launch
echo ========================================
echo.
echo Starting Scholar's Terminal...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.

REM Start backend in new window with full path
start "Scholar's Terminal - Backend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && uvicorn Scholars_api:app --reload --host 0.0.0.0 --port 8000"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window with full path
start "Scholar's Terminal - Frontend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend && npm run dev"

REM Wait 5 seconds for frontend to start
timeout /t 5 /nobreak >nul

REM Open browser
echo Opening browser...
start http://localhost:5173

echo.
echo ========================================
echo Scholar's Terminal is now running!
echo.
echo Backend window: Check for errors
echo Frontend window: Shows Vite dev server
echo Browser: Should open automatically
echo.
echo Press any key to close this launcher window...
pause >nul
