"""
LRC 解析器单元测试
"""

import pytest
from pathlib import Path
from pylrclibup.lrc.parser import (
    normalize_name,
    parse_lrc_file,
    ParsedLRC,
    TIMESTAMP_RE,
)


class TestNormalizeName:
    """测试 normalize_name 函数"""
    
    def test_basic_strip_and_lowercase(self):
        assert normalize_name("  Hello World  ") == "hello world"
    
    def test_fullwidth_punctuation(self):
        assert normalize_name("（测试）") == "(测试)"
        assert normalize_name("【标题】") == "[标题]"
        assert normalize_name("歌曲：名称") == "歌曲:名称"
    
    def test_cyrillic_mapping(self):
        assert normalize_name("Привёт") == "привет"
        assert normalize_name("Ёлка") == "елка"
    
    def test_multiple_spaces(self):
        assert normalize_name("hello    world") == "hello world"
    
    def test_empty_string(self):
        assert normalize_name("") == ""
    
    def test_unicode_normalization(self):
        # 全角字母应转为半角
        assert normalize_name("Ａｂｃ") == "abc"


class TestTimestampRegex:
    """测试时间戳正则表达式"""
    
    def test_standard_timestamp(self):
        assert TIMESTAMP_RE.match("[00:00.00]")
        assert TIMESTAMP_RE.match("[01:23.45]")
        assert TIMESTAMP_RE.match("[99:59.999]")
    
    def test_invalid_timestamp(self):
        assert not TIMESTAMP_RE.match("[0:00.00]")
        assert not TIMESTAMP_RE.match("[00:00]")
        assert not TIMESTAMP_RE.match("00:00.00")


class TestParseLrcFile:
    """测试 parse_lrc_file 函数"""
    
    def test_instrumental_detection(self, tmp_path: Path):
        lrc = tmp_path / "test.lrc"
        lrc.write_text("[00:00.00]纯音乐，请欣赏\n[00:01.00]歌词内容")
        
        result = parse_lrc_file(lrc)
        
        assert result.is_instrumental is True
        assert "纯音乐" not in result.synced
    
    def test_credit_removal(self, tmp_path: Path):
        lrc = tmp_path / "test.lrc"
        lrc.write_text(
            "[00:00.00]作词：张三\n"
            "[00:01.00]作曲：李四\n"
            "[00:02.00]这是歌词\n"
        )
        
        result = parse_lrc_file(lrc)
        
        assert "作词" not in result.synced
        assert "作曲" not in result.synced
        assert "这是歌词" in result.plain
    
    def test_empty_file(self, tmp_path: Path):
        lrc = tmp_path / "empty.lrc"
        lrc.write_text("")
        
        result = parse_lrc_file(lrc)
        
        assert result.synced == ""
        assert result.plain == ""
        assert result.is_instrumental is False
    
    def test_no_timestamp(self, tmp_path: Path):
        lrc = tmp_path / "no_ts.lrc"
        lrc.write_text("这不是有效的 LRC 文件")
        
        result = parse_lrc_file(lrc)
        
        assert result.synced == ""
        assert result.plain == ""
    
    def test_header_removal(self, tmp_path: Path):
        lrc = tmp_path / "header.lrc"
        lrc.write_text(
            "[ti:歌曲名]\n"
            "[ar:艺术家]\n"
            "[00:00.00]第一行歌词\n"
            "[00:05.00]第二行歌词\n"
        )
        
        result = parse_lrc_file(lrc)
        
        # 头部标签应被跳过
        assert "[ti:" not in result.synced
        assert "[ar:" not in result.synced
        assert "第一行歌词" in result.plain
    
    def test_translation_removal(self, tmp_path: Path):
        lrc = tmp_path / "trans.lrc"
        lrc.write_text(
            "[00:00.00]Hello world\n"
            "[00:00.00]你好世界\n"
            "[00:05.00]Goodbye\n"
        )
        
        result = parse_lrc_file(lrc, remove_translations=True)
        
        # 同一时间戳的中文行应被移除
        assert "Hello world" in result.plain
        assert "你好世界" not in result.plain
        assert "Goodbye" in result.plain
    
    def test_keep_translations(self, tmp_path: Path):
        lrc = tmp_path / "trans.lrc"
        lrc.write_text(
            "[00:00.00]Hello world\n"
            "[00:00.00]你好世界\n"
        )
        
        result = parse_lrc_file(lrc, remove_translations=False)
        
        assert "Hello world" in result.plain
        assert "你好世界" in result.plain
