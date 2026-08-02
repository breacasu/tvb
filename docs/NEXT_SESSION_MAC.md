# tvb - Mac Handoff

This document is the handoff for the next coding session on macOS.

## Repository

- Repository: `https://github.com/breacasu/tvb`
- Branch: `dev`
- Current commit: `c8113e2 Use Lisa defaults for empty presets`
- Do not work on or push to `main`.
- The old local folders `tvb-electron` and the previous non-git `tvb` copy are not the source of truth anymore.

Clone or update the repository on macOS and work on `dev`:

```bash
```

## Current State

The project is now one application named `tvb` with a shared Python backend
for the CLI and Electron GUI.

Implemented:

- Vite/React frontend and Electron main/preload process
- Shared Python CLI backend
- Project-local `.venv`; do not modify system Python
- ffprobe-first Atmos detection
- MediaInfo fallback only for ambiguous E-AC-3/TrueHD input
- Crop detection exposed through `MediaAnalyzer.detect_crop()`
- No separate `tvb-crop` executable
- No Ruby runtime or `transcode-video.rb`
- No `mkvmerge` fallback or mkvmerge in the release bundle
- ffprobe validation after every successful encode
- Invalid outputs are deleted and reported as failed
- Modern transparent icons in `build/icon.svg`, `build/icon.png`, `build/icon.ico` and `build/icon.icns`
- Windows tool lock and SHA256 verification
- GUI smoke-test helper in `tests/gui_smoke.py`
- Empty/missing `movie`, `tvshow` and `custom` parameters use Lisa Melton defaults

## Tested on Windows

- 25 unit tests after mkvmerge removal
- Windows PyInstaller build
- Windows NSIS installer
- Installed GUI with Atmos preview
- Installed GUI with HDMV/PGS preview
- 27 distinct subtitle inputs with 30-second preview
- 12 PGS cases retained PGS subtitles
- All 391 MKV files in the NAS collection pass ffprobe
- Atmos output retained the E-AC-3 Atmos profile

The test collection was on a NAS at:

```text
\\DS1817plus\Media\Unsortiert\Encode_Testfiles
```

The exact mount path may differ on macOS.

## Immediate Mac Work

The macOS arm64 tool manifest is now populated for the current Apple Silicon
target. `linux-x64` and `linux-arm64` remain pending because HandBrake only
publishes a Linux Flatpak bundle, not a standalone CLI runtime.

Complete the macOS target first:

1. Use the project-local `.venv` and install `requirements.txt`.
2. Run the macOS setup without changing global Python packages.
3. Obtain exact versions of HandBrakeCLI, ffprobe and libmediainfo.dylib.
4. Place them in the local ignored tool cache or `bin/`.
5. Add the macOS versions and SHA256 hashes to `tools.lock.json`.
6. Make `scripts/stage_tools.py` and `scripts/verify_tools.py` pass on macOS.
7. Verify executable permissions and dynamic library loading.
8. Run unit tests and a real 30-second Atmos and PGS preview.
9. Run `npm run build` and `npm run dist` on macOS.
10. Test the installed `.dmg`/application, not only the development start.

The steps above were completed on macOS 26.5 arm64. See `STATUS.md` for the
validated tool versions, previews and remaining signing/Intel follow-up.

Expected macOS runtime tools:

- HandBrakeCLI
- ffprobe
- libmediainfo.dylib only when the Atmos fallback is actually needed
- no Ruby
- no full ffmpeg binary
- no mkvmerge

## Configuration Semantics

If a mode parameter is empty or the mode section is missing, the generator
uses Lisa Melton's defaults:

- H.264/x264
- resolution-based bitrate
- multi-pass and turbo
- first audio track
- automatic forced subtitle handling
- conservative crop mode

The current example config intentionally defines HEVC presets. An empty preset
does not mean the current HEVC preset; it means the original Lisa defaults.

## Validation Before Any Push

Run at least:

```bash
.venv/bin/python -m unittest discover tests -v
.venv/bin/python scripts/verify_tools.py
npm run build:react
npm run build
npm run dist
```

Do not push to `main`. Push tested changes only to `dev` and report the commit
SHA, target platform, tool versions and test files used.

## Known Follow-Up Work

- Complete macOS and Linux tool bundles and release CI.
- Finish repository cleanup after the Mac validation.
- Recheck GUI automation's format-selection behavior on the target platform.
- Add third-party license/source files for every bundled binary.
