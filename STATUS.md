# tvb Status

Stand: 2026-08-02

## Current

- Shared Python backend for CLI and GUI
- Vite/React frontend
- Electron IPC with buffered JSON-line parsing
- One completion event with process exit status
- Project-local Python `.venv` for setup and PyInstaller
- ffprobe-first Atmos detection
- MediaInfo fallback for ambiguous E-AC-3/TrueHD input
- Invalid MKV input is rejected without source modification
- Crop detection exposed through `MediaAnalyzer`
- Windows tool manifest with SHA256 verification
- Windows PyInstaller and NSIS build working
- Runtime data stored in the application user-data directory
- Transparent application icons for Windows, macOS and Linux
- Installed GUI smoke test through UI Automation and Chrome DevTools
- Post-encode ffprobe validation; invalid outputs are removed

## Verified

- 25 Python unit tests pass
- React production build passes
- Windows Python bundle builds `tvb.exe`
- Windows installer builds successfully
- Bundled CLI dry-run works against NAS input
- Real short M4V encode succeeds with the bundled HandBrakeCLI
- Bundled Windows tools verified: HandBrakeCLI, ffprobe, libmediainfo
- Crop detection runs through `MediaAnalyzer` against a real NAS test file
- Installed GUI completes Atmos and HDMV/PGS preview workflows
- Atmos output retains the E-AC-3 Atmos profile and copy track
- PGS output retains both HDMV PGS subtitle tracks
- Both GUI outputs pass ffprobe
- All 391 MKV files in the NAS test collection pass ffprobe
- 27 distinct subtitle inputs pass the installed GUI preview matrix
- 12 HDMV/PGS cases retain PGS subtitles in their outputs
- No invalid MKV output was produced by the matrix

## Still Open

- Move the current project into the canonical `breacasu/tvb` repository
- Complete macOS and Linux tool manifests
- Reproducible CI downloads for all supported platforms
- Linux HandBrakeCLI bundle strategy
- Native macOS/Linux builds and installers
- Complete third-party license collection in release assets
- Full regression matrix over all non-subtitle encoding presets and test files
- Final parity review against the old CLI and `transcode-video.rb`

## Deliberately Removed

- Ruby runtime and `transcode-video.rb`
- `-H`/`--hibernate`
- CPU limiting
- User-visible `-m`/`--merge` option
- `mkvpropedit` subtitle post-processing
- `convert-video.rb` functionality
