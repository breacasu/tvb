#!/usr/bin/env python3
"""Build the bundled TVB CLI and crop detector with the local venv."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"
sys.path.insert(0, str(PYTHON_DIR))

from tool_paths import resolve_library, resolve_tool  # noqa: E402


def _macos_dependencies(path: Path) -> List[str]:
    result = subprocess.run(
        ["otool", "-L", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    dependencies = []
    for line in result.stdout.splitlines()[1:]:
        dependency = line.strip().split(" (", 1)[0]
        if dependency.startswith("/") and not dependency.startswith(
            ("/usr/lib/", "/usr/libexec/", "/System/", "/Library/Frameworks/")
        ):
            dependencies.append(dependency)
    return dependencies


def _run_install_name_tool(arguments: List[str]) -> None:
    result = subprocess.run(
        ["install_name_tool", *arguments],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"install_name_tool failed: {detail}")


def _prepare_macos_runtime_tools(paths: List[str]) -> List[Path]:
    """Copy non-system dylibs and make the temporary build set relocatable."""
    runtime_dir = PYTHON_DIR / "build" / "runtime-tools"
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
    runtime_dir.mkdir(parents=True)

    pending = []
    copied = {}
    for path_string in paths:
        source = Path(path_string)
        destination = runtime_dir / source.name
        shutil.copy2(source, destination)
        destination.chmod(destination.stat().st_mode | 0o200)
        copied[destination.name] = destination
        pending.append(destination)

    while pending:
        current = pending.pop()
        if current.suffix == ".dylib":
            _run_install_name_tool(
                ["-id", f"@loader_path/{current.name}", str(current)]
            )

        for dependency in _macos_dependencies(current):
            source = Path(dependency)
            if not source.is_file():
                raise SystemExit(f"macOS runtime dependency is unavailable: {dependency}")

            destination = runtime_dir / source.name
            if destination.name not in copied:
                shutil.copy2(source, destination)
                destination.chmod(destination.stat().st_mode | 0o200)
                copied[destination.name] = destination
                pending.append(destination)

            _run_install_name_tool(
                [
                    "-change",
                    dependency,
                    f"@loader_path/{destination.name}",
                    str(current),
                ]
            )

    return sorted(copied.values(), key=lambda path: path.name)


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
        "--additional-hooks-dir", str(PYTHON_DIR / "hooks"),
        "--add-data",
        f"{PYTHON_DIR / 'tvb-config.ini'}{separator}.",
    ]

    resolved_tools = []
    for tool in tools:
        path = resolve_tool(tool) if tool != "libmediainfo" else resolve_library(tool)
        if not path:
            raise SystemExit(f"Required bundled tool is unavailable: {tool}")
        resolved_tools.append(path)

    runtime_tools = (
        _prepare_macos_runtime_tools(resolved_tools)
        if sys.platform == "darwin"
        else [Path(path) for path in resolved_tools]
    )
    for path in runtime_tools:
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
