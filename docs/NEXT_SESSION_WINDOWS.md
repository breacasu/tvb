# tvb - Windows Handoff

This document is for the next validation session on Windows.

## Repository

- Repository: `https://github.com/breacasu/tvb`
- Branch: `dev`
- Current commit: `d74d406 Mark Linux unsupported`
- Do not work on or push to `main`.
- Use a local Windows checkout. Do not use the NAS as the Git worktree.

Clone or update the repository on Windows:

```bat
git clone --branch dev https://github.com/breacasu/tvb.git C:\Code\tvb
cd /d C:\Code\tvb
```

## Current State

- Shared Python backend for CLI and Electron GUI
- Project-local `.venv`; do not modify system Python
- Windows x64 and ARM64 tool manifests with SHA256 verification
- HandBrakeCLI `1.11.2`
- ffprobe `8.1.2` on Windows x64
- Current BtbN ffprobe build on Windows ARM64
- MediaInfo `26.05` on Windows x64 and ARM64
- Electron `43.2.0`
- Linux is explicitly unsupported because HandBrake publishes no standalone Linux CLI runtime

## Windows Setup

Run from the local checkout:

```bat
setup-electron.bat
setup.bat
call .venv\Scripts\activate.bat
python scripts\stage_tools.py
python scripts\verify_tools.py
npm ci
```

`stage_tools.py` replaces stale local files when a matching tool is available
from the cache, `C:\bin`, or `PATH`. The final `verify_tools.py` result must
show `OK` for HandBrakeCLI, ffprobe and libmediainfo.

## Required Tests

Run at least:

```bat
.venv\Scripts\python.exe -m unittest discover tests -v
npm run build:win
npm run dist:win
```

Install the generated NSIS installer and test the installed GUI, not only the
development start. Install test-only dependencies if GUI automation is used:

```bat
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
```

## Real Media Tests

Use the NAS collection, with the exact mount path adjusted for Windows:

```text
\\DS1817plus\Media\Unsortiert\Encode_Testfiles
```

Run a real 30-second Atmos preview with:

```text
Unsortiert\Encode_Testfiles\1080p\The.Mandalorian.S02E01.German.EAC3D.DL.2160p.HDR.WEBRip.x265-sample.mkv
```

Confirm the output retains `E-AC-3` with the Dolby Atmos profile.

Run a real 30-second PGS preview with:

```text
Unsortiert\Encode_Testfiles\1080p\Kong.Skull.Island.2017.German.DTS.DL.1080p.BluRay.x265-sample.mkv
```

Confirm the output retains `hdmv_pgs_subtitle`.

Both outputs must pass the bundled ffprobe validation. Run the installed GUI
smoke test and subtitle matrix if the existing Windows test collection is
available:

```bat
.venv\Scripts\python.exe tests\gui_smoke.py --help
```

## Before Push

- Confirm the installer uses bundled tools rather than `PATH` tools.
- Confirm Atmos and PGS outputs pass ffprobe.
- Confirm no invalid output remains after a failed encode.
- Run the full subtitle matrix if time permits.
- Commit only tested changes to `dev`.
- Report the commit SHA, Windows architecture, tool versions and test files.

## Known Follow-Up

- Linux remains unsupported.
- macOS arm64 validation is complete.
- macOS signing and notarization remain open.
- Third-party license/source files for every bundled binary still need completion.
