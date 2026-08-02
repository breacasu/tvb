#!/usr/bin/env python3
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from tool_paths import resolve_library


ATMOS_MARKERS = (
    "atmos",
    "dolby atmos",
    "dolby-atmos",
    "joc",
    "joint object coding",
    "joint-object-coding",
)


def _stream_text(stream: Dict[str, Any]) -> str:
    values: List[str] = []
    for key in ("codec_name", "codec_long_name", "profile", "codec_tag_string"):
        values.append(str(stream.get(key, "") or ""))
    for value in (stream.get("tags") or {}).values():
        values.append(str(value or ""))
    values.append(str(stream.get("side_data_list", "") or ""))
    return " ".join(values).lower()


def _ffprobe_atmos_tracks(media_info: Dict[str, Any]) -> Tuple[List[int], List[int]]:
    atmos_tracks: List[int] = []
    ambiguous_tracks: List[int] = []

    audio_number = 0
    for stream in media_info.get("streams", []):
        if stream.get("codec_type") != "audio":
            continue
        audio_number += 1
        text = _stream_text(stream)
        codec = str(stream.get("codec_name", "") or "").lower()

        if any(marker in text for marker in ATMOS_MARKERS):
            atmos_tracks.append(audio_number)
        elif codec in {"eac3", "truehd"}:
            # ffprobe may expose only the base codec for files whose Atmos
            # metadata is stored in a format-specific field.
            ambiguous_tracks.append(audio_number)

    return atmos_tracks, ambiguous_tracks


def _mediainfo_atmos_tracks(input_file: str) -> List[int]:
    """Use MediaInfo only for codecs ffprobe could not classify safely."""
    try:
        from pymediainfo import MediaInfo
    except ImportError:
        logging.warning("pymediainfo is unavailable; Atmos fallback disabled")
        return []

    try:
        media_info = MediaInfo.parse(
            input_file,
            library_file=resolve_library("libmediainfo"),
        )
        atmos_tracks: List[int] = []
        audio_track_counter = 0

        for track in media_info.tracks:
            if track.track_type != "Audio":
                continue
            audio_track_counter += 1
            fields = (
                getattr(track, "format", ""),
                getattr(track, "format_profile", ""),
                getattr(track, "title", ""),
                getattr(track, "codec_id", ""),
                getattr(track, "format_info", ""),
                getattr(track, "commercial_name", ""),
            )
            text = " ".join(str(value or "") for value in fields).lower()
            if any(marker in text for marker in ATMOS_MARKERS):
                atmos_tracks.append(audio_track_counter)

        return atmos_tracks
    except Exception as exc:
        logging.debug("MediaInfo Atmos fallback failed: %s", exc)
        return []


def detect_dolby_atmos(input_file: str, media_info: Optional[Dict[str, Any]] = None) -> List[int]:
    """Detect Atmos tracks using ffprobe first and MediaInfo only as fallback."""
    try:
        if media_info is None:
            from transcode.analyzer import MediaAnalyzer
            media_info = MediaAnalyzer().scan_media(input_file)

        atmos_tracks, ambiguous_tracks = _ffprobe_atmos_tracks(media_info)
        if ambiguous_tracks and not atmos_tracks:
            logging.debug(
                "ffprobe could not classify possible Atmos tracks %s; "
                "using MediaInfo fallback",
                ambiguous_tracks,
            )
            fallback_tracks = _mediainfo_atmos_tracks(input_file)
            atmos_tracks = sorted(set(atmos_tracks).union(fallback_tracks))

        logging.debug("Atmos tracks detected by ffprobe-first scan: %s", atmos_tracks)
        return atmos_tracks
    except Exception as exc:
        logging.debug("Error detecting Dolby Atmos: %s", exc)
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
