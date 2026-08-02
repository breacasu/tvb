#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
ARCH=$(uname -m)
PLATFORM="macos"
[ "$ARCH" = "arm64" ] && ARCH_LABEL="arm64" || ARCH_LABEL="x86_64"

echo "=== TVB Binary Setup ==="
echo "Platform: ${PLATFORM} / ${ARCH_LABEL}"
echo ""

mkdir -p "$BIN_DIR"

# --- HandBrakeCLI ---
HBCLI="$BIN_DIR/HandBrakeCLI"
if [ -f "$HBCLI" ]; then
    echo "[OK] HandBrakeCLI already exists at $HBCLI"
elif command -v HandBrakeCLI &>/dev/null; then
    echo "[OK] HandBrakeCLI found in PATH: $(command -v HandBrakeCLI)"
else
    HANDBRAKE_VERSION="1.9.2"
    if [ "$ARCH" = "arm64" ]; then
        HANDBRAKE_URL="https://github.com/HandBrake/HandBrake/releases/download/${HANDBRAKE_VERSION}/HandBrakeCLI-${HANDBRAKE_VERSION}-arm64.dmg"
    else
        HANDBRAKE_URL="https://github.com/HandBrake/HandBrake/releases/download/${HANDBRAKE_VERSION}/HandBrakeCLI-${HANDBRAKE_VERSION}-x86_64.dmg"
    fi
    echo "Downloading HandBrakeCLI ${HANDBRAKE_VERSION}..."
    DMG="HandBrakeCLI.dmg"
    curl -L --fail -o "$DMG" "$HANDBRAKE_URL"
    hdiutil attach "$DMG" -mountpoint /tmp/hb_mnt -nobrowse -quiet
    cp /tmp/hb_mnt/HandBrakeCLI "$HBCLI"
    hdiutil detach /tmp/hb_mnt -quiet
    rm "$DMG"
    chmod +x "$HBCLI"
    echo "[OK] HandBrakeCLI installed to $HBCLI"
fi

# --- ffprobe ---
FFPROBE="$BIN_DIR/ffprobe"
if [ -f "$FFPROBE" ]; then
    echo "[OK] ffprobe already exists at $FFPROBE"
elif command -v ffprobe &>/dev/null; then
    echo "[OK] ffprobe found in PATH: $(command -v ffprobe)"
else
    echo "Downloading ffprobe (static build)..."
    FFMPEG_URL="https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    curl -L --fail -o ffprobe.zip "$FFMPEG_URL"
    unzip -q -o ffprobe.zip -d "$BIN_DIR"
    rm ffprobe.zip
    chmod +x "$BIN_DIR"/ffprobe 2>/dev/null || true
    chmod +x "$FFPROBE" 2>/dev/null || true
    ls -la "$BIN_DIR"/ffprobe* 2>/dev/null

    if [ ! -f "$FFPROBE" ]; then
        echo "[WARN] ffprobe download failed. Install ffmpeg via: brew install ffmpeg"
    else
        echo "[OK] ffprobe installed to $FFPROBE"
    fi
fi

# --- libmediainfo (for pymediainfo / Dolby Atmos detection) ---
LIBMI="$BIN_DIR/libmediainfo.dylib"
if [ -f "$LIBMI" ]; then
    echo "[OK] libmediainfo already exists at $LIBMI"
else
    echo "Installing libmediainfo..."

    # Try Homebrew first
    if command -v brew &>/dev/null; then
        brew install libmediainfo 2>/dev/null || true
        MI_LIB=$(brew --prefix libmediainfo 2>/dev/null)/lib/libmediainfo.dylib
        if [ -f "$MI_LIB" ]; then
            cp "$MI_LIB" "$LIBMI"
            echo "[OK] libmediainfo installed from Homebrew"
        else
            echo "[WARN] brew install libmediainfo succeeded but lib not found at $MI_LIB"
        fi
    fi

    # Fallback: download from MediaArea if not found via brew
    if [ ! -f "$LIBMI" ]; then
        echo "Downloading libmediainfo.dylib from MediaArea..."
        MEDIAINFO_VERSION="24.06"
        if [ "$ARCH" = "arm64" ]; then
            LIBMI_URL="https://mediaarea.net/download/binary/libmediainfo0/${MEDIAINFO_VERSION}/MediaInfo_DLL_${MEDIAINFO_VERSION}_Mac_x64_WithoutInstaller.tar.bz2"
        else
            LIBMI_URL="https://mediaarea.net/download/binary/libmediainfo0/${MEDIAINFO_VERSION}/MediaInfo_DLL_${MEDIAINFO_VERSION}_Mac_x64_WithoutInstaller.tar.bz2"
        fi
        TARBALL="libmediainfo.tar.bz2"
        curl -L --fail -o "$TARBALL" "$LIBMI_URL" || {
            echo "[WARN] Download failed. Install manually: brew install libmediainfo"
            rm -f "$TARBALL"
        }
        if [ -f "$TARBALL" ]; then
            tar -xjf "$TARBALL" -C /tmp
            find /tmp -name "libmediainfo.dylib" -exec cp {} "$LIBMI" \; 2>/dev/null || true
            rm "$TARBALL"
            rm -rf /tmp/libmediainfo* 2>/dev/null || true
            if [ -f "$LIBMI" ]; then
                echo "[OK] libmediainfo.dylib downloaded to $LIBMI"
            else
                echo "[WARN] Could not extract libmediainfo.dylib from download"
            fi
        fi
    fi
fi

# --- Python dependencies ---
echo ""
echo "=== Python setup ==="
# Use a project-local environment. Never modify the user's global Python.
PYTHON_BASE=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON_BASE" ]; then
    echo "[ERROR] Python 3 is required to create the build environment."
    exit 1
fi

if [ ! -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    "$PYTHON_BASE" -m venv "$SCRIPT_DIR/.venv"
fi

PYTHON="$SCRIPT_DIR/.venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "=== Setup complete ==="
echo "Binaries in: $BIN_DIR"
echo ""
echo "Next: npm install && npm run build"
