#!/usr/bin/env python3
import os
import sys
import time
import shlex
import logging
import shutil
import subprocess
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Ensure package imports work when running from any directory
_pkg_dir = Path(__file__).resolve().parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from config.config_loader import TVBConfig, VIDEO_EXTENSIONS
from transcode.analyzer import MediaAnalyzer
from transcode.generator import HandBrakeGenerator
from features.atmos import detect_dolby_atmos, generate_atmos_aware_audio_params
from features.statistics import Filesize, write_statistics

__appname__ = "tvb - transcode video batch"
__version__ = "1.0.0"
__author__ = "breacasu <breacasu@posteo.de>"
__license__ = "MIT"

LOG_FILE = "transcode.log"
terminal_columns, _ = shutil.get_terminal_size()
config = None


def emit_json(msg_type, **kwargs):
    data = {"type": msg_type, **kwargs}
    line = json.dumps(data, ensure_ascii=False)
    print(line, flush=True)


class JsonLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            emit_json("log", level=record.levelname, message=msg)
        except Exception:
            pass


def setup_logging(verbose=False, debug=False):
    logging.getLogger().handlers.clear()
    log_level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING

    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_formatter = logging.Formatter("%(message)s")

    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)

    json_handler = JsonLogHandler()
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(json_handler)

    logging.debug("Logging system initialized")
    logging.info("TVB logging started")


def find_handbrake_cli():
    if getattr(sys, '_MEIPASS', None):
        bundled = Path(sys._MEIPASS) / "HandBrakeCLI"
        if bundled.exists():
            return str(bundled)

    path_result = shutil.which("HandBrakeCLI")
    if path_result:
        return path_result

    script_dir = Path(__file__).resolve().parent.parent
    bundled = script_dir / "bin" / "HandBrakeCLI"
    if bundled.exists():
        return str(bundled)

    typical_paths = [
        "/opt/homebrew/bin/HandBrakeCLI",
        "/usr/local/bin/HandBrakeCLI",
        "/usr/bin/HandBrakeCLI",
    ]
    for p in typical_paths:
        if os.path.exists(p):
            return p

    return "HandBrakeCLI"


def get_handbrake_version(handbrake_path):
    try:
        result = subprocess.run([handbrake_path, "--version"],
                                capture_output=True, text=True, timeout=10)
        match = re.search(r"(\d+\.\d+\.\d+)", result.stdout or result.stderr or "")
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def get_latest_handbrake_version():
    url = "https://handbrake.fr/downloads2.php"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode('utf-8')
        match = re.search(r'Current Version[:\s]*([\d.]+)', html)
        if match:
            return match.group(1)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logging.warning(f"Could not fetch latest HandBrakeCLI version: {e}")
    return None


def check_handbrake_version(installed, latest):
    if not installed:
        return "could not determine installed version"
    if not latest:
        return f"installed {installed} (could not check latest)"
    if installed == latest:
        return f"installed {installed} (up to date)"
    return f"installed {installed} (latest {latest}) — update recommended"


