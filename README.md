# TVB — Transcode Video Batch

Electron-App mit Python-Backend zum Batch-Transkodieren von Videodateien via HandBrakeCLI.

Der HandBrakeCLI-Generator ist **1:1 kompatibel** zu Lisa Meltons `transcode-video.rb`.

## Features

- **Batch-Encoding**: Beliebig viele Dateien oder ganze Ordner in einem Durchlauf
- **Auto-Detect Format**: Erkennt TV-Show (S01E01) vs. Movie automatisch
- **Forced Format**: Überschreibt Auto-Detect via `-f movie|tvshow|custom`
- **Preview-Modus**: Nur 30 Sekunden encodieren (`-P`)
- **Dry-Run**: Befehl anzeigen ohne zu encodieren (`-d`)
- **Dolby Atmos Preservation**: Atmos-Tracks werden automatisch als Copy durchgereicht
- **File Date Preservation**: Output behält Erstellungsdatum des Inputs
- **HandBrakeCLI Version Check**: Vergleicht installierte Version mit aktuellster

## Verzeichnisstruktur

```
tvb-electron/
├── electron/              # Electron main + preload
│   ├── main.js
│   └── preload.js
├── client/                # React-Frontend (Vite)
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       └── components/
├── python/                # Python-Backend
│   ├── tvb.py             # CLI-Einstieg
│   ├── tvb-config.ini     # Encoding-Presets
│   ├── transcode/
│   │   ├── generator.py   # HandBrakeCLI-Befehl (Ruby-kompatibel)
│   │   └── analyzer.py    # ffprobe Media-Analyse
│   ├── features/
│   │   ├── atmos.py       # Dolby Atmos Detection
│   │   └── statistics.py  # CSV-Statistiken
│   └── config/
│       └── config_loader.py
├── bin/                   # Gebündelte Binaries
│   ├── HandBrakeCLI
│   ├── ffprobe
│   └── libmediainfo.dylib
├── setup-electron.sh      # Electron-Installation für Dev
├── package.json
└── vite.config.js
```

## Installation (Development)

### 1. Electron

```bash
./setup-electron.sh
```

Installiert Electron v42.2.0 standalone unter `~/.local/electron/`.

### 2. Abhängigkeiten

```bash
npm install
```

### 3. Python-Build-Tools (optional, nur für Distribution)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyinstaller pymediainfo
```

## Verwendung

### CLI (ohne Electron)

```bash
# Einzelne Datei
python3 python/tvb.py -i "movie.mkv" -o "./output"

# Mehrere Dateien
python3 python/tvb.py \
  -i "movie1.mkv" \
  -i "movie2.mkv" \
  -i "movie3.mkv" \
  -o "./output"

# Ganzes Verzeichnis
python3 python/tvb.py -i "./videos/" -o "./output"

# TV-Show forcieren
python3 python/tvb.py -i "episode.mkv" -o "./output" -f tvshow

# Preview (30s) + Dry-Run
python3 python/tvb.py -i "movie.mkv" -o "./output" -P -d --debug
```

### GUI (Electron)

```bash
npm start
```

### Konfiguration

Die Datei `python/tvb-config.ini` enthält Presets für `[movie]`, `[tvshow]` und `[custom]`:

```ini
[movie]
parameter = --mode hevc --quality 24 --add-audio ger --add-audio eng --add-subtitle all

[tvshow]
parameter = --add-audio all --add-subtitle all -x encoder=vt_h265 -x quality=56 -x encoder-preset=quality
```

Die Parameter werden identisch zu Lisa Meltons `transcode-video.rb` geparst (siehe `PROJECT_PLAN.md`).

## Build & Distribution

### Vollständiger Build (React + Python)

```bash
npm run build
```

### macOS Distribution

```bash
npm run dist
```

Erzeugt `release/TVB-1.0.0-arm64.dmg` + `release/TVB-1.0.0-arm64-mac.zip`.

### Linux Distribution

```bash
npm run dist:linux
```

### GitHub Actions CI

Bei einem git Tag `v*` baut der Workflow `.github/workflows/build.yml` automatisch macOS + Linux.

## Technische Details

### Ruby-Kompatibilität

Der `HandBrakeGenerator` (`generator.py`) erzeugt **identische** HandBrakeCLI-Befehle wie Lisa Meltons `transcode-video.rb`. Die INI-Config ist nur ein Preset-Speicher — alle Parameter werden direkt an den Generator übergeben.

Abweichungen (bewusst):
- Audio-Track-Namen mit Kanalinfo: `"German AAC 5.1"`
- Untertitel-Namen lesbarer: `"German forced"` statt rohem `title`-Feld
- EAC3-Passthrough erfasst auch eac3 (verhindert sinnloses Re-encode)

### Version Check

Beim Start prüft `tvb.py`:
1. Lokale HandBrakeCLI-Version via `--version`
2. Aktuellste Version von `https://handbrake.fr/downloads2.php`
3. Loggt z.B. `"installed 1.8.2 (latest 1.11.1) — update recommended"`

### CLI vs GUI

Das Python-Backend ist CLI-first und erzeugt JSON-Zeilen auf stdout für Electron. Gleiches Backend für beide Modi — keine Code-Duplikation.

## Abhängigkeiten

| Komponente | Quelle | Bemerkung |
|---|---|---|
| HandBrakeCLI | `bin/` (gebündelt) | macOS, statisch gelinkt |
| ffprobe | `bin/` (gebündelt) | Von GitHub Release, statisch |
| libmediainfo | `bin/` (gebündelt) | Für pymediainfo |

## Lizenz

MIT License. Siehe `LICENSE`.

Copyright (c) 2026 Breacasu + DeepSeek V4 — Electron-Frontend, Python-Integration, zusätzliche Features.
Copyright (c) 2025 Lisa Melton — `transcode-video.rb` Algorithmus (Portierung in `generator.py`).