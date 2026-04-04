@echo off
REM Windows batch script to run PC Audio Monitor
REM This script handles activation of Python virtual environment if it exists

cd /d "%~dp0"

echo.
echo ========================================
echo PC Audio Monitor - Home Assistant
echo ========================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please copy .env.example to .env and configure:
    echo   1. HA_HOST = your Home Assistant IP
    echo   2. HA_TOKEN = your API token
    echo.
    echo See SETUP.md for detailed instructions.
    echo.
    pause
    exit /b 1
)

REM Check if HA_TOKEN is configured
for /f "tokens=*" %%i in ('type .env ^| find /v "^REM" ^| find "HA_TOKEN="') do set line=%%i
if "%line%"=="" (
    echo WARNING: HA_TOKEN not configured in .env
    echo Alerts will not be sent to Home Assistant
    echo.
)

REM Try to activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the app
python main.py

REM Keep window open on exit for error messages
if errorlevel 1 (
    echo.
    echo ERROR: Application exited with an error
    echo Check pc_audio_monitor.log for details
    echo.
    pause
)

exit /b %errorlevel%
