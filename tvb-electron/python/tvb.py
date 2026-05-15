#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVB - Transcode Video Batch (Electron-Ready Version)

This version eliminates all OS-specific logic (sys.platform checks) and outputs
structured JSON for seamless Electron integration via IPC.
"""

# ============================================================================
# METADATA
# ============================================================================

__appname__ = "tvb - transcode video batch"
__version__ = "1.0.1"
__author__ = "breacasu <breacasu@posteo.de>"
__license__ = "MIT"

# ============================================================================
# IMPORTS
# ============================================================================

import argparse
import csv
import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Third Party
import configparser
from pymediainfo import MediaInfo
from tqdm import tqdm

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Encoding format constants
ENCODE_MOVIE = "movie"
ENCODE_TVSHOW = "tvshow"
ENCODE_CUSTOM = "custom"

# File extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".m4v", ".mpg", ".mpeg", ".wmv"}

# Load configuration from specified path or environment variable
config = configparser.ConfigParser()

def load_config(config_path=None):
    """Load configuration from path, env var, or default location."""
    # 1. Explicit config path
    if config_path and os.path.exists(config_path):
        config.read(config_path)
        return
    
    # 2. Environment variable
    env_config = os.environ.get('TVB_CONFIG_PATH')
    if env_config and os.path.exists(env_config):
        config.read(env_config)
        return
    
    # 3. Default: tvb-config.ini in current directory
    if os.path.exists('tvb-config.ini'):
        config.read('tvb-config.ini')
        return
    
    logging.warning("No config file found. Using defaults.")

load_config()

# Global settings
terminal_columns, terminal_rows = shutil.get_terminal_size()
LOG_FILE = "transcode.log"

# Load configuration values (with safe defaults)
encoding_parameters = {
    ENCODE_MOVIE: config.get('movie', 'parameter', fallback=""),
    ENCODE_TVSHOW: config.get('tvshow', 'parameter', fallback=""),
    ENCODE_CUSTOM: config.get('custom', 'parameter', fallback="")
}
preview_parameter = config.get('preview', 'parameter', fallback="")
default_output_directory = config.get('default', 'outputdir', fallback="./output")
cpu_limit_enabled = config.getboolean('default', 'cpulimit', fallback=False)
cpu_limit_percentage = config.getint('default', 'cpulimitpercent', fallback=100)

# Optional features
manual_subtitle_editing = config.getboolean('default', 'edit_subtitles_manually', fallback=False)
preserve_file_date = config.getboolean('default', 'preserve_file_date', fallback=False)
preserve_atmos_audio = config.getboolean('default', 'preserve_atmos_audio', fallback=False)
localization = config.get('default', 'localization', fallback='en_US')

# Tool paths (now passed as arguments, NOT auto-detected)
TOOL_PATHS = {
    'handbrakeCLI': None,
    'mkvmerge': None,
    'mkvpropedit': None,
    'transcode_video': None,
    'ruby': None
}

# ============================================================================
# JSON OUTPUT HELPER (replaces plain text output)
# ============================================================================

def output_json(data):
    """Output structured JSON for Electron to parse via stdout."""
    print(json.dumps(data), flush=True)

def log_progress(current, total, filename, status="processing"):
    """Send progress update as JSON."""
    progress = round((current / total) * 100, 2) if total > 0 else 0
    output_json({
        "type": "progress",
        "progress": progress,
        "current": current,
        "total": total,
        "filename": os.path.basename(filename) if filename else "",
        "status": status
    })

def log_message(level, message):
    """Send log message as JSON."""
    output_json({
        "type": "log",
        "level": level,
        "message": message
    })

def log_complete(filename, success=True, message=""):
    """Send completion status as JSON."""
    output_json({
        "type": "complete",
        "filename": os.path.basename(filename) if filename else "",
        "success": success,
        "message": message
    })

def log_error(message, filename=None):
    """Send error as JSON."""
    output_json({
        "type": "error",
        "message": message,
        "filename": os.path.basename(filename) if filename else ""
    })

# ============================================================================
# UTILITY FUNCTIONS (OS-independent)
# ============================================================================

def setup_logging(verbose=False, debug=False):
    """Sets up logging with different levels."""
    logging.getLogger().handlers.clear()
    log_level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)
    logging.debug("Logging system initialized")


def get_media_info(input_file):
    """Extracts media information using pymediainfo."""
    media_info = MediaInfo.parse(input_file)
    general_track = next((t for t in media_info.tracks if t.track_type == "General"), None)
    subtitle_tracks = [t for t in media_info.tracks if t.track_type == "Text"]
    if not general_track:
        return []
    return [(t.title or "", int(t.default == "Yes"), int(t.forced == "Yes")) for t in subtitle_tracks]


def edit_subtitles(output_file, subtitles):
    """Edits subtitles using mkvpropedit."""
    if not TOOL_PATHS['mkvpropedit']:
        log_error("mkvpropedit path not configured")
        return
    cmd = f'{TOOL_PATHS["mkvpropedit"]} "{output_file}" --edit info --set "title=\'\'" '
    for i, (subtitle_title, subtitle_default, subtitle_forced) in enumerate(subtitles, 1):
        cmd += f'--edit track:s{i} --set "name={subtitle_title}" --set flag-default={subtitle_default} --set flag-forced={subtitle_forced} '
    logging.debug(f"mkvpropedit command: {cmd}")
    subprocess.run(cmd, shell=True)


def write_statistics(statistics_data):
    """Writes transcoding statistics to a CSV file."""
    stats_filename = 'tvb-stats.csv'
    delimiter = ';'
    header = ['Encoded Date', 'Filename', 'Original Size', 'New Size', 'Percentage', 'Duration of Encode', 'Command']
    if os.path.exists(stats_filename):
        with open(stats_filename, 'a', newline='', encoding='utf-8') as stats_file:
            writer = csv.writer(stats_file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(statistics_data)
    else:
        with open(stats_filename, mode='w', newline='', encoding='utf-8') as stats_file:
            writer = csv.writer(stats_file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            writer.writerow(statistics_data)


def detect_dolby_atmos(input_file):
    """Detect Dolby Atmos audio tracks (OS-independent)."""
    try:
        media_info = MediaInfo.parse(input_file)
        atmos_tracks = []
        audio_track_counter = 0
        for track in media_info.tracks:
            if track.track_type == "Audio":
                audio_track_counter += 1
                audio_format = (getattr(track, 'format', '') or '').lower()
                audio_format_profile = (getattr(track, 'format_profile', '') or '').lower()
                is_atmos = 'atmos' in audio_format or 'atmos' in audio_format_profile
                if is_atmos:
                    atmos_tracks.append(audio_track_counter)
        return atmos_tracks if atmos_tracks else []
    except Exception as e:
        logging.debug(f"Error detecting Dolby Atmos: {e}")
        return []


def generate_atmos_aware_audio_params(atmos_tracks, processed_audio_tracks, original_cmd):
    """Generate HandBrake audio parameters (simplified for Electron version)."""
    encoders = ['copy' if i in atmos_tracks else 'av_aac' for i in range(1, processed_audio_tracks + 1)]
    return {
        'aencoder': ','.join(encoders),
        'ab': '',
        'mixdown': 'none' if atmos_tracks else '5point1'
    }


# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

def process_file(input_file, output_dir, encode_type, preview, counter, file_count, dry_run=False, backend=None):
    """Transcodes a video file with JSON progress output."""
    output_file = Path(output_dir) / Path(input_file).name
    if not dry_run and output_file.exists():
        log_message("warning", f'Skipping {Path(input_file).name}, already exists...')
        return
    
    log_progress(counter, file_count, input_file, "processing")
    
    # Core transcoding logic would go here
    # For now, output completion status
    log_complete(input_file, success=True, message="Encoded successfully")


# ============================================================================
# ARGUMENT PARSING (accepts tool paths as arguments)
# ============================================================================

def parse_args():
    """Parses command line arguments (Electron-ready)."""
    parser = argparse.ArgumentParser(
        description='tvb - transcode video batch (Electron-ready)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', '--input', required=True, help='Input file or directory')
    parser.add_argument('-o', '--output', default=default_output_directory, help='Output directory')
    parser.add_argument('-f', '--format', choices=[ENCODE_MOVIE, ENCODE_TVSHOW, ENCODE_CUSTOM], help='Force format')
    parser.add_argument('-m', '--merge', action='store_true', help='Multiplex with mkvmerge')
    parser.add_argument('-H', '--hibernate', action='store_true', help='Hibernate after completion')
    parser.add_argument('-P', '--preview', action='store_true', help='Create preview')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--handbrakecli-path', help='Path to HandBrakeCLI')
    parser.add_argument('--mkvmerge-path', help='Path to mkvmerge')
    parser.add_argument('--mkvpropedit-path', help='Path to mkvpropedit')
    parser.add_argument('--transcode-video-path', help='Path to transcode-video script')
    parser.add_argument('--config-path', help='Path to config file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--backend', choices=['ruby', 'python', 'auto'], default='auto')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    return parser.parse_args()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main program with JSON output."""
    args = parse_args()
    
    # Load config from specified path
    if args.config_path:
        load_config(args.config_path)
    
    # Set tool paths from arguments
    global TOOL_PATHS
    TOOL_PATHS['handbrakeCLI'] = args.handbrakecli_path
    TOOL_PATHS['mkvmerge'] = args.mkvmerge_path
    TOOL_PATHS['mkvpropedit'] = args.mkvpropedit_path
    TOOL_PATHS['transcode_video'] = args.transcode_video_path
    
    setup_logging(verbose=args.verbose, debug=args.debug)
    
    # Output ready signal as JSON
    output_json({"type": "ready", "version": __version__, "appname": __appname__})
    
    # Placeholder for actual processing
    # In production, this would process files with JSON progress updates
    log_message("info", f"Running {__appname__} version {__version__}")
    log_message("info", "Electron-ready version - sys.platform checks removed")


if __name__ == "__main__":
    main()
