#!/usr/bin/env python3
"""Stage verified platform tools from a cache or local installation."""

import argparse
import hashlib
import json
import os
import platform
import shutil
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


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def cache_dir() -> Path:
    configured = os.environ.get("TVB_TOOLS_CACHE")
    if configured:
        return Path(configured)
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "tvb" / "tools"
    return Path.home() / ".cache" / "tvb" / "tools"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage TVB runtime tools")
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--target", type=Path, default=ROOT / "bin")
    args = parser.parse_args()

    target_platform = platform_key()
    manifest = json.loads((ROOT / "tools.lock.json").read_text(encoding="utf-8"))
    tools = manifest["platforms"].get(target_platform)
    if not tools or "status" in tools:
        print(f"No complete tool manifest exists for {target_platform}.", file=sys.stderr)
        return 2

    source_root = (args.source or cache_dir()) / target_platform
    args.target.mkdir(parents=True, exist_ok=True)
    failed = False

    for name, expected in tools.items():
        filename = expected["filename"]
        candidates = [source_root / filename, args.target / filename]
        installed = resolve_tool(name)
        if installed:
            candidates.append(Path(installed))
        if sys.platform == "win32":
            candidates.append(Path("C:/bin") / filename)
        path_installed = shutil.which(filename) or shutil.which(name)
        if path_installed:
            candidates.append(Path(path_installed))

        source = None
        seen = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen or not candidate.is_file():
                continue
            seen.add(resolved)
            if file_hash(candidate) == expected["sha256"]:
                source = candidate
                break

        if source is None:
            existing = next((path for path in candidates if path.is_file()), None)
            if existing:
                print(f"MISMATCH {name}: no candidate matches the locked SHA256")
            else:
                print(f"MISSING {name}: place {filename} in {source_root}")
            failed = True
            continue

        actual = file_hash(source)
        if actual != expected["sha256"]:
            print(f"MISMATCH {name}: {source}")
            failed = True
            continue

        destination = args.target / filename
        if source.resolve() != destination.resolve():
            # Homebrew libraries can be staged read-only; unlink first so a
            # previous staging run cannot block replacement on macOS.
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            shutil.copy2(source, destination)
        print(f"STAGED {name}: {destination}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
