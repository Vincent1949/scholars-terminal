@echo off
REM Ollama Auto-Start Script for Windows Startup
REM Place this in: C:\Users\[YourUsername]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup

title Ollama Service
echo Starting Ollama service...

REM Wait a bit for system to fully boot
timeout /t 15 /nobreak > nul

REM Start Ollama (this window will stay open minimized)
ollama serve

REM If Ollama exits, this script ends too
echo Ollama service stopped.
pause
