#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVB Crop Detector

Python module for detecting crop values in video files.
This is a Python port of Lisa Melton's detect-crop.rb tool.

Detect unused outside area of video tracks and print TOP:BOTTOM:LEFT:RIGHT crop values 
to standard output. This tool helps identify black bars (letterboxing/pillarboxing) 
in video files so they can be cropped out during transcoding.

Usage: python tvb-crop_detector.py [OPTIONS] <video_file> [mode]

Options:
    mode               Crop detection mode: 'auto' or 'conservative' (default: conservative)
    
Examples:
    # Detect crop values with conservative mode (default)
    python tvb-crop_detector.py video.mkv
    
    # Detect crop values with auto mode
    python tvb-crop_detector.py video.mkv auto
    
    # Multiple files
    python tvb-crop_detector.py video1.mkv video2.mkv

Output:
    Prints crop values in format: TOP:BOTTOM:LEFT:RIGHT
    Example: 140:140:0:0 (removes 140 pixels from top and bottom)

Requirements:
    - HandBrakeCLI (must be in PATH)
    - Python 3.6+

Copyright (C) 2025 breacasu <breacasu@posteo.de>
Based on detect-crop.rb by Lisa Melton
Distributed under the MIT license (MIT)
"""

# Standard Library
import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
from typing import Tuple, Optional

# ============================================================================
# METADATA
# ============================================================================

__appname__ = "TVB Crop Detector"
__version__ = "1.0.0"
__author__ = "breacasu <breacasu@posteo.de>"
__license__ = "MIT"


class CropDetector:
    """Class for detecting optimal crop values in video files."""

    def __init__(self, mode: str = 'conservative'):
        """
        Initialize the crop detector.

        Args:
            mode: Crop detection mode ('auto' or 'conservative')
        """
        self.mode = mode
        self.handbrake_path = self._find_handbrake()

    def _find_handbrake(self) -> str:
        """Find HandBrakeCLI executable in system PATH."""
        try:
            result = subprocess.run(['which', 'HandBrakeCLI'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: assume HandBrakeCLI is in PATH
            return 'HandBrakeCLI'

    def detect_crop(self, input_file: str) -> str:
        """
        Detect optimal crop values for a video file.

        Args:
            input_file: Path to the input video file

        Returns:
            Crop values as string in format "TOP:BOTTOM:LEFT:RIGHT"
        """
        logging.debug(f"Detecting crop values for: {input_file}")

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as temp_file:
            temp_output = temp_file.name

        try:
            # Run HandBrakeCLI with crop detection
            cmd = [
                self.handbrake_path,
                '--input', input_file,
                '--output', temp_output,
                '--format', 'av_mkv',
                '--stop-at', 'seconds:1',
                '--crop-mode', self.mode,
                '--encoder', 'x265_10bit',
                '--encoder-preset', 'ultrafast',
                '--audio', '0'  # No audio processing
            ]

            logging.debug(f"Running crop detection command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse crop values from output
            crop_values = self._parse_crop_from_output(result.stderr + result.stdout)

            if crop_values:
                logging.info(f"Detected crop values for {input_file}: {crop_values}")
                return crop_values
            else:
                logging.warning(f"No crop values found for {input_file}, using default")
                return '0:0:0:0'

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to detect crop values for '{input_file}': {e}"
            logging.error(error_msg)
            return '0:0:0:0'
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_output):
                    os.unlink(temp_output)
            except OSError:
                pass  # Ignore cleanup errors

    def _parse_crop_from_output(self, output: str) -> Optional[str]:
        """
        Parse crop values from HandBrakeCLI output.

        Args:
            output: HandBrakeCLI stderr/stdout output

        Returns:
            Crop values as string or None if not found
        """
        # Look for crop information in output
        # Format: ", crop (TOP/BOTTOM/LEFT/RIGHT): "
        crop_pattern = r', crop \((\d+)/(\d+)/(\d+)/(\d+)\): '

        match = re.search(crop_pattern, output)
        if match:
            top, bottom, left, right = match.groups()
            return f"{top}:{bottom}:{left}:{right}"

        return None

    def detect_crop_batch(self, input_files: list) -> list:
        """
        Detect crop values for multiple files.

        Args:
            input_files: List of input file paths

        Returns:
            List of tuples (filename, crop_values)
        """
        results = []

        for input_file in input_files:
            try:
                crop_values = self.detect_crop(input_file)
                results.append((input_file, crop_values))
            except Exception as e:
                logging.error(f"Failed to detect crop for {input_file}: {e}")
                results.append((input_file, '0:0:0:0'))

        return results


# Convenience functions
def detect_crop(input_file: str, mode: str = 'conservative') -> str:
    """Convenience function to detect crop values."""
    detector = CropDetector(mode)
    return detector.detect_crop(input_file)


def detect_crop_batch(input_files: list, mode: str = 'conservative') -> list:
    """Convenience function to detect crop values for multiple files."""
    detector = CropDetector(mode)
    return detector.detect_crop_batch(input_files)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='TVB Crop Detector - Detect crop values for video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('input_files', nargs='+',
                        help='Input video file(s)')
    parser.add_argument('-m', '--mode', choices=['auto', 'conservative'],
                        default='conservative',
                        help='Crop detection mode (default: conservative)')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(levelname)s:%(message)s')
    
    # Process each input file
    for input_file in args.input_files:
        try:
            crop_values = detect_crop(input_file, args.mode)
            if len(args.input_files) > 1:
                # Multiple files: include filename in output
                print(f"{crop_values},\"{input_file}\"")
            else:
                # Single file: just crop values
                print(crop_values)
        except Exception as e:
            print(f"Error processing {input_file}: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
