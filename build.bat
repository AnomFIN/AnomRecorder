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

echo.
echo Building executable...

REM Prepare PyInstaller command with all necessary options
set "ICON_FILE=logo.ico"
if not exist "%ICON_FILE%" (
  set "ICON_FILE=app.ico"
)

if not exist "%ICON_FILE%" (
  echo ERROR: No icon file found. Expected "logo.ico" or "app.ico" in %cd%.
  pause
  exit /b 1
)

REM Build with hidden imports and data files
pyinstaller --onefile ^
    --windowed ^
    --name AnomRecorder ^
    --icon=%ICON_FILE% ^
    --add-data "config.json;." ^
    --add-data "settings.json;." ^
    --add-data "logo.png;." ^
    --add-data "logo_256.png;." ^
    --add-data "src;src" ^
    --hidden-import=PIL ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=numpy._core ^
    --hidden-import=numpy._core._multiarray_umath ^
    --hidden-import=tkinter ^
    --hidden-import=sounddevice ^
    --hidden-import=watchdog ^
    --hidden-import=send2trash ^
    --collect-all sounddevice ^
    --collect-all numpy ^
    usb_cam_viewer.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above for details.
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build completed successfully!
echo Executable location: dist\AnomRecorder.exe
echo ================================================
pause
