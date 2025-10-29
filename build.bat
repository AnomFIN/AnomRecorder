@echo off
REM Build script for AnomRecorder - Creates standalone executable
REM Requires PyInstaller to be installed

echo ================================================
echo AnomRecorder Build Script
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
echo Converting logo to ICO format...
python convert_logo_to_ico.py

echo.
echo Building executable...
pyinstaller --onefile ^
    --windowed ^
    --name AnomRecorder ^
    --icon=logo.ico ^
    --add-data "config.json;." ^
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
echo Icon: logo.ico
echo ================================================
pause
