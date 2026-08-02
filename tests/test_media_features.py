import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from features.atmos import _ffprobe_atmos_tracks, detect_dolby_atmos
from transcode.crop_detector import CropDetector
from tvb import split_command


class TestAtmosDetection(unittest.TestCase):
    def test_explicit_ffprobe_atmos_profile_is_detected(self):
        media_info = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "eac3",
                    "profile": "Dolby Digital Plus + Atmos",
                }
            ]
        }

        self.assertEqual(_ffprobe_atmos_tracks(media_info), ([1], []))

    def test_ambiguous_truehd_is_sent_to_fallback(self):
        media_info = {
            "streams": [
                {"codec_type": "audio", "codec_name": "truehd"}
            ]
        }

        with patch("features.atmos._mediainfo_atmos_tracks", return_value=[1]) as fallback:
            self.assertEqual(detect_dolby_atmos("movie.mkv", media_info), [1])
            fallback.assert_called_once_with("movie.mkv")

    def test_normal_audio_does_not_load_mediainfo(self):
        media_info = {
            "streams": [
                {"codec_type": "audio", "codec_name": "aac"}
            ]
        }

        with patch("features.atmos._mediainfo_atmos_tracks") as fallback:
            self.assertEqual(detect_dolby_atmos("movie.mkv", media_info), [])
            fallback.assert_not_called()

    def test_explicit_atmos_marker_avoids_fallback_for_other_eac3_tracks(self):
        media_info = {
            "streams": [
                {"codec_type": "audio", "codec_name": "eac3"},
                {
                    "codec_type": "audio",
                    "codec_name": "eac3",
                    "profile": "Dolby Digital Plus + Dolby Atmos",
                },
            ]
        }

        with patch("features.atmos._mediainfo_atmos_tracks") as fallback:
            self.assertEqual(detect_dolby_atmos("movie.mkv", media_info), [2])
            fallback.assert_not_called()


class TestCropDetection(unittest.TestCase):
    def test_crop_output_is_parsed(self):
        output = "[info] scan: crop (140/140/0/0): autocrop"
        self.assertEqual(CropDetector._parse_crop(output), "140:140:0:0")

    def test_missing_crop_defaults_to_zero(self):
        self.assertIsNone(CropDetector._parse_crop("no crop information"))


class TestCommandParsing(unittest.TestCase):
    def test_windows_paths_keep_backslashes(self):
        command = r'C:\Tools\HandBrakeCLI.exe --input "C:\Video Files\input.mkv"'
        args = split_command(command)
        self.assertEqual(args[0], r'C:\Tools\HandBrakeCLI.exe')
        self.assertEqual(args[2], r'C:\Video Files\input.mkv')


if __name__ == "__main__":
    unittest.main(verbosity=2)
