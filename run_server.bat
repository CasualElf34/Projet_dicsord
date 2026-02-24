@echo off
echo ============================================
echo  LIKOO SERVER LAUNCHER
echo ============================================
cd /d "%~dp0"
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Installing/updating dependencies...
pip install --upgrade -r requirements.txt
echo.
echo ============================================
echo  Starting server...
echo ============================================
python server.py
pause
