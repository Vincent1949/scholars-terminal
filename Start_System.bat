@echo off
REM Scholar's Terminal - Unified Knowledge Chatbot Launcher
REM Updated: January 2026

echo ============================================================
echo        SCHOLAR'S TERMINAL - Knowledge Chatbot System
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo Python found
echo.

REM Check if virtual environment exists
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found - using system Python
    echo (Optional: Run 'python -m venv venv' to create one)
)

echo.
echo Starting Scholar's Terminal...
echo The system will:
echo   1. Check Ollama status
echo   2. Update vector databases in background
echo   3. Launch the Gradio web interface
echo.

REM Start the unified chatbot system
python start_chatbot.py

echo.
echo Goodbye!
pause
