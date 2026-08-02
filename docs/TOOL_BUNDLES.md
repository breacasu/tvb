# Tool Bundles

TVB release installers must work without a system Python, Ruby, HandBrake or
ffprobe installation.

## Source Repository

Platform binaries are not committed to Git. They are too large, platform
specific and difficult to update safely in normal source history.

## Local Development

`TVB_TOOLS_CACHE` may point to a cache outside the repository. The default is:

- Windows: `%LOCALAPPDATA%\tvb\tools`
- macOS/Linux: `~/.cache/tvb/tools`

The cache contains a platform subdirectory such as `win32-x64`. The staging
script copies only files matching `tools.lock.json` and verifies their SHA256
hashes before placing them in the local ignored `bin/` directory.

```text
tools-cache/
└── win32-x64/
    ├── HandBrakeCLI.exe
    ├── ffprobe.exe
    ├── libmediainfo.dll
```

This allows a developer to build offline after the cache has been populated.
The cache is not needed by end users because release installers contain the
tools already.

## CI and Releases

GitHub Actions must fetch the exact versions in `tools.lock.json`, verify the
checksums, build on the native target runner and publish only the finished
installer as a GitHub Release asset. A clean runner must never use tools from
its global `PATH`.

The Windows x64/ARM64 and macOS arm64 manifests are populated from verified
platform artifacts. Linux is still the most involved target because HandBrake
currently distributes its Linux CLI through Flatpak rather than a simple
standalone archive; the release build needs a reproducible source build or an
extracted, license-compliant runtime bundle.
