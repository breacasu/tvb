#!/usr/bin/env python3
"""Verify locally available runtime tools against tools.lock.json."""

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from tool_paths import resolve_tool  # noqa: E402


def platform_key():
    if sys.platform == "win32":
        return "win32-arm64" if "ARM64" in os.environ.get("PROCESSOR_ARCHITECTURE", "") else "win32-x64"
    if sys.platform == "darwin":
        return "darwin-arm64" if platform.machine() == "arm64" else "darwin-x64"
    if sys.platform == "linux":
        return "linux-arm64" if platform.machine() in {"aarch64", "arm64"} else "linux-x64"
    return "linux-x64"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    manifest = json.loads((ROOT / "tools.lock.json").read_text(encoding="utf-8"))
    target = platform_key()
    tools = manifest["platforms"].get(target)
    if not tools or "status" in tools:
        print(f"No complete tool manifest exists for {target}.", file=sys.stderr)
        return 2

    failed = False
    for name, expected in tools.items():
        path_string = resolve_tool(name)
        if not path_string:
            print(f"MISSING {name}: {expected['filename']}")
            failed = True
            continue
        actual = sha256(Path(path_string))
        if actual != expected["sha256"]:
            print(f"MISMATCH {name}: {path_string}")
            print(f"  expected {expected['sha256']}")
            print(f"  actual   {actual}")
            failed = True
        else:
            print(f"OK {name} {expected['version']}: {path_string}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
