# TVB Electron — Projekt-Status

Stand: 21. Mai 2026

## Erledigt

### Phase 1: Python-Backend (vollständig)

| Komponente | Beschreibung |
|---|---|
| `python/tvb.py` | Haupt-CLI, neuer Flow ohne Ruby (ffprobe → HandBrakeGenerator → subprocess). JSON-Ausgabe für Electron, JsonLogHandler (stdout=JSON, stderr=Text). Unterstützt mehrere `-i` Argumente für Batch-Input |
| `python/transcode/analyzer.py` | MediaAnalyzer via ffprobe, get_video/audio/subtitle_streams |
| `python/transcode/generator.py` | HandBrakeGenerator, parse_transcode_video_params (Config-Kompatibel), generate_command_list, Language-Map, Codec-Namen, Atmos-Erkennung im Generator |
| `python/features/atmos.py` | detect_dolby_atmos via pymediainfo, generate_atmos_aware_audio_params |
| `python/features/statistics.py` | CSV-Statistiken, Filesize-Helper |
| `python/config/config_loader.py` | ConfigParser mit Inline-Kommentar-Stripping, TVBConfig-Klasse |
| `python/tvb-config.ini` | Encoding-Parameter für movie/tvshow/custom, Atmos/Date-Datum-Konfiguration |

### Phase 2: Electron-Frontend (vollständig)

| Komponente | Beschreibung |
|---|---|
| `electron/main.js` | IPC-Handler (transcode:start/stop, config, stats, logs, dialog, tools). Wandelt Python-JSON in renderer-Events um. Dialog erlaubt Ordner + Mehrfachauswahl |
| `electron/preload.js` | contextBridge: onProgress, onLog, onComplete, onError, readStats, readLogs, etc. |
| `client/src/TranscodeControl.jsx` | Eingabe (Input/Output/Format), Toggles (Preview/Atmos/Dry-Run), Start/Stop. Input unterstützt Ordner + mehrere Dateien. Preview-Label dynamisch aus Config |
| `client/src/ProgressDisplay.jsx` | Batch-Progress + File-Progress Bars |
| `client/src/StatsDashboard.jsx` | CSV-Parsing mit Quoting, Pagination (4/Seite), Tooltip bei Hover, neueste zuerst |
| `client/src/LogViewer.jsx` | Live-Logs, Auto-Scroll, Clear (leert Log + Anzeige), Level-Einfärbung, linksbündig |
| `client/src/ConfigEditor.jsx` | Config-Textarea mit Save, informiert App über Config-Änderungen |
| `client/src/CollapsibleSection.jsx` | Zusammenklappbare Blöcke für Stats/Log/Config |

### GUI-Fixes + Features (Session 21. Mai)

| Fix / Feature | Beschreibung |
|---|---|
| Input mit Mehrfachauswahl + Ordner | Dialog erlaubt `openFile + openDirectory + multiSelections`, Python akzeptiert mehrere `-i` |
| Log Viewer linksbündig | Timestamp/Level nur bei vorhandenem Timestamp rendern, `min-width` entfernt |
| Clear-Button leert Anzeige | `onClear`-Callback leert Parent-State (`logs[]`) zusätzlich zur Log-Datei |
| Responsive Layout | `max-width` entfernt, Padding/Abstände reduziert, Elemente stretchen mit Fenster |
| Preview-Label dynamisch | Liest `duration:` aus `[preview]`-Sektion nach "Save Config" und zeigt `30s`/`5min` etc. |
| Audio-Track-Namen mit Kanalinfo | `_get_audio_track_name()` ergänzt Mono/Stereo/5.1/7.1 anhand der Kanäle |
| HandBrakeCLI Version | `get_handbrake_version()` loggt installierte Version (z.B. `1.8.2`) |

### Electron-Runtime

- Electron v42.2.0 separat unter `~/.local/electron/` (nicht per npm im Projekt — `require('electron')` shadowed sonst den built-in)
- Start: `ELECTRON_RUN_AS_NODE="" /Users/stephan/.local/electron/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron .`
- Dev-Modus: Vite auf Port 5173, Electron fällt auf `client/dist/index.html` zurück

