@echo off
chcp 65001 >nul
echo ========================================
echo   Pi Memory - Service Starter
echo ========================================
echo.

:: Check Redis
netstat -ano | findstr :6379 >nul
if %errorlevel% equ 0 (
    echo [OK] Redis already running on 6379
) else (
    echo [INFO] Starting Redis...
    start "" "D:\Redis-x64-5.0.14.1\redis-server.exe"
    timeout /t 2 >nul
    netstat -ano | findstr :6379 >nul
    if %errorlevel% equ 0 (
        echo [OK] Redis started
    ) else (
        echo [WARN] Redis may not have started properly
    )
)

:: Check PostgreSQL
netstat -ano | findstr :5432 >nul
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL already running on 5432
) else (
    echo [INFO] Starting PostgreSQL...
    "C:\Program Files\PostgreSQL\17\bin\pg_ctl" start -D "C:\Program Files\PostgreSQL\17\data" -w
)

echo.
echo ========================================
echo   Done
echo ========================================
echo.
pause
