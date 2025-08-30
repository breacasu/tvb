#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tvb - transcode video batch
# Thanks to Lisa Melton.
#
# Copyright (C) 2025 breacasu <breacasu@posteo.de>
#
# Distributed under the MIT license (MIT)

__appname__ = "tvb - transcode video batch"
__version__ = "0.9"
__author__ = "breacasu <breacasu@posteo.de>"
__license__ = "MIT"
# Syntax
__doc__ = '''\
Batch encode files with the wonderful transcode-video scripts by Lisa Melton

Overall, this script allows users to transcode video files in batch mode using customizable settings and options,
and it supports both movie and TV show formats. Additionally, it provides verbose and debug logging options and
supports hibernating the computer after the transcoding process is completed.

Usage: ./tvb_wrapper.sh [options]

Options:
    -i <input>       Input file or directory (required)
    -o <output>      Output directory (default: from config)
    -f <format>      Force format for all files [movie/tvshow/custom]
    -m               Multiplex with mkvmerge
    -H               Hibernate after completion
    -P               Create preview (30 seconds)
    -d               Dry-run mode (show commands without execution)
    -v               Verbose output
    --debug          Debug mode with detailed logging
    --version        Show version information
    -h               Display help and exit

Examples:
    # ./tvb_wrapper.sh -i "homeland.S01E01.mp4" -o "/tvshows/encoded"
    > Encode single file with auto-detected format

    # ./tvb_wrapper.sh -i "/movies/source" -o "/encoded"
    > Encode all videos in directory

    # ./tvb_wrapper.sh -i "/movies/source" -o "/encoded" -f movie
    > Force movie format for all files

    # ./tvb_wrapper.sh -i "testvideo.mp4" -d
    > Show commands without executing (dry-run)

    # ./tvb_wrapper.sh -i "testvideo.mp4" -P
    > Create 30-second preview

    # ./tvb_wrapper.sh -i "testvideo.mp4" -m
    > Multiplex with mkvmerge after encoding

    # ./tvb_wrapper.sh -i "testvideo.mp4" -H
    > Hibernate after completion
'''

import os
import sys
import csv
import time
import shlex
import logging
import shutil
import subprocess
import re
import locale
from pathlib import Path
from datetime import datetime
from pymediainfo import MediaInfo
from tqdm import tqdm
import configparser
import requests
from bs4 import BeautifulSoup
import argparse

# Konfiguration laden
config = configparser.ConfigParser()
config.read('tvb-config.ini')

# Global settings
terminal_columns, terminal_rows = shutil.get_terminal_size()
ENCODE_MOVIE = "movie"
ENCODE_TVSHOW = "tvshow"
ENCODE_CUSTOM = "custom"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".flv", ".m4v", ".mpg", ".mpeg", ".wmv"}
LOG_FILE = "transcode.log"

# Load config values
encoding_parameters = {
    ENCODE_MOVIE: config.get('movie', 'parameter', fallback=""),
    ENCODE_TVSHOW: config.get('tvshow', 'parameter', fallback=""),
    ENCODE_CUSTOM: config.get('custom', 'parameter', fallback="")
}
preview_parameter = config.get('preview', 'parameter', fallback="")
default_output_directory = config.get('default', 'outputdir', fallback="./output")
cpu_limit_enabled = config.getboolean('default', 'cpulimit', fallback=False)
cpu_limit_percentage = config.getint('default', 'cpulimitpercent', fallback=100)
# Optional subtitle editing (since transcode-video handles this automatically)
manual_subtitle_editing = config.getboolean('default', 'edit_subtitles_manually', fallback=False)
# Preserve original file date/timestamp on encoded files
preserve_file_date = config.getboolean('default', 'preserve_file_date', fallback=True)
# Preserve Dolby Atmos audio tracks
preserve_atmos_audio = config.getboolean('default', 'preserve_atmos_audio', fallback=False)
# Localization setting for date format in statistics
localization = config.get('default', 'localization', fallback='en_US')

def find_tool_in_path(tool_name, config_section=None, config_key=None):
    """Searches for a tool in PATH and uses config as fallback."""
    # Typical paths for different platforms
    typical_paths = {
        'darwin': [  # macOS
            '/opt/homebrew/bin',
            '/usr/local/bin',
            '/usr/bin',
            '/opt/homebrew/opt/ruby/bin',
            '/usr/local/opt/ruby/bin'
        ],
        'win32': [   # Windows
            'C:\\bin',
            'C:\\Program Files\\HandBrake',
            'C:\\Ruby26-x64\\bin',
            'C:\\Ruby25-x64\\bin'
        ],
        'linux': [   # Linux
            '/usr/bin',
            '/usr/local/bin',
            '/opt/bin',
            '/snap/bin'
        ]
    }
    
    # Search in PATH
    if shutil.which(tool_name):
        found_path = shutil.which(tool_name)
        logging.debug(f"Tool '{tool_name}' found in PATH: {found_path}")
        return found_path
    
    # Search in typical paths
    platform_paths = typical_paths.get(sys.platform, [])
    for path in platform_paths:
        full_path = os.path.join(path, tool_name)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            logging.debug(f"Tool '{tool_name}' found in typical path: {full_path}")
            return full_path
    
    # Fallback: Config value
    if config_section and config_key and config_section in config and config_key in config[config_section]:
        config_path = config[config_section][config_key]
        logging.debug(f"Tool '{tool_name}' used from config: {config_path}")
        return config_path
    
    # Last fallback: Tool name
    logging.warning(f"Tool '{tool_name}' not found, using name: {tool_name}")
    return tool_name

