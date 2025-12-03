# ===== lrc/__init__.py =====

"""
LRC 模块：解析和匹配歌词文件
"""

from .parser import parse_lrc_file, write_lrc_file, cleanse_lrc_file, ParsedLRC, normalize_name
from .matcher import find_lrc_for_track, split_artists, match_artists
from .yaml_matcher import find_lrc_for_yaml_meta

__all__ = [
    "parse_lrc_file",
    "write_lrc_file",
    "cleanse_lrc_file",
    "ParsedLRC",
    "normalize_name",
    "find_lrc_for_track",
    "split_artists",
    "match_artists",
    "find_lrc_for_yaml_meta",
]
