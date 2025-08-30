# 📋 TVB - Umfassende Test-Checkliste

## 🎯 1. Command-Line-Parameter

### Basis-Parameter
- [ ] `-i <input>` - Einzelne Datei
- [ ] `-i <directory>` - Verzeichnis mit Unterordnern
- [ ] `-o <output>` - Benutzerdefinierter Output-Pfad
- [ ] `-f movie` - Force Movie-Format
- [ ] `-f tvshow` - Force TV-Show-Format
- [ ] `-f custom` - Force Custom-Format

### Spezielle Modi
- [ ] `-d` - Dry-Run (Befehle anzeigen ohne Ausführung)
- [ ] `-P` - Preview-Modus (30 Sekunden)
- [ ] `-m` - Multiplex mit mkvmerge
- [ ] `-H` - Hibernate nach Fertigstellung

### Logging & Debug
- [ ] `-v` - Verbose-Modus
- [ ] `--debug` - Debug-Modus mit detailliertem Logging
- [ ] `--version` - Versionsanzeige
- [ ] `-h` - Hilfe anzeigen

---

## ⚙️ 2. Config-Datei Optionen

### Encoding-Parameter
- [ ] `[tvshow]` Parameter mit H.265 Hardware-Encoding
- [ ] `[movie]` Parameter mit AV1-Encoding
- [ ] `[custom]` Parameter mit Legacy-HEVC
- [ ] `[preview]` Parameter für Preview-Funktionalität

### Default-Einstellungen
- [ ] `cpulimit = no` → Kein CPU-Limit
- [ ] `cpulimit = yes` + `cpulimitpercent = 600` → CPU-Limit aktiv
- [ ] `localization = 'german'` → Deutsche Lokalisierung
- [ ] `edit_subtitles_manually = no` → Automatische Subtitle-Verarbeitung
- [ ] `edit_subtitles_manually = yes` → Manuelle Subtitle-Bearbeitung
- [ ] `preserve_file_date = yes` → Original-Datum beibehalten
- [ ] `preserve_file_date = no` → Aktuelles Datum verwenden

### Tool-Pfade
- [ ] Automatische Tool-Detection (PATH + typische Pfade)
- [ ] Fallback auf Config-Pfade bei fehlender automatischer Detection
- [ ] `[transcode_video_path]` für verschiedene Plattformen
- [ ] `[mkvpropedit_path]`, `[mkvmerge_path]`, `[ffmpeg_path]`, `[handbrakecli_path]`

---

## 🎬 3. Encoding-Formate & Codecs

### Video-Codecs
- [ ] H.265 Hardware-Encoding (`vt_h265`)
- [ ] AV1 Software-Encoding (`svt_av1`)
- [ ] Legacy H.265 (`x265`)
- [ ] Verschiedene Quality-Einstellungen (24, 33, 56)

### Audio-Verarbeitung
- [ ] Dolby Atmos Detection & Preservation
- [ ] Mehrkanal-Audio (5.1, 7.1)
- [ ] Stereo-Downmix bei Bedarf
- [ ] Verschiedene Audio-Codecs (AAC, AC-3, E-AC-3)

### Dateiformate
- [ ] `.mkv` - Matroska-Container
- [ ] `.mp4` - MP4-Container
- [ ] `.m4v` - M4V-Container
- [ ] Gemischte Formate in einem Batch

---

## 🔍 4. Automatische Features

### Format-Detection
- [ ] TV-Shows: `Show.Name.S01E01.Episode.Title.mkv`
- [ ] Movies: `Movie.Name.(Year).mkv`
- [ ] Custom: Alle anderen Formate
- [ ] Override mit `-f` Parameter

### Dolby Atmos
- [ ] Erkennung von Atmos-Tracks
- [ ] `copy`-Modus für Atmos-Tracks
- [ ] `av_aac` für normale Tracks
- [ ] Korrektes Mixdown-Handling (none für Atmos)

### Progress-Tracking
- [ ] Batch-Progress (File X of Y)
- [ ] Dateiname-Anzeige (mit Abkürzung bei langen Namen)
- [ ] Echtzeit-Fortschritt mit tqdm-Balken
- [ ] FPS und ETA-Anzeige
- [ ] Abschluss-Statistiken

---

## 🛠️ 5. Tool-Detection & Pfade

### Automatische Detection
- [ ] `transcode-video` in PATH gefunden
- [ ] `HandBrakeCLI` Version 1.8.0+ erkannt
- [ ] `mkvmerge`, `mkvpropedit`, `ffmpeg` gefunden
- [ ] Versionswarnung bei veraltetem HandBrakeCLI

### Fallback-Mechanismen
- [ ] Config-Pfade bei fehlender PATH-Detection
- [ ] Plattformspezifische Pfade (macOS/Windows)
- [ ] Legacy-Pfad-Unterstützung

