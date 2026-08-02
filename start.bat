@echo off
setlocal
set "APP_DIR=%~dp0"
set "ELECTRON=%USERPROFILE%\.local\electron\node_modules\electron\dist\electron.exe"
set ELECTRON_RUN_AS_NODE=

if exist "%ELECTRON%" (
    "%ELECTRON%" "%APP_DIR%electron\main.js"
) else (
    echo [ERROR] Electron not found at: %ELECTRON%
    echo Please run setup-electron.bat first.
    pause
    exit /b 1
)
