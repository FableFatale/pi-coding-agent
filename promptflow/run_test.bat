@echo off
cd /d "%~dp0"
echo Running optimization test...
python run_optimize.py
if errorlevel 1 (
    echo Error occurred
) else (
    echo Done
)
pause
