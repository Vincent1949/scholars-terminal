@echo off
echo ========================================
echo  Rebuilding Frontend
echo ========================================
echo.
echo This will rebuild the React app...
echo.

cd D:\Claude\Projects\scholars-terminal\frontend

echo Cleaning old build...
if exist dist rmdir /s /q dist

echo Building...
call npm run build

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo The frontend is now ready in the dist folder.
echo You can now run FINAL_LAUNCH.bat
echo.
pause
