@echo off
REM Simple build script without icon
REM Use this if you don't have an icon file

echo ================================================
echo AnomRecorder Simple Build Script
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

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile ^
    --windowed ^
    --name AnomRecorder ^
    usb_cam_viewer.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build completed successfully!
echo Executable location: dist\AnomRecorder.exe
echo ================================================
pause
