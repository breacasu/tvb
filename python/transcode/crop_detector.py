#!/usr/bin/env python3
"""Python implementation of Lisa Melton's detect-crop.rb utility."""

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from tool_paths import require_tool


class CropDetectionError(RuntimeError):
    pass


class CropDetector:
    def __init__(self, mode: str = "conservative", handbrake_path: Optional[str] = None):
        if mode not in {"auto", "conservative"}:
            raise ValueError(f"Unsupported crop mode: {mode}")
        self.mode = mode
        self.handbrake_path = handbrake_path or require_tool("HandBrakeCLI")

    @staticmethod
    def _parse_crop(output: str) -> Optional[str]:
        match = re.search(r"(?:,|:)\s*crop\s*\((\d+/\d+/\d+/\d+)\):", output)
        return match.group(1).replace("/", ":") if match else None

    def detect_crop(self, input_file: str) -> str:
        input_path = Path(input_file)
        if not input_path.is_file():
            raise CropDetectionError(f"Input file does not exist: {input_file}")

        with tempfile.TemporaryDirectory(prefix="tvb-crop-") as temp_dir:
            output_path = Path(temp_dir) / "probe.mkv"
            command = [
                self.handbrake_path,
                "--input", str(input_path),
                "--output", str(output_path),
                "--format", "av_mkv",
                "--stop-at", "seconds:1",
                "--crop-mode", self.mode,
                "--encoder", "x265_10bit",
                "--encoder-preset", "ultrafast",
                "--audio", "0",
            ]
            logging.debug("Crop detection command: %s", command)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode != 0:
                raise CropDetectionError(
                    f"HandBrake crop detection failed for '{input_file}' "
                    f"(exit code {result.returncode})"
                )

            crop = self._parse_crop(f"{result.stdout}\n{result.stderr}")
            return crop or "0:0:0:0"

    def detect_crop_batch(self, input_files: Iterable[str]) -> List[Tuple[str, str]]:
        results = []
        for input_file in input_files:
            results.append((input_file, self.detect_crop(input_file)))
        return results
