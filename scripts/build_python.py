#!/usr/bin/env python3
"""Build the bundled TVB CLI and crop detector with the local venv."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"
sys.path.insert(0, str(PYTHON_DIR))

from tool_paths import resolve_library, resolve_tool  # noqa: E402


def pyinstaller_path() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
    return ROOT / ".venv" / "bin" / "pyinstaller"


def build(entry: str, name: str, tools: List[str]) -> None:
    executable = pyinstaller_path()
    if not executable.is_file():
        raise SystemExit(
            f"PyInstaller not found at {executable}. Run setup.bat or setup.sh first."
        )

    separator = ";" if os.name == "nt" else ":"
    command = [
        str(executable),
        "--clean",
        "--onefile",
        "--name", name,
        "--paths", str(PYTHON_DIR),
        "--distpath", str(PYTHON_DIR / "dist"),
        "--workpath", str(PYTHON_DIR / "build" / name),
        "--specpath", str(PYTHON_DIR),
        "--hidden-import", "configparser",
        "--hidden-import", "transcode.analyzer",
        "--hidden-import", "transcode.generator",
        "--hidden-import", "transcode.crop_detector",
        "--hidden-import", "features.atmos",
        "--hidden-import", "features.statistics",
        "--hidden-import", "config.config_loader",
        "--add-data",
        f"{PYTHON_DIR / 'tvb-config.ini'}{separator}.",
    ]

    for tool in tools:
        path = resolve_tool(tool) if tool != "libmediainfo" else resolve_library(tool)
        if not path:
            raise SystemExit(f"Required bundled tool is unavailable: {tool}")
        command.extend(["--add-binary", f"{path}{separator}."])

    command.append(str(PYTHON_DIR / entry))
    subprocess.run(command, cwd=PYTHON_DIR, check=True)


def main() -> int:
    dist_dir = PYTHON_DIR / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    expected = {"tvb.exe"} if os.name == "nt" else {"tvb"}
    for old_output in dist_dir.glob("tvb*"):
        if old_output.name not in expected and old_output.is_file():
            old_output.unlink()

    tools = ["HandBrakeCLI", "ffprobe", "libmediainfo"]
    build("tvb.py", "tvb", tools)
    return 0


if __name__ == "__main__":
    sys.exit(main())
