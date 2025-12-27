@echo off
REM Quick run script for AnomRecorder
REM Automatically uses virtual environment if available

echo Starting AnomRecorder...

REM Check if venv exists, use it if available
if exist "%~dp0.venv\Scripts\python.exe" (
    echo Using virtual environment...
    "%~dp0.venv\Scripts\python.exe" "%~dp0usb_cam_viewer.py"
) else (
    python "%~dp0usb_cam_viewer.py"
)

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Make sure dependencies are installed.
    echo Run: install.bat
    pause
)