def find_transcode_video():
    """Searches for transcode-video in typical paths."""
    # Typical paths for transcode-video
    typical_paths = {
        'darwin': [
            #'/usr/local/bin/transcode-video.rb.',  # Priority 1: System installation (with dot)
            '/usr/local/bin/transcode-video.rb',   # Priority 2: Without dot
            '/usr/local/bin/transcode-video',      # Priority 3: Executable
            '/opt/homebrew/bin/transcode-video.rb',
            '/opt/homebrew/bin/transcode-video',
            '/usr/bin/transcode-video.rb',
            '/usr/bin/transcode-video',
            #'/Users/stephan/SynologyDrive/Code/video_transcoding/transcode-video.rb'  # Fallback
        ],
        'win32': [
            'C:\\Ruby26-x64\\bin\\transcode-video.bat',
            'C:\\Ruby25-x64\\bin\\transcode-video.bat',
            'C:\\bin\\transcode-video.bat'
        ],
        'linux': [
            '/usr/local/bin/transcode-video.rb',
            '/usr/local/bin/transcode-video',
            '/usr/bin/transcode-video.rb',
            '/usr/bin/transcode-video',
            '/opt/bin/transcode-video.rb',
            '/opt/bin/transcode-video'
        ]
    }
    
    # Search in typical paths
    platform_paths = typical_paths.get(sys.platform, [])
    for path in platform_paths:
        if os.path.exists(path):
            if path.endswith('.rb'):
                # Ruby script found
                ruby_path = shutil.which('ruby') or '/usr/bin/ruby'
                full_command = f"{ruby_path} {path}"
                logging.debug(f"transcode-video Ruby script found: {full_command}")
                return full_command
            else:
                # Executable found
                logging.debug(f"transcode-video executable found: {path}")
                return path
    
    # Fallback: Config value
    if 'transcode_video_path' in config and sys.platform in config['transcode_video_path']:
        config_path = config['transcode_video_path'][sys.platform]
        logging.debug(f"transcode-video used from config: {config_path}")
        return config_path
    
    # Last fallback
    logging.warning("transcode-video not found, using default path")
    return "/usr/bin/ruby /path/to/transcode-video.rb"

def find_tool_path(tool_name, config_section=None):
    """Intelligente Tool-Suche: PATH -> typische Pfade -> Config"""
    
    # 1. Suche im PATH
    path_result = shutil.which(tool_name)
    if path_result:
        return path_result
    
    # 2. Typische Pfade für verschiedene Plattformen
    typical_paths = {
        'darwin': [  # macOS
            '/opt/homebrew/bin',
            '/usr/local/bin',
            '/usr/bin',
            '/opt/homebrew/opt/ruby/bin',
            '/usr/local/opt/ruby/bin'
        ],
        'win32': [   # Windows
            'C:\\bin',
            'C:\\Program Files\\HandBrake',
            'C:\\Ruby26-x64\\bin',
            'C:\\Ruby25-x64\\bin'
        ],
        'linux': [   # Linux
            '/usr/bin',
            '/usr/local/bin',
            '/opt/bin',
            '/snap/bin'
        ]
    }
    
    platform_paths = typical_paths.get(sys.platform, [])
    for path in platform_paths:
        full_path = os.path.join(path, tool_name)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    
    # 3. Config-Wert als Fallback
    if config_section and config_section in config and sys.platform in config[config_section]:
        return config[config_section][sys.platform]
    
    # Wenn nichts gefunden wurde, verwende den Tool-Namen (wird wahrscheinlich im PATH gefunden)
    return tool_name

def find_transcode_video_path():
    """Spezielle Suche für transcode-video mit Ruby-Integration"""
    
    # Typische Pfade für transcode-video
    typical_paths = {
        'darwin': [
            '/usr/local/bin/transcode-video.rb',
            '/usr/local/bin/transcode-video',
            '/opt/homebrew/bin/transcode-video.rb',
            '/opt/homebrew/bin/transcode-video',
            '/usr/bin/transcode-video.rb',
            '/usr/bin/transcode-video'
        ],
        'win32': [
            'C:\\Ruby26-x64\\bin\\transcode-video.bat',
            'C:\\Ruby25-x64\\bin\\transcode-video.bat'
        ],
        'linux': [
            '/usr/local/bin/transcode-video.rb',
            '/usr/local/bin/transcode-video',
            '/usr/bin/transcode-video.rb',
            '/usr/bin/transcode-video'
        ]
    }
    
    # Suche in typischen Pfaden
    platform_paths = typical_paths.get(sys.platform, [])
    for path in platform_paths:
        if os.path.exists(path):
            if path.endswith('.rb'):
                # Ruby-Skript gefunden - finde Ruby und kombiniere
                ruby_path = shutil.which('ruby') or '/usr/bin/ruby'
                return f"{ruby_path} {path}"
            else:
                # Executable gefunden
                return path
    
    # Config-Fallback
    if 'transcode_video_path' in config and sys.platform in config['transcode_video_path']:
        return config['transcode_video_path'][sys.platform]
    
    # Letzter Fallback
    return "/usr/bin/ruby /usr/local/bin/transcode-video.rb"

# Tool-Pfade intelligent finden
transcode_video_path = find_transcode_video_path()
path_mkvpropedit = find_tool_path('mkvpropedit', 'mkvpropedit_path')
path_mkvmerge = find_tool_path('mkvmerge', 'mkvmerge_path')

class AttrDict(dict):
    """Dictionary with attribute access."""
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class Filesize(object):
    """Container for file sizes with readable representation."""
    chunk = 1024
    units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    precisions = [0, 0, 1, 2, 2, 2]

    def __init__(self, size):
        self.size = size

    def __int__(self):
        return self.size

    def __str__(self):
        if self.size == 0:
            return '0 bytes'
        from math import log
        unit = self.units[min(int(log(self.size, self.chunk)), len(self.units) - 1)]
        return self.format(unit)

    def format(self, unit):
        if unit not in self.units:
            raise Exception("Not a valid file size unit: %s" % unit)
        if self.size == 1 and unit == 'bytes':
            return '1 byte'
        exponent = self.units.index(unit)
        quotient = float(self.size) / self.chunk**exponent
        precision = self.precisions[exponent]
        format_string = '{:.%sf} {}' % (precision)
        return format_string.format(quotient, unit)

