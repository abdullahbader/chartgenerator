@echo off
echo Starting Charts Generator...
echo.
cd /d "%~dp0backend"
start "Charts Generator Backend" cmd /k "python app.py"
echo Waiting for server to start...
timeout /t 3 /nobreak >nul
start "" http://localhost:5000
echo.
echo Browser opened. Keep the "Charts Generator Backend" window open while using the app.
pause
