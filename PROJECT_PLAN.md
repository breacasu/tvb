# Plan: TVB Electron - Vollständige Portierung der CLI-Funktionalität

## Ziel
Eigenständige Electron-App mit **komplett selbst enthaltener** CLI-Funktionalität (keine externen Ruby/Python-Installationen, kein HandBrakeCLI installieren nötig, kein libmediainfo installieren nötig).

## Analyse der originalen `tvb.py` (1289 Zeilen)

### Kern-Architektur (Original)
1. **Tool-Erkennung** (`find_transcode_video_path`, `find_tool_path`) - PATH, typische Pfade, Config-Fallback
2. **Dateisammlung** (`TranscodeList._collect_files`) - rekursiv, Video-Extensions
3. **Format-Erkennung** (`TranscodeList._detect_formats`) - Regex `[sS]\d+[eE]\d+` → tvshow, sonst movie
4. **Transcode-Video Dry-Run** (`get_transcode_command`) - Ruby-Skript mit Config-Parametern aufrufen → generiert HandBrakeCLI-Befehl
5. **HandBrakeCLI-Extraktion** (`process_file`) - Aus Dry-Run Output den HandBrakeCLI-Befehl parsen
6. **Befehlsmodifikation** (`modify_handbrake_output_path`) - Output-Pfad, Preview, Atmos-Preservation
7. **Encoding** (`subprocess.Popen`) - HandBrakeCLI mit tqdm-Progressbar
8. **Post-Processing** - Statistiken, Subtitle-Editing, File-Date Preservation

### Features (Original) - Entscheidungen
| Feature | Status | Kommentar |
|---|---|---|
| Auto-Detect Format | **✅ Beibehalten** | Regex auf Dateiname |
| Forced Format (-f) | **✅ Beibehalten** | Überschreibt Auto-Detect |
| Dolby Atmos Detection | **✅ Beibehalten** | pymediainfo → mehrere Indikatoren |
| Atmos Preservation | **✅ Beibehalten** | Audio-Parameter Modifikation (copy-encoder) |
| Subtitle Editing | **✅ Beibehalten** | mkvpropedit (optional, manuell) |
| Mux (-m) | **❌ Entfernt** | Stattdessen automatische ffprobe-Prüfung nach Encoding. Nur bei defekten Headern mkvmerge |
| Preview (-P) | **✅ Beibehalten** | 30 Sekunden Clip |
| Dry-Run (-d) | **✅ Beibehalten** | Command anzeigen, nicht ausführen |
| CPU Limit | **❌ Entfernt** | Wurde fast nie genutzt |
| Hibernate (-H) | **❌ Entfernt** | Wurde fast nie genutzt |
| Preserve File Date | **✅ Beibehalten** | os.utime |
| Version Check | **✅ Beibehalten** | Im Log ausgeben, Hinweis wenn neueres HandBrakeCLI verfügbar |
| Statistics | **✅ Beibehalten** | CSV mit locale-basiertem Datumsformat |
| Logging | **✅ Beibehalten** | Sehr ausführlich (Debug + Info), hilfreich für Debugging |
| Config-basierte Parameter | **✅ Beibehalten** | movie/tvshow/custom Sections |

### Funktionsweise (Original)
```
Input-Datei → transcode-video.rb --dry-run → HandBrakeCLI-Command wird ausgegeben
→ Command wird geparst → modify_handbrake_output_path() → tatsächliches Encoding
```

**Kritisch**: Der HandBrakeCLI-Befehl **nicht selbst** bauen, sondern durch den transcode-video Algorithmus generieren lassen (Dry-Run). Das Python-Backend muss diesen Algorithmus **nachbilden**.

## Architektur-Entscheidung

### Option A: Vollständig Bundled (EINZIGE Option)
- **HandBrakeCLI** als Binary mitgeliefert (in `tvb-electron/bin/`)
- **Python** via PyInstaller/embedded (keine System-Installation)
- **libmediainfo** als Bibliothek mitgeliefert (für pymediainfo)
- **pymediainfo** als Python-Dependency im Bundle
- **mkvmerge/mkvpropedit** als Binary mitgeliefert (falls für Subtitles nötig)

### Entscheidung: Kein Ruby
- `transcode-video.rb` existiert **nicht** mehr
- Die Logik von `transcode-video` (HandBrakeCLI-Befehl generieren) wird in **Python** portiert
- Das Python-Backend führt also beides aus:
  1. Dry-Run mit eigener Logik (statt transcode-video.rb)
  2. HandBrakeCLI-Befehl generieren (statt aus Ruby-Output parsen)
  3. Zusätzliche Features (Atmos, Preview, etc.)

## Phasenplan

### Phase 1: Python-Backend komplett neu schreiben (HÖCHSTE Priorität)
**Ziel**: `tvb-electron/python/tvb.py` ersetzt transcode-video.rb komplett und fügt eigene Features hinzu.

