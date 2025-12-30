@echo off
echo ========================================
echo Powerball Dev Panel Launcher
echo ========================================
echo.
echo Starting Dev Panel via WSL (for SSH key access)...
echo Installing dependencies if needed...
echo.

REM Run via WSL, install flask (use --break-system-packages for newer Python)
wsl -e bash -c "pip3 install --break-system-packages -q flask 2>/dev/null || pip3 install -q flask 2>/dev/null || true; cd /mnt/s/py/powerball_simulator && python3 dev_panel.py"

echo.
echo Open http://localhost:5050 in your browser
pause
