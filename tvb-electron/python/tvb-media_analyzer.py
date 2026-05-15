#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# media_analyzer.py
#
# Python module for analyzing media files using ffprobe
# Replaces the scan_media functionality from the Ruby scripts
#

# Standard Library
import json
import logging
import mimetypes
import os
import subprocess
from typing import Dict, Any, Optional


class MediaAnalyzer:
    """Class for analyzing media files using ffprobe."""

    def __init__(self):
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffprobe(self) -> str:
        """Find ffprobe executable in system PATH."""
        try:
            result = subprocess.run(['which', 'ffprobe'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: assume ffprobe is in PATH
            return 'ffprobe'

    def scan_media(self, file_path: str) -> Dict[str, Any]:
        """
        Scan media file and return parsed JSON information.

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary containing media information from ffprobe

        Raises:
            RuntimeError: If scanning fails
            json.JSONDecodeError: If JSON parsing fails
        """
        logging.debug(f'Scanning media file: {file_path}')

        # Check if file exists and is readable
        if not os.path.exists(file_path):
            error_msg = f"File does not exist: '{file_path}'"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        
        if not os.access(file_path, os.R_OK):
            error_msg = f"File is not readable: '{file_path}'"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Check if file is actually a media file (basic check)
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith(('video/', 'audio/')):
                error_msg = f"File does not appear to be a media file: '{file_path}' (detected type: {mime_type})"
                logging.error(error_msg)
                raise RuntimeError(error_msg)
        except Exception:
            # If mimetypes fails, continue with ffprobe check
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
            
            # Check if ffprobe returned any output
            if not result.stdout.strip():
                error_msg = f"No media information found for file: '{file_path}' - file may be corrupted or not a valid media file"
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            media_info = json.loads(result.stdout)
            
            # Validate that we have at least one stream
            if not media_info.get('streams'):
                error_msg = f"No media streams found in file: '{file_path}' - file may be corrupted or not a valid media file"
                logging.error(error_msg)
                raise RuntimeError(error_msg)

            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f'Media info: {json.dumps(media_info, indent=2)}')

            return media_info

        except subprocess.CalledProcessError as e:
            # Provide more specific error messages based on the error
            if e.returncode == 1:
                error_msg = f"File is not a valid media file or is corrupted: '{file_path}'"
            else:
                error_msg = f"Failed to scan media file '{file_path}': {e}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse media information for '{file_path}': {e}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

    def get_video_stream(self, media_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract the first video stream from media information.

        Args:
            media_info: Media information dictionary from ffprobe

        Returns:
            Video stream dictionary or None if no video stream found
        """
        for stream in media_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                return stream
        return None

    def get_audio_streams(self, media_info: Dict[str, Any]) -> list:
        """
        Extract all audio streams from media information.

        Args:
            media_info: Media information dictionary from ffprobe

        Returns:
            List of audio stream dictionaries
        """
        return [stream for stream in media_info.get('streams', [])
                if stream.get('codec_type') == 'audio']

    def get_subtitle_streams(self, media_info: Dict[str, Any]) -> list:
        """
        Extract all subtitle streams from media information.

        Args:
            media_info: Media information dictionary from ffprobe

        Returns:
            List of subtitle stream dictionaries
        """
        return [stream for stream in media_info.get('streams', [])
                if stream.get('codec_type') == 'subtitle']

    def get_stream_info(self, media_info: Dict[str, Any], stream_type: str) -> list:
        """
        Extract streams of specific type from media information.

        Args:
            media_info: Media information dictionary from ffprobe
            stream_type: Type of stream ('video', 'audio', 'subtitle')

        Returns:
            List of stream dictionaries of the specified type
        """
        return [stream for stream in media_info.get('streams', [])
                if stream.get('codec_type') == stream_type]


# Convenience functions for backward compatibility
def scan_media(file_path: str) -> Dict[str, Any]:
    """Convenience function to scan media file."""
    analyzer = MediaAnalyzer()
    return analyzer.scan_media(file_path)


if __name__ == '__main__':
    # Simple test
    import sys

    if len(sys.argv) != 2:
        print("Usage: python media_analyzer.py <video_file>")
        sys.exit(1)

    analyzer = MediaAnalyzer()
    try:
        media_info = analyzer.scan_media(sys.argv[1])
        print(f"Successfully scanned: {sys.argv[1]}")
        print(f"Format: {media_info['format']['format_name']}")
        print(f"Duration: {media_info['format'].get('duration', 'unknown')}")

        video_streams = analyzer.get_video_streams(media_info)
        audio_streams = analyzer.get_audio_streams(media_info)
        subtitle_streams = analyzer.get_subtitle_streams(media_info)

        print(f"Video streams: {len(video_streams)}")
        print(f"Audio streams: {len(audio_streams)}")
        print(f"Subtitle streams: {len(subtitle_streams)}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
