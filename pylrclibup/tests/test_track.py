# ===== tests/test_track.py（完整修复版本）=====

"""
TrackMeta 多格式支持测试
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from pylrclibup.model import TrackMeta


class TestTrackMetaMultiFormat:
    """测试多格式音频文件支持"""
    
    @patch('pylrclibup.model.track.MutaFile')
    def test_mp3_format(self, mock_muta, tmp_path: Path):
        """测试 MP3 格式（ID3v2 标签）"""
        audio_file = tmp_path / "test.mp3"
        audio_file.touch()
        
        # 模拟 MP3 标签结构
        mock_audio = Mock()
        mock_audio.tags = {
            "TIT2": Mock(text=["Test Song"]),
            "TPE1": Mock(text=["Test Artist"]),
            "TALB": Mock(text=["Test Album"]),
        }
        # ✅ 使用 180.6 避免银行家舍入的边界情况
        mock_audio.info = Mock(length=180.6)
        mock_muta.return_value = mock_audio
        
        result = TrackMeta.from_audio_file(audio_file)
        
        assert result is not None
        assert result.track == "Test Song"
        assert result.artist == "Test Artist"
        assert result.album == "Test Album"
        assert result.duration == 181
    
    @patch('pylrclibup.model.track.MutaFile')
    def test_m4a_format(self, mock_muta, tmp_path: Path):
        """测试 M4A 格式（iTunes MP4 标签）"""
        audio_file = tmp_path / "test.m4a"
        audio_file.touch()
        
        # 模拟 M4A 标签结构
        mock_audio = Mock()
        mock_audio.tags = {
            "©nam": ["M4A Song"],
            "©ART": ["M4A Artist"],
            "©alb": ["M4A Album"],
        }
        mock_audio.info = Mock(length=200.0)
        mock_muta.return_value = mock_audio
        
        result = TrackMeta.from_audio_file(audio_file)
        
        assert result is not None
        assert result.track == "M4A Song"
        assert result.artist == "M4A Artist"
        assert result.album == "M4A Album"
        assert result.duration == 200
    
    @patch('pylrclibup.model.track.MutaFile')
    def test_flac_format(self, mock_muta, tmp_path: Path):
        """测试 FLAC 格式（Vorbis Comments）"""
        audio_file = tmp_path / "test.flac"
        audio_file.touch()
        
        # 模拟 FLAC 标签结构
        mock_audio = Mock()
        mock_audio.tags = {
            "TITLE": ["FLAC Song"],
            "ARTIST": ["FLAC Artist"],
            "ALBUM": ["FLAC Album"],
        }
        mock_audio.info = Mock(length=250.3)
        mock_muta.return_value = mock_audio
        
        result = TrackMeta.from_audio_file(audio_file)
        
        assert result is not None
        assert result.track == "FLAC Song"
        assert result.artist == "FLAC Artist"
        assert result.album == "FLAC Album"
        assert result.duration == 250
    
    @patch('pylrclibup.model.track.MutaFile')
    def test_missing_tags(self, mock_muta, tmp_path: Path):
        """测试标签不完整的情况"""
        audio_file = tmp_path / "incomplete.mp3"
        audio_file.touch()
        
        mock_audio = Mock()
        mock_audio.tags = {
            "TIT2": Mock(text=["Only Title"]),
            # 缺少 artist 和 album
        }
        mock_audio.info = Mock(length=100.0)
        mock_muta.return_value = mock_audio
        
        result = TrackMeta.from_audio_file(audio_file)
        
        assert result is None
    
    @patch('pylrclibup.model.track.MutaFile')
    def test_invalid_duration(self, mock_muta, tmp_path: Path):
        """测试无效时长"""
        audio_file = tmp_path / "invalid.mp3"
        audio_file.touch()
        
        mock_audio = Mock()
        mock_audio.tags = {
            "TIT2": Mock(text=["Song"]),
            "TPE1": Mock(text=["Artist"]),
            "TALB": Mock(text=["Album"]),
        }
        mock_audio.info = Mock(length=0)  # 无效时长
        mock_muta.return_value = mock_audio
        
        result = TrackMeta.from_audio_file(audio_file)
        
        assert result is None
    
    def test_from_mp3_backward_compatibility(self, tmp_path: Path):
        """测试 from_mp3() 向后兼容性"""
        with patch('pylrclibup.model.track.TrackMeta.from_audio_file') as mock_from_audio:
            mock_from_audio.return_value = Mock()
            
            audio_file = tmp_path / "test.mp3"
            audio_file.touch()
            
            result = TrackMeta.from_mp3(audio_file)
            
            mock_from_audio.assert_called_once_with(audio_file)
