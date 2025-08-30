# TVB - Transcode Video Batch

A modern Python script for batch video transcoding using Lisa Melton's `video_transcoding` tool (2025 version).

## Version
Current version: 0.9

## Key Changes in Version 0.9
- **Complete adaptation to Lisa Melton's new `video_transcoding` script** (2025)
- **Intelligent tool detection** - automatically finds tools in PATH and typical installation locations
- **Advanced output path handling** - modifies HandBrakeCLI commands to use custom output directories
- **Dry-run mode** - displays complete transcode-video and HandBrakeCLI commands without execution
- **Dolby Atmos preservation** - automatically detects and preserves Atmos audio tracks
- **Enhanced progress tracking** - shows batch progress, current file, and encoding statistics
- **Virtual environment support** - encapsulated execution with all dependencies
- **Cross-platform compatibility** - works on macOS, Windows, and Linux

## Prerequisites

### System Dependencies
- **Python 3.8+**
- **Ruby** (for video_transcoding)
- **HandBrakeCLI 1.8.0+** (for video encoding - script checks version automatically)
- **FFmpeg** (for media information)
- **mkvpropedit** (for editing Matroska file properties)
- **mkvmerge** (for multiplexing streams)

### Python Dependencies
- `pymediainfo>=7.0.1` (media information extraction)
- `tqdm>=4.65.0` (progress bars)
- `requests>=2.31.0` (HTTP requests)
- `beautifulsoup4>=4.12.0` (HTML parsing)
- `lxml>=4.9.0` (XML processing)
- `cpulimit>=0.1` (optional CPU usage limiting)

## Installation

### 1. System Dependencies
Install the required system tools:

**macOS (using Homebrew):**
```bash
brew install handbrake ffmpeg mkvtoolnix ruby
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install handbrake-cli ffmpeg mkvtoolnix ruby
```

**Windows:**
Download and install from official websites:
- HandBrakeCLI
- FFmpeg
- MKVToolNix
- Ruby

### 2. video_transcoding Installation
Install Lisa Melton's video_transcoding tool:

```bash
# Clone the repository
git clone https://github.com/lisamelton/video_transcoding.git
cd video_transcoding

# Install (this will create transcode-video.rb in /usr/local/bin/)
sudo ./install
```

### 3. Python Virtual Environment Setup

**macOS/Linux:**
```bash
# Make setup script executable
chmod +x setup_venv.sh

# Run setup
./setup_venv.sh
```

**Windows:**
```cmd
# Run setup
setup_venv.bat
```

### 4. Activate Environment
After setup, activate the virtual environment:

**macOS/Linux:**
```bash
source activate_tvb.sh
```

**Windows:**
```cmd
activate_tvb.bat
```

## Configuration

### Setup Your Personal Configuration

1. **Copy the example config:**

   **macOS/Linux:**
   ```bash
   # Option 1: Manual copy
   cp tvb-config.ini.example tvb-config.ini

   # Option 2: Use setup script (recommended)
   ./setup_config.sh
   ```

   **Windows:**
   ```cmd
   # Option 1: Manual copy
   copy tvb-config.ini.example tvb-config.ini

   # Option 2: Use setup script (recommended)
   setup_config.bat
   ```

2. **Edit the configuration:**

   **macOS/Linux:**
   ```bash
   # Adjust directories to your needs
   inputdir = '/your/input/directory'
   outputdir = '/your/output/directory'

   # Optional: Enable features you need
   preserve_atmos_audio = yes  # For Dolby Atmos support
   cpulimit = yes              # For CPU limiting
   ```

   **Windows:**
   ```cmd
   # Adjust directories to your needs
   inputdir = 'C:\your\input\directory'
   outputdir = 'C:\your\output\directory'

   # Optional: Enable features you need
   preserve_atmos_audio = yes  # For Dolby Atmos support
   cpulimit = yes              # For CPU limiting
   ```

### Configuration File
The script uses a configuration file for encoding parameters and tool paths:

