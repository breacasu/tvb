@echo off
REM TVB - Virtual Environment Setup Script für Windows
REM Automatische Einrichtung des Python Virtual Environment

echo 🎬 TVB - Transcode Video Batch Setup
echo =====================================

REM Prüfe ob Python 3 installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Python 3.8 oder höher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python Version gefunden: %PYTHON_VERSION%

REM Prüfe ob venv verfügbar ist
python -c "import venv" >nul 2>&1
if errorlevel 1 (
    echo ❌ venv Modul ist nicht verfügbar!
    echo Bitte installieren Sie python3-venv.
    pause
    exit /b 1
)

REM Erstelle venv Verzeichnis
set VENV_DIR=tvb_venv
if exist "%VENV_DIR%" (
    echo ⚠️  Virtual Environment existiert bereits.
    set /p REBUILD="Möchten Sie es neu erstellen? (y/N): "
    if /i "%REBUILD%"=="y" (
        echo 🗑️  Lösche altes venv...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo 📁 Verwende existierendes venv.
    )
)

if not exist "%VENV_DIR%" (
    echo 🔧 Erstelle Virtual Environment...
    python -m venv "%VENV_DIR%"
)

REM Aktiviere venv
echo 🚀 Aktiviere Virtual Environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo ⬆️  Upgrade pip...
python -m pip install --upgrade pip

REM Installiere Requirements
echo 📦 Installiere Python-Pakete...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ❌ requirements.txt nicht gefunden!
    pause
    exit /b 1
)

REM Erstelle Aktivierungsskript
echo 📝 Erstelle Aktivierungsskript...
(
echo @echo off
echo REM TVB Environment Aktivierung
echo echo 🎬 Aktiviere TVB Environment...
echo call tvb_venv\Scripts\activate.bat
echo echo ✅ TVB Environment aktiviert!
echo echo 💡 Verwende 'python tvb.py --help' für Hilfe
echo echo 💡 Verwende 'deactivate' zum Beenden
) > activate_tvb.bat

REM Erstelle Wrapper-Skript
echo 🔗 Erstelle TVB Wrapper...
(
echo @echo off
echo REM TVB Wrapper Script
echo REM Führt tvb.py im virtuellen Environment aus
echo.
echo set SCRIPT_DIR=%%~dp0
echo cd /d "%%SCRIPT_DIR%%"
echo.
echo REM Aktiviere venv
echo call tvb_venv\Scripts\activate.bat
echo.
echo REM Führe tvb.py aus
echo python tvb.py %%*
echo.
echo REM Deaktiviere venv
echo deactivate
) > tvb_wrapper.bat

echo.
echo ✅ Setup abgeschlossen!
echo.
echo 📋 Nächste Schritte:
echo 1. Aktiviere das Environment:
echo    activate_tvb.bat
echo.
echo 2. Oder verwende den Wrapper direkt:
echo    tvb_wrapper.bat -i C:\pfad\zu\videos -o C:\ausgabe
echo.
echo 3. Konfiguriere tvb-config.ini mit deinen Pfaden
echo.
echo 4. Teste mit einer Datei:
echo    tvb_wrapper.bat -i testvideo.mp4 -o .\output -V
echo.
echo 🔧 System-Abhängigkeiten:
echo - Ruby ^(für video_transcoding^)
echo - HandBrakeCLI
echo - FFmpeg
echo - mkvpropedit
echo - mkvmerge ^(optional^)
echo.
echo 📚 Siehe README.md für weitere Informationen
echo.
pause
