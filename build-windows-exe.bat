@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build standalone Windows .exe for USB Camera Viewer
REM Requirements: Python 3.9+ installed (py launcher)

cd /d %~dp0

if not exist .venv (
  echo Creating virtual environment...
  py -3 -m venv .venv
)

call .venv\Scripts\activate

echo Installing dependencies...
pip install --upgrade pip >nul
pip install opencv-python pillow pyinstaller requests

set ADD_DATA=
if exist models (
  echo Bundling local models/ directory.
  set ADD_DATA=--add-data models;models
)

echo Building EXE...
set VERSION_FILE=scripts\version_info.txt
if exist %VERSION_FILE% (
  pyinstaller --clean -F -w usb_cam_viewer.py --name "Kamerajarjestelma" %ADD_DATA% --version-file %VERSION_FILE%
) else (
  pyinstaller --clean -F -w usb_cam_viewer.py --name "Kamerajarjestelma" %ADD_DATA%
)

echo.
echo Build complete. EXE at: dist\Kamerajarjestelma.exe
echo Double-click to run. The app lists USB cameras and plays livestream.

endlocal
