@echo off
chcp 65001 >nul
title 停止所有服务

echo.
echo ========================================
echo      停止所有服务
echo ========================================
echo.

echo 正在查找并停止服务...
echo.

REM 停止 Python 进程 (Flask 后端)
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [1/2] 停止后端服务 (Python)...
    taskkill /F /IM python.exe >nul 2>&1
    echo       [OK] 后端服务已停止
) else (
    echo [1/2] 后端服务未运行
)

echo.

REM 停止 Node 进程 (Vite 前端)
tasklist /FI "IMAGENAME eq node.exe" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [2/2] 停止前端服务 (Node)...
    taskkill /F /IM node.exe >nul 2>&1
    echo       [OK] 前端服务已停止
) else (
    echo [2/2] 前端服务未运行
)

echo.
echo ========================================
echo      所有服务已停止
echo ========================================
echo.

pause

