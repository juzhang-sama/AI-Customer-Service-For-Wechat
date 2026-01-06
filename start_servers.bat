@echo off
chcp 65001 >nul
title dt-ai-helper-starter
setlocal enabledelayedexpansion

echo.
echo ========================================
echo      dt-ai-helper - 生产级启动器
echo ========================================
echo.

cd /d "%~dp0"

REM 1. 清理冲突进程
echo [1/4] 正在清理旧的进程...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 1 >nul

REM 2. 检查 Python 环境
echo [2/4] 检查后端运行环境...
if exist .venv\Scripts\activate.bat (
    echo [OK] Python 虚拟环境正常.
) else (
    echo [ERROR] 未找到 .venv 文件夹! 
    echo 请先运行: python -m venv .venv
    pause
    exit /b 1
)

REM 3. 检查 Node.js 环境
echo [3/4] 检查前端运行环境...
if exist node_modules (
    echo [OK] 依赖库 (node_modules) 正常.
) else (
    echo [WARNING] 未找到 node_modules, 正在尝试自动安装 (npm install)...
    call npm install
)

REM 4. 启动服务
echo.
echo [4/4] 正在启动全量服务...

REM 启动后端并重定向日志
if not exist logs mkdir logs
echo 正在启动后端 (Port 5000)...
start "Backend - Flask" cmd /c "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python python\api_server.py > logs\backend.log 2>&1"

timeout /t 3 >nul

echo 正在启动前端 (Port 5173)...
start "Frontend - Vite" cmd /c "cd /d "%~dp0" && npm run dev > logs\frontend.log 2>&1"

echo.
echo ========================================
echo      服务已进入后台运行状态
echo ========================================
echo.
echo 后端访问地址:  http://localhost:5000
echo 前端访问地址:  http://localhost:5173
echo.
echo 实时日志请查看: logs/ 目录
echo.
echo 【提示】请不要关闭弹出的两个黑窗口。
echo.
pause

