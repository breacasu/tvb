#!/usr/bin/env python3
import logging
import re

try:
    from pymediainfo import MediaInfo
except ImportError:
    MediaInfo = None


def detect_dolby_atmos(input_file):
    if MediaInfo is None:
        logging.warning("pymediainfo not installed, Atmos detection disabled")
        return []

    try:
        media_info = MediaInfo.parse(input_file)
        atmos_tracks = []
        audio_track_counter = 0

        for track in media_info.tracks:
            if track.track_type == "Audio":
                audio_track_counter += 1
                track_number = audio_track_counter

                audio_format = (getattr(track, 'format', '') or '').lower()
                audio_format_profile = (getattr(track, 'format_profile', '') or '').lower()
                audio_title = (getattr(track, 'title', '') or '').lower()
                audio_codec_id = (getattr(track, 'codec_id', '') or '').lower()
                audio_format_info = (getattr(track, 'format_info', '') or '').lower()
                audio_commercial_name = (getattr(track, 'commercial_name', '') or '').lower()

                atmos_indicators = [
                    'atmos', 'dolby atmos', 'dolby-atmos',
                    'dolby digital plus atmos', 'dd+ atmos',
                    'truehd atmos', 'true-hd atmos'
                ]
                joc_indicators = [
                    'joc', 'joint object coding', 'joint-object-coding',
                    'enhanced ac-3 joc', 'e-ac-3 joc'
                ]

                all_audio_fields = [
                    audio_format_profile, audio_title, audio_format_info,
                    audio_commercial_name, audio_codec_id
                ]

                is_atmos = False

                for field_value in all_audio_fields:
                    if any(indicator in field_value for indicator in atmos_indicators):
                        is_atmos = True
                        break

                if not is_atmos:
                    for field_value in all_audio_fields:
                        if any(indicator in field_value for indicator in joc_indicators):
                            is_atmos = True
                            break

                if not is_atmos and 'truehd' in audio_format and 'atmos' in audio_format_profile:
                    is_atmos = True

                if not is_atmos and 'e-ac-3' in audio_format and \
                   any('joc' in field for field in all_audio_fields):
                    is_atmos = True

                if not is_atmos and 'dolby digital plus with dolby atmos' in audio_commercial_name:
                    is_atmos = True

                if is_atmos:
                    atmos_tracks.append(track_number)

                logging.debug(f"Audio track {track_number}: format={audio_format}, "
                              f"profile={audio_format_profile}, title={audio_title}, "
                              f"codec_id={audio_codec_id}, info={audio_format_info}, "
                              f"commercial={audio_commercial_name}, is_atmos={is_atmos}")

        return atmos_tracks

    except Exception as e:
        logging.debug(f"Error detecting Dolby Atmos: {e}")
        return []


def generate_atmos_aware_audio_params(atmos_tracks, processed_audio_tracks, original_cmd):
    encoders = []
    bitrates = []
    mixdowns = []

    original_encoders = []
    original_bitrates = []
    original_mixdowns = []

    aencoder_match = re.search(r'--aencoder\s+([^-\s]+)', original_cmd)
    if aencoder_match:
        original_encoders = aencoder_match.group(1).split(',')

    ab_match = re.search(r'--ab\s+([^-\s]+)', original_cmd)
    if ab_match:
        original_bitrates = ab_match.group(1).split(',')

    mixdown_match = re.search(r'--mixdown\s+([^-\s]+)', original_cmd)
    if mixdown_match:
        original_mixdowns = mixdown_match.group(1).split(',')

    for i in range(1, processed_audio_tracks + 1):
        if i in atmos_tracks:
            encoders.append('copy')
            bitrates.append('')
            mixdowns.append('none')
        else:
            track_index = i - 1
            encoders.append(original_encoders[track_index] if track_index < len(original_encoders) else 'av_aac')
            bitrates.append(original_bitrates[track_index] if track_index < len(original_bitrates) else '')
            mixdowns.append(original_mixdowns[track_index] if track_index < len(original_mixdowns) else '5point1')

    encoder_param = ','.join(encoders)
    bitrate_param = ','.join(filter(None, bitrates))
    mixdown_param = ','.join(mixdowns)

    return {
        'aencoder': encoder_param,
        'ab': bitrate_param if bitrate_param else '',
        'mixdown': mixdown_param
    }