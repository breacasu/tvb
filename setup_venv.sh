#!/bin/bash

# TVB - Virtual Environment Setup Script
# Automatische Einrichtung des Python Virtual Environment

set -e  # Exit on error

echo "🎬 TVB - Transcode Video Batch Setup"
echo "====================================="

# Prüfe ob Python 3 installiert ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 ist nicht installiert!"
    echo "Bitte installieren Sie Python 3.8 oder höher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python Version gefunden: $PYTHON_VERSION"

# Prüfe ob venv verfügbar ist
if ! python3 -c "import venv" &> /dev/null; then
    echo "❌ venv Modul ist nicht verfügbar!"
    echo "Bitte installieren Sie python3-venv."
    exit 1
fi

# Erstelle venv Verzeichnis
VENV_DIR="tvb_venv"
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual Environment existiert bereits."
    read -p "Möchten Sie es neu erstellen? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Lösche altes venv..."
        rm -rf "$VENV_DIR"
    else
        echo "📁 Verwende existierendes venv."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Erstelle Virtual Environment..."
    python3 -m venv "$VENV_DIR"
fi

# Aktiviere venv
echo "🚀 Aktiviere Virtual Environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrade pip..."
pip install --upgrade pip

# Installiere Requirements
echo "📦 Installiere Python-Pakete..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt nicht gefunden!"
    exit 1
fi

# Erstelle Aktivierungsskript
echo "📝 Erstelle Aktivierungsskript..."
cat > activate_tvb.sh << 'EOF'
#!/bin/bash
# TVB Environment Aktivierung
echo "🎬 Aktiviere TVB Environment..."
source tvb_venv/bin/activate
echo "✅ TVB Environment aktiviert!"
echo "💡 Verwende 'python tvb.py --help' für Hilfe"
echo "💡 Verwende 'deactivate' zum Beenden"
EOF

chmod +x activate_tvb.sh

# Erstelle Wrapper-Skript
echo "🔗 Erstelle TVB Wrapper..."
cat > tvb_wrapper.sh << 'EOF'
#!/bin/bash
# TVB Wrapper Script
# Führt tvb.py im virtuellen Environment aus

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Aktiviere venv
source tvb_venv/bin/activate

# Führe tvb.py aus
python tvb.py "$@"

# Deaktiviere venv
deactivate
EOF

chmod +x tvb_wrapper.sh

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "📋 Nächste Schritte:"
echo "1. Aktiviere das Environment:"
echo "   source activate_tvb.sh"
echo ""
echo "2. Oder verwende den Wrapper direkt:"
echo "   ./tvb_wrapper.sh -i /pfad/zu/videos -o /ausgabe"
echo ""
echo "3. Konfiguriere tvb-config.ini mit deinen Pfaden"
echo ""
echo "4. Teste mit einer Datei:"
echo "   ./tvb_wrapper.sh -i testvideo.mp4 -o ./output -V"
echo ""
echo "🔧 System-Abhängigkeiten:"
echo "- Ruby (für video_transcoding)"
echo "- HandBrakeCLI"
echo "- FFmpeg"
echo "- mkvpropedit"
echo "- mkvmerge (optional)"
echo ""
echo "📚 Siehe README.md für weitere Informationen"
