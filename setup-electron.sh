#!/bin/bash
# Setup Electron for TVB — installs to ~/.local/electron
set -e

ELECTRON_VERSION="42.2.0"
ELECTRON_DIR="$HOME/.local/electron"
ARCH=$(uname -m)
OS=$(uname -s)

case "$OS" in
  Darwin)
    ARCH_NAME="darwin-x64"
    [ "$ARCH" = "arm64" ] && ARCH_NAME="darwin-arm64"
    ELECTRON_BINARY="node_modules/electron/dist/Electron.app/Contents/MacOS/Electron"
    ;;
  Linux)
    ARCH_NAME="linux-x64"
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
      ARCH_NAME="linux-arm64"
    fi
    ELECTRON_BINARY="node_modules/electron/dist/electron"
    ;;
  *)
    echo "Unsupported operating system: $OS"
    exit 1
    ;;
esac

echo "Setting up Electron v${ELECTRON_VERSION} for ${ARCH_NAME}..."

# Install npm package without binary
mkdir -p "$ELECTRON_DIR"
cd "$ELECTRON_DIR"
npm init -y --silent 2>/dev/null || true
ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm install electron@${ELECTRON_VERSION} --save-dev --silent 2>/dev/null

# Download and extract Electron binary
ZIP="electron-v${ELECTRON_VERSION}-${ARCH_NAME}.zip"
if [ ! -f "$ELECTRON_BINARY" ]; then
  echo "Downloading Electron binary..."
  curl -L --fail -o "$ZIP" "https://github.com/electron/electron/releases/download/v${ELECTRON_VERSION}/${ZIP}"
  unzip -q -o "$ZIP" -d node_modules/electron/dist
  rm "$ZIP"
  if [ "$OS" = "Darwin" ]; then
    echo -n "Electron.app/Contents/MacOS/Electron" > node_modules/electron/path.txt
  else
    chmod +x "$ELECTRON_BINARY"
  fi
fi

echo "Electron v${ELECTRON_VERSION} ready at $ELECTRON_DIR"
echo ""
echo "To start TVB:"
echo "  cd \"$(cd "$(dirname "$0")" && pwd)\""
echo "  npm start"
echo ""
echo "To build a distributable package:"
echo "  npm run dist"
