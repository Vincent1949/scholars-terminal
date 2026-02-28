@echo off
echo ========================================
echo  Scholar's Terminal v3.0 - Multi-DB
echo ========================================
echo.
echo Starting Scholar's Terminal with Multi-Database Support...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:3000
echo.
echo Databases:
echo   - Scholar's Terminal DB (books, research papers)
echo   - RAG DB (newsletters, knowledge base)
echo.

REM Start backend in new window with full path
start "Scholar's Terminal - Backend (Multi-DB)" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend\src && uvicorn Scholars_api:app --reload --host 127.0.0.1 --port 8000"

REM Wait 5 seconds for backend to fully start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend in new window with full path
start "Scholar's Terminal - Frontend" cmd /k "cd /d D:\Claude\Projects\scholars-terminal\frontend && npm run dev"

REM Wait 10 seconds for frontend to start (longer delay for Vite)
echo Waiting for frontend to start...
timeout /t 10 /nobreak >nul

REM Open browser
echo Opening browser...
start http://127.0.0.1:3000

echo.
echo ========================================
echo Scholar's Terminal v3.0 is now running!
echo.
echo Backend window: Check database connections
echo Frontend window: Shows Vite dev server
echo Browser: Opens at http://127.0.0.1:3000
echo.
echo MULTI-DATABASE FEATURES:
echo   - Search across both databases
echo   - Filter by database (Scholar's Terminal / RAG DB)
echo   - Filter by source (books, newsletters, research)
echo   - Combined results from all sources
echo.
echo If port issues persist, run as Administrator
echo.
echo Press any key to close this launcher window...
pause >nul
