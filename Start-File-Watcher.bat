@echo off
echo ========================================
echo  Scholar's Terminal - File Watcher
echo ========================================
echo.

cd /d D:\Claude\Projects\scholars-terminal

echo Monitoring:  D:\Books and D:\GitHub
echo Database:    D:\Claude\Projects\scholars-terminal\data\vector_db
echo Log file:    D:\Claude\Projects\scholars-terminal\logs\watcher.log
echo.
echo Press Ctrl+C to stop the watcher.
echo.

python file_watcher.py

pause
