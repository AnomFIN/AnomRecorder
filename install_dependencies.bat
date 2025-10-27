@echo off
REM Install dependencies for AnomRecorder

echo ================================================
echo Installing AnomRecorder Dependencies
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

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo Dependencies installed successfully!
echo You can now run: python usb_cam_viewer.py
echo ================================================
pause
