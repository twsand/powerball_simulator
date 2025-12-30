@echo off
echo ========================================
echo Powerball Dev Panel Launcher
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing Flask...
    pip install flask flask-socketio
)

echo Starting Dev Panel...
echo.
echo Open http://localhost:5050 in your browser
echo.
python dev_panel.py
pause
