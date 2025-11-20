@echo off
echo ========================================
echo MFA Authentication System Setup
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    echo Download the LTS version and restart your terminal.
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Node.js version:
node --version
echo.
echo Python version:
python --version
echo.

echo ========================================
echo Setting up Backend...
echo ========================================
cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Setting up environment file...
if not exist .env copy .env.example .env

echo Creating database...
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created!')"

cd ..

echo.
echo ========================================
echo Setting up Frontend...
echo ========================================
cd frontend

echo Installing Node.js dependencies...
call npm install

echo Setting up environment file...
if not exist .env copy .env.example .env

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo 1. Open terminal and run: cd backend && venv\Scripts\activate && python app.py
echo 2. Open another terminal and run: cd frontend && npm start
echo.
echo Or run start-windows.bat
echo.
pause