class TranscodeList(object):
    """Class for processing input files and format detection."""
    def __init__(self, input_path="", encode_type=None):
        self.input_directory = input_path
        self.file_list = self._collect_files()
        self.processed_list = []
        self.forced_format = encode_type
        if (self.forced_format == None):
            self.processed_list = self._detect_formats()
        else:
            self.processed_list = self._apply_forced_format()

    def _collect_files(self):
        """Collects all video files from the input directory."""
        video_files = []

        if os.path.isdir(self.input_directory) and os.path.exists(self.input_directory):
            for root, _, files in os.walk(self.input_directory):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in VIDEO_EXTENSIONS:
                        video_files.append(os.path.join(root, file))
        elif os.path.isfile(self.input_directory) and os.path.exists(self.input_directory):
            _, ext = os.path.splitext(self.input_directory)
            if ext.lower() in VIDEO_EXTENSIONS:
                video_files.append(self.input_directory)
        else:
            logging.error("The input file/dir does not exist: %s" % self.input_directory)
            sys.exit(1)

        logging.debug("No. of video files collected : %s" % len(video_files))
        return video_files

    def _detect_formats(self):
        """Automatically detects format based on filename."""
        format_list = []
        for file_path in self.file_list:
            m = re.match(r"(.*?)[.\s][sS](\d{1,2})[eE](\d{1,3}).*", os.path.basename(file_path))
            match = re.search(r"(.*?)[.\s][sS](\d{1,2})[eE](\d{1,3}).*", os.path.basename(file_path))
            if match:
                logging.debug("%s is a TV-Show." % os.path.basename(file_path))
                format_list.append((file_path, "tvshow"))
                logging.debug("TV-Show name: %s" % m.group(1))
                logging.debug("TV-Show series number: %s" % m.group(2))
                logging.debug("TV-Show episode: %s" % m.group(3))
            else:
                logging.debug("%s is not a TV-Show." % os.path.basename(file_path))
                format_list.append((file_path, "movie"))
        return format_list

    def _apply_forced_format(self):
        """Uses the specified format for all files."""
        format_list = []
        for file_path in self.file_list:
            format_list.append((file_path, self.forced_format))
        return format_list

# Setup logging
def setup_logging(verbose=False, debug=False):
    """Sets up logging with different levels."""
    # Clear any existing handlers to avoid duplicates
    logging.getLogger().handlers.clear()

    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING

    # Create formatters
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(message)s")

    # Setup file handler
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(file_formatter)

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)

    # Test logging
    logging.debug("Logging system initialized")
    logging.info("TVB logging started")

def get_platform_encoding():
    """Returns the correct encoding setting for different platforms."""
    return "cp775" if sys.platform.startswith("win32") else "utf-8"

def get_media_info(input_file):
    """Extracts media information using pymediainfo."""
    media_info = MediaInfo.parse(input_file)
    general_track = next((t for t in media_info.tracks if t.track_type == "General"), None)
    subtitle_tracks = [t for t in media_info.tracks if t.track_type == "Text"]

    if not general_track:
        logging.debug("No general track information found.")
        return []

    logging.info(f"File size: {general_track.file_size}")
    logging.info(f"Number of subtitles: {general_track.count_of_text_streams}")

    return [(t.title or "", int(t.default == "Yes"), int(t.forced == "Yes")) for t in subtitle_tracks]

def edit_subtitles(output_file, subtitles):
    """Edits subtitles using `mkvpropedit`."""
    cmd = f'{path_mkvpropedit} "{output_file}" --edit info --set "title=\'\'" '
    
    for i, (subtitle_title, subtitle_default, subtitle_forced) in enumerate(subtitles, 1):
        cmd += f'--edit track:s{i} --set "name={subtitle_title}" --set flag-default={subtitle_default} --set flag-forced={subtitle_forced} '

    logging.debug(f"mkvpropedit command: {cmd}")
    subprocess.run(shlex.split(cmd))

