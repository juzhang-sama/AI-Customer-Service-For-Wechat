@echo off
chcp 65001 >nul
title dt-ai-helper-starter
setlocal enabledelayedexpansion

echo.
echo ========================================
echo      dt-ai-helper - Server Starter
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM Cleanup old processes
echo [1/4] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 1 >nul

REM Check Python environment
echo [2/4] Checking backend environment...
if exist .venv\Scripts\activate.bat (
    echo [OK] Python venv found.
) else (
    echo [ERROR] .venv folder not found! 
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Check Node.js environment
echo [3/4] Checking frontend environment...
if exist node_modules (
    echo [OK] node_modules found.
) else (
    echo [WARNING] node_modules not found, installing...
    call npm install
)

REM Start services
echo.
echo [4/4] Starting services...

if not exist logs mkdir logs

echo Starting Backend (Port 5000)...
start "Backend - Flask" cmd /k "cd /d "%PROJECT_ROOT%" && call .venv\Scripts\activate.bat && python python\api_server.py"

timeout /t 3 >nul

echo Starting Frontend (Port 5173)...
start "Frontend - Vite" cmd /c "cd /d "%PROJECT_ROOT%" && npm run dev > logs\frontend.log 2>&1"

echo.
echo ========================================
echo      Services are running in background
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Logs are in logs/ directory
echo.
echo [TIP] Please do not close the two popup windows.
echo.
pause

