@echo off
chcp 65001 >nul
title dt-ai-helper-starter

echo.
echo ========================================
echo      dt-ai-helper - One-Click Start
echo ========================================
echo.

cd /d "%~dp0"

REM Cleanup old processes to avoid port conflicts
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

REM Check environment
if exist .venv\Scripts\activate.bat (
    echo [OK] Python environment found.
) else (
    echo [ERROR] .venv folder not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Check backend
if exist python\api_server.py (
    echo [OK] Backend script found.
) else (
    echo [ERROR] python\api_server.py not found!
    pause
    exit /b 1
)

echo.
echo [1/2] Starting Backend (Flask)...
start "Backend - Port 5000" cmd /c "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python python\api_server.py"

timeout /t 3 >nul

echo [2/2] Starting Frontend (Vite)...
start "Frontend - Port 5173" cmd /c "cd /d "%~dp0" && npm run dev"

echo.
echo ========================================
echo      Services are starting...
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Done! Please keep the command windows open.
echo.
pause

