@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "BIN_DIR=%SCRIPT_DIR%bin"

echo === TVB Binary Setup ===
echo Platform: Windows
echo.

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

:: --- HandBrakeCLI ---
set "HBCLI=%BIN_DIR%\HandBrakeCLI.exe"
if exist "%HBCLI%" (
    echo [OK] HandBrakeCLI already exists
) else (
    where HandBrakeCLI >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [OK] HandBrakeCLI found in PATH
    ) else (
        set "HANDBRAKE_VERSION=1.9.2"
        set "HANDBRAKE_URL=https://github.com/HandBrake/HandBrake/releases/download/!HANDBRAKE_VERSION!/HandBrakeCLI-!HANDBRAKE_VERSION!-win-x86_64.zip"
        echo Downloading HandBrakeCLI !HANDBRAKE_VERSION!...
        curl -L --fail -o hbcli.zip "!HANDBRAKE_URL!"
        powershell -Command "Expand-Archive -Path 'hbcli.zip' -DestinationPath '!BIN_DIR!' -Force"
        del hbcli.zip
        echo [OK] HandBrakeCLI installed
    )
)

:: --- ffprobe ---
set "FFPROBE=%BIN_DIR%\ffprobe.exe"
if exist "%FFPROBE%" (
    echo [OK] ffprobe already exists
) else (
    where ffprobe >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [OK] ffprobe found in PATH
    ) else (
        echo [INFO] ffprobe must be installed manually.
        echo        Download from: https://ffmpeg.org/download.html
        echo        Place ffprobe.exe in %BIN_DIR%
    )
)

:: --- Python dependencies ---
echo.
echo === Python setup ===
cd /d "%SCRIPT_DIR%"
if exist "requirements.txt" (
    python -m pip install -r requirements.txt 2>nul
)
python -m pip install pymediainfo 2>nul

echo.
echo === Setup complete ===
echo Binaries in: %BIN_DIR%
echo.
echo Next: npm start