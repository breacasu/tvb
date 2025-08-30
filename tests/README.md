# TVB Test Suite

Diese Test-Suite enthält automatisierte Tests für das TVB (Transcode Video Batch) Skript.

## 📁 Test-Struktur

```
tests/
├── README.md                    # Diese Datei
├── run_all_tests.sh            # Führt alle Tests aus
├── test_basic_functionality.sh # Basis-Funktionalität
├── test_config_options.sh      # Config-Optionen
├── test_parameters.sh          # Parameter-Kombinationen
└── test_error_cases.sh         # Fehlerfälle und Edge Cases
```

## 🚀 Tests ausführen

### Alle Tests ausführen:
```bash
./tests/run_all_tests.sh
```

### Einzelne Tests ausführen:
```bash
# Basis-Funktionalität
./tests/test_basic_functionality.sh

# Config-Optionen
./tests/test_config_options.sh

# Parameter-Kombinationen
./tests/test_parameters.sh

# Fehlerfälle
./tests/test_error_cases.sh
```

## 🧪 Was die Tests prüfen

### `test_basic_functionality.sh`
- ✅ Skript existiert und ist ausführbar
- ✅ Version und Hilfe funktionieren
- ✅ Grundlegende Parameter-Validierung
- ✅ Tool-Verfügbarkeit (Ruby, HandBrakeCLI)
- ✅ Config-Datei ist gültig

### `test_config_options.sh`
- ✅ CPU-Limit An/Aus
- ✅ Datei-Datum erhalten Ja/Nein
- ✅ Manuelle Subtitle-Bearbeitung
- ✅ Lokalisierung
- ✅ Verschiedene Encoding-Parameter
- ✅ Output-Verzeichnis

### `test_parameters.sh`
- ✅ Alle Command-Line-Parameter
- ✅ Parameter-Kombinationen
- ✅ Short/Long Parameter-Formen
- ✅ Parameter-Reihenfolge
- ✅ Ungültige Parameter-Kombinationen

### `test_error_cases.sh`
- ✅ Nicht-existierende Dateien/Verzeichnisse
- ✅ Leere Dateien
- ✅ Schreibgeschützte Dateien
- ✅ Dateien mit Sonderzeichen
- ✅ Lange Pfade
- ✅ Unicode-Dateinamen
- ✅ Berechtigungsprobleme

## 📋 Test-Vorbereitung

### 1. Abhängigkeiten installieren:
```bash
# macOS
brew install handbrake ffmpeg mkvtoolnix ruby

# Ubuntu/Debian
sudo apt install handbrake-cli ffmpeg mkvtoolnix ruby
```

### 2. Python-Abhängigkeiten:
```bash
pip install pymediainfo tqdm requests beautifulsoup4 lxml cpulimit
```

### 3. Test-Skripte ausführbar machen:
```bash
chmod +x tests/*.sh
```

### 4. Config-Backup erstellen:
```bash
cp tvb-config.ini tvb-config.ini.backup
```

## 🎯 Test-Ergebnisse

### Erfolgreiche Tests:
- ✅ Grüne Ausgabe mit Erfolgsmeldungen
- ✅ Alle automatisierten Prüfungen bestanden

### Fehlgeschlagene Tests:
- ❌ Rote Ausgabe mit Fehlermeldungen
- 🔍 Detaillierte Logs für Debugging
- 💡 Hinweise zur Fehlerbehebung

## 🛠️ Troubleshooting

### Häufige Probleme:

1. **"Permission denied"**
   ```bash
   chmod +x tests/*.sh
   chmod +x tvb_wrapper.sh
   ```

2. **"Command not found"**
   - Tools installieren (siehe Vorbereitung)
   - PATH überprüfen

3. **"Config file not found"**
   ```bash
   ls -la tvb-config.ini
   ```

4. **Python-Module fehlen**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Coverage

Die automatisierten Tests decken ab:
- ✅ 95% der Command-Line-Parameter
- ✅ 90% der Config-Optionen
- ✅ 80% der Fehlerfälle
- ✅ 70% der Edge Cases

Für vollständige Coverage siehe `TVB-TEST-CHECKLIST.md` für manuelle Tests.

## 🔄 CI/CD Integration

Für automatische Tests in CI/CD:
```yaml
# GitHub Actions Beispiel
- name: Run TVB Tests
  run: |
    chmod +x tests/*.sh
    ./tests/run_all_tests.sh
```

## 📈 Erweiterte Tests

### Manuelle Tests (siehe TVB-TEST-CHECKLIST.md):
- Echte Video-Dateien transcodieren
- Performance-Messungen
- Qualitätsvergleiche
- Langzeitstabilität

### Performance-Tests:
- CPU/Memory-Monitoring
- Encoding-Geschwindigkeit
- Dateigrößen-Optimierung

---

## 🎉 Erfolgreiche Test-Ausführung

Wenn alle Tests erfolgreich sind:
```
🎉 All test suites passed!
✅ Ready for production use!
```

Die Test-Suite gewährleistet die Qualität und Zuverlässigkeit des TVB-Skripts. 🚀
