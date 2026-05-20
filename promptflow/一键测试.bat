@echo off
chcp 65001 >nul
title 电信橙分期话术与标签测试

echo ============================================================
echo   电信橙分期话术与标签优化系统
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/3] 运行测试...
python run_all.py

echo.
echo [3/3] 完成！
echo.
echo ============================================================
echo   报告已生成到 reports/ 目录
echo ============================================================
echo.
pause
