@echo off
cd /d %~dp0

if not exist .venv (
    echo [1/5] Creating virtual environment with Python 3.11...
    py -3.11 -m venv .venv
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing backend dependencies...
pip install -r requirements.txt

echo [5/5] Starting backend server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause