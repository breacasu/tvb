@echo off
REM Setup Electron for TVB on Windows
REM Installs Electron standalone in %USERPROFILE%\.local\electron

set ELECTRON_VERSION=42.2.0
set ELECTRON_DIR=%USERPROFILE%\.local\electron
set ARCH=%PROCESSOR_ARCHITECTURE%
if "%ARCH%"=="AMD64" set ARCH_NAME=win32-x64
if "%ARCH%"=="ARM64" set ARCH_NAME=win32-arm64

echo Setting up Electron v%ELECTRON_VERSION% for %ARCH_NAME%...

if not exist "%ELECTRON_DIR%" mkdir "%ELECTRON_DIR%"
cd /d "%ELECTRON_DIR%"

if not exist "node_modules\electron\dist\electron.exe" (
    echo Installing Electron package...
    call npm init -y >nul 2>&1
    set ELECTRON_SKIP_BINARY_DOWNLOAD=1
    call npm install electron@%ELECTRON_VERSION% --save-dev >nul 2>&1

    echo Downloading Electron binary...
    set ZIP=electron-v%ELECTRON_VERSION%-%ARCH_NAME%.zip
    curl -L --fail -o "%ZIP%" "https://github.com/electron/electron/releases/download/v%ELECTRON_VERSION%/%ZIP%"
    powershell -Command "Expand-Archive -Path '%ZIP%' -DestinationPath 'node_modules\electron\dist' -Force"
    del "%ZIP%"
)

echo Electron v%ELECTRON_VERSION% ready at %ELECTRON_DIR%
echo.
echo To start TVB:
echo   cd C:\path\to\tvb-electron
echo   npm start
echo.
echo To build a distributable package:
echo   npm run dist:win