```ini
# TVB - Transcode Video Batch Configuration
# Copy tvb-config.ini.example to tvb-config.ini and adjust settings

# Encoding presets for different content types
# Choose the preset that matches your video content

[tvshow]
# Example: Hardware H.265 encoding for TV shows
# Fast encoding, excellent quality, preserves all audio/subtitle tracks
parameter = --add-audio all --add-subtitle all -x encoder=vt_h265 -x quality=56 -x encoder-preset=quality

[movie]
# Example: Modern AV1 encoding for movies
# Best compression efficiency, German/English audio focus
parameter = --mode av1 --add-audio ger --add-audio eng --add-subtitle all

[custom]
# Example: Software H.265 encoding for any content
# Compatible with all systems, includes all tracks
parameter = --mode hevc --quality 24 --add-audio all --add-subtitle all

[preview]
# Preview encoding: Creates short clips for testing
# 30 seconds is usually sufficient for quality assessment
parameter = --stop-at duration:30

[default]
# ==========================================
# GENERAL SETTINGS
# ==========================================

# Input/Output directories (REQUIRED - adjust to your system)
inputdir = '/path/to/input/videos'
outputdir = '/path/to/output/directory'

# CPU Usage Control (optional)
cpulimit = no                    # Enable CPU limiting? (yes/no)
cpulimitpercent = 400           # CPU usage limit (100 per core, e.g. 400 = 4 cores)

# Language & Localization
localization = 'en_US'           # Locale for date format in CSV statistics
                                 # Examples: 'en_US', 'de_DE', 'fr_FR', 'es_ES', 'nl_NL', 'default'
                                 # Uses system default if locale is not available

# Subtitle Processing
edit_subtitles_manually = no     # Manual subtitle editing (usually automatic)

# File Handling
preserve_file_date = no         # Keep original file timestamps? (yes/no)

# ==========================================
# ADVANCED FEATURES
# ==========================================

# Dolby Atmos Support (optional)
preserve_atmos_audio = no        # Detect and preserve Dolby Atmos tracks

# ==========================================
# TOOL PATHS (usually not needed)
# ==========================================
# The script automatically finds tools in your PATH
# Only configure these if automatic detection fails

[transcode_video_path]
# Ruby script for video transcoding (usually found automatically)
macos = '/usr/local/bin/transcode-video.rb'
windows = "C:\\Ruby\\bin\\transcode-video.bat"

[mkvpropedit_path]
# MKV metadata editor (part of MKVToolNix)
macos = '/usr/local/bin/mkvpropedit'
windows = "C:\\Program Files\\MKVToolNix\\mkvpropedit.exe"

[mkvmerge_path]
# MKV multiplexer (part of MKVToolNix)
macos = '/usr/local/bin/mkvmerge'
windows = "C:\\Program Files\\MKVToolNix\\mkvmerge.exe"

[ffmpeg_path]
# FFmpeg for media analysis
macos = '/usr/local/bin/ffmpeg'
windows = "C:\\ffmpeg\\bin\\ffmpeg.exe"

[handbrakecli_path]
# HandBrake command line encoder
macos = '/usr/local/bin/HandBrakeCLI'
windows = "C:\\Program Files\\HandBrake\\HandBrakeCLI.exe"
```

**Important:**
- The script automatically detects tools in PATH and typical installation locations. The path sections in the config file are only used as fallbacks if automatic detection fails.
- `preserve_file_date = yes/no`: Controls whether encoded files should keep the original file's date/timestamp or use the current date/time.
- `cpulimit = yes/no`: Enables CPU usage limiting to prevent system overload during encoding.
- `edit_subtitles_manually = yes/no`: Manual subtitle editing (usually not needed as transcode-video handles this automatically).
- **Audio Encoding:** The script preserves original audio parameters from transcode-video for non-Atmos tracks, including your language selection (use `--add-audio ger --add-audio eng` for German+English). Dolby Atmos preservation is optional and can be enabled with `preserve_atmos_audio = yes` in the config. When enabled, Atmos tracks are automatically detected and preserved using `copy` encoder. When disabled (default), all audio tracks are processed normally without special Atmos handling.

## Usage

### Basic Usage
```bash
# Transcode a single file
./tvb_wrapper.sh -i "/path/to/video.mkv" -o "/output/directory"

# Transcode all videos in a directory
./tvb_wrapper.sh -i "/input/directory" -o "/output/directory"

# Force specific format for all files
./tvb_wrapper.sh -i "/input/directory" -o "/output/directory" -f movie
```

### Advanced Options
```bash
# Dry-run mode (show commands without execution)
./tvb_wrapper.sh -i "/input/video.mkv" -d

# Create preview (30 seconds)
./tvb_wrapper.sh -i "/input/video.mkv" -P

# Multiplex with mkvmerge
./tvb_wrapper.sh -i "/input/video.mkv" -m

# Hibernate after completion
./tvb_wrapper.sh -i "/input/video.mkv" -H

# Verbose output
./tvb_wrapper.sh -i "/input/video.mkv" -v

# Debug mode
./tvb_wrapper.sh -i "/input/video.mkv" --debug

# Show version
./tvb_wrapper.sh --version
```

### Command Line Arguments
- `-i, --input`: Input file or directory (required)
- `-o, --output`: Output directory (default: from config)
- `-f, --format`: Force format for all files [movie/tvshow/custom]
- `-m, --merge`: Multiplex with mkvmerge
- `-H, --hibernate`: Hibernate after completion
- `-P, --preview`: Create preview (30 seconds)
- `-d, --dry-run`: Show commands without execution
- `-v, --verbose`: Verbose output
- `--debug`: Debug mode
- `--version`: Show version information

## Features

