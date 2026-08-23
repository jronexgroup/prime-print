@echo off
echo ==========================================
echo   Runova Print Agent Setup
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo [3/3] Starting agent...
echo.
echo ==========================================
echo   Enter your server URL (default: http://localhost:8000)
echo ==========================================
set /p SERVER="Server URL: "
if "%SERVER%"=="" set SERVER=http://localhost:8000

python runova_agent.py --server %SERVER%

pause
