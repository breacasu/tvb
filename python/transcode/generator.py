#!/usr/bin/env python3
import logging
import shlex
import re
from typing import Dict, Any, List, Optional, Tuple


class HandBrakeGenerator:

    MODE_H264 = 'h264'
    MODE_HEVC = 'hevc'
    MODE_NVENC_HEVC = 'nvenc_hevc'
    MODE_AV1 = 'av1'
    MODE_NVENC_AV1 = 'nvenc_av1'
    MODE_NONE = 'none'

    AUDIO_AAC = 'aac'
    AUDIO_OPUS = 'opus'
    AUDIO_EAC3 = 'eac3'
    AUDIO_NONE = 'none'

    LANG_MAP = {
        'ger': 'German', 'deu': 'German', 'eng': 'English',
        'fre': 'French', 'fra': 'French', 'spa': 'Spanish',
        'ita': 'Italian', 'jpn': 'Japanese', 'chi': 'Chinese', 'zho': 'Chinese',
        'rus': 'Russian', 'ara': 'Arabic', 'por': 'Portuguese',
        'nld': 'Dutch', 'dut': 'Dutch', 'swe': 'Swedish',
        'nor': 'Norwegian', 'fin': 'Finnish', 'dan': 'Danish',
        'pol': 'Polish', 'tur': 'Turkish', 'cze': 'Czech', 'ces': 'Czech',
        'hun': 'Hungarian', 'rum': 'Romanian', 'ron': 'Romanian',
        'tha': 'Thai', 'kor': 'Korean', 'hin': 'Hindi',
        'gre': 'Greek', 'ell': 'Greek', 'heb': 'Hebrew',
        'vie': 'Vietnamese', 'bul': 'Bulgarian', 'ukr': 'Ukrainian',
        'hrv': 'Croatian', 'srp': 'Serbian',
    }

    CODEC_MAP = {
        'ac3': 'Dolby Digital', 'eac3': 'Dolby Digital Plus',
        'aac': 'AAC', 'mp3': 'MP3', 'opus': 'Opus',
        'vorbis': 'Vorbis', 'flac': 'FLAC', 'pcm': 'PCM',
        'truehd': 'TrueHD', 'dts': 'DTS', 'dca': 'DTS',
    }

    TARGET_ENCODER_MAP = {
        'av_aac': 'AAC', 'fdk_aac': 'AAC (FDK)', 'ca_aac': 'AAC (CoreAudio)',
        'ac3': 'Dolby Digital', 'eac3': 'Dolby Digital Plus',
        'opus': 'Opus', 'mp3': 'MP3', 'flac': 'FLAC',
        'copy': None,
    }

    @staticmethod
    def _resolve_language(lang_code: str) -> str:
        return HandBrakeGenerator.LANG_MAP.get(lang_code.lower(), lang_code.upper() if lang_code else '')

    @staticmethod
    def _resolve_codec_name(codec_name: str) -> str:
        return HandBrakeGenerator.CODEC_MAP.get(codec_name.lower(), codec_name.upper() if codec_name else '')

    @staticmethod
    def _resolve_target_encoder(encoder: str) -> str:
        return HandBrakeGenerator.TARGET_ENCODER_MAP.get(encoder, encoder.upper() if encoder else '')

    def __init__(self, mode: str = MODE_H264, preset: Optional[str] = None,
                 bitrate: Optional[int] = None, quality: Optional[float] = None,
                 audio_mode: str = AUDIO_AAC, bframe_refs: bool = True,
                 aac_encoder: str = 'av_aac', ac3_surround: bool = False,
                 media_analyzer=None):
        self.mode = mode
        self.preset = preset
        self.bitrate = bitrate
        self.quality = quality
        self.audio_mode = audio_mode
        self.bframe_refs = bframe_refs
        self.aac_encoder = aac_encoder
        self.ac3_surround = ac3_surround
        self._media_analyzer = media_analyzer

        self.audio_selections = [{'track': 1, 'language': None, 'title': None}]
        self.subtitle_selections = []
        self.add_all_subtitles = False
        self.burn_subtitle = 'auto'
        self.extra_options = {}
        self.vbv_size = None
        self._atmos_tracks = []

        if mode in [self.MODE_AV1, self.MODE_NVENC_AV1]:
            if audio_mode == self.AUDIO_AAC:
                self.audio_mode = self.AUDIO_OPUS

    def add_audio_selection(self, track: Optional[int] = None,
                            language: Optional[str] = None,
                            title: Optional[str] = None):
        self.audio_selections.append({'track': track, 'language': language, 'title': title})

    def add_subtitle_selection(self, track: Optional[int] = None,
                               language: Optional[str] = None,
                               title: Optional[str] = None):
        self.subtitle_selections.append({'track': track, 'language': language, 'title': title})

    def set_burn_subtitle(self, value):
        self.burn_subtitle = value
        if value is not None:
            self.subtitle_selections = []

    def add_extra_option(self, name: str, value: Optional[str] = None):
        self.extra_options[name] = value

    def set_atmos_tracks(self, atmos_tracks: List[int]):
        self._atmos_tracks = atmos_tracks

    def generate_command(self, input_file: str, output_file: str,
                         media_info: Dict[str, Any]) -> str:
        cmd_list = self.generate_command_list(input_file, output_file, media_info)
        return self._escape_command(cmd_list)

    def generate_command_list(self, input_file: str, output_file: str,
                               media_info: Dict[str, Any]) -> List[str]:
        cmd = ['HandBrakeCLI', '--input', str(input_file), '--output', str(output_file)]

        video_options = self._get_video_options(media_info)
        cmd.extend(video_options)

        audio_options = self._get_audio_options(media_info)
        cmd.extend(audio_options)

        subtitle_options = self._get_subtitle_options(media_info)
        cmd.extend(subtitle_options)

        encoder_options = self._get_encoder_options()
        custom_encoder_options = self.extra_options.get('encopts')
        if custom_encoder_options:
            encoder_options = ':'.join(
                option for option in [encoder_options, custom_encoder_options] if option
            )
        if encoder_options:
            cmd.extend(['--encopts', encoder_options])

        for name, value in self.extra_options.items():
            if name == 'encopts':
                continue
            cmd.append(f'--{name}')
            if value is not None:
                cmd.append(value)

        return cmd

    def _get_video_options(self, media_info: Dict[str, Any]) -> List[str]:
        if not self._media_analyzer:
            return []
        video = self._media_analyzer.get_video_stream(media_info)
        if not video:
            return []

        options = []
        preset = self.preset
        bitrate = self.bitrate
        quality = self.quality

        if 'encoder' not in self.extra_options:
            encoder = self._get_video_encoder(video)
            if encoder:
                options.extend(['--encoder', encoder])

            if self.quality is not None:
                quality = self._format_quality(self.quality)

            width = video.get('width', 0) or 0
            height = video.get('height', 0) or 0

            if self.mode == self.MODE_H264:
                if width > 1280 or height > 720:
                    rate = 5000
                    if width > 1920 or height > 1080:
                        options.extend(['--maxWidth', '1920', '--maxHeight', '1080', '--loose-anamorphic'])
                        if video.get('color_space', 'bt709') != 'bt709':
                            options.extend(['--colorspace', 'bt709'])
                elif width > 720 or height > 576:
                    rate = 2500
                else:
                    rate = 1250

                self.vbv_size = rate * 3

                if self.quality is None:
                    if self.bitrate is not None:
                        clamped = max(self.bitrate, int(rate * 0.8))
                        clamped = min(clamped, int(rate * 1.6))
                        bitrate = str(clamped)
                    else:
                        bitrate = str(rate)
                    if 'multi-pass' not in self.extra_options:
                        options.extend(['--multi-pass', '--turbo'])
                else:
                    bitrate = None

            elif self.mode == self.MODE_HEVC:
                if quality is None and bitrate is None:
                    quality = '24'

            elif self.mode == self.MODE_NVENC_HEVC:
                if quality is None and bitrate is None:
                    quality = '30'

            elif self.mode == self.MODE_AV1:
                if bitrate is None:
                    quality = self._format_av1_quality(self.quality)
                preset = self._clamp_av1_preset(self.preset)

            elif self.mode == self.MODE_NVENC_AV1:
                if bitrate is None:
                    quality = self._format_nvenc_av1_quality(self.quality)
                preset = self._clamp_av1_preset(self.preset)

        if preset and 'encoder-preset' not in self.extra_options:
            options.extend(['--encoder-preset', preset])

        if bitrate and 'vb' not in self.extra_options:
            options.extend(['--vb', bitrate])

        if quality and 'quality' not in self.extra_options:
            options.extend(['--quality', quality])

            if self.mode == self.MODE_H264 and self.vbv_size is None:
                self.vbv_size = 15000

        if not any(opt in self.extra_options for opt in ['rate', 'vfr', 'cfr', 'pfr']):
            options.extend(self._get_rate_options(video))

        if not any(opt in self.extra_options for opt in ['crop', 'crop-mode']):
            options.extend(['--crop-mode', 'conservative'])

        return options

    def _get_video_encoder(self, video: Dict[str, Any]) -> Optional[str]:
        mapping = {
            self.MODE_H264: 'x264',
            self.MODE_HEVC: 'x265_10bit',
            self.MODE_NVENC_HEVC: 'nvenc_h265_10bit',
            self.MODE_AV1: 'svt_av1_10bit',
            self.MODE_NVENC_AV1: 'nvenc_av1_10bit',
            self.MODE_NONE: None,
        }
        return mapping.get(self.mode, 'x264')

    def _get_rate_options(self, video: Dict[str, Any]) -> List[str]:
        codec_name = video.get('codec_name', '')
        avg_frame_rate = video.get('avg_frame_rate', '')

        if codec_name == 'mpeg2video' and avg_frame_rate == '30000/1001':
            return ['--rate', '29.97', '--cfr']

        return ['--rate', '60']

    def _format_quality(self, quality: float) -> str:
        return str(min(max(quality, 0.0), 51.0))

    @staticmethod
    def _format_av1_quality(quality: Optional[float]) -> str:
        if quality is None:
            return '30'
        return str(min(max(int(quality), 0), 63))

    @staticmethod
    def _format_nvenc_av1_quality(quality: Optional[float]) -> str:
        if quality is None:
            return '37'
        return str(min(max(int(quality), 0), 63))

    @staticmethod
    def _clamp_av1_preset(preset: Optional[int]) -> str:
        if preset is None:
            return '8'
        return str(min(max(int(preset), -1), 13))

    def _get_audio_options(self, media_info: Dict[str, Any]) -> List[str]:
        if any(opt in self.extra_options for opt in ['audio', 'all-audio', 'first-audio']):
            return []
        if not self._media_analyzer:
            return []

        audio_tracks = self._media_analyzer.get_audio_streams(media_info)
        if not audio_tracks:
            return []

        selected_tracks = self._process_audio_selections(media_info)
        if not selected_tracks:
            return []

        track_list = []
        encoder_list = []
        bitrate_list = []
        mixdown_list = []
        name_list = []

        for track_info in selected_tracks:
            track_list.append(str(track_info['index']))
            if 'aencoder' not in self.extra_options:
                track_number = track_info['index']
                encoder, bitrate, mixdown = self._get_audio_encoding_params(track_info['stream'], track_number)
                encoder_list.append(encoder)
                bitrate_list.append(bitrate)
                mixdown_list.append(mixdown)
            if len(selected_tracks) > 1 and 'aname' not in self.extra_options:
                target_enc = encoder_list[-1] if encoder_list else ''
                name = self._get_audio_track_name(track_info['stream'], target_enc)
                name_list.append(name)

        options = ['--audio', ','.join(track_list)]
        if encoder_list and 'aencoder' not in self.extra_options:
            options.extend(['--aencoder', ','.join(encoder_list)])
        if bitrate_list and 'ab' not in self.extra_options:
            non_empty = [b for b in bitrate_list if b]
            if non_empty:
                options.extend(['--ab', ','.join(non_empty)])
        if mixdown_list and 'mixdown' not in self.extra_options:
            non_empty = [m for m in mixdown_list if m]
            if non_empty:
                options.extend(['--mixdown', ','.join(non_empty)])
        if name_list and 'aname' not in self.extra_options:
            options.extend(['--aname', ','.join(name_list)])

        return options

    def _process_audio_selections(self, media_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self._media_analyzer:
            return []
        audio_tracks = self._media_analyzer.get_audio_streams(media_info)
        selected_tracks = []

        for selection in self.audio_selections:
            if selection['track']:
                track_index = selection['track'] - 1
                if 0 <= track_index < len(audio_tracks):
                    selected_tracks.append({'index': selection['track'], 'stream': audio_tracks[track_index]})
            elif selection['language']:
                for i, track in enumerate(audio_tracks):
                    language = track.get('tags', {}).get('language', '')
                    if selection['language'] == 'all' or language == selection['language']:
                        selected_tracks.append({'index': i + 1, 'stream': track})
            elif selection['title']:
                for i, track in enumerate(audio_tracks):
                    title = track.get('tags', {}).get('title', '')
                    if selection['title'].lower() in title.lower():
                        selected_tracks.append({'index': i + 1, 'stream': track})

        seen = set()
        unique = []
        for t in selected_tracks:
            if t['index'] not in seen:
                seen.add(t['index'])
                unique.append(t)
        return unique

    def _get_audio_encoding_params(self, stream: Dict[str, Any], track_number: int = 0) -> Tuple[str, str, str]:
        channels = int(stream.get('channels', 2))
        codec_name = stream.get('codec_name', '')

        if track_number in self._atmos_tracks:
            return 'copy', '', ''

        if self.audio_mode == self.AUDIO_AAC:
            if (codec_name == 'aac' and channels <= 6) or \
               (self.ac3_surround and codec_name == 'ac3' and channels > 2):
                return 'copy', '', ''
            encoder = self.aac_encoder
            if self.ac3_surround:
                return 'ac3', '448', self._get_mixdown(channels)
            return encoder, self._get_aac_bitrate(channels), self._get_mixdown(channels)

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
        return {1: '80', 2: '128'}.get(channels, '384')

    def _get_opus_bitrate(self, channels: int) -> str:
        return {1: '64', 2: '96'}.get(channels, '320')

    def _get_eac3_bitrate(self, channels: int) -> str:
        return {1: '96', 2: '192'}.get(channels, '448')

    def _get_mixdown(self, channels: int) -> str:
        return {1: 'mono', 2: 'stereo'}.get(channels, '5point1')

    def _get_audio_track_name(self, stream: Dict[str, Any], target_encoder: str = '') -> str:
        lang_code = stream.get('tags', {}).get('language', '')
        language = self._resolve_language(lang_code)
        channels = int(stream.get('channels', 2))

        channel_map = {1: 'Mono', 2: 'Stereo', 6: '5.1', 8: '7.1'}
        channel_label = channel_map.get(channels, f'{channels}ch')

        if target_encoder == 'copy':
            codec_name = stream.get('codec_name', '')
            codec_label = self._resolve_codec_name(codec_name)
            profile = stream.get('profile', '') or ''
            if 'atmos' in profile.lower():
                codec_label = f'{codec_label} Atmos'
        elif target_encoder:
            codec_label = self._resolve_target_encoder(target_encoder)
        else:
            codec_name = stream.get('codec_name', '')
            codec_label = self._resolve_codec_name(codec_name)

        parts = [p for p in [language, codec_label, channel_label] if p]
        name = ' '.join(parts)

        return name.replace(',', '","')

    def _get_subtitle_options(self, media_info: Dict[str, Any]) -> List[str]:
        if any(opt in self.extra_options for opt in ['subtitle', 'all-subtitles', 'first-subtitle']):
            return []
        if not self._media_analyzer:
            return []

        subtitle_tracks = self._media_analyzer.get_subtitle_streams(media_info)
        if not subtitle_tracks:
            return []

        options = []

        if self.add_all_subtitles:
            track_list = []
            default_track = None
            name_list = []
            for i, track in enumerate(subtitle_tracks, 1):
                track_list.append(str(i))
                if track.get('disposition', {}).get('forced') == 1 and default_track is None:
                    default_track = str(i)
                if 'subname' not in self.extra_options:
                    name = self._get_subtitle_track_name(track)
                    name_list.append(name)
            if track_list:
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
        if not self._media_analyzer:
            return None
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
        if not self._media_analyzer:
            return []
        subtitle_tracks = self._media_analyzer.get_subtitle_streams(media_info)
        selected = []
        for selection in self.subtitle_selections:
            if selection['track']:
                idx = selection['track'] - 1
                if 0 <= idx < len(subtitle_tracks):
                    selected.append({'index': selection['track'], 'stream': subtitle_tracks[idx]})
            elif selection['language']:
                for i, t in enumerate(subtitle_tracks):
                    lang = t.get('tags', {}).get('language', '')
                    if selection['language'] == 'all' or lang == selection['language']:
                        selected.append({'index': i + 1, 'stream': t})
            elif selection['title']:
                for i, t in enumerate(subtitle_tracks):
                    title = t.get('tags', {}).get('title', '')
                    if selection['title'].lower() in title.lower():
                        selected.append({'index': i + 1, 'stream': t})
        seen = set()
        unique = []
        for t in selected:
            if t['index'] not in seen:
                seen.add(t['index'])
                unique.append(t)
        return unique

    def _get_subtitle_track_name(self, stream: Dict[str, Any]) -> str:
        lang_code = stream.get('tags', {}).get('language', '')
        language = self._resolve_language(lang_code)
        title = stream.get('tags', {}).get('title', '') or ''

        if not title:
            return language if language else ''

        if language and title.lower().startswith(language.lower()):
            return title.replace(',', '","')

        if language:
            name = f"{language} {title}"
        else:
            name = title

        return name.replace(',', '","')

    def _get_encoder_options(self) -> Optional[str]:
        if 'encoder' in self.extra_options:
            return None
        if self.mode == self.MODE_H264:
            vs = self.vbv_size or 15000
            return f"vbv-maxrate={vs}:vbv-bufsize={vs}"
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

    def _escape_command(self, cmd: List[str]) -> str:
        def escape_if_needed(arg: str) -> str:
            return f'"{arg}"' if ' ' in arg else arg
        return ' '.join(escape_if_needed(a) for a in cmd)

    def parse_transcode_video_params(self, format_params: str):
        try:
            params = shlex.split(format_params)
        except ValueError:
            params = format_params.split()

        i = 0
        while i < len(params):
            param = params[i]
            if not param.startswith('-'):
                i += 1
                continue
            if param.startswith('--'):
                param_name = param[2:]
            else:
                param_name = param[1:]
            param_value = None
            if i + 1 < len(params) and not params[i + 1].startswith('--'):
                param_value = params[i + 1]
                i += 2
            else:
                i += 1

            if param_name == 'mode' and param_value:
                mapping = {
                    'h264': self.MODE_H264, 'hevc': self.MODE_HEVC,
                    'nvenc-hevc': self.MODE_NVENC_HEVC, 'av1': self.MODE_AV1,
                    'nvenc-av1': self.MODE_NVENC_AV1, 'none': self.MODE_NONE,
                }
                self.mode = mapping.get(param_value, self.MODE_H264)
                if self.mode in [self.MODE_AV1, self.MODE_NVENC_AV1]:
                    self.audio_mode = self.AUDIO_OPUS
            elif param_name == 'preset' and param_value:
                self.preset = param_value
            elif param_name == 'bitrate' and param_value:
                self.bitrate = int(param_value)
                self.quality = None
            elif param_name == 'quality' and param_value:
                self.quality = float(param_value)
                self.bitrate = None
            elif param_name == 'audio-mode' and param_value:
                mapping = {'aac': self.AUDIO_AAC, 'opus': self.AUDIO_OPUS,
                           'eac3': self.AUDIO_EAC3, 'none': self.AUDIO_NONE}
                self.audio_mode = mapping.get(param_value, self.AUDIO_AAC)
            elif param_name == 'add-audio' and param_value:
                if param_value.isdigit():
                    self.add_audio_selection(track=int(param_value))
                elif len(param_value) == 3 and param_value.isalpha():
                    self.add_audio_selection(language=param_value.lower())
                else:
                    self.add_audio_selection(title=param_value)
            elif param_name == 'add-subtitle' and param_value:
                if param_value.lower() == 'all':
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
            elif param_name == 'no-bframe-refs':
                self.bframe_refs = False
            elif param_name == 'aac-encoder' and param_value:
                if param_value in ['av_aac', 'fdk_aac', 'ca_aac']:
                    self.aac_encoder = param_value
            elif param_name in ('extra', 'x') and param_value:
                if '=' in param_value:
                    name, value = param_value.split('=', 1)
                    self.add_extra_option(name, value)
                else:
                    self.add_extra_option(param_value, None)
            elif param_name == 'stop-at' and param_value:
                self.add_extra_option('stop-at', param_value)

        logging.debug(f"HandBrakeGenerator configured with: {format_params}")


def generate_transcode_command(input_file: str, output_file: str,
                               media_info: Dict[str, Any], **kwargs) -> str:
    generator = HandBrakeGenerator(**kwargs)
    return generator.generate_command(input_file, output_file, media_info)