### Automatic Format Detection
The script automatically detects video format based on filename:
- **TV Shows**: `Show Name - S01E01 - Episode.mkv`
- **Movies**: `Movie Name (Year).mkv` or `Movie Name.mkv`
- **Custom**: All other formats

### Intelligent Tool Detection
- Searches for tools in system PATH
- Checks typical installation locations
- Uses config file paths as fallback
- Supports multiple platforms (macOS, Windows, Linux)
- **Automatically checks HandBrakeCLI version** and warns about outdated installations

### Advanced Output Handling
- Modifies HandBrakeCLI commands to use specified output directories
- Handles complex path structures and quoting
- No need to copy files after encoding
- Maintains directory structure (subfolders are preserved in output)

### Dolby Atmos Preservation
- Automatically detects Dolby Atmos audio tracks (E-AC-3 JOC, TrueHD Atmos, etc.)
- Preserves Atmos tracks using `copy` encoder to maintain original quality
- Adjusts other audio tracks to optimal settings while respecting user language preferences
- Prevents quality loss on Atmos content
- Optional feature: can be disabled in config for users who don't need Atmos support
- Compatible with all major Atmos formats and codecs
- **Setup**: Set `preserve_atmos_audio = yes` in `tvb-config.ini` to enable

### Enhanced Progress Tracking
- Real-time progress bars with batch information
- Shows current file and overall progress
- File size comparison and compression ratios
- Encoding statistics and ETA
- CSV output for detailed analysis

### Subtitle Handling
- Automatic subtitle flag management by transcode-video
- Support for forced and default subtitles
- Optional manual subtitle editing

## Output Files

### Transcoding Results
- Encoded video files in specified output directory
- Maintains original directory structure
- Matroska (.mkv) format with H.264/H.265/AV1 video codecs
- Dolby Atmos tracks preserved when detected and enabled (see Dolby Atmos Preservation feature)
- File date preservation - can be disabled with `preserve_file_date = no`

### Statistics
- `tvb-stats.csv`: Comprehensive encoding statistics
- Columns: Date, Filename, Original Size, New Size, Compression Ratio, Encoding Time, Command, Success Status

### Logs
- `transcode.log`: Detailed execution log with debug information
- Console output with batch progress, current file, and encoding statistics
- HandBrakeCLI command modifications logged for troubleshooting

## Known Issues

### Tool Detection
- Ensure tools are properly installed and accessible in PATH
- Check config file paths if automatic detection fails
- Verify Ruby installation for video_transcoding
- **HandBrakeCLI version should be 1.8.0+** - script automatically checks and warns about outdated versions
- Update HandBrakeCLI if version warnings appear during startup

### File Paths and Output
- Use absolute paths for best compatibility
- Avoid special characters in file names and paths
- Ensure sufficient disk space (at least 2x input file size)
- Output directory must be writable

### Encoding Issues
- Preview mode requires HandBrakeCLI 1.8.0+ (same as main encoding)
- Hardware acceleration may cause compatibility issues with some codecs
- Some exotic audio formats may not be fully supported

### Performance
- **CPU limiting**: Enable with `cpulimit = yes` in config for system stability
- **Quality settings**: Lower values = better quality, higher values = faster encoding
- **Hardware encoders**: vt_h265, nvenc provide faster encoding than software encoders

## Support

### Troubleshooting
1. **Tool not found**: Check installation and PATH, verify config file paths
2. **Permission errors**: Ensure write access to output directory
3. **Encoding failures**: Verify input file integrity, check HandBrakeCLI version
4. **Audio issues**: Check audio track formats with MediaInfo, ensure proper language selection
5. **Path issues**: Use absolute paths, avoid special characters
6. **System resource issues**: Reduce quality settings, enable CPU limiting, or check available RAM for very large files

### Debug Options
Use debug flags for detailed troubleshooting:

```bash
# Verbose output
./tvb_wrapper.sh -i "/input/video.mkv" -v

# Debug mode with full logging
./tvb_wrapper.sh -i "/input/video.mkv" --debug

# Dry-run to see all commands
./tvb_wrapper.sh -i "/input/video.mkv" -d --debug
```

### Log Files and Analysis
- **transcode.log**: Detailed execution log with debug information
- **tvb-stats.csv**: Encoding statistics for performance analysis
- **Console output**: Real-time progress and error messages

### Version Information
Check versions of all components:
```bash
# Check HandBrakeCLI version (script does this automatically on startup)
HandBrakeCLI --version

# Check Ruby version (for video_transcoding)
ruby --version

# Check Python and pip versions
python3 --version && pip3 --version

# Update HandBrakeCLI if needed (macOS with Homebrew)
brew update && brew upgrade handbrake
```

## License
This script is provided as-is for educational and personal use.

## Credits
- **Lisa Melton** for the excellent `video_transcoding` tool (2025 version)
- **HandBrake** team for the powerful video transcoding engine
- **FFmpeg** project for media handling capabilities
- **Dolby Laboratories** for Atmos audio technology