---

## 🚨 6. Edge Cases & Fehlerbehandlung

### Datei-Handling
- [ ] Bereits existierende Output-Dateien (Überspringen)
- [ ] Nicht-lesbare Input-Dateien
- [ ] Beschädigte Video-Dateien
- [ ] Sehr große Dateien (>50GB)
- [ ] Dateien ohne Audio-Tracks

### Pfad-Probleme
- [ ] Pfade mit Leerzeichen
- [ ] Pfade mit Sonderzeichen
- [ ] Nicht-ASCII-Zeichen in Dateinamen
- [ ] Relative vs. absolute Pfade
- [ ] Netzwerk-Pfade (SMB, NFS)

### System-Ressourcen
- [ ] CPU-Limit bei hoher Auslastung
- [ ] Speicherbegrenzung bei großen Dateien
- [ ] Festplattenplatz-Prüfung
- [ ] Unterbrechung während Encoding (Ctrl+C)

---

## 📊 7. Statistiken & Logging

### CSV-Statistiken
- [ ] Korrekte Spalten: Datum, Dateiname, Original-Größe, Neue Größe, Kompression, Zeit, Befehl
- [ ] Kompressionsrate-Berechnung
- [ ] Encoding-Zeit-Erfassung
- [ ] Erfolgs-/Fehler-Status

### Logging
- [ ] `transcode.log` mit allen Meldungen
- [ ] Debug-Modus mit vollständigen Details
- [ ] Fehlerhafte Encodings werden geloggt
- [ ] HandBrakeCLI Command-Modifikationen

---

## 🧪 8. Integrationstests

### Komplette Workflows
- [ ] Einzeldatei-Encoding mit allen Optionen
- [ ] Batch-Encoding mehrerer Dateien
- [ ] Gemischte Formate (Movies + TV-Shows)
- [ ] Preview + Multiplex + Hibernate

### Config-Kombinationen
- [ ] CPU-Limit + Preserve-Date + Verbose
- [ ] Dolby Atmos + Custom-Format + Debug
- [ ] Alle Optionen gleichzeitig aktiviert

### Cross-Plattform
- [ ] macOS mit Homebrew-Installation
- [ ] Windows mit manueller Tool-Installation
- [ ] Verschiedene Python-Versionen (3.8+)

---

## 🎯 9. Performance-Tests

### Encoding-Geschwindigkeit
- [ ] Hardware-Encoding vs. Software-Encoding
- [ ] Verschiedene Quality-Einstellungen
- [ ] CPU-Limit Einfluss auf Performance
- [ ] Preview-Modus Performance

### Ressourcen-Verbrauch
- [ ] CPU-Auslastung mit/ohne Limit
- [ ] Speicherverbrauch bei großen Dateien
- [ ] Festplatten-I/O bei mehreren parallelen Encodings

---

## ✅ 10. Abschluss-Tests

### Qualitätssicherung
- [ ] Alle Command-Line-Hilfen funktionieren
- [ ] Versionsinformation korrekt
- [ ] README mit aktuellen Informationen
- [ ] Beispiel-Commands funktionieren

### Regression-Tests
- [ ] Alte Funktionalität noch verfügbar
- [ ] Rückwärtskompatibilität gewahrt
- [ ] Bestehende Configs funktionieren weiter

---

## 📝 Test-Vorbereitung

### Test-Dateien
- [ ] Kleine Testvideos (1-5 Min) für schnelle Tests
- [ ] Dolby Atmos Testdatei
- [ ] Verschiedene Container-Formate
- [ ] Dateien mit Untertiteln

### Test-Umgebung
- [ ] Backup der aktuellen Config
- [ ] Separate Test-Verzeichnisse
- [ ] Ausreichend Festplattenplatz
- [ ] Monitoring-Tools bereit (Activity Monitor, etc.)

---

## 🏃 Automatisierte Tests

Für automatisierte Tests siehe:
- `tests/test_basic_functionality.sh` - Basis-Tests
- `tests/test_config_options.sh` - Config-Optionen
- `tests/test_parameters.sh` - Parameter-Kombinationen
- `tests/test_error_cases.sh` - Fehlerfälle

### Quick-Start für Tests:
```bash
# Alle automatisierten Tests ausführen
./tests/run_all_tests.sh

# Einzelne Test-Kategorien
./tests/test_basic_functionality.sh
./tests/test_config_options.sh
```

Diese Checkliste deckt alle wichtigen Aspekte des TVB-Skripts ab. Beginne mit den Basis-Tests und arbeite dich systematisch durch die fortgeschrittenen Features!

**Pro-Tipp:** Erstelle für jeden Test einen separaten Branch/Zweig, um Änderungen nachverfolgen zu können. 📋✨
