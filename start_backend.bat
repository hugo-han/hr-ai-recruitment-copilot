@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0backend"

echo [1/5] Check port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo   WARNING: port 8000 already in use (PID %%a)
)
echo.

echo [2/5] Clean old database...
if exist local_dev.db del /f local_dev.db
if exist .obs-local rmdir /s /q .obs-local
echo   OK

echo [3/5] Run alembic migrations...
set DATABASE_URL=sqlite:///./local_dev.db
set PYTHONPATH=%cd%
call .venv\Scripts\activate.bat
alembic upgrade head
if errorlevel 1 (
    echo   ALBEMIC FAILED
    pause
    exit /b 1
)
echo   OK

echo [4/5] Seed test users...
python seed.py
if errorlevel 1 (
    echo   SEED FAILED
    pause
    exit /b 1
)

echo [5/5] Start backend in new window...
start "hr-backend" cmd /c "cd /d %cd% && call .venv\Scripts\activate.bat && set DATABASE_URL=sqlite:///./local_dev.db && set PYTHONPATH=%cd% && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Waiting 5 sec...
ping -n 6 127.0.0.1 >nul

echo --- health ---
curl -s http://localhost:8000/api/health
echo.
echo --- login (hr/hr123) ---
curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"hr\",\"password\":\"hr123\"}"
echo.
echo ==========================================
echo  Backend: http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo.
echo  Test accounts:
echo    admin       / admin123
echo    hr          / hr123
echo    hr_lead     / lead123
echo    interviewer / iv123
echo ==========================================
pause
