# ===== tests/test_config.py =====

"""
配置模块单元测试
"""

import pytest
import os
from pathlib import Path
from pylrclibup.config import AppConfig


class TestAppConfig:
    """测试 AppConfig 类"""
    
    def test_default_values(self, tmp_path: Path, monkeypatch):
        # 清除环境变量
        monkeypatch.delenv("PYLRCLIBUP_TRACKS_DIR", raising=False)
        monkeypatch.delenv("PYLRCLIBUP_LRC_DIR", raising=False)
        monkeypatch.delenv("PYLRCLIBUP_DONE_TRACKS_DIR", raising=False)
        monkeypatch.delenv("PYLRCLIBUP_DONE_LRC_DIR", raising=False)
        
        monkeypatch.chdir(tmp_path)
        
        config = AppConfig.from_env_and_defaults()
        
        assert config.tracks_dir == tmp_path
        assert config.lrc_dir == tmp_path
        assert config.done_tracks_dir is None
        assert config.done_lrc_dir is None
        assert config.follow_mp3 is False
        assert config.rename_lrc is False
        assert config.cleanse_lrc is False
        assert config.preview_lines == 10
        assert config.max_http_retries == 5
    
    def test_explicit_dirs(self, tmp_path: Path):
        tracks = tmp_path / "tracks"
        lrc = tmp_path / "lrc"
        done_tracks = tmp_path / "done_tracks"
        done_lrc = tmp_path / "done_lrc"
        
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tracks,
            lrc_dir=lrc,
            done_tracks_dir=done_tracks,
            done_lrc_dir=done_lrc,
        )
        
        assert config.tracks_dir == tracks
        assert config.lrc_dir == lrc
        assert config.done_tracks_dir == done_tracks
        assert config.done_lrc_dir == done_lrc
    
    def test_follow_mode(self, tmp_path: Path):
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            follow_mp3=True,
        )
        
        assert config.follow_mp3 is True
    
    def test_rename_mode(self, tmp_path: Path):
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            rename_lrc=True,
        )
        
        assert config.rename_lrc is True
    
    def test_cleanse_mode(self, tmp_path: Path):
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            cleanse_lrc=True,
        )
        
        assert config.cleanse_lrc is True
    
    def test_combined_modes(self, tmp_path: Path):
        # 测试 -d 模式（follow + rename + cleanse）
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            follow_mp3=True,
            rename_lrc=True,
            cleanse_lrc=True,
        )
        
        assert config.follow_mp3 is True
        assert config.rename_lrc is True
        assert config.cleanse_lrc is True
    
    def test_backward_compatibility_pair_mode(self, tmp_path: Path):
        # -d 模式的向后兼容属性
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            follow_mp3=True,
            rename_lrc=True,
            cleanse_lrc=True,
        )
        
        assert config.pair_lrc_with_track_dir is True
    
    def test_backward_compatibility_match_mode(self, tmp_path: Path):
        # -m 模式的向后兼容属性
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
            follow_mp3=True,
            rename_lrc=True,
            cleanse_lrc=True,
        )
        
        assert config.match_mode is True
    
    def test_backward_compatibility_keep_in_place(self, tmp_path: Path):
        # 原地模式的向后兼容属性
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tmp_path,
            lrc_dir=tmp_path,
        )
        
        assert config.keep_in_place is True
    
    def test_env_override(self, tmp_path: Path, monkeypatch):
        env_tracks = tmp_path / "env_tracks"
        monkeypatch.setenv("PYLRCLIBUP_TRACKS_DIR", str(env_tracks))
        
        config = AppConfig.from_env_and_defaults()
        
        assert config.tracks_dir == env_tracks
    
    def test_explicit_overrides_env(self, tmp_path: Path, monkeypatch):
        env_tracks = tmp_path / "env_tracks"
        explicit_tracks = tmp_path / "explicit_tracks"
        
        monkeypatch.setenv("PYLRCLIBUP_TRACKS_DIR", str(env_tracks))
        
        config = AppConfig.from_env_and_defaults(tracks_dir=explicit_tracks)
        
        assert config.tracks_dir == explicit_tracks