## Noch offen / Ausstehend

### Cross-Platform Packaging

| Komponente | Status | Beschreibung |
|---|---|---|
| Windows-Build | ❌ | Benötigt native `.exe`/`.dll` in `bin/` + Build auf Windows |
| Linux-Build | ❌ | CI via GitHub Actions möglich (`.github/workflows/build.yml` vorhanden) |

### Dokumentation

| Komponente | Status |
|---|---|
| README mit Installation, Usage, Build | ✅ |
| macOS-Notarisierung | ❌ (erfordert Apple Developer Account) |

### Unit-Tests

| Kategorie | Tests | Status |
|---|---|---|
| Video Options | HEVC/NVENC/AV1 Defaults, H264 Bitrate/Downscale/VBV, Framerate | ✅ 9 Tests |
| Audio Options | AAC Copy/Encode, OPUS/EAC3 Bitrates, EAC3 Copy-Conditions | ✅ 4 Tests |
| Audio Track Names | Kanalinfo (Stereo/5.1) in Track-Name | ✅ 1 Test |
| Encoder Options | NVENC HEVC/AV1 spatial_aq + b_ref_mode, H264 VBV | ✅ 3 Tests |

**Gesamt: 16 Tests** — alle grün. Ausführung: `python3 -m unittest discover tests/ -v`

### Projektstruktur (nach Bereinigung)

```
tvb-electron/
├── .gitignore
├── LICENSE              MIT
├── PROJECT_PLAN.md
├── STATUS.md
├── README.md
├── package.json
├── vite.config.js
├── setup-electron.sh    macOS Dev-Setup
├── setup-electron.bat   Windows Dev-Setup
├── bin/                 Gebündelte Binaries
├── client/              React-Frontend (Vite)
├── electron/            Electron main + preload
├── python/              Python-Backend
└── tests/               Unit-Tests
```
| File Date Preservation (yes) | ✅ `preserve_file_date=yes`, Input/Output: `Feb 6 2016` identisch |
| Umlaute + Sonderzeichen | ✅ `Ä`, `'`, Spaces im Dateinamen — kein Fehler |
| CSV Stats | ✅ Korrektes Quoting, Encoding-Dauer, Größenvergleich |

### Gefundene & behobene Bugs

| Bug | Ursache | Fix |
|---|---|---|
| Leeres `--mixdown` Argument | `_get_audio_encoding_params` gibt `''` für Copy-Tracks → `','.join([''])` → `--mixdown ` (leer) | `generator.py`: Empty-Werte filtern vor `','.join()` |
| Pfade mit Leerzeichen brechen | `' '.join(cmd_list)` → `shlex.split()` zerbricht Pfade an Spaces | `tvb.py`: `quote_arg()` wrapper quoted Pfade beim String-Join |
| CSV-Duplikate | `tvb-stats.csv` wird nicht vor jedem Lauf geleert → Append-Mode sammelt alte Einträge | Dokumentiert (kein Bug, intended behavior)

### Build-Befehle

```bash
# Kompletter Build (React + Python)
npm run build

# Distribution erstellen (macOS)
npm run dist

# Distribution (Linux — nur auf Linux)
npm run dist:linux

# CI-Build (GitHub Actions)
# → git tag v1.0.0 && git push --tags
# → Workflow .github/workflows/build.yml baut macOS + Linux automatisch
```

### Bekannte Limitationen

- **Keine macOS-Notarisierung**: Ad-hoc Signatur ohne Developer-ID — führt zu Gatekeeper-Warnung beim ersten Start. Für Notarisierung wird ein Apple Developer Account ($99/Jahr) benötigt
- **Cross-Platform Builds**: GitHub Actions Workflow (`.github/workflows/build.yml`) erstellt bei git Tag `v*` automatisch macOS DMG + Linux AppImage. Für Windows werden native Binaries (HandBrakeCLI.exe, ffprobe.exe, libmediainfo.dll) im `bin/` Ordner benötigt
- **Pyinstaller-Bundle**: HandBrakeCLI, libmediainfo.dylib und ffprobe sind im pyinstaller-Binary eingebettet (47MB total)

