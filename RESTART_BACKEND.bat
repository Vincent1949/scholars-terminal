@echo off
cd /d D:\Claude\Projects\scholars-terminal\frontend\src
echo Starting Scholar's Terminal Backend...
uvicorn Scholars_api:app --reload --host 127.0.0.1 --port 8000
pause
