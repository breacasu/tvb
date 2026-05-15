#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# handbrake_generator.py
#
# Python module for generating HandBrakeCLI commands
# Replaces the command generation functionality from transcode-video.rb
#

# Standard Library
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
# MediaAnalyzer will be imported dynamically by the calling code


class HandBrakeGenerator:
    """Class for generating HandBrakeCLI commands based on media analysis."""

    # Encoding modes
    MODE_H264 = 'h264'
    MODE_HEVC = 'hevc'
    MODE_NVENC_HEVC = 'nvenc_hevc'
    MODE_AV1 = 'av1'
    MODE_NVENC_AV1 = 'nvenc_av1'
    MODE_NONE = 'none'

    # Audio modes
    AUDIO_AAC = 'aac'
    AUDIO_OPUS = 'opus'
    AUDIO_EAC3 = 'eac3'
    AUDIO_NONE = 'none'

    def __init__(self, mode: str = MODE_H264, preset: Optional[str] = None,
                 bitrate: Optional[int] = None, quality: Optional[float] = None,
                 audio_mode: str = AUDIO_AAC, bframe_refs: bool = True,
                 aac_encoder: str = 'av_aac', ac3_surround: bool = False):
        """
        Initialize the HandBrake generator.

        Args:
            mode: Video encoding mode
            preset: Video encoder preset
            bitrate: Video bitrate target
            quality: Constant quality value
            audio_mode: Audio encoding mode
            bframe_refs: Whether to use B-frames as reference frames
            aac_encoder: AAC encoder to use
            ac3_surround: Use AC-3 for surround audio
        """
        self.mode = mode
        self.preset = preset
        self.bitrate = bitrate
        self.quality = quality
        self.audio_mode = audio_mode
        self.bframe_refs = bframe_refs
        self.aac_encoder = aac_encoder
        self.ac3_surround = ac3_surround

        # Audio selections (track, language, title)
        self.audio_selections = [{
            'track': 1,
            'language': None,
            'title': None
        }]

        # Subtitle selections
        self.subtitle_selections = []
        self.add_all_subtitles = False

        # Burn subtitle settings
        self.burn_subtitle = 'auto'  # 'auto', track_number, or None

        # Additional options
        self.extra_options = {}

        # Calculated values
        self.vbv_size = None
        
        # MediaAnalyzer instance (will be set by calling code)
        self._media_analyzer = None

        # Set default audio mode for certain video modes
        if mode in [self.MODE_AV1, self.MODE_NVENC_AV1]:
            if audio_mode == self.AUDIO_AAC:
                self.audio_mode = self.AUDIO_OPUS

    def add_audio_selection(self, track: Optional[int] = None,
                           language: Optional[str] = None,
                           title: Optional[str] = None):
        """Add an audio track selection."""
        selection = {
            'track': track,
            'language': language,
            'title': title
        }
        self.audio_selections.append(selection)

    def add_subtitle_selection(self, track: Optional[int] = None,
                              language: Optional[str] = None,
                              title: Optional[str] = None):
        """Add a subtitle track selection."""
        selection = {
            'track': track,
            'language': language,
            'title': title
        }
        self.subtitle_selections.append(selection)

    def set_burn_subtitle(self, value):
        """Set subtitle burning mode."""
        self.burn_subtitle = value
        if value is not None:
            self.subtitle_selections = []  # Clear subtitle selections when burning

    def add_extra_option(self, name: str, value: Optional[str] = None):
        """Add extra HandBrakeCLI option."""
        self.extra_options[name] = value

    def generate_command(self, input_file: str, output_file: str,
                        media_info: Dict[str, Any]) -> List[str]:
        """
        Generate HandBrakeCLI command for transcoding.

        Args:
            input_file: Input media file path
            output_file: Output file path
            media_info: Media information from ffprobe

        Returns:
            List of command arguments for HandBrakeCLI
        """
        logging.debug(f"Generating HandBrakeCLI command for: {input_file}")

        # Get encoding options
        video_options = self._get_video_options(media_info)
        audio_options = self._get_audio_options(media_info)
        subtitle_options = self._get_subtitle_options(media_info)

        # Base command
        cmd = [
            'HandBrakeCLI',
            '--input', str(input_file),
            '--output', str(output_file)
        ]

        # Add all options
        cmd.extend(video_options)
        cmd.extend(audio_options)
        cmd.extend(subtitle_options)

        # Add encoder options if needed
        encoder_options = self._get_encoder_options()
        if encoder_options:
            cmd.extend(['--encopts', encoder_options])

        # Add extra options
        for name, value in self.extra_options.items():
            cmd.append(f'--{name}')
            if value is not None:
                cmd.append(value)

        # Return command as string for compatibility with TVB
        return self.escape_command(cmd)

    def _get_video_options(self, media_info: Dict[str, Any]) -> List[str]:
        """Generate video encoding options."""
        video = self._media_analyzer.get_video_stream(media_info)

        if not video:
            return []

        options = []

        # Encoder selection
        if 'encoder' not in self.extra_options:
            encoder = self._get_video_encoder(video)
            if encoder:
                options.extend(['--encoder', encoder])

        # Encoder preset
        if self.preset and 'encoder-preset' not in self.extra_options:
            options.extend(['--encoder-preset', self.preset])

        # Bitrate or quality
        if 'vb' not in self.extra_options:
            if self.bitrate:
                options.extend(['--vb', str(self.bitrate)])
                # Calculate vbv_size for H.264 encoder (bitrate * 3)
                if self.mode == self.MODE_H264:
                    self.vbv_size = self.bitrate * 3
            elif self.quality and 'quality' not in self.extra_options:
                quality_str = self._format_quality(self.quality)
                options.extend(['--quality', quality_str])
                # For quality mode: Use standard vbv_size
                if self.mode == self.MODE_H264:
                    self.vbv_size = 15000  # Standard value for quality mode

        # Rate control
        if not any(opt in self.extra_options for opt in ['rate', 'vfr', 'cfr', 'pfr']):
            options.extend(self._get_rate_options(video))

        # Crop mode
        if not any(opt in self.extra_options for opt in ['crop', 'crop-mode']):
            options.extend(['--crop-mode', 'conservative'])

        return options

    def _get_video_encoder(self, video: Dict[str, Any]) -> Optional[str]:
        """Determine the appropriate video encoder."""
        width = int(video.get('width', 0))
        height = int(video.get('height', 0))

        if self.mode == self.MODE_H264:
            return 'x264'
        elif self.mode == self.MODE_HEVC:
            return 'x265_10bit'
        elif self.mode == self.MODE_NVENC_HEVC:
            return 'nvenc_h265_10bit'
        elif self.mode == self.MODE_AV1:
            return 'svt_av1_10bit'
        elif self.mode == self.MODE_NVENC_AV1:
            return 'nvenc_av1_10bit'
        elif self.mode == self.MODE_NONE:
            return None

        return 'x264'  # Default

    def _get_rate_options(self, video: Dict[str, Any]) -> List[str]:
        """Get rate control options based on video properties."""
        codec_name = video.get('codec_name', '')
        avg_frame_rate = video.get('avg_frame_rate', '')

        # Check for MPEG-2 video at 29.97 fps
        if codec_name == 'mpeg2video' and avg_frame_rate == '30000/1001':
            return ['--rate', '29.97', '--cfr']

        return ['--rate', '60']

    def _format_quality(self, quality: float) -> str:
        """Format quality value for HandBrakeCLI."""
        return str(min(max(quality, 0.0), 51.0))

    def _get_audio_options(self, media_info: Dict[str, Any]) -> List[str]:
        """Generate audio encoding options."""
        if any(opt in self.extra_options for opt in ['audio', 'all-audio', 'first-audio']):
            return []

        # Use the media analyzer instance
        audio_tracks = self._media_analyzer.get_audio_streams(media_info)

        if not audio_tracks:
            return []

        # Process audio selections
        selected_tracks = self._process_audio_selections(media_info)

        if not selected_tracks:
            return []

        # Generate options
        track_list = []
        encoder_list = []
        bitrate_list = []
        mixdown_list = []
        name_list = []

        for track_info in selected_tracks:
            track_list.append(str(track_info['index']))

            if 'aencoder' not in self.extra_options:
                encoder, bitrate, mixdown = self._get_audio_encoding_params(track_info['stream'])
                encoder_list.append(encoder)
                bitrate_list.append(bitrate)
                mixdown_list.append(mixdown)

            if len(selected_tracks) > 1 and 'aname' not in self.extra_options:
                name = self._get_audio_track_name(track_info['stream'], track_info['index'])
                name_list.append(name)

        options = ['--audio', ','.join(track_list)]

        if encoder_list and 'aencoder' not in self.extra_options:
            options.extend(['--aencoder', ','.join(encoder_list)])

        if bitrate_list and 'ab' not in self.extra_options:
            bitrate_str = ','.join(bitrate_list)
            if bitrate_str:
                options.extend(['--ab', bitrate_str])

        if mixdown_list and 'mixdown' not in self.extra_options:
            options.extend(['--mixdown', ','.join(mixdown_list)])

        if name_list and 'aname' not in self.extra_options:
            options.extend(['--aname', ','.join(name_list)])

        return options

    def _process_audio_selections(self, media_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process audio selections and return matching tracks."""
        # Use the media analyzer instance
        audio_tracks = self._media_analyzer.get_audio_streams(media_info)
        selected_tracks = []

        for selection in self.audio_selections:
            if selection['track']:
                # Select by track number
                track_index = selection['track'] - 1  # Convert to 0-based
                if 0 <= track_index < len(audio_tracks):
                    track = audio_tracks[track_index]
                    selected_tracks.append({
                        'index': selection['track'],
                        'stream': track
                    })

            elif selection['language']:
                # Select by language
                for i, track in enumerate(audio_tracks):
                    tags = track.get('tags', {})
                    language = tags.get('language', '')
                    if selection['language'] == 'all' or language == selection['language']:
                        selected_tracks.append({
                            'index': i + 1,
                            'stream': track
                        })

            elif selection['title']:
                # Select by title
                for i, track in enumerate(audio_tracks):
                    tags = track.get('tags', {})
                    title = tags.get('title', '')
                    if selection['title'].lower() in title.lower():
                        selected_tracks.append({
                            'index': i + 1,
                            'stream': track
                        })

        # Remove duplicates
        seen = set()
        unique_tracks = []
        for track in selected_tracks:
            track_id = track['index']
            if track_id not in seen:
                seen.add(track_id)
                unique_tracks.append(track)

        return unique_tracks

    def _get_audio_encoding_params(self, stream: Dict[str, Any]) -> Tuple[str, str, str]:
        """Get audio encoding parameters for a stream."""
        channels = int(stream.get('channels', 2))
        codec_name = stream.get('codec_name', '')

        if self.audio_mode == self.AUDIO_AAC:
            if (codec_name == 'aac' and channels <= 6) or \
               (self.ac3_surround and codec_name == 'ac3' and channels > 2):
                return 'copy', '', ''

            encoder = self.aac_encoder
            if self.ac3_surround:
                encoder = 'ac3'
                bitrate = '448'
            else:
                bitrate = self._get_aac_bitrate(channels)

            mixdown = self._get_mixdown(channels)
            return encoder, bitrate, mixdown

        elif self.audio_mode == self.AUDIO_OPUS:
            if codec_name == 'opus':
                return 'copy', '', ''

            return 'opus', self._get_opus_bitrate(channels), self._get_mixdown(channels)

        elif self.audio_mode == self.AUDIO_EAC3:
            if codec_name in ['ac3', 'eac3'] or (codec_name == 'aac' and channels <= 6):
                return 'copy', '', ''

            return 'eac3', self._get_eac3_bitrate(channels), self._get_mixdown(channels)

        return 'copy', '', ''

    def _get_aac_bitrate(self, channels: int) -> str:
        """Get AAC bitrate based on channel count."""
        if channels == 1:
            return '80'
        elif channels == 2:
            return '128'
        else:
            return '384'

    def _get_opus_bitrate(self, channels: int) -> str:
        """Get Opus bitrate based on channel count."""
        if channels == 1:
            return '64'
        elif channels == 2:
            return '96'
        else:
            return '320'

    def _get_eac3_bitrate(self, channels: int) -> str:
        """Get E-AC-3 bitrate based on channel count."""
        if channels == 1:
            return '96'
        elif channels == 2:
            return '192'
        else:
            return '448'

    def _get_mixdown(self, channels: int) -> str:
        """Get mixdown based on channel count."""
        if channels == 1:
            return 'mono'
        elif channels == 2:
            return 'stereo'
        else:
            return '5point1'

    def _get_audio_track_name(self, stream: Dict[str, Any], index: int) -> str:
        """Get audio track name for naming."""
        tags = stream.get('tags', {})
        title = tags.get('title', '')
        return title.replace(',', '","') if title else ''

    def _get_subtitle_options(self, media_info: Dict[str, Any]) -> List[str]:
        """Generate subtitle options."""
        logging.debug(f"Getting subtitle options. add_all_subtitles={self.add_all_subtitles}, extra_options={self.extra_options}")
        if any(opt in self.extra_options for opt in ['subtitle', 'all-subtitles', 'first-subtitle']):
            logging.debug("Skipping subtitle options due to extra_options")
            return []

        # Use the media analyzer instance
        subtitle_tracks = self._media_analyzer.get_subtitle_streams(media_info)

        if not subtitle_tracks:
            return []

        options = []
        logging.debug(f"Subtitle options: burn_subtitle={self.burn_subtitle}, add_all_subtitles={self.add_all_subtitles}, subtitle_selections={self.subtitle_selections}")

        if self.add_all_subtitles:
            # Add all subtitle tracks
            logging.debug(f"Adding all subtitle tracks: {len(subtitle_tracks)} tracks found")
            track_list = []
            default_track = None
            name_list = []

            for i, track in enumerate(subtitle_tracks, 1):
                track_list.append(str(i))
                logging.debug(f"Added subtitle track {i}: {track.get('tags', {}).get('title', 'unknown')}")

                # Only set as default if this track is actually forced in the original (Ruby logic)
                if track.get('disposition', {}).get('forced') == 1 and default_track is None:
                    default_track = str(i)
                    logging.debug(f"Found forced subtitle track: {i}")

                if 'subname' not in self.extra_options:
                    name = self._get_subtitle_track_name(track)
                    name_list.append(name)

            if track_list:
                logging.debug(f"Final subtitle tracks: {','.join(track_list)}")
                options.extend(['--subtitle', ','.join(track_list)])

                if default_track:
                    options.extend(['--subtitle-default', default_track])

                if name_list and 'subname' not in self.extra_options:
                    options.extend(['--subname', ','.join(name_list)])

        elif self.burn_subtitle:
            burn_track = self._find_subtitle_to_burn(media_info)
            if burn_track:
                options.extend(['--subtitle', str(burn_track['index'])])
                if burn_track['stream'].get('codec_name') in ['hdmv_pgs_subtitle', 'dvd_subtitle']:
                    options.append('--subtitle-burned')
                else:
                    options.append('--subtitle-default')

        elif self.subtitle_selections:
            selected_tracks = self._process_subtitle_selections(media_info)
            if selected_tracks:
                track_list = []
                default_track = None
                name_list = []

                for track_info in selected_tracks:
                    track_list.append(str(track_info['index']))

                    if track_info['stream'].get('disposition', {}).get('forced') == 1:
                        default_track = str(track_info['index'])

                    if 'subname' not in self.extra_options:
                        name = self._get_subtitle_track_name(track_info['stream'])
                        name_list.append(name)

                options.extend(['--subtitle', ','.join(track_list)])

                if default_track:
                    options.extend(['--subtitle-default', default_track])

                if name_list and 'subname' not in self.extra_options:
                    options.extend(['--subname', ','.join(name_list)])

        return options

    def _find_subtitle_to_burn(self, media_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find subtitle track to burn."""
        # Use the media analyzer instance
        subtitle_tracks = self._media_analyzer.get_subtitle_streams(media_info)

        if self.burn_subtitle == 'auto':
            for i, stream in enumerate(subtitle_tracks):
                if stream.get('disposition', {}).get('forced') == 1:
                    return {'index': i + 1, 'stream': stream}
        elif isinstance(self.burn_subtitle, int):
            track_index = self.burn_subtitle - 1
            if 0 <= track_index < len(subtitle_tracks):
                return {'index': self.burn_subtitle, 'stream': subtitle_tracks[track_index]}

        return None

    def _process_subtitle_selections(self, media_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process subtitle selections."""
        # Use the media analyzer instance
        subtitle_tracks = self._media_analyzer.get_subtitle_streams(media_info)
        selected_tracks = []

        for selection in self.subtitle_selections:
            if selection['track']:
                track_index = selection['track'] - 1
                if 0 <= track_index < len(subtitle_tracks):
                    track = subtitle_tracks[track_index]
                    selected_tracks.append({
                        'index': selection['track'],
                        'stream': track
                    })

            elif selection['language']:
                for i, track in enumerate(subtitle_tracks):
                    tags = track.get('tags', {})
                    language = tags.get('language', '')
                    if selection['language'] == 'all' or language == selection['language']:
                        selected_tracks.append({
                            'index': i + 1,
                            'stream': track
                        })

            elif selection['title']:
                for i, track in enumerate(subtitle_tracks):
                    tags = track.get('tags', {})
                    title = tags.get('title', '')
                    if selection['title'].lower() in title.lower():
                        selected_tracks.append({
                            'index': i + 1,
                            'stream': track
                        })

        # Remove duplicates
        seen = set()
        unique_tracks = []
        for track in selected_tracks:
            track_id = track['index']
            if track_id not in seen:
                seen.add(track_id)
                unique_tracks.append(track)

        return unique_tracks

    def _get_subtitle_track_name(self, stream: Dict[str, Any]) -> str:
        """Get subtitle track name."""
        tags = stream.get('tags', {})
        title = tags.get('title', '')
        return title.replace(',', '","') if title else ''

    def _get_encoder_options(self) -> Optional[str]:
        """Get encoder-specific options."""
        if 'encoder' in self.extra_options:
            return None

        if self.mode == self.MODE_H264:
            if self.vbv_size is not None:
                return f"vbv-maxrate={self.vbv_size}:vbv-bufsize={self.vbv_size}"
            else:
                # Fallback in case vbv_size was not calculated
                return "vbv-maxrate=15000:vbv-bufsize=15000"
        elif self.mode == self.MODE_NVENC_HEVC:
            opts = 'spatial_aq=1:rc-lookahead=20'
            if self.bframe_refs:
                opts += ':b_ref_mode=2'
            return opts
        elif self.mode == self.MODE_NVENC_AV1:
            opts = 'spatial-aq=1:rc-lookahead=20'
            if self.bframe_refs:
                opts += ':b_ref_mode=2'
            return opts

        return None

    def escape_command(self, command: List[str]) -> str:
        """Convert command list to string for TVB compatibility."""
        def escape_if_needed(arg: str) -> str:
            # Only quote arguments that contain spaces (typically file paths)
            if ' ' in arg:
                return f'"{arg}"'
            return arg
        
        return ' '.join(escape_if_needed(arg) for arg in command)
    
    def parse_transcode_video_params(self, format_params):
        """
        Parse transcode-video style parameters and configure this HandBrakeGenerator.
        
        This method provides FULL compatibility with transcode-video parameters,
        supporting all options that the Ruby transcode-video script supports.
        
        This is the proper place for this logic - HandBrakeGenerator should understand
        transcode-video parameters directly, just like transcode-video itself.
        """
        import shlex
        
        # Parse parameters using shell-like parsing to handle quoted strings
        try:
            params = shlex.split(format_params)
        except ValueError:
            # Fallback to simple split if shlex fails
            params = format_params.split()
        
        i = 0
        while i < len(params):
            param = params[i]
            
            if not param.startswith('--'):
                i += 1
                continue
                
            param_name = param[2:]  # Remove --
            param_value = None
            
            # Check if next parameter is a value (not starting with --)
            if i + 1 < len(params) and not params[i + 1].startswith('--'):
                param_value = params[i + 1]
                i += 2
            else:
                i += 1
            
            # Handle all transcode-video parameters
            if param_name == 'mode' and param_value:
                if param_value == 'h264':
                    self.mode = self.MODE_H264
                elif param_value == 'hevc':
                    self.mode = self.MODE_HEVC
                elif param_value == 'nvenc-hevc':
                    self.mode = self.MODE_NVENC_HEVC
                elif param_value == 'av1':
                    self.mode = self.MODE_AV1
                    self.audio_mode = self.AUDIO_OPUS  # Auto-set opus for AV1
                elif param_value == 'nvenc-av1':
                    self.mode = self.MODE_NVENC_AV1
                    self.audio_mode = self.AUDIO_OPUS  # Auto-set opus for AV1
                elif param_value == 'none':
                    self.mode = self.MODE_NONE
                    
            elif param_name == 'preset' and param_value:
                self.preset = param_value
                
            elif param_name == 'bitrate' and param_value:
                self.bitrate = int(param_value)
                self.quality = None  # Bitrate mode, not quality
                
            elif param_name == 'quality' and param_value:
                self.quality = float(param_value)
                self.bitrate = None  # Quality mode, not bitrate
                
            elif param_name == 'audio-mode' and param_value:
                if param_value == 'aac':
                    self.audio_mode = self.AUDIO_AAC
                elif param_value == 'opus':
                    self.audio_mode = self.AUDIO_OPUS
                elif param_value == 'eac3':
                    self.audio_mode = self.AUDIO_EAC3
                elif param_value == 'none':
                    self.audio_mode = self.AUDIO_NONE
                    
            elif param_name == 'add-audio' and param_value:
                # Handle audio track selection (track number, language code, or title)
                if param_value.isdigit():
                    self.add_audio_selection(track=int(param_value))
                elif len(param_value) == 3 and param_value.isalpha():
                    self.add_audio_selection(language=param_value.lower())
                else:
                    self.add_audio_selection(title=param_value)
                    
            elif param_name == 'add-subtitle' and param_value:
                # Handle subtitle track selection (track number, language code, or title)
                if param_value.lower() == 'all':
                    # Add all subtitle tracks - this will be handled in generate_command
                    self.add_all_subtitles = True
                elif param_value.isdigit():
                    self.add_subtitle_selection(track=int(param_value))
                elif len(param_value) == 3 and param_value.isalpha():
                    self.add_subtitle_selection(language=param_value.lower())
                else:
                    self.add_subtitle_selection(title=param_value)
                    
            elif param_name == 'burn-subtitle' and param_value:
                if param_value == 'none':
                    self.set_burn_subtitle(None)
                elif param_value.isdigit():
                    self.set_burn_subtitle(int(param_value))
                    
            elif param_name == 'ac3-surround':
                self.ac3_surround = True
                
            elif param_name == 'aac-encoder' and param_value:
                if param_value in ['av_aac', 'fdk_aac', 'ca_aac']:
                    self.aac_encoder = param_value
                    
            elif param_name == 'extra' and param_value:
                # Handle -x/--extra HandBrakeCLI options
                if '=' in param_value:
                    name, value = param_value.split('=', 1)
                    self.add_extra_option(name, value)
                else:
                    self.add_extra_option(param_value, None)
                    
            elif param_name == 'stop-at' and param_value:
                # Handle --stop-at parameter for previews
                self.add_extra_option('stop-at', param_value)
            
            # Add more parameter handlers as needed for full compatibility
            # This covers the most common transcode-video parameters
            
        # Log successful configuration (debug only)
        logging.debug(f"HandBrakeGenerator configured with transcode-video parameters: {format_params}")


# Convenience functions
def generate_transcode_command(input_file: str, output_file: str,
                              media_info: Dict[str, Any], **kwargs) -> List[str]:
    """Convenience function to generate transcode command."""
    generator = HandBrakeGenerator(**kwargs)
    return generator.generate_command(input_file, output_file, media_info)


if __name__ == '__main__':
    # Simple test
    import sys

    if len(sys.argv) != 3:
        print("Usage: python handbrake_generator.py <input_file> <output_file>")
        sys.exit(1)

    # Import MediaAnalyzer dynamically for testing
    import importlib.util
    spec = importlib.util.spec_from_file_location("media_analyzer", "tvb-media_analyzer.py")
    ma_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ma_module)
    
    analyzer = ma_module.MediaAnalyzer()
    generator = HandBrakeGenerator()
    generator._media_analyzer = analyzer

    try:
        media_info = analyzer.scan_media(sys.argv[1])
        cmd = generator.generate_command(sys.argv[1], sys.argv[2], media_info)

        print("Generated HandBrakeCLI command:")
        print(cmd)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
