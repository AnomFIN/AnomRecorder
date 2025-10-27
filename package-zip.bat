@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build EXE and package it into a zip ready to share
REM Requires: Windows with Python 3.9+ and PowerShell (Compress-Archive)

cd /d %~dp0\..

call scripts\build-windows-exe.bat || goto :err

if not exist release mkdir release
if exist stage rmdir /s /q stage
mkdir stage

REM Collect files into staging folder
copy /y dist\Kamerajarjestelma.exe stage\ >nul
if exist README_windows_camera.md copy /y README_windows_camera.md stage\ >nul
if exist logo.png copy /y logo.png stage\ >nul

REM Include local models if present
if exist models (
  xcopy /e /i /y models stage\models\ >nul
)

REM Create zip using PowerShell Compress-Archive
powershell -NoProfile -Command "Compress-Archive -Path 'stage\*' -DestinationPath 'release\kamera_final.zip' -Force" || goto :err

echo.
echo Packaged: release\kamera_final.zip
echo Share this zip. On the target PC: unzip, then run Kamerajarjestelma.exe

REM Cleanup staging
rmdir /s /q stage

exit /b 0

:err
echo Packaging failed. See errors above.
exit /b 1
