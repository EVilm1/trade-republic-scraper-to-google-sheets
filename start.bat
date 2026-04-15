@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ❌ python.exe not found
    pause
    exit /b
)
.venv\Scripts\python.exe main.py
pause