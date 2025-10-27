@echo off
REM Clean build artifacts and generated files

echo Cleaning build artifacts...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist *.spec del /q *.spec

echo Clean completed!
pause