def write_statistics(statistics_data):
    """Writes transcoding statistics to a CSV file."""
    stats_filename = 'tvb-stats.csv'
    delimiter = ';'
    header = ['Encoded Date', 'Filename', 'Original Size', 'New Size', 'Percentage', 'Duration of Encode', 'Command']
    
    if os.path.exists(stats_filename):
        logging.debug('Stats file exists, appending data')
        with open(stats_filename, 'a', newline='', encoding='utf-8') as stats_file:
            writer = csv.writer(stats_file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(statistics_data)
    else:
        logging.debug('Stats file does not exist, creating file, writing header and data')
        with open(stats_filename, mode='w', newline='', encoding='utf-8') as stats_file:
            writer = csv.writer(stats_file, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            writer.writerow(statistics_data)

def set_target_date(source, target):
    """Setzt das Änderungsdatum der Datei."""
    old_date = os.path.getmtime(source)
    os.utime(target, (old_date, old_date))

def hibernate(hibernate_tag=None):
    """Hiberniert den Computer nach der Transkodierung."""
    if not hibernate_tag:
        return
        
    if sys.platform.startswith('freebsd'):
        logging.debug('freebsd plattform detected, hibernating...')
    elif sys.platform.startswith('linux'):
        logging.debug('linux platform detected, hibernating...')
    elif sys.platform.startswith('win32'):
        logging.debug('windows plattform detected, hibernating...')
        os.system(r'%windir%\system32\rundll32.exe powrprof.dll,SetSuspendState Hibernate')
    elif sys.platform.startswith('darwin'):
        logging.debug('mac os plattform detected, hibernating...')
        cmd = "pmset sleepnow"
        args = shlex.split(cmd)
        logging.debug('Execute commands: %s' % args)
        subprocess.Popen(args, bufsize=1, stdout=subprocess.PIPE, universal_newlines=True)

def merge_file(input_file, output_dir):
    """Multiplexiert eine Datei mit mkvmerge."""
    output_file = Path(output_dir, Path(input_file).stem + ".mkv")
    
    if output_file.exists():
        logging.info(f'Skipping {Path(input_file).name}, already exists...')
        return

    logging.info(f'Multiplexing: {Path(input_file).name}')
    
    cmd = f'{path_mkvmerge} -o "{output_file}" "{input_file}"'
    args = shlex.split(cmd)
    
    logging.debug(f"mkvmerge command: {cmd}")
    result = subprocess.run(args, capture_output=True, text=True, encoding=get_platform_encoding())
    
    if result.returncode == 0:
        logging.info(f'Successfully multiplexed: {Path(input_file).name}')
        if preserve_file_date:
            set_target_date(input_file, output_file)
    else:
        logging.error(f'Failed to multiplex: {Path(input_file).name}')
        logging.error(f'Error: {result.stderr}')

def modify_handbrake_output_path(handbrake_cmd, output_file, preview=False, atmos_tracks=None):
    """Modifies the HandBrakeCLI command to set the correct output path, add preview if requested, and preserve Dolby Atmos."""
    import re

    # Step 1: Extract the original output filename from the command
    # Find everything between --output and the next parameter (which starts with --)
    output_match = re.search(r'--output\s+(.+?)(?=\s--|$)', handbrake_cmd)

    if not output_match:
        logging.warning("Could not find --output parameter in HandBrakeCLI command")
        return handbrake_cmd

    original_output = output_match.group(1).strip()

    # Step 2: Clean the output file path
    clean_output_path = str(output_file).replace("'", "").replace('"', "")

    # Step 3: Replace the output parameter
    new_output_param = f'--output "{clean_output_path}"'
    modified_cmd = handbrake_cmd.replace(f'--output {original_output}', new_output_param)

    # Step 4: Clean up any remaining duplicate filename parts
    # Split and filter out any parts that look like the original filename
    parts = modified_cmd.split()
    cleaned_parts = []
    found_output_param = False

    for i, part in enumerate(parts):
        if part.startswith('--output'):
            found_output_param = True
            cleaned_parts.append(part)
        elif found_output_param and part == original_output:
            # This is the duplicate we want to remove
            logging.debug(f"Removed duplicate filename: {part}")
            continue
        else:
            cleaned_parts.append(part)

    final_cmd = ' '.join(cleaned_parts)

    logging.debug(f"🔧 Output path modification: '{original_output}' → '{clean_output_path}'")
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        # Only show full commands in debug mode to avoid cluttering logs
        logging.debug(f"🔧 Original HandBrakeCLI command: {handbrake_cmd}")
        logging.debug(f"🔧 Modified HandBrakeCLI command: {final_cmd}")
    else:
        logging.debug("🔧 HandBrakeCLI command modified for output path")

    # Step 5: Modify audio parameters for Dolby Atmos preservation
    if atmos_tracks:
        logging.info(f"🎵 Applying Dolby Atmos preservation to HandBrakeCLI command for tracks: {atmos_tracks}")

        # Extract audio track count from the command
        audio_match = re.search(r'--audio\s+([^-\s]+)', final_cmd)
        if audio_match:
            try:
                audio_tracks_str = audio_match.group(1)
                processed_tracks = [int(x) for x in audio_tracks_str.split(',')]
                max_processed_track = max(processed_tracks)
                logging.debug(f"🎵 Found {len(processed_tracks)} processed audio tracks: {audio_tracks_str}")

                # Check if any Atmos tracks are outside the processed range
                unprocessed_atmos_tracks = [track for track in atmos_tracks if track > max_processed_track]
                if unprocessed_atmos_tracks:
                    logging.warning(f"⚠️  Atmos tracks {unprocessed_atmos_tracks} are outside the processed range (max: {max_processed_track})")
                    logging.warning("⚠️  These Atmos tracks will not be included due to current audio language selection")
                    logging.info("💡 To include these Atmos tracks, add their language to your --add-audio parameters")

                # Only process Atmos tracks that are actually being processed
                relevant_atmos_tracks = [track for track in atmos_tracks if track <= max_processed_track]

                if relevant_atmos_tracks:
                    # Generate proper audio parameters for relevant tracks, preserving original parameters for non-Atmos tracks
                    audio_params = generate_atmos_aware_audio_params(relevant_atmos_tracks, len(processed_tracks), handbrake_cmd)

                    # Replace audio encoder
                    if '--aencoder' in final_cmd:
                        # Replace existing aencoder
                        final_cmd = re.sub(r'--aencoder\s+[^-\s]+', f'--aencoder {audio_params["aencoder"]}', final_cmd)
                    else:
                        # Add aencoder if not present
                        final_cmd = final_cmd.replace('--audio ', f'--audio {audio_tracks_str} --aencoder {audio_params["aencoder"]} ')

                    # Replace or add bitrate parameters
                    if audio_params['ab']:
                        if '--ab' in final_cmd:
                            final_cmd = re.sub(r'--ab\s+[^-\s]+', f'--ab {audio_params["ab"]}', final_cmd)
                        else:
                            final_cmd = final_cmd.replace('--aencoder ', f'--aencoder {audio_params["aencoder"]} --ab {audio_params["ab"]} ')

                    # Replace mixdown parameters
                    if '--mixdown' in final_cmd:
                        final_cmd = re.sub(r'--mixdown\s+[^-\s]+', f'--mixdown {audio_params["mixdown"]}', final_cmd)
                    else:
                        final_cmd = final_cmd.replace('--aencoder ', f'--aencoder {audio_params["aencoder"]} --mixdown {audio_params["mixdown"]} ')

                    logging.info("🎵 HandBrakeCLI audio parameters successfully modified for Atmos preservation")
                    logging.debug(f"🎵 New audio params: aencoder={audio_params['aencoder']}, ab={audio_params['ab']}, mixdown={audio_params['mixdown']}")
                else:
                    # No relevant Atmos tracks, skip Atmos processing
                    logging.debug("🎵 No Atmos tracks in processed range, skipping Atmos parameter modification")
            except (ValueError, AttributeError) as e:
                logging.warning(f"Could not parse audio track information for Atmos processing: {e}")
        else:
            logging.warning("Could not determine audio track count for Atmos parameter generation")

    # Step 6: Add preview option if requested
    if preview and preview_parameter:
        # Add preview parameter before the input file (which should be the last parameter)
        final_cmd = final_cmd.rstrip() + f' {preview_parameter}'

    return final_cmd


def get_installed_handbrake_version():
    """Get the installed HandBrakeCLI version."""
    try:
        # Run HandBrakeCLI with the --version option
        output = subprocess.check_output(["HandBrakeCLI", "--version"], text=True, stderr=subprocess.STDOUT)
        # Extract the version number using regular expression
        matches = re.search(r"(\d+\.\d+\.\d+)", output)
        if matches:
            return matches.group(1)
    except subprocess.CalledProcessError as e:
        print(f"Error while checking HandBrakeCLI version: {e.output}")
    return None


def get_latest_handbrake_version():
    """Get the latest HandBrakeCLI version from the official website."""
    url = "https://handbrake.fr/downloads2.php"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        # Find all h2 elements on the page
        h2_elements = soup.find_all("h2")
        for h2_element in h2_elements:
            # Check if the h2 element contains the text "Current Version"
            if "Current Version" in h2_element.string:
                # Extract the version number from the element text
                version_pattern = r"(\d+\.\d+\.\d+)"
                matches = re.search(version_pattern, h2_element.text)
                if matches:
                    logging.debug("Fetched HandBrakeCLI version: %s" % matches.group(1))
                    return matches.group(1)
    except requests.RequestException as e:
        print(f"Error while fetching the latest version of HandBrakeCLI: {e}")
    return None


def check_latest_handbrake_version(installed_version, latest_version):
    """Check if the installed HandBrakeCLI version is the latest."""
    if installed_version == latest_version:
        print(f"You have the latest version of HandBrakeCLI ({installed_version}).")
    else:
        print(f"Your installed version ({installed_version}) of HandBrakeCLI is outdated. The latest version is {latest_version}. Please update.")


def detect_dolby_atmos(input_file):
    """Detect Dolby Atmos audio tracks and return track information."""
    try:
        media_info = MediaInfo.parse(input_file)
        atmos_tracks = []

        audio_track_counter = 0
        for track in media_info.tracks:
            if track.track_type == "Audio":
                audio_track_counter += 1  # Increment audio track counter
                # Safely get audio properties, defaulting to empty string if None
                audio_format = (getattr(track, 'format', '') or '').lower()
                audio_format_profile = (getattr(track, 'format_profile', '') or '').lower()
                audio_title = (getattr(track, 'title', '') or '').lower()
                audio_codec_id = (getattr(track, 'codec_id', '') or '').lower()
                audio_format_info = (getattr(track, 'format_info', '') or '').lower()
                audio_commercial_name = (getattr(track, 'commercial_name', '') or '').lower()

                # Use audio track counter for proper parameter ordering (1, 2, 3, etc.)
                track_number = audio_track_counter

                # Extended Atmos indicators including JOC (Joint Object Coding)
                atmos_indicators = [
                    'atmos', 'dolby atmos', 'dolby-atmos',
                    'dolby digital plus atmos', 'dd+ atmos',
                    'truehd atmos', 'true-hd atmos'
                ]

                joc_indicators = [
                    'joc', 'joint object coding', 'joint-object-coding',
                    'enhanced ac-3 joc', 'e-ac-3 joc'
                ]

                # Check all fields for Atmos indicators
                all_audio_fields = [
                    audio_format_profile,
                    audio_title,
                    audio_format_info,
                    audio_commercial_name,
                    audio_codec_id
                ]

                is_atmos = False

                # Check for Atmos in any field
                for field_value in all_audio_fields:
                    if any(indicator in field_value for indicator in atmos_indicators):
                        logging.debug(f"🎵 Atmos detected in track {track_number}: {field_value}")
                        is_atmos = True
                        break

                # Check for JOC (Joint Object Coding) which indicates Atmos
                if not is_atmos:
                    for field_value in all_audio_fields:
                        if any(indicator in field_value for indicator in joc_indicators):
                            logging.debug(f"🎵 Atmos detected via JOC in track {track_number}: {field_value}")
                            is_atmos = True
                            break

                # Check for specific Atmos codec combinations
                if not is_atmos and 'truehd' in audio_format and 'atmos' in audio_format_profile:
                    logging.debug(f"🎵 Atmos detected in track {track_number}: TrueHD with Atmos profile")
                    is_atmos = True

                # Check for E-AC-3 JOC (Dolby Digital Plus with Atmos)
                if not is_atmos and 'e-ac-3' in audio_format and any('joc' in field for field in all_audio_fields):
                    logging.debug(f"🎵 Atmos detected in track {track_number}: E-AC-3 with JOC (Dolby Digital Plus Atmos)")
                    is_atmos = True

                # Check for Dolby Digital Plus with Atmos in commercial name
                if not is_atmos and 'dolby digital plus with dolby atmos' in audio_commercial_name:
                    logging.debug(f"🎵 Atmos detected in track {track_number}: Commercial name contains 'Dolby Digital Plus with Dolby Atmos'")
                    is_atmos = True

                if is_atmos:
                    atmos_tracks.append(track_number)

                # Debug logging for audio tracks (only in debug mode)
                logging.debug(f"Audio track {track_number}: format={audio_format}, profile={audio_format_profile}, title={audio_title}, codec_id={audio_codec_id}, info={audio_format_info}, commercial={audio_commercial_name}, is_atmos={is_atmos}")

        return atmos_tracks if atmos_tracks else []

    except Exception as e:
        logging.debug(f"Error detecting Dolby Atmos: {e}")
        return []





def generate_atmos_aware_audio_params(atmos_tracks, processed_audio_tracks, original_cmd):
    """Generate HandBrake audio parameters that preserve Atmos tracks while keeping original parameters for others."""

    encoders = []
    bitrates = []
    mixdowns = []

    # Extract original audio parameters from the HandBrakeCLI command
    original_encoders = []
    original_bitrates = []
    original_mixdowns = []

    # Extract aencoder parameter
    aencoder_match = re.search(r'--aencoder\s+([^-\s]+)', original_cmd)
    if aencoder_match:
        original_encoders = aencoder_match.group(1).split(',')
        logging.debug(f"🎵 Original encoders: {original_encoders}")

    # Extract ab parameter
    ab_match = re.search(r'--ab\s+([^-\s]+)', original_cmd)
    if ab_match:
        original_bitrates = ab_match.group(1).split(',')
        logging.debug(f"🎵 Original bitrates: {original_bitrates}")

    # Extract mixdown parameter
    mixdown_match = re.search(r'--mixdown\s+([^-\s]+)', original_cmd)
    if mixdown_match:
        original_mixdowns = mixdown_match.group(1).split(',')
        logging.debug(f"🎵 Original mixdowns: {original_mixdowns}")

    # Process each track
    for i in range(1, processed_audio_tracks + 1):
        if i in atmos_tracks:
            # Preserve Atmos track - use copy
            encoders.append('copy')
            bitrates.append('')  # No bitrate limit for Atmos
            mixdowns.append('none')  # Preserve original channel layout
            logging.debug(f"🎵 Track {i}: Atmos detected - using copy encoder")
        else:
            # Keep original parameters for non-Atmos tracks
            track_index = i - 1  # Convert to 0-based index

            # Get original encoder or default to av_aac
            if track_index < len(original_encoders):
                encoders.append(original_encoders[track_index])
            else:
                encoders.append('av_aac')

            # Get original bitrate or default to empty (let HandBrake decide)
            if track_index < len(original_bitrates):
                bitrates.append(original_bitrates[track_index])
            else:
                bitrates.append('')

            # Get original mixdown or default to 5point1
            if track_index < len(original_mixdowns):
                mixdowns.append(original_mixdowns[track_index])
            else:
                mixdowns.append('5point1')

            logging.debug(f"🎵 Track {i}: Using original parameters - encoder: {encoders[-1]}, bitrate: {bitrates[-1]}, mixdown: {mixdowns[-1]}")

    encoder_param = ','.join(encoders)
    bitrate_param = ','.join(filter(None, bitrates))  # Remove empty strings
    mixdown_param = ','.join(mixdowns)

    logging.debug(f"🎵 Generated audio parameters: encoders={encoder_param}, bitrates={bitrate_param}, mixdowns={mixdown_param}")

    params = {
        'aencoder': encoder_param,
        'ab': bitrate_param if bitrate_param else '',
        'mixdown': mixdown_param
    }

    return params


def get_transcode_command(input_file, output_file, encode_type, preview):
    """Gets the transcode-video command without executing it."""
    # Preview option is handled in modify_handbrake_output_path, not here

    # Determine parameters based on format
    if encode_type == ENCODE_MOVIE:
        format_params = encoding_parameters[ENCODE_MOVIE]
    elif encode_type == ENCODE_TVSHOW:
        format_params = encoding_parameters[ENCODE_TVSHOW]
    else:
        format_params = encoding_parameters[ENCODE_CUSTOM]

    # Check for Dolby Atmos and log detection (only if enabled)
    atmos_tracks = []
    if preserve_atmos_audio:
        atmos_tracks = detect_dolby_atmos(input_file)
        if atmos_tracks:
            logging.info(f"🎵 Dolby Atmos detected in tracks: {atmos_tracks}")
            logging.debug(f"🎵 Atmos tracks detected in file - will preserve codec during HandBrakeCLI processing")
    else:
        # Check if there are Atmos tracks even when disabled, and inform user
        potential_atmos_tracks = detect_dolby_atmos(input_file)
        if potential_atmos_tracks:
            logging.info(f"🎵 Dolby Atmos detected in tracks: {potential_atmos_tracks} (preservation disabled in config)")
            logging.info("💡 Set 'preserve_atmos_audio = yes' in tvb-config.ini to enable Atmos preservation")
        else:
            logging.debug("🎵 No Dolby Atmos tracks detected in file")
        atmos_tracks = []  # Ensure no Atmos processing when disabled

    arguments = f'{transcode_video_path} {format_params} --dry-run "{input_file}"'
    return arguments, atmos_tracks

def process_file(input_file, output_dir, encode_type, preview, counter, file_count, dry_run=False):
    """Transcodes a video using transcode-video."""
    output_file = Path(output_dir) / Path(input_file).name
    
    if not dry_run and output_file.exists():
        if preserve_file_date:
            set_target_date(input_file, output_file)
            logging.info(f'Skipping {Path(input_file).name}, already exists...')
            return

    progress = (counter / file_count) * 100
    progress = round(progress, 2)

    logging.info(f'Processing: {Path(input_file).name}')
    logging.info(f'File {counter} of {file_count} - {progress}%')

    transcode_cmd, atmos_tracks = get_transcode_command(input_file, output_file, encode_type, preview)
    logging.debug(f"transcode-video command: {transcode_cmd}")

    if dry_run:
        print(f"\n🔍 DRY-RUN for: {Path(input_file).name}")
        print(f"📋 transcode-video command:")
        print(f"   {transcode_cmd}")
        
        # Execute only the dry-run to see the HandBrakeCLI command
        args = shlex.split(transcode_cmd)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding=get_platform_encoding())
        
        gethbCmd = ""
        while True:
            retcode = proc.poll()
            try:
                out = proc.stdout.readline()
                if 'HandBrakeCLI' in out:
                    gethbCmd = out.strip()
                    print(f"🔧 HandBrakeCLI command (Original):")
                    print(f"   {gethbCmd}")
                    
                    # Show the modified command as well
                    modified_cmd = modify_handbrake_output_path(gethbCmd, output_file, preview, atmos_tracks)
                    print(f"🔧 HandBrakeCLI command (with output path):")
                    print(f"   {modified_cmd}")
                    break
            except:
                pass
            if retcode is not None:
                break
        
        if not gethbCmd:
            print(f"⚠️  No HandBrakeCLI command found!")
        
        print("-" * 80)
        return

    # Normal transcoding
    args = shlex.split(transcode_cmd)
    
    # First phase: Dry-run to get the HandBrakeCLI command
    logging.info("Starting transcode-video dry-run to get HandBrakeCLI command...")
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding=get_platform_encoding())

    gethbCmd = ""
    timeout_counter = 0
    max_timeout = 30  # 30 seconds timeout
    
    while True:
        retcode = proc.poll()
        try:
            out = proc.stdout.readline()
            if out:
                logging.debug(f"transcode-video output: {out.strip()}")
                if 'HandBrakeCLI' in out:
                    gethbCmd = out.strip()
                    logging.info("Found HandBrakeCLI command in transcode-video output")
                    break
        except Exception as e:
            logging.error(f"Error reading transcode-video output: {e}")
            break
        
        if retcode is not None:
            logging.info(f"transcode-video process finished with return code: {retcode}")
            break
            
        timeout_counter += 1
        if timeout_counter > max_timeout:
            logging.error("Timeout waiting for HandBrakeCLI command from transcode-video")
            proc.terminate()
            break

    logging.debug(f'Command from transcode-video: {gethbCmd}')

    if not gethbCmd:
        logging.error(f'Failed to get HandBrakeCLI command for: {Path(input_file).name}')
        return

    # Modify the HandBrakeCLI command to use our desired output path
    hbCmd = modify_handbrake_output_path(gethbCmd, output_file, preview, atmos_tracks)
    
    logging.debug(f'Final HandBrakeCLI command: {hbCmd}')

    # Second phase: Actual transcoding
    if cpu_limit_enabled:
        hbCmd = f'cpulimit --limit={cpu_limit_percentage} -i -z {hbCmd}'
    
    hbCmd = shlex.split(hbCmd)
    
    try:
        proc = subprocess.Popen(hbCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding=get_platform_encoding())
    except Exception as e:
        logging.error(f'Encoding failed -> {Path(input_file).name}, {e}')
        return

    start_time = time.time()

    # Create descriptive progress bar with file name and batch progress
    file_name = Path(input_file).name
    batch_progress = f"File {counter} of {file_count}"

    # Truncate filename if too long, but keep it informative
    max_filename_length = terminal_columns - 10
    if len(file_name) > max_filename_length:
        # Try to keep the episode info if it's a TV show
        if ' - S' in file_name and ' - ' in file_name:
            # For TV shows, keep the show name and episode info
            parts = file_name.split(' - ')
            if len(parts) >= 3:
                show_name = parts[0][:20]
                episode_info = ' - '.join(parts[-2:])  # Last two parts (season + episode)
                display_name = f"{show_name}... - {episode_info}"
            else:
                display_name = file_name[:max_filename_length-3] + "..."
        else:
            display_name = file_name[:max_filename_length-3] + "..."
    else:
        display_name = file_name

    # Print batch progress info before starting the progress bar
    print(f"\n📁 {batch_progress}")
    print(f"🎬 Encoding: {display_name}")
    print("-" * terminal_columns)

    bar_length = terminal_columns - 45
    tqdm_bar = tqdm(total=100,
                    desc="Progress",
                    bar_format='{desc}: {percentage:3.0f}%|{bar:' + str(bar_length) + '}{postfix}',
                    ncols=terminal_columns)
    while proc.poll() is None:
        out = proc.stdout.readline()
        matches = re.match(r'.*\s(\d+\.\d+)\s%.*avg\s(\d+\.\d+).*ETA\s(\d+)h(\d+)m(\d+)s', out)
        if matches:
            tqdm_bar.update(int(float(matches.group(1))) - tqdm_bar.n)
            tqdm_bar.set_postfix_str(f"avg {matches.group(2)} fps, ETA {matches.group(3)}h{matches.group(4)}m{matches.group(5)}s")
            tqdm_bar.refresh()
    tqdm_bar.close()

    # Print completion message
    elapsed_time = time.time() - start_time
    print(f"\n✅ Completed: {display_name}")
    print(f"⏱️  Encoding time: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
    print("=" * terminal_columns)

    # Post-processing
    if os.path.exists(output_file):
        original_size = Filesize(os.path.getsize(input_file))
        new_size = Filesize(os.path.getsize(output_file))
        logging.info(f'Original/New file size: {original_size}/{new_size}')
        
        # Edit subtitles (only if manually activated)
        if manual_subtitle_editing:
            subtitles = get_media_info(output_file)
            if subtitles:
                edit_subtitles(output_file, subtitles)
            else:
                logging.debug("Subtitle editing skipped (transcode-video handles this automatically)")

        # Write statistics
        elapsed_time = time.time() - start_time
        elapsed_time_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        logging.info(f'Elapsed time: {elapsed_time_formatted}')
        
        # Set locale based on configuration
        # Try to use the configured locale, fallback to system default if not available
        locale_set = False
        if hasattr(locals(), 'localization') and localization and localization.lower() != 'default':
            # Use the local variable if it exists
            loc_setting = localization
        elif 'localization' in globals():
            # Use the global variable
            loc_setting = globals()['localization']
        else:
            # Default fallback
            loc_setting = 'en_US'

        if loc_setting and loc_setting.lower() != 'default':
            # Try different variations of the locale string
            locale_variations = [
                loc_setting,
                f"{loc_setting}.UTF-8",
                f"{loc_setting}.utf8",
                loc_setting.replace('-', '_'),
                f"{loc_setting.replace('-', '_')}.UTF-8"
            ]

            for loc in locale_variations:
                try:
                    locale.setlocale(locale.LC_ALL, loc)
                    logging.debug(f"Successfully set locale to: {loc}")
                    locale_set = True
                    break
                except locale.Error:
                    continue

            if not locale_set:
                logging.debug(f"Locale '{loc_setting}' not available, using system default")
                locale.setlocale(locale.LC_ALL, '')
        else:
            locale.setlocale(locale.LC_ALL, '')

        # Use strftime with current locale settings
        # This will automatically format dates according to the locale
        try:
            now = datetime.today().strftime('%c')  # %c uses locale's preferred date/time format
        except (ValueError, OSError):
            # Fallback if locale formatting fails
            now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        percent_val = '{:.2%}'.format(os.path.getsize(output_file) / os.path.getsize(input_file))
        stats_data = [now, Path(input_file).name, original_size, new_size, percent_val, elapsed_time_formatted, gethbCmd]
        write_statistics(stats_data)

        if preserve_file_date:
            set_target_date(input_file, output_file)

def find_videos_in_directory(input_dir):
    """Finds all video files in a directory."""
    return [str(file) for file in Path(input_dir).rglob("*") if file.suffix.lower() in VIDEO_EXTENSIONS]

def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description='tvb - transcode video batch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('-i', '--input', required=True,
                        help='Input file or directory (including files in subfolders)')
    parser.add_argument('-o', '--output', default=default_output_directory,
                        help='Output directory (default: %(default)s)')
    parser.add_argument('-f', '--format', choices=[ENCODE_MOVIE, ENCODE_TVSHOW, ENCODE_CUSTOM],
                        help='Set the format for ALL files from -i [movie/tvshow/custom] (optional, if not set, the script detects format)')
    parser.add_argument('-m', '--merge', action='store_true',
                        help='Multiplex the file with mkvmerge, copies all streams into a new file')
    parser.add_argument('-H', '--hibernate', action='store_true',
                        help='Hibernate computer after encoding is finished')
    parser.add_argument('-P', '--preview', action='store_true',
                        help='Create preview (optional, default is 30 seconds)')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Show HandBrakeCLI commands without executing (dry run)')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed information and progress')
    parser.add_argument('--debug', action='store_true',
                        help='Show detailed technical information and full logs')
    
    return parser.parse_args()

