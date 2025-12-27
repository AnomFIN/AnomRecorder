@echo off
REM ============================================================================
REM AnomRecorder Windows Installer - Bulletproof Batch Launcher
REM
REM This script provides a robust entry point for the Windows installer.
REM It handles PowerShell execution policy, provides fallbacks, and ensures
REM a professional user experience with zero manual intervention.
REM
REM Features:
REM - Auto-detects PowerShell availability
REM - Handles execution policy gracefully
REM - Falls back to Python installer if needed
REM - Never crashes - comprehensive error handling
REM - Professional error messages
REM ============================================================================

setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%install.ps1"
set "PY_SCRIPT=%SCRIPT_DIR%install.py"
set "LOG_FILE=%SCRIPT_DIR%installer.log"

REM Initialize error flag
set "ERROR_OCCURRED=0"

REM Clear screen for clean presentation
cls

REM Display banner
echo.
echo ============================================================================
echo                 AnomRecorder Windows Installer
echo ============================================================================
echo.
echo         Automated installation of AnomRecorder
echo         This will install all dependencies and set up the application
echo.
echo ============================================================================
echo.

REM Log start time
echo [%DATE% %TIME%] Installation started >> "%LOG_FILE%" 2>nul

REM Check if PowerShell is available
echo [1/5] Checking for PowerShell...
where pwsh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PS_COMMAND=pwsh"
    echo      Found PowerShell Core ^(pwsh^)
    goto :CHECK_EXECUTION_POLICY
)

where powershell >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PS_COMMAND=powershell"
    echo      Found Windows PowerShell
    goto :CHECK_EXECUTION_POLICY
)

REM PowerShell not found, try Python fallback
echo      PowerShell not found, using Python installer fallback
goto :PYTHON_FALLBACK

:CHECK_EXECUTION_POLICY
REM Check PowerShell execution policy
echo.
echo [2/5] Checking PowerShell execution policy...

%PS_COMMAND% -NoProfile -ExecutionPolicy Bypass -Command "Write-Host '     PowerShell is accessible'" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo      WARNING: PowerShell execution policy may be restricted
    echo      Attempting to bypass for this session...
    echo [%DATE% %TIME%] PowerShell execution policy restricted, using bypass >> "%LOG_FILE%" 2>nul
)

:RUN_POWERSHELL
REM Run PowerShell installer
echo.
echo [3/5] Running PowerShell installer...
echo      This may take several minutes...
echo.

REM Try to run PowerShell script with execution policy bypass
REM Capture output for better debugging
%PS_COMMAND% -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================================
    echo      Installation completed successfully!
    echo ============================================================================
    goto :SUCCESS
)

REM If PowerShell failed, try Python fallback
echo.
echo      PowerShell installer encountered an issue (exit code: %ERRORLEVEL%)
echo      Check installer.log for details
echo      Falling back to Python installer...
echo [%DATE% %TIME%] PowerShell installer failed with code %ERRORLEVEL%, falling back to Python >> "%LOG_FILE%" 2>nul

:PYTHON_FALLBACK
REM Check if Python is available
echo.
echo [3/5] Checking for Python...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================================
    echo      ERROR: Python is not installed or not in PATH
    echo ============================================================================
    echo.
    echo      Python 3.8 or higher is required to install AnomRecorder.
    echo.
    echo      Please install Python from: https://www.python.org/downloads/
    echo.
    echo      Make sure to check "Add Python to PATH" during installation!
    echo.
    echo ============================================================================
    set "ERROR_OCCURRED=1"
    goto :ERROR_EXIT
)

echo      Python is available
echo [%DATE% %TIME%] Using Python installer >> "%LOG_FILE%" 2>nul

REM Check if Python installer exists
if not exist "%PY_SCRIPT%" (
    echo.
    echo ============================================================================
    echo      ERROR: Python installer script not found
    echo ============================================================================
    echo.
    echo      Expected location: %PY_SCRIPT%
    echo.
    echo      Please ensure you have the complete AnomRecorder package.
    echo.
    echo ============================================================================
    set "ERROR_OCCURRED=1"
    goto :ERROR_EXIT
)

REM Run Python installer
echo.
echo [4/5] Running Python installer...
echo      This may take several minutes...
echo.

python "%PY_SCRIPT%" --venv
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================================================
    echo      ERROR: Python installer failed
    echo ============================================================================
    echo.
    echo      The installation encountered errors.
    echo.
    echo      Troubleshooting steps:
    echo      1. Check your internet connection
    echo      2. Ensure you have Python 3.8 or higher
    echo      3. Try running as Administrator
    echo      4. Check the log file: %LOG_FILE%
    echo.
    echo      For detailed error information, run:
    echo      python install.py --venv
    echo.
    echo ============================================================================
    set "ERROR_OCCURRED=1"
    goto :ERROR_EXIT
)

:SUCCESS
echo.
echo [5/5] Installation complete!
echo.
echo ============================================================================
echo      AnomRecorder has been installed successfully!
echo ============================================================================
echo.
echo      To run AnomRecorder:
echo        - Double-click: run.bat
echo        - Or run: python usb_cam_viewer.py
echo.
echo      Installation log: %LOG_FILE%
echo.
echo ============================================================================
echo.
echo [%DATE% %TIME%] Installation completed successfully >> "%LOG_FILE%" 2>nul

REM Prompt to start application
set /p "LAUNCH=Would you like to start AnomRecorder now? (Y/n): "
if /i "!LAUNCH!"=="y" goto :LAUNCH_APP
if /i "!LAUNCH!"=="" goto :LAUNCH_APP
goto :NORMAL_EXIT

:LAUNCH_APP
echo.
echo Starting AnomRecorder...
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    start "" "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%usb_cam_viewer.py"
) else (
    start "" python "%SCRIPT_DIR%usb_cam_viewer.py"
)
echo.
echo Application launched!
goto :NORMAL_EXIT

:ERROR_EXIT
echo.
echo [%DATE% %TIME%] Installation failed with errors >> "%LOG_FILE%" 2>nul
pause
exit /b 1

:NORMAL_EXIT
echo.
echo Press any key to exit...
pause >nul
exit /b 0
