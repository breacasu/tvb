# tvb Project Plan

## Goal

Deliver one project named `tvb` with a shared CLI/GUI backend. Release
installers must contain all runtime tools and must not require system Python,
Ruby, HandBrakeCLI, ffprobe, MediaInfo or MKVToolNix.

## Completed Foundation

- Python backend separated into analyzer, generator, features and config
- Electron GUI starts the Python backend through a secure preload bridge
- JSON-line protocol for logs, progress, errors and completion
- ffprobe-first Atmos detection with conditional MediaInfo fallback
- Invalid media input is rejected without source modification
- Crop detector ported from detect-crop.rb and exposed through `MediaAnalyzer`
- Local `.venv` setup and PyInstaller build helper
- Windows tool lock, staging and verification
- Windows installer build

## Phase 1: Backend Reliability

- Complete CLI option and generator parity tests
- Validate output naming and nested input directories
- Test failed encodes, cancellation and partial outputs
- Test subtitle handling for SRT, ASS, DVD and HDMV/PGS input
- Run the real NAS test matrix

## Phase 2: Tool Bundles

- Complete exact tool manifests for Windows, macOS and Linux
- Implement archive download and extraction with checksum verification
- Keep platform binaries outside Git history
- Build native platform bundles in GitHub Actions
- Include third-party licenses and source links in releases
- Resolve Linux HandBrakeCLI distribution or source-build strategy

## Phase 3: Application Integration

- Complete packaged GUI smoke tests
- Add clear tool and process error display
- Verify user-data locations for logs, statistics and configuration
- Add CLI launchers for macOS and Linux distributions
- Finish naming migration from `tvb-electron` to `tvb`

## Phase 4: Repository Consolidation

- Use `breacasu/tvb` as the canonical repository
- Move the current application to the repository root
- Compare and remove the old nested `tvb/tvb-electron` copy
- Archive legacy wrappers and Ruby sources temporarily
- Remove generated files and personal data from the source tree
- Publish the first tagged `tvb` release
