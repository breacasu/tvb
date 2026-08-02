import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'python'))

from transcode.generator import HandBrakeGenerator


class MockAnalyzer:
    """Simuliert MediaAnalyzer für deterministische Tests."""
    def __init__(self, video_info=None, audio_streams=None, subtitle_streams=None):
        self._video_info = video_info or {}
        self._audio_streams = audio_streams or []
        self._subtitle_streams = subtitle_streams or []

    def get_video_stream(self, media_info):
        return self._video_info

    def get_audio_streams(self, media_info):
        return self._audio_streams

    def get_subtitle_streams(self, media_info):
        return self._subtitle_streams


class TestGeneratorVideoOptions(unittest.TestCase):

    def setUp(self):
        self.mock_1080p = MockAnalyzer({'width': 1920, 'height': 1080,
                                         'codec_name': 'h264', 'avg_frame_rate': '24000/1001'})

    def test_hevc_default_quality(self):
        """HEVC ohne Quality/Bitrate → Default Quality 24"""
        g = HandBrakeGenerator(mode='hevc')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--quality', opts)
        self.assertIn('24', opts)

    def test_h264_no_quality_bitrate_default(self):
        """H264 ohne Quality/Bitrate → auflösungsbasierte Bitrate + Multi-Pass + Turbo"""
        g = HandBrakeGenerator(mode='h264')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--vb', opts)
        self.assertIn('5000', opts)
        self.assertIn('--multi-pass', opts)
        self.assertIn('--turbo', opts)
        self.assertEqual(g.vbv_size, 15000)

    def test_h264_4k_downscale(self):
        """H264 bei 4K → maxWidth/maxHeight + colorspace bt709"""
        mock_4k = MockAnalyzer({'width': 3840, 'height': 2160,
                                 'codec_name': 'hevc', 'avg_frame_rate': '24000/1001',
                                 'color_space': 'bt2020nc'})
        g = HandBrakeGenerator(mode='h264')
        g._media_analyzer = mock_4k
        opts = g._get_video_options({})
        self.assertIn('--maxWidth', opts)
        self.assertIn('1920', opts)
        self.assertIn('--maxHeight', opts)
        self.assertIn('1080', opts)
        self.assertIn('--loose-anamorphic', opts)
        self.assertIn('--colorspace', opts)

    def test_nvenc_hevc_default_quality(self):
        """NVENC HEVC ohne Quality/Bitrate → Default Quality 30"""
        g = HandBrakeGenerator(mode='nvenc_hevc')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--quality', opts)
        self.assertIn('30', opts)

    def test_av1_defaults(self):
        """AV1 ohne Angaben → Quality 30, Preset 8"""
        g = HandBrakeGenerator(mode='av1')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--quality', opts)
        self.assertIn('30', opts)
        self.assertIn('--encoder-preset', opts)
        self.assertIn('8', opts)

    def test_nvenc_av1_defaults(self):
        """NVENC AV1 ohne Angaben → Quality 37, Preset 8"""
        g = HandBrakeGenerator(mode='nvenc_av1')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--quality', opts)
        self.assertIn('37', opts)

    def test_frame_rate_mpeg2(self):
        """mpeg2video@30000/1001 → --rate 29.97 --cfr"""
        mock_mpeg2 = MockAnalyzer({'width': 720, 'height': 576,
                                    'codec_name': 'mpeg2video',
                                    'avg_frame_rate': '30000/1001'})
        g = HandBrakeGenerator(mode='hevc')
        g._media_analyzer = mock_mpeg2
        opts = g._get_video_options({})
        self.assertIn('--rate', opts)
        self.assertIn('29.97', opts)
        self.assertIn('--cfr', opts)

    def test_frame_rate_default_60(self):
        """Normales Video → --rate 60 (VFR-Cap)"""
        g = HandBrakeGenerator(mode='hevc')
        g._media_analyzer = self.mock_1080p
        opts = g._get_video_options({})
        self.assertIn('--rate', opts)
        self.assertIn('60', opts)
        self.assertNotIn('--cfr', opts)