#### 1.1 transcode-video-Algorithmus in Python nachbilden
- Analysiere `transcode-video.rb` (von Lisa Melton) → extrahiere die HandBrakeCLI-Generierungslogik
- Implementiere in Python:
  - Input-Analyse (Auflösung, Codecs, HDR?)
  - Crop-Erkennung (autocrop)
  - Bitrate-Berechnung basierend auf Auflösung
  - Audio-Track Auswahl (Sprachen)
  - Untertitel-Auswahl
- Ergebnis: Funktion `generate_handbrake_cmd(input_file, output_file, format_type)` gibt den **vollständigen** HandBrakeCLI-Befehl zurück

#### 1.2 Alle Flags implementieren
| Flag | Funktion |
|---|---|
| `-i` | Input (Datei oder Verzeichnis) |
| `-o` | Output-Verzeichnis |
| `-f` | Forced format (movie/tvshow/custom) |
| `-f` (fehlt) | Auto-detect via Regex |
| `-P` | Preview (30s) |
| `-d` | Dry-run |
| `--debug` | Debug-Logging |
| `--verbose` | Verbose-Logging |

#### 1.3 Zusatz-Features portieren
- `detect_dolby_atmos()` → `pymediainfo` nutzen
- `modify_handbrake_output_path()` → Atmos-Preservation, Output-Pfad, Preview
- `preserve_file_date` → `os.utime`
- `manual_subtitle_editing` → `mkvpropedit` (optional)
- `write_statistics()` → CSV mit locale-Formatierung

#### 1.4 Logging-Konzept
```python
# Python-Backend schreibt ins Log-File UND sendet JSON an Electron
def log(level, message):
    # 1. In transcode.log schreiben
    logging.log(level, message)
    # 2. JSON an stdout für Electron
    print(json.dumps({"type": "log", "level": level, "message": message}), flush=True)
```

### Phase 2: Electron-Frontend stabilisieren (Höhere Priorität)

#### 2.1 IPC-Korrektur (ONE-TIME Registration)
```javascript
// Alle ipcMain.handle() EINMALIG auf Module-Ebene registrieren
// NIE innerhalb von anderen Handlern
```

#### 2.2 Argument-Mapping
| UI-Control | CLI-Flag |
|---|---|
| Input File/Dir | `-i` |
| Output Dir | `-o` |
| Format Dropdown | `-f` (oder leer für Auto) |
| Preview Toggle | `-P` |
| Dry-Run Toggle | `-d` |
| Preserve Atmos Toggle | Config-Key `preserve_atmos_audio` |
| Preserve File Date Toggle | Config-Key `preserve_file_date` |
| Backend Dropdown | **Entfällt** (nur Python) |

#### 2.3 Live-Updates
- **Progress**: `transcode:progress` → Batch + File Progress Bars
- **Logs**: `transcode:log` → LogViewer (live anhängen, nicht remounten)
- **Stats**: `transcode:complete` → StatsDashboard reload via key-change
- **Button-State**: `transcode:complete` → "Start Transcoding" wieder aktivieren

### Phase 3: Packaging & Bundling (Mittlere Priorität)

#### 3.1 Python-Bundle
```bash
# PyInstaller oder einfacher: Python embedded für Windows/Mac
cd tvb-electron/python
pyinstaller --onefile tvb.py \
  --add-binary "libmediainfo.dylib:." \
  --add-binary "HandBrakeCLI:." \
  --hidden-import pymediainfo \
  --hidden-import configparser
```

#### 3.2 Electron-Builder
```json
// package.json electron-builder section
"build": {
  "extraResources": [
    "python/dist/tvb",
    "bin/HandBrakeCLI",
    "bin/libmediainfo*"
  ]
}
```

#### 3.3 Setup
- `setup-electron.sh` → Installiert Electron-Binary (NPM)
- Keine Python-Installation vom Nutzer nötig
- Keine HandBrakeCLI-Installation vom Nutzer nötig

### Phase 4: Testing (Kritisch)

#### 4.1 Test-Matrix
| Test | Erwartet |
|---|---|
| Auto-Detect Movie | HandBrakeCLI-Befehl mit movie-Parametern |
| Auto-Detect TV-Show | HandBrakeCLI-Befehl mit tvshow-Parametern (S01E01) |
| Forced Format | Überschreibt Auto-Detect |
| Preview | Nur 30s, Datei ist kleiner |
| Dry-Run | Command im Log, kein Encoding |
| Atmos File | Atmos erkannt, copy-encoder im Command |
| Stats | CSV-Eintrag nach Encoding sichtbar |
| File Date | Output hat gleiches Datum wie Input |

#### 4.2 Cross-Platform
- macOS (ARM64): Erstmaliger Fokus
- Windows (x64): Später via electron-builder
- Linux (x64): Später

