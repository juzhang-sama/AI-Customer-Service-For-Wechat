@echo off
chcp 65001 >nul
title 后端服务 - Flask

echo.
echo ========================================
echo      后端服务器 (Flask)
echo ========================================
echo.

cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    echo [OK] 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] 虚拟环境不存在
    pause
    exit /b 1
)

echo.
echo ========================================
echo      启动 Flask 服务器
echo ========================================
echo.
echo 地址: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python python\api_server.py

pause

