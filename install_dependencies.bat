@echo off
REM Install dependencies for AnomRecorder
REM This script now uses the new install.py with reactive GUI

echo ================================================
echo Installing AnomRecorder
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Launching installer...
python install.py

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    pause
    exit /b 1
)

pause
