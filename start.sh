#!/bin/sh
set -eu

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ELECTRON_DIR="${HOME}/.local/electron/node_modules/electron/dist"

case "$(uname -s)" in
  Darwin)
    ELECTRON="${ELECTRON_DIR}/Electron.app/Contents/MacOS/Electron"
    ;;
  Linux)
    ELECTRON="${ELECTRON_DIR}/electron"
    ;;
  *)
    echo "Unsupported operating system: $(uname -s)" >&2
    exit 1
    ;;
esac

if [ ! -x "$ELECTRON" ]; then
  echo "Electron runtime not found at: $ELECTRON" >&2
  echo "Run setup-electron.sh first." >&2
  exit 1
fi

unset ELECTRON_RUN_AS_NODE
exec "$ELECTRON" "$APP_DIR/electron/main.js" "$@"