class TestGeneratorAudioOptions(unittest.TestCase):

    def setUp(self):
        self.mock_aac_stereo = MockAnalyzer(
            video_info={'codec_name': 'h264', 'width': 1920, 'height': 1080},
            audio_streams=[{'index': 1, 'codec_name': 'aac', 'channels': 2,
                            'tags': {'language': 'eng', 'title': 'Stereo'}}]
        )

    def test_aac_copy_stereo(self):
        """AAC ≤6ch → copy (kein Re-encode)"""
        g = HandBrakeGenerator(mode='hevc', audio_mode='aac')
        g._media_analyzer = self.mock_aac_stereo
        opts = g._get_audio_options({})
        self.assertIn('copy', ' '.join(opts))

    def test_aac_encode_51(self):
        """5.1 ohne ac3-surround → aac-encode mit Bitrate 384"""
        mock_51 = MockAnalyzer(
            video_info={'codec_name': 'h264', 'width': 1920, 'height': 1080},
            audio_streams=[{'index': 1, 'codec_name': 'ac3', 'channels': 6,
                            'tags': {'language': 'eng'}}]
        )
        g = HandBrakeGenerator(mode='hevc', audio_mode='aac')
        g._media_analyzer = mock_51
        opts = g._get_audio_options({})
        self.assertIn('av_aac', ' '.join(opts))

    def test_opus_bitrates(self):
        """OPUS Bitrates: 1ch=64, 2ch=96, >2ch=320"""
        for ch, expected in [(1, '64'), (2, '96'), (6, '320')]:
            mock = MockAnalyzer(
                video_info={'codec_name': 'h264', 'width': 1920, 'height': 1080},
                audio_streams=[{'index': 1, 'codec_name': 'aac', 'channels': ch,
                                'tags': {'language': 'eng'}}]
            )
            g = HandBrakeGenerator(mode='hevc', audio_mode='opus')
            g._media_analyzer = mock
            opts = ' '.join(g._get_audio_options({}))
            self.assertIn(expected, opts, f'OPUS {ch}ch → Bitrate {expected}')

    def test_eac3_copy_conditions(self):
        """EAC3: ac3/eac3 oder aac≤6ch → copy"""
        for codec in ['ac3', 'eac3', 'aac']:
            mock = MockAnalyzer(
                video_info={'codec_name': 'h264', 'width': 1920, 'height': 1080},
                audio_streams=[{'index': 1, 'codec_name': codec, 'channels': 2,
                                'tags': {'language': 'eng'}}]
            )
            g = HandBrakeGenerator(mode='hevc', audio_mode='eac3')
            g._media_analyzer = mock
            opts = ' '.join(g._get_audio_options({}))
            self.assertIn('copy', opts, f'EAC3 {codec} → copy')


class TestGeneratorAudioTrackNames(unittest.TestCase):

    def test_channel_label_in_name(self):
        """Track-Name enthält Kanalinfo (Stereo/5.1) bei mehreren Tracks"""
        mock = MockAnalyzer(
            video_info={'codec_name': 'h264', 'width': 1920, 'height': 1080},
            audio_streams=[
                {'index': 1, 'codec_name': 'aac', 'channels': 2,
                 'tags': {'language': 'eng', 'title': 'Stereo'}},
                {'index': 2, 'codec_name': 'ac3', 'channels': 6,
                 'tags': {'language': 'ger', 'title': 'Surround'}},
            ]
        )
        g = HandBrakeGenerator(mode='hevc', audio_mode='aac')
        g._media_analyzer = mock
        g.add_audio_selection(track=2)
        opts = g._get_audio_options({})
        opt_str = ' '.join(opts)
        self.assertIn('Stereo', opt_str)
        self.assertIn('5.1', opt_str)


class TestGeneratorEncoderOptions(unittest.TestCase):

    def test_nvenc_hevc_options(self):
        """NVENC HEVC → spatial_aq + rc-lookahead + b_ref_mode"""
        g = HandBrakeGenerator(mode='nvenc_hevc', bframe_refs=True)
        opts = g._get_encoder_options()
        self.assertIn('spatial_aq=1', opts)
        self.assertIn('rc-lookahead=20', opts)
        self.assertIn('b_ref_mode=2', opts)

    def test_nvenc_av1_options(self):
        """NVENC AV1 → spatial-aq + rc-lookahead + b_ref_mode"""
        g = HandBrakeGenerator(mode='nvenc_av1', bframe_refs=True)
        opts = g._get_encoder_options()
        self.assertIn('spatial-aq=1', opts)
        self.assertIn('rc-lookahead=20', opts)
        self.assertIn('b_ref_mode=2', opts)

    def test_h264_vbv_options(self):
        """H264 → vbv-maxrate + vbv-bufsize"""
        g = HandBrakeGenerator(mode='h264')
        g.vbv_size = 15000
        opts = g._get_encoder_options()
        self.assertIn('vbv-maxrate=15000', opts)
        self.assertIn('vbv-bufsize=15000', opts)

    def test_custom_encopts_are_merged(self):
        g = HandBrakeGenerator(mode='nvenc_hevc')
        g.parse_transcode_video_params('-x encopts=custom=1')
        command = g.generate_command_list('input.mkv', 'output.mkv', {})
        self.assertEqual(command.count('--encopts'), 1)
        self.assertIn('spatial_aq=1:rc-lookahead=20:b_ref_mode=2:custom=1', command)

    def test_no_bframe_refs_is_applied(self):
        g = HandBrakeGenerator(mode='nvenc_hevc')
        g.parse_transcode_video_params('--no-bframe-refs')
        self.assertNotIn('b_ref_mode=2', g._get_encoder_options())


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
