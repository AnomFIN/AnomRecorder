@echo off
REM Install dependencies for AnomRecorder
REM This script redirects to the new robust installer

echo ================================================
echo Installing AnomRecorder
echo ================================================
echo.
echo Launching enhanced installer...
echo.

REM Call the new robust installer
call "%~dp0install.bat"

exit /b %ERRORLEVEL%
