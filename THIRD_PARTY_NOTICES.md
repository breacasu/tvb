# Third-Party Notices

The development tree does not commit platform binaries. Release installers
contain the exact versions listed in the release manifest and must include the
corresponding license texts and source links.

## Runtime Tools

- HandBrakeCLI: https://github.com/HandBrake/HandBrake
- FFmpeg/ffprobe: https://ffmpeg.org/
- MediaInfo / MediaInfoLib: https://mediaarea.net/MediaInfo
The release build must record the version, source archive, SHA256 checksum and
license for every platform-specific binary. The concrete ffprobe build also
determines whether FFmpeg GPL obligations apply; see
https://ffmpeg.org/legal.html.

## JavaScript Dependencies

Electron, React, ReactDOM, Vite and electron-builder are distributed under the
licenses declared by their respective packages in `package-lock.json`.

This file is intentionally a release checklist until the platform tool
manifest and automated license collection are implemented.
