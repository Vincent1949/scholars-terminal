@echo off
echo ========================================
echo  Scholar's Terminal v3.0 - Multi-DB
echo  (IPv4 Only Mode)
echo ========================================
echo.

REM Force Node.js to use IPv4 only
set NODE_OPTIONS=--dns-result-order=ipv4first

echo Starting with IPv4-only mode...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8080
echo.

REM Start backend in new window
start "Scholar's Terminal - Backend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && set NODE_OPTIONS=--dns-result-order=ipv4first && uvicorn Scholars_api:app --reload --host 127.0.0.1 --port 8000"

REM Wait 3 seconds
timeout /t 3 /nobreak >nul

REM Start frontend in new window with IPv4 forced
start "Scholar's Terminal - Frontend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend && set NODE_OPTIONS=--dns-result-order=ipv4first && npm run dev"

REM Wait 5 seconds
timeout /t 5 /nobreak >nul

echo Opening browser...
start http://127.0.0.1:8080

echo.
echo ========================================
echo If you still get permission errors:
echo   1. Run this .bat file as Administrator
echo   2. Check Windows Firewall settings
echo   3. Check IObit Malware Fighter
echo ========================================
echo.
pause
