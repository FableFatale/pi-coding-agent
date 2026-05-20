@echo off
chcp 65001 >nul
echo ========================================
echo   Pi Memory 三层记忆系统启动器
echo ========================================
echo.

:: 1. 启动 Redis
echo [1/2] 启动 Redis...
start "" "D:\Redis-x64-5.0.14.1\redis-server.exe"
echo     Redis 已启动 (端口 6379)

:: 2. 启动 PostgreSQL
echo.
echo [2/2] 启动 PostgreSQL...
"C:\Program Files\PostgreSQL\17\bin\pg_ctl" start -D "C:\Program Files\PostgreSQL\17\data" -w
echo     PostgreSQL 已启动 (端口 5432)

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
pause
