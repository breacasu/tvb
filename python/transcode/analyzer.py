#!/usr/bin/env python3
import json
import logging
import mimetypes
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class MediaAnalyzer:
    def __init__(self):
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffprobe(self) -> str:
        if getattr(sys, '_MEIPASS', None):
            bundled = Path(sys._MEIPASS) / "ffprobe"
            if bundled.exists():
                return str(bundled)

        script_dir = Path(__file__).resolve().parent.parent.parent
        bundled = script_dir / "bin" / "ffprobe"
        if bundled.exists():
            return str(bundled)

        try:
            result = subprocess.run(['which', 'ffprobe'],
                                   capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return 'ffprobe'

    def scan_media(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise RuntimeError(f"File does not exist: '{file_path}'")
        if not os.access(file_path, os.R_OK):
            raise RuntimeError(f"File is not readable: '{file_path}'")

        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith(('video/', 'audio/')):
                raise RuntimeError(f"File does not appear to be a media file: '{file_path}'")
        except Exception:
            pass

        cmd = [
            self.ffprobe_path,
            '-loglevel', 'quiet',
            '-show_streams',
            '-show_format',
            '-print_format', 'json',
            file_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if not result.stdout.strip():
                raise RuntimeError(f"No media information found for file: '{file_path}'")

            media_info = json.loads(result.stdout)
            if not media_info.get('streams'):
                raise RuntimeError(f"No media streams found in file: '{file_path}'")

            logging.debug(f'Media info: {json.dumps(media_info, indent=2)}')
            return media_info

        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise RuntimeError(f"File is not a valid media file or is corrupted: '{file_path}'")
            raise RuntimeError(f"Failed to scan media file '{file_path}': {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse media information for '{file_path}': {e}")

    def get_video_streams(self, media_info: Dict[str, Any]) -> list:
        return [s for s in media_info.get('streams', []) if s.get('codec_type') == 'video']

    def get_video_stream(self, media_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for stream in media_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                return stream
        return None

    def get_audio_streams(self, media_info: Dict[str, Any]) -> list:
        return [s for s in media_info.get('streams', []) if s.get('codec_type') == 'audio']

    def get_subtitle_streams(self, media_info: Dict[str, Any]) -> list:
        return [s for s in media_info.get('streams', []) if s.get('codec_type') == 'subtitle']

    def get_stream_info(self, media_info: Dict[str, Any], stream_type: str) -> list:
        return [s for s in media_info.get('streams', []) if s.get('codec_type') == stream_type]


def scan_media(file_path: str) -> Dict[str, Any]:
    analyzer = MediaAnalyzer()
    return analyzer.scan_media(file_path)
