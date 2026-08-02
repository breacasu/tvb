@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "BIN_DIR=%SCRIPT_DIR%bin"
set "C_BIN_DIR=C:\bin"

echo === TVB Windows Setup ===
echo.

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

:: ==========================
:: 1. HandBrakeCLI
:: ==========================
set "HBCLI=%BIN_DIR%\HandBrakeCLI.exe"
if exist "%HBCLI%" goto :hb_done

if exist "%C_BIN_DIR%\HandBrakeCLI.exe" (
    copy "%C_BIN_DIR%\HandBrakeCLI.exe" "%HBCLI%" >nul
    echo [OK] HandBrakeCLI copied from C:\bin
    goto :hb_done
)

where HandBrakeCLI >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] HandBrakeCLI found in PATH
    goto :hb_done
)

set "HANDBRAKE_VERSION=1.11.2"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "HANDBRAKE_ARCH=aarch64"
) else (
    set "HANDBRAKE_ARCH=x86_64"
)
set "HANDBRAKE_URL=https://github.com/HandBrake/HandBrake/releases/download/!HANDBRAKE_VERSION!/HandBrakeCLI-!HANDBRAKE_VERSION!-win-!HANDBRAKE_ARCH!.zip"
echo Downloading HandBrakeCLI !HANDBRAKE_VERSION!...
curl -L --fail -o hbcli.zip "!HANDBRAKE_URL!"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to download HandBrakeCLI
    echo        Download manually from: https://handbrake.fr/downloads2.php
    pause
    exit /b 1
)
powershell -NoProfile -Command "Expand-Archive -Path 'hbcli.zip' -DestinationPath '!BIN_DIR!' -Force" >nul
del hbcli.zip
echo [OK] HandBrakeCLI installed to bin\

:hb_done

:: ==========================
:: 2. ffprobe
:: ==========================
set "FFPROBE=%BIN_DIR%\ffprobe.exe"
if exist "%FFPROBE%" goto :ff_done

if exist "%C_BIN_DIR%\ffprobe.exe" (
    copy "%C_BIN_DIR%\ffprobe.exe" "%FFPROBE%" >nul
    echo [OK] ffprobe copied from C:\bin
    goto :ff_done
)

where ffprobe >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [OK] ffprobe found in PATH
    goto :ff_done
)

if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-winarm64-gpl.zip"
) else (
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
)
echo Downloading ffprobe (ffmpeg essentials)...
curl -L --fail -o ffmpeg.zip "!FFMPEG_URL!"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to download ffprobe
    echo        Download manually from: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

echo Extracting ffprobe.exe...
powershell -NoProfile -Command "$tmp='%TEMP%\ffmpeg_extract'; Expand-Archive -Path 'ffmpeg.zip' -DestinationPath $tmp -Force; Get-ChildItem $tmp -Recurse -Filter 'ffprobe.exe' | Copy-Item -Destination '%FFPROBE%' -Force; Remove-Item $tmp -Recurse -Force" >nul
del ffmpeg.zip

if exist "%FFPROBE%" (
    echo [OK] ffprobe installed to bin\
) else (
    echo [ERROR] Could not extract ffprobe.exe
    pause
    exit /b 1
)

:ff_done

:: ==========================
:: 3. libmediainfo.dll
:: ==========================
set "LIBMI=%BIN_DIR%\libmediainfo.dll"
if exist "%LIBMI%" goto :libmi_done

if exist "%C_BIN_DIR%\libmediainfo.dll" (
    copy "%C_BIN_DIR%\libmediainfo.dll" "%LIBMI%" >nul
    echo [OK] libmediainfo.dll copied from C:\bin
    goto :libmi_done
)

set "MEDIAINFO_VERSION=26.05"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "MEDIAINFO_ARCH=ARM64"
) else (
    set "MEDIAINFO_ARCH=x64"
)
set "LIBMI_URL=https://mediaarea.net/download/binary/libmediainfo0/!MEDIAINFO_VERSION!/MediaInfo_DLL_!MEDIAINFO_VERSION!_Windows_!MEDIAINFO_ARCH!_WithoutInstaller.zip"
echo Downloading libmediainfo.dll !MEDIAINFO_VERSION!...
curl -L --fail -o libmi.zip "!LIBMI_URL!"
if !ERRORLEVEL! neq 0 (
    echo [WARN] Failed to download libmediainfo.dll
        echo        pymediainfo Atmos detection will not work
    echo        Download manually from: https://mediaarea.net/en/MediaInfo/Download/Windows
    echo        Place libmediainfo.dll in %BIN_DIR%
    goto :libmi_skip
)

echo Extracting libmediainfo.dll...
powershell -NoProfile -Command "$tmp='%TEMP%\libmi_extract'; Expand-Archive -Path 'libmi.zip' -DestinationPath $tmp -Force; $found=Get-ChildItem $tmp -Recurse -Include '*.dll'; if($found) { Copy-Item $found[0].FullName -Destination '%LIBMI%' -Force } else { write-host 'NO_DLL found' }; Remove-Item $tmp -Recurse -Force"
del libmi.zip

if exist "%LIBMI%" (
    echo [OK] libmediainfo.dll installed to bin\
) else (
    echo [WARN] Could not extract libmediainfo.dll
    echo       Download manually from: https://mediaarea.net/en/MediaInfo/Download/Windows
)

:libmi_done
:libmi_skip

:: ==========================
:: 4. Python venv + deps
:: ==========================
echo.
echo === Python setup ===
cd /d "%SCRIPT_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

if not exist "requirements.txt" (
    echo pymediainfo > requirements.txt
    echo pyinstaller >> requirements.txt
)

echo Installing Python dependencies...
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet

echo.
echo === Setup complete ===
echo Binaries in: %BIN_DIR%
echo Python venv:  .venv\
echo.
echo Next steps:
echo   npm install
echo   npm run build:react
echo   npm run start:win
echo.
echo For distribution:
echo   npm run dist:win
