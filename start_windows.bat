@echo off
REM Quick start script for Windows

echo Starting Nonprofit Intelligence Platform...
echo ================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/upgrade pip
echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
pip install -r requirements.txt >nul 2>&1

REM Start the application
echo ================================================
echo Starting application...
echo Access at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ================================================
echo Press Ctrl+C to stop the server
echo.

REM Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