class TranscodeList:
    def __init__(self, input_paths, encode_type=None):
        self.input_paths = input_paths if isinstance(input_paths, list) else [input_paths]
        self.file_list = self._collect_files()
        self.processed_list = []
        self.forced_format = encode_type
        if self.forced_format is None:
            self.processed_list = self._detect_formats()
        else:
            self.processed_list = self._apply_forced_format()

    @staticmethod
    def _is_video_file(file_path):
        _, ext = os.path.splitext(file_path)
        return ext.lower() in VIDEO_EXTENSIONS

    def _collect_files(self):
        video_files = []
        for input_path in self.input_paths:
            if os.path.isdir(input_path) and os.path.exists(input_path):
                for root, _, files in os.walk(input_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if self._is_video_file(full_path):
                            video_files.append(full_path)
            elif os.path.isfile(input_path) and os.path.exists(input_path):
                if self._is_video_file(input_path):
                    video_files.append(input_path)
            else:
                logging.error(f"The input file/dir does not exist: {input_path}")
                sys.exit(1)

        logging.debug(f"No. of video files collected: {len(video_files)}")
        return video_files

    def _detect_formats(self):
        format_list = []
        for file_path in self.file_list:
            match = re.search(r"(.*?)[.\s][sS](\d{1,2})[eE](\d{1,3}).*", os.path.basename(file_path))
            if match:
                logging.debug(f"{os.path.basename(file_path)} is a TV-Show.")
                format_list.append((file_path, "tvshow"))
            else:
                logging.debug(f"{os.path.basename(file_path)} is not a TV-Show.")
                format_list.append((file_path, "movie"))
        return format_list

    def _apply_forced_format(self):
        return [(fp, self.forced_format) for fp in self.file_list]


def set_target_date(source, target):
    old_date = os.path.getmtime(source)
    os.utime(target, (old_date, old_date))


def modify_handbrake_output_path(handbrake_cmd, atmos_tracks=None, preview=False):
    cmd_str = handbrake_cmd if isinstance(handbrake_cmd, str) else ' '.join(handbrake_cmd)

    if atmos_tracks:
        audio_match = re.search(r'--audio\s+([^-\s]+)', cmd_str)
        if audio_match:
            try:
                audio_tracks_str = audio_match.group(1)
                processed_tracks = [int(x) for x in audio_tracks_str.split(',')]
                max_processed_track = max(processed_tracks)

                relevant_atmos_tracks = [t for t in atmos_tracks if t <= max_processed_track]
                if relevant_atmos_tracks:
                    audio_params = generate_atmos_aware_audio_params(
                        relevant_atmos_tracks, len(processed_tracks), cmd_str)

                    if '--aencoder' in cmd_str:
                        cmd_str = re.sub(r'--aencoder\s+[^-\s]+',
                                         f'--aencoder {audio_params["aencoder"]}', cmd_str)
                    if audio_params['ab']:
                        if '--ab' in cmd_str:
                            cmd_str = re.sub(r'--ab\s+[^-\s]+',
                                             f'--ab {audio_params["ab"]}', cmd_str)
                    if '--mixdown' in cmd_str:
                        cmd_str = re.sub(r'--mixdown\s+[^-\s]+',
                                         f'--mixdown {audio_params["mixdown"]}', cmd_str)

                    logging.info("Audio parameters modified for Atmos preservation")
            except (ValueError, AttributeError) as e:
                logging.warning(f"Could not parse audio tracks for Atmos: {e}")

    if preview:
        preview_param = config.get_preview_params()
        cmd_str = cmd_str.rstrip() + f' {preview_param}'

    return cmd_str


def process_file(input_file, output_dir, encode_type, preview, counter, file_count, dry_run=False):
    output_file = Path(output_dir) / Path(input_file).name

    if not dry_run and output_file.exists():
        if config.preserve_file_date:
            set_target_date(input_file, output_file)
            logging.info(f'Skipping {Path(input_file).name}, already exists...')
        return

    progress = round((counter / file_count) * 100, 2)
    logging.info(f'Processing: {Path(input_file).name}')
    logging.info(f'File {counter} of {file_count} - {progress}%')

    emit_json("progress", current=counter, total=file_count,
              progress=progress, filename=Path(input_file).name)

    analyzer = MediaAnalyzer()
    media_info = analyzer.scan_media(input_file)

    format_params = config.get_format_params(encode_type)
    generator = HandBrakeGenerator(media_analyzer=analyzer)
    generator.parse_transcode_video_params(format_params)

    handbrake_path = find_handbrake_cli()
    fmt = Path(output_file).suffix.lower()
    if fmt == '.mkv':
        generator.add_extra_option('format', 'av_mkv')
    elif fmt == '.mp4':
        generator.add_extra_option('format', 'av_mp4')

    atmos_tracks = []
    if config.preserve_atmos_audio:
        atmos_tracks = detect_dolby_atmos(input_file)
        if atmos_tracks:
            logging.info(f"Dolby Atmos detected in tracks: {atmos_tracks}")
            generator.set_atmos_tracks(atmos_tracks)
    else:
        potential_atmos = detect_dolby_atmos(input_file)
        if potential_atmos:
            logging.info(f"Dolby Atmos tracks: {potential_atmos} (preservation disabled in config)")

    cmd_list = generator.generate_command_list(str(input_file), str(output_file), media_info)
    cmd_list[0] = handbrake_path

    def quote_arg(arg):
        return f'"{arg}"' if ' ' in arg else arg
    cmd_str = ' '.join(quote_arg(a) for a in cmd_list)
    final_cmd = modify_handbrake_output_path(cmd_str, preview=preview, atmos_tracks=atmos_tracks)

    if dry_run:
        print(f"\n DRY-RUN for: {Path(input_file).name}")
        print(f" HandBrakeCLI command:")
        print(f"   {final_cmd}")
        print("-" * 80)
        emit_json("dry_run", filename=Path(input_file).name, command=final_cmd)
        return

    logging.info(f'Encoding: {Path(input_file).name}')
    logging.debug(f'HandBrakeCLI command: {final_cmd}')
    start_time = time.time()

    try:
        proc = subprocess.Popen(shlex.split(final_cmd),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, encoding='utf-8')
    except Exception as e:
        logging.error(f'Encoding failed -> {Path(input_file).name}, {e}')
        emit_json("error", filename=Path(input_file).name, message=str(e))
        return

    while proc.poll() is None:
        out = proc.stdout.readline()
        matches = re.match(r'.*\s(\d+\.\d+)\s%.*avg\s(\d+\.\d+).*ETA\s(\d+)h(\d+)m(\d+)s', out)
        if matches:
            pct = float(matches.group(1))
            fps = matches.group(2)
            eta = f"{matches.group(3)}h{matches.group(4)}m{matches.group(5)}s"
            if pct % 10 < 0.01:
                logging.info(f'{Path(input_file).name}: {pct:.1f}% @ {fps} fps, ETA {eta}')
            emit_json("progress", current=counter, total=file_count,
                      progress=progress, filename=Path(input_file).name,
                      filePercent=pct, fps=fps, eta=eta)

    elapsed_time = time.time() - start_time
    elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
    logging.info(f'Encoding completed: {Path(input_file).name} in {elapsed_str}')
    emit_json("file_complete", filename=Path(input_file).name, elapsed=elapsed_str)

    if os.path.exists(output_file):
        original_size = Filesize(os.path.getsize(input_file))
        new_size = Filesize(os.path.getsize(output_file))
        logging.info(f'Original/New file size: {original_size}/{new_size}')

        try:
            now = datetime.today().strftime('%c')
        except (ValueError, OSError):
            now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        percent_val = '{:.2%}'.format(os.path.getsize(output_file) / os.path.getsize(input_file))
        stats_data = [now, Path(input_file).name, str(original_size),
                      str(new_size), percent_val, elapsed_str, final_cmd]
        write_statistics(stats_data)
        emit_json("stats_written", filename=Path(input_file).name)

        if config.preserve_file_date:
            set_target_date(input_file, output_file)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='tvb - transcode video batch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('-i', '--input', required=True, action='append', dest='inputs',
                        help='Input file(s) or director(ies)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output directory')
    parser.add_argument('-f', '--format', choices=['movie', 'tvshow', 'custom'],
                        help='Force format for all files')
    parser.add_argument('-P', '--preview', action='store_true',
                        help='Create preview (30 seconds)')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Show commands without executing')
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode')

    return parser.parse_args()


