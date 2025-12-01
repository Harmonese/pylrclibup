"""
LRC 匹配器单元测试
"""

import pytest
from pathlib import Path
from pylrclibup.lrc.matcher import (
    split_artists,
    match_artists,
    parse_lrc_filename,
)


class TestSplitArtists:
    """测试 split_artists 函数"""
    
    def test_single_artist(self):
        assert split_artists("Artist") == ["artist"]
    
    def test_feat_separator(self):
        result = split_artists("Artist A feat. Artist B")
        assert "artist a" in result
        assert "artist b" in result
    
    def test_featuring_separator(self):
        result = split_artists("Artist A featuring Artist B")
        assert "artist a" in result
        assert "artist b" in result
    
    def test_ampersand_separator(self):
        result = split_artists("Artist A & Artist B")
        assert "artist a" in result
        assert "artist b" in result
    
    def test_chinese_separator(self):
        result = split_artists("艺术家A和艺术家B")
        assert "艺术家a" in result
        assert "艺术家b" in result
    
    def test_comma_separator(self):
        result = split_artists("A,B,C")
        assert len(result) == 3
    
    def test_x_separator(self):
        result = split_artists("Artist A x Artist B")
        assert "artist a" in result
        assert "artist b" in result
    
    def test_mixed_separators(self):
        result = split_artists("A & B feat. C / D")
        assert len(result) == 4
    
    def test_dedup(self):
        result = split_artists("A & A & B")
        assert result.count("a") == 1


class TestMatchArtists:
    """测试 match_artists 函数"""
    
    def test_exact_match(self):
        assert match_artists(["artist"], ["artist"]) is True
    
    def test_partial_match(self):
        assert match_artists(["a", "b"], ["b", "c"]) is True
    
    def test_no_match(self):
        assert match_artists(["a", "b"], ["c", "d"]) is False
    
    def test_case_insensitive(self):
        assert match_artists(["Artist"], ["ARTIST"]) is True
    
    def test_empty_lists(self):
        assert match_artists([], []) is False
        assert match_artists(["a"], []) is False


class TestParseLrcFilename:
    """测试 parse_lrc_filename 函数"""
    
    def test_standard_format(self, tmp_path: Path):
        lrc = tmp_path / "Artist - Song.lrc"
        lrc.touch()
        
        artists, title = parse_lrc_filename(lrc)
        
        assert "artist" in artists
        assert title == "song"
    
    def test_multiple_artists(self, tmp_path: Path):
        lrc = tmp_path / "A & B - Song.lrc"
        lrc.touch()
        
        artists, title = parse_lrc_filename(lrc)
        
        assert "a" in artists
        assert "b" in artists
        assert title == "song"
    
    def test_no_separator(self, tmp_path: Path):
        lrc = tmp_path / "SongWithoutArtist.lrc"
        lrc.touch()
        
        artists, title = parse_lrc_filename(lrc)
        
        assert artists == []
        assert title == ""
    
    def test_multiple_separators(self, tmp_path: Path):
        lrc = tmp_path / "Artist - Song - Remix.lrc"
        lrc.touch()
        
        artists, title = parse_lrc_filename(lrc)
        
        assert "artist" in artists
        assert title == "song - remix"