def main():
    """Main program."""
    args = parse_args()
    setup_logging(verbose=args.verbose, debug=getattr(args, 'debug', False))
    
    logging.info(f"Running {__appname__} version {__version__}")

    # Check HandBrakeCLI version
    latest_version = get_latest_handbrake_version()
    logging.info(f"Latest HandBrakeCLI version: {latest_version}")
    if latest_version:
        installed_version = get_installed_handbrake_version()
        logging.info(f"Installed HandBrakeCLI version: {installed_version}")
        if installed_version:
            check_latest_handbrake_version(installed_version, latest_version)
        else:
            print("HandBrakeCLI is not installed or an error occurred while checking the version.")
    else:
        print("Failed to fetch the latest version of HandBrakeCLI.")

    # Debug: Show found tools
    logging.info("🔍 Tool search completed:")
    logging.info(f"  transcode-video: {transcode_video_path}")
    logging.info(f"  mkvpropedit: {path_mkvpropedit}")
    logging.info(f"  mkvmerge: {path_mkvmerge}")
    
    # Check if transcode-video path exists
    if ' ' in transcode_video_path:  # Ruby command with script
        parts = transcode_video_path.split()
        ruby_path = parts[0]
        script_path = parts[1]
        if not os.path.exists(ruby_path):
            logging.error(f"Ruby not found: {ruby_path}")
            sys.exit(1)
        if not os.path.exists(script_path):
            logging.error(f"transcode-video script not found: {script_path}")
            logging.error("Please install video_transcoding or check the paths")
            sys.exit(1)
    elif not os.path.exists(transcode_video_path):
        logging.error(f"transcode-video not found: {transcode_video_path}")
        logging.error("Please install video_transcoding or check the paths")
        sys.exit(1)
    
    # Validate and create output directory (only if not dry-run)
    if not args.dry_run:
        output_dir = args.output
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
                logging.info(f"Created output directory: {output_dir}")
            except OSError as e:
                logging.warning(f"Failed to create specified output directory: {output_dir}")
                logging.warning(f"Error: {e}")
                logging.info(f"Trying default output directory: {default_output_directory}")
                output_dir = default_output_directory
                
                # Try to create default directory
                if not os.path.isdir(output_dir):
                    try:
                        os.makedirs(output_dir)
                        logging.info(f"Created default output directory: {output_dir}")
                    except OSError as e2:
                        logging.warning(f"Failed to create default output directory: {output_dir}")
                        logging.warning(f"Error: {e2}")
                        
                        # Last resort: create local output directory
                        local_output_dir = "./output"
                        logging.info(f"Creating local output directory: {local_output_dir}")
                        try:
                            os.makedirs(local_output_dir, exist_ok=True)
                            output_dir = local_output_dir
                            logging.info(f"Successfully created local output directory: {output_dir}")
                        except OSError as e3:
                            logging.error(f"Failed to create any output directory")
                            logging.error(f"Errors: {e}, {e2}, {e3}")
                            logging.error("Please check permissions or specify a valid output directory with -o")
                            sys.exit(1)
        args.output = output_dir
    
    # Collect and process files
    encode_list = TranscodeList(input_path=args.input, encode_type=args.format)
    logging.debug(f"Collected files: {encode_list.processed_list}")
    
    if not encode_list.processed_list:
        logging.error("No video files found to process.")
        sys.exit(1)
    
    # Print batch overview
    file_count = len(encode_list.processed_list)
    if args.dry_run:
        print('🔍 TVB - Dry Run Mode')
        print('=' * terminal_columns)
        print(f'📋 Found {file_count} video file(s) to process')
    else:
        print('=' * terminal_columns)
        print('🎬 Transcode-Video Batch Encoding')
        print('=' * terminal_columns)
        print(f'📊 Batch: {file_count} video file(s) to process')
        print(f'🎯 Output: {args.output}')
        print('-' * terminal_columns)

    counter = 0
    
    for line in encode_list.processed_list:
        counter += 1
        input_file = line[0]
        encode_type = line[1]
        
        if args.merge:
            if not args.dry_run:
                merge_file(input_file, args.output)
        else:
            process_file(input_file, args.output, encode_type, args.preview, counter, file_count, args.dry_run)

    # Print final summary (only for actual encoding, not dry-run)
    if not args.dry_run and file_count > 0:
        print('\n' + '=' * terminal_columns)
        print('🎉 Batch Encoding Complete!')
        print('=' * terminal_columns)
        print(f'✅ Processed: {file_count} video file(s)')
        print(f'📁 Output: {args.output}')

        # Count successfully created files
        successful_files = 0
        for line in encode_list.processed_list:
            input_file = line[0]
            output_file = os.path.join(args.output, os.path.basename(input_file))
            if os.path.exists(output_file):
                successful_files += 1

        print(f'📈 Success rate: {successful_files}/{file_count} files')
        print('=' * terminal_columns)

    # Hibernate after transcoding (only if not dry-run)
    if not args.dry_run:
        hibernate(args.hibernate)

if __name__ == "__main__":
    main()