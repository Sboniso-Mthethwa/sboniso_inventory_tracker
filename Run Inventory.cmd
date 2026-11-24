@echo off
setlocal
set "runtime=%LOCALAPPDATA%\FletRuntimes\inventory-0.28.3\Scripts\python.exe"
if not exist "%runtime%" (
    echo The Inventory Tracker runtime is missing for this Windows account.
    pause
    exit /b 1
)
"%runtime%" -B "%~dp0main.py"
if errorlevel 1 (
    pause
    exit /b 1
)
