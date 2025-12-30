@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build standalone Windows .exe for USB Camera Viewer
REM Requirements: Python 3.9+ installed (py launcher)

cd /d %~dp0\..

if not exist .venv (
  echo Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.9+ is installed
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate
if errorlevel 1 (
  echo ERROR: Failed to activate virtual environment
  pause
  exit /b 1
)

echo Installing dependencies...
pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: Failed to upgrade pip
  pause
  exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Failed to install dependencies
  pause
  exit /b 1
)

set ADD_DATA=--add-data "config.json;." --add-data "settings.json;." --add-data "logo.png;." --add-data "logo_256.png;." --add-data "src;src"

if exist models (
  echo Bundling local models/ directory.
  set ADD_DATA=%ADD_DATA% --add-data models;models
)

REM Prepare icon file
set ICON_FILE=logo.ico
if not exist %ICON_FILE% set ICON_FILE=app.ico

echo Building EXE...
set VERSION_FILE=scripts\version_info.txt
if exist %VERSION_FILE% (
  pyinstaller --clean -F -w usb_cam_viewer.py --name "Kamerajarjestelma" ^
    --icon=%ICON_FILE% ^
    %ADD_DATA% ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=tkinter ^
    --hidden-import=sounddevice ^
    --hidden-import=watchdog ^
    --hidden-import=send2trash ^
    --collect-all sounddevice ^
    --version-file=%VERSION_FILE%
) else (
  pyinstaller --clean -F -w usb_cam_viewer.py --name "Kamerajarjestelma" ^
    --icon=%ICON_FILE% ^
    %ADD_DATA% ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=tkinter ^
    --hidden-import=sounddevice ^
    --hidden-import=watchdog ^
    --hidden-import=send2trash ^
    --collect-all sounddevice
)

if errorlevel 1 (
  echo.
  echo ERROR: Build failed!
  echo Check the error messages above for details.
  pause
  exit /b 1
)

echo.
echo ================================================
echo Build complete. EXE at: dist\Kamerajarjestelma.exe
echo Double-click to run. The app lists USB cameras and plays livestream.
echo ================================================
pause

endlocal
