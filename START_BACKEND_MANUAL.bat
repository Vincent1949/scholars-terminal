@echo off
echo ========================================
echo  Starting Scholar's Terminal Backend
echo ========================================
echo.
cd /d D:\Claude\Projects\scholars-terminal\frontend\src
echo Current directory: %CD%
echo.
echo Starting uvicorn...
echo.
uvicorn Scholars_api:app --reload --host 127.0.0.1 --port 8000
pause
