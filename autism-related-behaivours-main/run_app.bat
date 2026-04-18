@echo off
echo ===================================================
echo Starting Autism Behavior Recognition System
echo ===================================================

if not exist venv\Scripts\activate.bat (
    echo Error: Virtual environment not found.
    echo Please run install.bat first!
    pause
    exit /b 1
)

call venv\Scripts\activate
python desktop_app.py
pause
