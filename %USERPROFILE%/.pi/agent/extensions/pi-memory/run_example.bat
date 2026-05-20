@echo off
chcp 65001 >nul
title Pi Memory 运行示例

echo ============================================================
echo   Pi Memory 运行示例
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] 检查依赖...
pip show redis psycopg2-binary >nul 2>&1
if errorlevel 1 (
    echo 安装依赖...
    pip install redis psycopg2-binary python-dotenv -q
)

echo [2/2] 运行示例...
python examples\basic_usage.py

echo.
pause
