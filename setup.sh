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
    if [ "$ARCH" = "arm64" ]; then
        FFMPEG_URL="https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    else
        FFMPEG_URL="https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    fi
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
    echo "Installing libmediainfo via Homebrew..."
    if command -v brew &>/dev/null; then
        brew install libmediainfo 2>/dev/null || true
        MI_LIB=$(brew --prefix libmediainfo 2>/dev/null)/lib/libmediainfo.dylib
        if [ -f "$MI_LIB" ]; then
            cp "$MI_LIB" "$LIBMI"
            echo "[OK] libmediainfo installed to $LIBMI"
        else
            echo "[WARN] Could not find libmediainfo after brew install"
        fi
    else
        echo "[WARN] Homebrew not found. Install manually: brew install libmediainfo"
    fi
fi

# --- Python dependencies ---
echo ""
echo "=== Python setup ==="
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null || true
fi
pip3 install pymediainfo 2>/dev/null || true

echo ""
echo "=== Setup complete ==="
echo "Binaries in: $BIN_DIR"
echo ""
echo "Next: npm start"