def main():
    global config
    args = parse_args()

    config_path = os.environ.get('TVB_CONFIG_PATH')
    config = TVBConfig(config_path)

    setup_logging(verbose=args.verbose, debug=args.debug)

    logging.info(f"Running {__appname__} version {__version__}")
    emit_json("version", app=__appname__, version=__version__)

    handbrake_path = find_handbrake_cli()
    logging.info(f"HandBrakeCLI: {handbrake_path}")
    emit_json("tool", name="HandBrakeCLI", path=handbrake_path)

    hb_version = get_handbrake_version(handbrake_path)
    latest_version = get_latest_handbrake_version()
    version_msg = check_handbrake_version(hb_version, latest_version)
    logging.info(f"HandBrakeCLI: {version_msg}")
    emit_json("version_check", tool="HandBrakeCLI", installed=hb_version, latest=latest_version)

    output_dir = args.output or config.get_output_dir()

    if not args.dry_run:
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
                logging.info(f"Created output directory: {output_dir}")
            except OSError as e:
                logging.error(f"Failed to create output directory: {output_dir}")
                sys.exit(1)

    encode_list = TranscodeList(input_paths=args.inputs, encode_type=args.format)
    if not encode_list.processed_list:
        logging.error("No video files found to process.")
        sys.exit(1)

    file_count = len(encode_list.processed_list)
    if args.dry_run:
        print(' TVB - Dry Run Mode')
        print('=' * terminal_columns)
        print(f' Found {file_count} video file(s) to process')
    else:
        print('=' * terminal_columns)
        print(' TVB Batch Encoding')
        print('=' * terminal_columns)
        print(f' Batch: {file_count} video file(s)')
        print(f' Output: {output_dir}')
        print('-' * terminal_columns)

    counter = 0
    for line in encode_list.processed_list:
        counter += 1
        input_file = line[0]
        encode_type = line[1]

        process_file(input_file, output_dir, encode_type,
                     args.preview, counter, file_count, args.dry_run)

    if not args.dry_run and file_count > 0:
        print('\n' + '=' * terminal_columns)
        print(' Batch Encoding Complete!')
        print('=' * terminal_columns)
        print(f' Processed: {file_count} video file(s)')
        print(f' Output: {output_dir}')
        print('=' * terminal_columns)

        emit_json("complete", files=file_count, output=str(output_dir))


if __name__ == "__main__":
    main()