## Kritische Randbedingungen

1. **Keine externen Abhängigkeiten**: HandBrakeCLI, libmediainfo, Python alles bundled
2. **Ruby-frei**: transcode-video.rb Logik komplett in Python
3. **Deterministisch**: Gleiche Input → Gleicher HandBrakeCLI-Befehl
4. **Zukunftssicher**: HandBrakeCLI-Version ist fest im Bundle, keine API-Änderungen von außen

## Core-Design: Ruby-kompatibler HandBrakeCLI-Generator

**Der `HandBrakeGenerator` (`generator.py`) ist 1:1 kompatibel zu Lisa Meltons `transcode-video.rb`.**

Die INI-Config (`tvb-config.ini`) ist nur ein **Komfort-Feature** um Presets zu speichern. Alle dort definierten Parameter (`--mode`, `--quality`, `--add-audio`, etc.) werden durch `parse_transcode_video_params()` geparst und direkt an den Generator übergeben — identisch zur Ruby-CLI.

| Kategorie | Status | Abgleich mit Ruby |
|---|---|---|
| Encoder-Auswahl (h264/hevc/nvenc-hevc/av1/nvenc-av1/none) | ✅ 1:1 | x264, x265_10bit, nvenc_h265_10bit, svt_av1_10bit, nvenc_av1_10bit |
| H264 Bitrate (auflösungsbasiert) | ✅ 1:1 | 1250/2500/5000, Clamping 80%-160%, VBV = Bitrate × 3 |
| H264 Downscale (>1080p) | ✅ 1:1 | `--maxWidth 1920 --maxHeight 1080 --loose-anamorphic` + ggf. `--colorspace bt709` |
| H264 Multi-Pass + Turbo | ✅ 1:1 | Nur wenn kein `--quality` gesetzt |
| HEVC Default Quality | ✅ 1:1 | 24 |
| NVENC HEVC Default Quality | ✅ 1:1 | 30 |
| AV1 Default Quality + Preset | ✅ 1:1 | Quality 30 [0–63], Preset 8 [-1–13] |
| NVENC AV1 Default Quality + Preset | ✅ 1:1 | Quality 37 [0–63], Preset 8 [-1–13] |
| Framerate | ✅ 1:1 | mpeg2video@29.97: `--rate 29.97 --cfr`, sonst: `--rate 60` (VFR-Cap) |
| NVENC Encoder Options | ✅ 1:1 | `spatial_aq=1:rc-lookahead=20`, `b_ref_mode=2` bei bframe_refs |
| H264 VBV/Encoder Options | ✅ 1:1 | `vbv-maxrate=<size>:vbv-bufsize=<size>` |
| Audio Selections (track/language/title) | ✅ 1:1 | Gleiche Filterlogik + `uniq` |
| Audio AAC Bitrates + Mixdown | ✅ 1:1 | 80/mono, 128/stereo, 384/5point1 (ac3 448 bei ac3-surround) |
| Audio OPUS Bitrates + Mixdown | ✅ 1:1 | 64/mono, 96/stereo, 320/5point1 |
| Audio EAC3 Bitrates + Mixdown | ✅ 1:1 | 96/mono, 192/stereo, 448/5point1 |
| Subtitle Burn-In (auto/manual/none) | ✅ 1:1 | `hdmv_pgs_subtitle`/`dvd_subtitle` → burned, sonst → default |
| Subtitle Selections | ✅ 1:1 | track/language/title Filter + forced-default |
| Extra Options (`-x`/`--extra`) | ✅ 1:1 | `--extra name=value` und `--extra name` |
| Crop-Mode | ✅ 1:1 | `--crop-mode conservative` |

**Bewusste Abweichungen vom Original:**

| Abweichung | Grund |
|---|---|
| Audio-Track-Namen: `"German AAC 5.1"` statt Rubys leerem ersten Track + `title`-Feld | Bessere Lesbarkeit + Kanalinfo |
| Subtitle-Namen: `"German forced"` statt Rubys rohem `title`-Feld | Bessere Lesbarkeit |
| EAC3 copy-Bedingung: `ac3` + `eac3` statt Rubys `/ac3$/` | Verhindert sinnloses eac3→eac3 Re-encode |
| Subtitle `add_all` statt Ruby's forced-first + selections | Einfachere Logik, deckt alle Fälle ab |

## Dual-Use: CLI + GUI

Das Python-Backend ist bewusst als **CLI-first** konzipiert:

```bash
# Reine CLI-Verwendung (ohne Electron):
./tvb-electron/python/tvb -i "movie.mkv" -o "./output" -f movie

# Ausgabe: JSON-Zeilen für Progress + Logs + Completion
# Die JSON-Ausgabe ist für Electron gedacht, stört im Terminal nicht
```

