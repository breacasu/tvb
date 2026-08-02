#!/usr/bin/env python3
"""Resolve TVB's bundled command line tools.

Released applications must use the tools shipped with the application.  The
PATH lookup remains available for development and for diagnostics only.
"""

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional


TOOL_FILENAMES = {
    "HandBrakeCLI": "HandBrakeCLI.exe" if sys.platform == "win32" else "HandBrakeCLI",
    "ffprobe": "ffprobe.exe" if sys.platform == "win32" else "ffprobe",
    "libmediainfo": (
        "libmediainfo.dll"
        if sys.platform == "win32"
        else "libmediainfo.dylib"
        if sys.platform == "darwin"
        else "libmediainfo.so"
    ),
}


def _platform_key() -> str:
    system = {
        "win32": "win32",
        "darwin": "darwin",
        "linux": "linux",
    }.get(sys.platform, sys.platform)
    architecture = (
        os.environ.get("PROCESSOR_ARCHITECTURE", "")
        + os.environ.get("PROCESSOR_ARCHITEW6432", "")
        + platform.machine()
    ).lower()
    arch = "arm64" if "arm64" in architecture or "aarch64" in architecture else "x64"
    return f"{system}-{arch}"


def _with_platform_subdirectory(directory: Path) -> Iterable[Path]:
    yield directory
    yield directory / _platform_key()


def _candidate_directories() -> Iterable[Path]:
    seen = set()
    roots = []

    configured = os.environ.get("TVB_TOOLS_DIR")
    if configured:
        roots.append(Path(configured))

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
        roots.append(Path(meipass) / "tools")

    executable_dir = Path(sys.executable).resolve().parent
    roots.append(executable_dir)
    roots.append(executable_dir / "tools")

    project_root = Path(__file__).resolve().parent.parent
    roots.append(project_root / "bin")
    roots.append(project_root / "vendor")
    roots.append(project_root / "tools")

    for root in roots:
        for candidate in _with_platform_subdirectory(root):
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


def resolve_tool(name: str, *, allow_path: bool = True) -> Optional[str]:
    """Return an absolute path to a tool, or ``None`` when unavailable."""

    filename = TOOL_FILENAMES.get(name, name)
    for directory in _candidate_directories():
        candidate = directory / filename
        if candidate.is_file():
            return str(candidate)
        if name == "libmediainfo":
            matches = sorted(directory.glob("libmediainfo.*"))
            if matches:
                return str(matches[0])

    bundled_only = bool(getattr(sys, "_MEIPASS", None)) or os.environ.get("TVB_BUNDLED_ONLY") == "1"
    if allow_path and not bundled_only:
        found = shutil.which(filename) or shutil.which(name)
        if found:
            return found

    return None


def require_tool(name: str, *, allow_path: bool = True) -> str:
    path = resolve_tool(name, allow_path=allow_path)
    if path:
        return path
    filename = TOOL_FILENAMES.get(name, name)
    raise FileNotFoundError(
        f"TVB tool '{name}' was not found. Expected bundled file '{filename}'."
    )


def resolve_library(name: str = "libmediainfo", *, allow_path: bool = True) -> Optional[str]:
    return resolve_tool(name, allow_path=allow_path)
