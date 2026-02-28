@echo off
REM ============================================
REM Scholar's Terminal - Database Builder
REM ============================================

echo.
echo ============================================
echo Scholar's Terminal - Database Builder
echo ============================================
echo.
echo This will build your knowledge base from
echo the sources configured in database_config.yaml
echo.
echo Press Ctrl+C to cancel, or
pause
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if config file exists
if not exist database_config.yaml (
    echo Error: database_config.yaml not found
    echo Please create the configuration file first
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import yaml" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install pyyaml chromadb pypdf2 tqdm
    echo.
)

REM Run the builder
echo Starting database build...
echo.
python build_database.py

echo.
echo ============================================
if errorlevel 1 (
    echo Build failed! Check database_build.log
) else (
    echo Build complete!
    echo Your knowledge base is ready to use.
)
echo ============================================
echo.
pause
