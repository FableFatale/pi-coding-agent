@echo off
chcp 65001 >nul
title Pi Memory 初始化

echo ============================================================
echo   Pi Memory 数据库初始化
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装Python
    pause
    exit /b 1
)

echo [2/4] 安装依赖...
pip install -e . -q
if errorlevel 1 (
    echo [错误] 安装失败
    pause
    exit /b 1
)
echo [OK] 依赖安装完成

echo.
echo [3/4] 初始化数据库...
python init_db.py

echo.
echo [4/4] 完成！
echo.
pause
