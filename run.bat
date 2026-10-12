@echo off
setlocal
echo ============================================================
echo   ReimburseAI - Expense ^& Reimbursement Assistant (Windows)
echo ============================================================

cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 is not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: Create and activate virtual environment if not present
if not exist ".venv" (
    echo [*] Creating Python virtual environment in .venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

:: Install dependencies if needed
python -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing required dependencies from requirements.txt...
    pip install -r requirements.txt
)

:: Run the dynamic runner
python run.py %*
pause
