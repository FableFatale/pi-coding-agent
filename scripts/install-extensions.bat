@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Pi Coding Agent - 扩展安装脚本
echo ========================================
echo.

set "PI_DIR=%USERPROFILE%\.pi\agent"
set "EXT_DIR=%PI_DIR%\extensions"
set "MEMORY_DIR=%PI_DIR%\memory"
set "PROFILE_DIR=%PI_DIR%\profile"
set "CACHE_DIR=%PI_DIR%\project-cache"

echo [1/8] 创建目录结构...
if not exist "%EXT_DIR%" mkdir "%EXT_DIR%"
if not exist "%MEMORY_DIR%" mkdir "%MEMORY_DIR%"
if not exist "%MEMORY_DIR%\notes" mkdir "%MEMORY_DIR%\notes"
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"
if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"

echo [2/8] 复制官方扩展...
xcopy /E /I /Y "%~dp0..\pi-subagents" "%EXT_DIR%\pi-subagents\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-messenger" "%EXT_DIR%\pi-messenger\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-mcp-adapter" "%EXT_DIR%\pi-mcp-adapter\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-web-access" "%EXT_DIR%\pi-web-access\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-btw" "%EXT_DIR%\pi-btw\" 2>nul

echo [3/8] 复制记忆系统扩展...
xcopy /E /I /Y "%~dp0..\pi-memory" "%EXT_DIR%\pi-memory\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-user-profile" "%EXT_DIR%\pi-user-profile\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-project-context" "%EXT_DIR%\pi-project-context\" 2>nul

echo [4/8] 复制工具扩展...
xcopy /E /I /Y "%~dp0..\pi-code-runner" "%EXT_DIR%\pi-code-runner\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-test-runner" "%EXT_DIR%\pi-test-runner\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-debugger" "%EXT_DIR%\pi-debugger\" 2>nul
xcopy /E /I /Y "%~dp0..\pi-deploy" "%EXT_DIR%\pi-deploy\" 2>nul

echo [5/8] 创建记忆系统文件...
if not exist "%MEMORY_DIR%\MEMORY.md" (
    echo # 核心记忆 > "%MEMORY_DIR%\MEMORY.md"
    echo. >> "%MEMORY_DIR%\MEMORY.md"
)
if not exist "%MEMORY_DIR%\HEARTBEAT.md" (
    echo # 心跳任务 > "%MEMORY_DIR%\HEARTBEAT.md"
    echo. >> "%MEMORY_DIR%\HEARTBEAT.md"
)
if not exist "%MEMORY_DIR%\TODO.md" (
    echo # 待办事项 > "%MEMORY_DIR%\TODO.md"
    echo. >> "%MEMORY_DIR%\TODO.md"
)

echo [6/8] 创建用户档案文件...
if not exist "%PROFILE_DIR%\USER.md" (
    echo --- > "%PROFILE_DIR%\USER.md"
    echo name:  >> "%PROFILE_DIR%\USER.md"
    echo timezone: Asia/Shanghai >> "%PROFILE_DIR%\USER.md"
    echo language: zh-CN >> "%PROFILE_DIR%\USER.md"
    echo platform: windows >> "%PROFILE_DIR%\USER.md"
    echo --- >> "%PROFILE_DIR%\USER.md"
    echo. >> "%PROFILE_DIR%\USER.md"
    echo # 关于用户 >> "%PROFILE_DIR%\USER.md"
)
if not exist "%PROFILE_DIR%\PREFERENCES.md" (
    echo # 用户偏好 > "%PROFILE_DIR%\PREFERENCES.md"
    echo. >> "%PROFILE_DIR%\PREFERENCES.md"
    echo ## 包管理器 >> "%PROFILE_DIR%\PREFERENCES.md"
    echo 优先级：pnpm ^> npm ^> yarn >> "%PROFILE_DIR%\PREFERENCES.md"
)
if not exist "%PROFILE_DIR%\HABITS.md" (
    echo # 使用习惯 > "%PROFILE_DIR%\HABITS.md"
    echo. >> "%PROFILE_DIR%\HABITS.md"
)

echo [7/8] 创建配置文件...
if not exist "%PI_DIR%\auth.json" (
    echo { } > "%PI_DIR%\auth.json"
)
if not exist "%PI_DIR%\models.json" (
    (
        echo {
        echo   "providers": {
        echo     "minimax": {
        echo       "baseUrl": "https://api.minimaxi.com/anthropic",
        echo       "api": "anthropic-messages",
        echo       "apiKey": "",
        echo       "models": [
        echo         {
        echo           "id": "MiniMax-M2.7-highspeed",
        echo           "input": ["text"],
        echo           "contextWindow": 204800,
        echo           "maxTokens": 32000
        echo         }
        echo       ]
        echo     }
        echo   }
        echo }
    ) > "%PI_DIR%\models.json"
)

echo [8/8] 安装 npm 依赖...
set "PATH=%ProgramFiles%\nodejs;%PATH%"
for /d %%d in ("%EXT_DIR%\pi-*") do (
    cd /d "%%d" 2>nul
    if exist "package.json" (
        echo 安装 %%~nxd...
        call npm install --ignore-scripts 2>nul
    )
)

echo.
echo ========================================
echo 安装完成!
echo ========================================
echo.
echo 扩展目录: %EXT_DIR%
echo 记忆存储: %MEMORY_DIR%
echo 用户档案: %PROFILE_DIR%
echo.
echo 请在 %PI_DIR%\auth.json 中填入你的 API Key
echo.
echo 运行: %~dp0..\pi.bat
echo.
pause
