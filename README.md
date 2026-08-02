# tvb - Transcode Video Batch

Cross-platform GUI and CLI for batch video transcoding with HandBrakeCLI.
The Python backend is shared by both interfaces and does not require Ruby.

## Features

- Batch encoding of files, directories and recursive directory trees
- Automatic TV-show/movie detection via `S01E01` filenames
- Forced format selection with `-f movie|tvshow|custom`
- Preview mode with `-P`
- Dry-run mode with `-d`
- Dolby Atmos detection via ffprobe first; MediaInfo is used only for ambiguous E-AC-3/TrueHD tracks
- Invalid input metadata is reported without modifying or remuxing the source
- Crop detection through the `MediaAnalyzer`
- File-date preservation
- JSON output for the GUI and readable text output with `--text`

Release installers contain the required runtime tools. Development builds use
the project-local `.venv` and a local tool cache. System Python installations
are not modified by the setup scripts.

## Structure

```text
tvb/
├── electron/              Electron main process and preload bridge
├── client/                React frontend
├── python/                Shared CLI backend
│   ├── transcode/         Analyzer, generator and crop detection
│   ├── features/          Atmos and statistics
│   └── config/            Configuration loader
├── scripts/               Build helpers
├── tests/                 Unit tests
├── bin/                   Local platform-tool cache, not source-controlled
└── package.json
```

## Development Setup

### Windows

```batch
setup-electron.bat
setup.bat
python scripts/stage_tools.py
python scripts/verify_tools.py
npm install
npm run build:win
npm run start:win
```

### macOS

```bash
./setup-electron.sh
./setup.sh
.venv/bin/python scripts/stage_tools.py
.venv/bin/python scripts/verify_tools.py
npm install
npm run build
npm start
```

`setup.sh` creates `.venv` and installs all Python build dependencies there.
It does not install packages into the system Python.

Linux is currently not supported because HandBrake does not publish a
standalone Linux CLI runtime. The Linux GitHub Actions workflow only validates
upstream tools and development checks.

## CLI

### Windows

```batch
.venv\Scripts\python.exe python\tvb.py -i "movie.mkv" -o "output"
.venv\Scripts\python.exe -c "from transcode.analyzer import MediaAnalyzer; print(MediaAnalyzer().detect_crop('movie.mkv'))"
```

### macOS

```bash
.venv/bin/python python/tvb.py -i "movie.mkv" -o "output"
.venv/bin/python -c "from transcode.analyzer import MediaAnalyzer; print(MediaAnalyzer().detect_crop('movie.mkv'))"
```

Examples:

```text
tvb.py -i movie.mkv -o output -f movie
tvb.py -i videos/ -o output -P -d --debug
tvb.py -i episode.mkv --preserve-atmos
tvb.py -i episode.mkv --no-preserve-atmos
MediaAnalyzer().detect_crop("movie.mkv", mode="conservative")
```

The packaged Windows application provides `tvb.bat` for the CLI. The GUI executable is internally named
`tvb-gui.exe` so it cannot collide with the Windows CLI `tvb.exe`.

## Configuration

`python/tvb-config.ini` contains encoding presets. Tool paths are deliberately
not user configuration: bundled tools are resolved automatically. Developers
may set `TVB_TOOLS_DIR` to use a local tool cache.

```ini
[movie]
parameter = --mode hevc --quality 24 --add-audio ger --add-audio eng --add-subtitle all

[tvshow]
parameter = --mode hevc --quality 24 --add-audio all --add-subtitle all

[custom]
parameter = --mode hevc --quality 24 --add-audio all --add-subtitle all
```

Statistics use ISO-8601 timestamps. The old locale setting is no longer
needed and is ignored.

## Build and Distribution

```bash
  npm run build       # React + Python for macOS
  npm run build:win   # React + Python for Windows
  npm run dist:win   # Windows installer
  npm run dist        # macOS distribution
```

The Python build creates the `tvb` executable and embeds the required tools
available in the platform tool bundle. Generated files in
`python/dist`, `python/build` and `release` are not source files.

The planned release process downloads exact tool versions per platform,
verifies SHA256 checksums, creates a native installer and publishes the
installer as a GitHub Release asset. Platform binaries are not committed to
the Git repository.

## Testing

```bash
python -m unittest discover tests -v
npm run build:react
```

Real media test files are kept outside the repository. The current Windows
test collection is available at:

```text
\\DS1817plus\Media\Unsortiert\Encode_Testfiles
```

## License

MIT License. See `LICENSE` and the third-party notices included with releases.
