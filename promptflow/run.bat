@echo off
cd /d %~dp0
title PromptFlow

echo ============================================================
echo  PromptFlow - Prompt Workflow Validator
echo ============================================================
echo.

REM 安装依赖
echo [1/3] Installing dependencies...
pip install networkx -q
if errorlevel 1 (
    echo Error: Failed to install networkx
    pause
    exit /b 1
)
echo    OK

REM 运行 CLI
echo.
echo [2/3] Running CLI...
echo.

REM 检查是否提供了参数
if "%~1"=="" (
    echo Usage:
    echo   run.bat "C:\path\to\prompt.md"
    echo   run.bat prompt.md --run-tests
    echo   run.bat prompt.md --export html -o report.html
    echo.
    echo Press any key to run demo with sample prompt...
    pause >nul
    set "PROMPT_FILE=sample_prompt.md"
) else (
    set "PROMPT_FILE=%*"
)

python cli_run.py %PROMPT_FILE% -v

echo.
echo [3/3] Complete!
echo.
pause