## Key Learnings

### Electron + require('electron')

`require('electron')` im main process funktioniert NICHT, wenn `node_modules/electron/` existiert. Die npm package exportiert ab v22+ nur den Binary-Pfad als String, shadowed den built-in. Lösung: Electron separat installieren (`~/.local/electron/`), `ELECTRON_RUN_AS_NODE` unset.

### Vite + Electron

- Vite-Config im Root, `root: 'client'`, `base: './'`
- Build: `npm run build:react` → `client/dist/`
- Electron lädt `client/dist/index.html` (production) oder `localhost:5173` (dev)

### Python Backend

- **Log-Duplikate vermeiden**: `console_handler` → stderr, `JsonLogHandler` → stdout. Nur JsonLogHandler liefert JSON an Electron.
- **`-x` Parameter**: `startswith('--')` erfasst keine Single-Dash-Params → separat behandeln.
- **Config Inline-Kommentare**: `re.sub(r'\s+#.*$', '', line)` statt `partition('#').
- **Atmos im Generator**: `set_atmos_tracks()` vor `generate_command_list()` aufrufen, damit Encoder und Track-Namen konsistent sind.
- **Leeres `--mixdown` vermeiden**: Bei `aencoder copy` wird kein Mixdown benötigt. Leere Mixdown-/Bitrate-Werte in `_get_audio_options()` filtern.
- **Pfade mit Leerzeichen quoten**: `' '.join(cmd_list)` bricht Pfade mit Spaces. `quote_arg()` in `process_file()` stelltsicher, dass `shlex.split()` korrekt parst.
- **CSV-Kommando-Quote**: Das Kommando wird mit `"` gequotet in die CSV geschrieben. `""`-Escaping im CSV-Parser (`StatsDashboard`) wird korrekt behandelt.

### React / CSS

- **CSV mit `\r\n`**: `split('\n')` hinterlässt `\r` am letzten Feld → `line.replace(/\r$/, '')` vor Parsen.
- **CSV-Quoting**: `split(';')` zerlegt quoted fields → eigener Parser mit InQuotes-Tracking.
- **Pagination**: `reverse()` für neueste zuerst, `slice()` für Pages, Button-Navigation.
- **Tooltip**: via React State + `getBoundingClientRect`, nicht CSS-`:hover`.
- **Collapsible Sections**: Eigenes Component, Header mit ▾/▸, Body wird conditional gerendert.

## Projekt-Struktur

```
/Users/stephan/SynologyDrive/Code/tvb-electron/
├── .gitignore
├── .venv/                     ← Python venv für pyinstaller (Build-Tool)
├── PROJECT_PLAN.md
├── STATUS.md                  ← diese Datei
├── package.json
├── setup-electron.sh          ← Electron-Setup für Dev-Umgebung
├── vite.config.js
├── build/                     ← electron-builder build resources
├── release/                   ← electron-builder Output (DMG, ZIP)
├── bin/
│   ├── HandBrakeCLI
│   └── libmediainfo.dylib
├── electron/
│   ├── main.js
│   └── preload.js
├── client/
│   ├── index.html
│   ├── dist/                  ← Vite-Build-Output
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── TranscodeControl.jsx/css
│           ├── ProgressDisplay.jsx/css
│           ├── StatsDashboard.jsx/css
│           ├── LogViewer.jsx/css
│           ├── ConfigEditor.jsx/css
│           └── CollapsibleSection.jsx
├── python/
│   ├── tvb.py
│   ├── tvb-config.ini
│   ├── tvb.spec               ← pyinstaller spec (generiert)
│   ├── dist/                  ← pyinstaller Output (tvb binary)
│   ├── build/                 ← pyinstaller build cache
│   ├── __init__.py
│   ├── transcode/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   └── generator.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── atmos.py
│   │   └── statistics.py
│   └── config/
│       ├── __init__.py
│       └── config_loader.py
└── old_project_sources/       ← Referenz (unverändert)
```

## Start-Befehle

```bash
# CLI Dry-Run
cd python && python3 tvb.py -i "/pfad/datei.mkv" -d

# GUI (vorher build:react)
npm run build:react && npm start
```