@echo off
REM Research Scanner Quick Test
REM Tests the research scanner integration

echo.
echo ========================================
echo  RESEARCH SCANNER INTEGRATION TEST
echo ========================================
echo.

REM Test 1: Check Python dependencies
echo [1/4] Checking dependencies...
python -c "import apscheduler; import sentence_transformers; print('  ✓ Dependencies installed')" 2>nul
if errorlevel 1 (
    echo   ✗ Missing dependencies!
    echo   Run: pip install apscheduler sentence-transformers
    pause
    exit /b 1
)

REM Test 2: Test source connectivity
echo [2/4] Testing research sources...
cd research_scanner
python scanner.py test-sources
if errorlevel 1 (
    echo   ✗ Source test failed!
    pause
    exit /b 1
)
cd ..

REM Test 3: Check scanner status
echo [3/4] Checking scanner configuration...
cd research_scanner
python scanner.py status
cd ..

REM Test 4: Verify API integration
echo [4/4] Checking if API file is ready...
if exist "frontend\src\Scholars_api_integrated.py" (
    echo   ✓ Integrated API file created
    echo.
    echo   To activate:
    echo   1. Backup: copy frontend\src\Scholars_api.py frontend\src\Scholars_api_BACKUP.py
    echo   2. Replace: copy frontend\src\Scholars_api_integrated.py frontend\src\Scholars_api.py
    echo   3. Start: python frontend\src\Scholars_api.py
) else (
    echo   ✗ Integrated API file not found!
)

echo.
echo ========================================
echo  TEST COMPLETE
echo ========================================
echo.
echo Next steps:
echo   1. Review: RESEARCH_SCANNER_SETUP.md
echo   2. Install dependencies if needed
echo   3. Replace Scholars_api.py with integrated version
echo   4. Start backend and test endpoints
echo.
pause
