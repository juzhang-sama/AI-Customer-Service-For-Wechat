@echo off
chcp 65001 >nul
title 前端服务 - Vite

echo.
echo ========================================
echo      前端服务器 (Vite)
echo ========================================
echo.

cd /d "%~dp0"

echo ========================================
echo      启动 Vite 开发服务器
echo ========================================
echo.
echo 地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

npm run dev

pause

