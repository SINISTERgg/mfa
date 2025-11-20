@echo off
echo Starting MFA Authentication System...
echo.

REM Start backend
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Close the server windows to stop the application.
echo.

