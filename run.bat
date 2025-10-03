@echo off
title Claude Session Manager
echo Starting Claude Session Manager...
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.7+
    pause
    exit /b 1
)

REM Check if main file exists
if not exist "main_application.py" (
    echo ERROR: main_application.py not found!
    echo Please make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import psutil, win32gui, tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Some required packages might be missing.
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Create data directories if they don't exist
if not exist "claude_session_data" (
    echo Creating data directories...
    mkdir claude_session_data
    mkdir claude_session_data\logs
    mkdir claude_session_data\sessions
    mkdir claude_session_data\tokens
    mkdir claude_session_data\confirmations
    mkdir claude_session_data\backups
)

echo.
echo Starting Claude Session Manager...
echo Close this window to exit the application.
echo.

REM Run the launcher (safer than direct main app)
python simple_launcher.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code: %errorlevel%
    echo Check the console output above for error details.
    pause
)

echo.
echo Claude Session Manager closed.
pause