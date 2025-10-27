@echo off
REM Quick run script for AnomRecorder

echo Starting AnomRecorder...
python usb_cam_viewer.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Make sure dependencies are installed.
    echo Run: install_dependencies.bat
    pause
)