**Vorteil**: Gleiches Backend für beide Modi. Keine Code-Duplikation.

## Argument-Vereinheitlichung (Lisa Melton Konvention)

**Regel**: Jedes Argument hat eine **kurze** (`-x`) und eine **lange** (`--xxxxx`) Form. Keine Ausnahmen.

| Kurz | Lang | Quelle | Funktion |
|---|---|---|---|
| `-i` | `--input` | Beide | Input-Datei oder Verzeichnis |
| `-o` | `--output` | Beide | Output-Verzeichnis |
| `-f` | `--format` | Dein Feature | Format: movie / tvshow / custom / auto |
| `-P` | `--preview` | Dein Feature | 30-Sekunden Preview |
| `-d` | `--dry-run` | Dein Feature | Command anzeigen, nicht ausführen |
| `-m` | `--mux` | Dein Feature | Mux mit mkvmerge (nur bei defekten Headern) |
| `--crop` | `--crop` | transcode-video | Crop-Detection (auto/manual) |
| `--rate` | `--rate` | transcode-video | Framerate (auto/film/video) |
| `--target` | `--target` | transcode-video | Target-Größe |
| `--add-audio` | `--add-audio` | transcode-video | Audio-Sprachen hinzufügen |
| `--audio-width` | `--audio-width` | transcode-video | Audio-Breite |
| `--no-auto-burn` | `--no-auto-burn` | transcode-video | Kein Auto-Burn |

**Implementierung**: `argparse` mit `add_argument('-i', '--input', ...)` für alle Argumente.

**Hinweis**: Config-Parameter (movie/tvshow/custom) bleiben in `tvb-config.ini`. CLI-Flags sind für Ausführungs-Optionen, Config für Encoding-Parameter.

## Für Umsetzung benötigte Dateien

### A) Aus aktuellem Projekt übernehmbar
| Datei | Status | Grund |
|---|---|---|
| `tvb-electron/electron/main.js` | **Anpassen** | IPC-Struktur OK, aber Handler müssen vereinfacht werden |
| `tvb-electron/electron/preload.js` | **Anpassen** | API-Expos OK, ggf. um Listener erweitern |
| `tvb-electron/client/src/App.js` | **Anpassen** | State-Lifting + Key-Remount für Stats |
| `tvb-electron/client/src/components/TranscodeControl.jsx` | **Anpassen** | Controls OK, Argument-Mapping muss stimmen |
| `tvb-electron/client/src/components/ProgressDisplay.jsx` | **Übernehmen** | Funktioniert, geringe Änderungen |
| `tvb-electron/client/src/components/StatsDashboard.jsx` | **Anpassen** | CSV-Lesen OK, Reload-Trigger |
| `tvb-electron/client/src/components/LogViewer.jsx` | **Anpassen** | Live-Log-Subscriber muss stabil sein |
| `tvb-electron/client/src/components/ConfigEditor.jsx` | **Übernehmen** | Funktioniert |
| `tvb-electron/client/src/index.css` | **Übernehmen** | Dark Theme OK |
| `tvb-electron/python/tvb-config.ini.example` | **Übernehmen** | Config-Struktur bleibt |

### B) Komplett neu zu schreiben
| Datei | Grund |
|---|---|
| `tvb-electron/python/tvb.py` | Ruby-Logik nachbilden, alle Features |
| `tvb-electron/python/transcode_logic.py` | Transcode-Video-Algorithmus als Modul |
| `tvb-electron/python/atmos_handler.py` | Atmos-Erkennung & Preservation |
| `tvb-electron/python/handbrake_generator.py` | HandBrakeCLI-Befehl generieren |
| `tvb-electron/python/statistics.py` | CSV-Schreiben mit Locale |

### C) Neues Projekt-Verzeichnis (Vorschlag)
```
tvb/
├── electron/
│   ├── main.js
│   ├── preload.js
│   └── resources/
│       └── HandBrakeCLI
├── client/
│   ├── src/
│   │   └── components/
│   └── public/
├── python/
│   ├── tvb.py           # CLI-Einstieg
│   ├── transcode/
│   │   ├── generator.py
│   │   ├── analyzer.py
│   │   └── cmd_builder.py
│   ├── features/
│   │   ├── atmos.py
│   │   ├── preview.py
│   │   └── statistics.py
│   └── config/
│       └── config_loader.py
├── bin/
│   ├── HandBrakeCLI
│   ├── libmediainfo.dylib
│   └── mkvmerge
├── tvb-config.ini
└── package.json
```

## Nächste Schritte

1. Neues Verzeichnis erstellen
2. Benötigte Dateien aus altem Projekt kopieren (Siehe Tabelle A)
3. Neue Python-Module schreiben (Siehe Tabelle B)
4. Electron-Frontend anpassen
5. Testing
