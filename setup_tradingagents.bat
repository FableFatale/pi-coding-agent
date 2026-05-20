@echo off
echo ========================================
echo TradingAgents-CN 项目安装脚本
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 建议以管理员身份运行此脚本
    echo.
)

:: 1. 克隆仓库
echo [步骤 1/6] 克隆仓库...
if exist "D:\TradingAgents-CN" (
    echo 目录已存在，跳过克隆。如需更新请手动执行 git pull
) else (
    git clone https://github.com/hsliuping/TradingAgents-CN.git D:\TradingAgents-CN
    if %errorlevel% neq 0 (
        echo [错误] 克隆失败，请确保已安装 Git
        echo 下载地址: https://git-scm.com/download/win
        pause
        exit /b 1
    )
)

:: 2. 进入目录
cd /d D:\TradingAgents-CN
echo [步骤 2/6] 进入项目目录: %CD%

:: 3. 创建虚拟环境
echo [步骤 3/6] 创建Python虚拟环境...
if exist "venv" (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 4. 激活虚拟环境并安装依赖
echo [步骤 4/6] 安装依赖...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

:: 5. 复制 .env.example 为 .env
echo [步骤 5/6] 配置环境变量...
if exist ".env.example" (
    if exist ".env" (
        echo .env 文件已存在，跳过复制
    ) else (
        copy .env.example .env
        echo 请编辑 .env 文件配置 API 密钥
    )
) else (
    echo [警告] 未找到 .env.example 文件
)

:: 6. 查看并显示启动说明
echo [步骤 6/6] 显示启动说明...
echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 项目目录: D:\TradingAgents-CN
echo 虚拟环境: D:\TradingAgents-CN\venv
echo.
echo 启动应用前，请先:
echo 1. 编辑 .env 文件配置您的 API 密钥
echo 2. 查看 README.md 了解启动方式
echo.
echo 常用命令:
echo   activate    - 激活虚拟环境
echo   python main.py - 运行主程序
echo   streamlit run app/main.py - 运行 Web 界面
echo.
echo ========================================
pause
