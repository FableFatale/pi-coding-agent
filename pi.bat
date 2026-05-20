@echo off
set "PATH=C:\Program Files\nodejs;%PATH%"
node "%~dp0node_modules\@mariozechner\pi-coding-agent\dist\cli.js" %*
