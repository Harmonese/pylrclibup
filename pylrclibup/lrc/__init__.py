from .parser import (
    normalize_name,
    ParsedLRC,
    parse_lrc_file,
    write_lrc_file,
)

from .matcher import (
    split_artists,
    match_artists,
    parse_lrc_filename,
    find_lrc_for_track,
)

__all__ = [
    "normalize_name",
    "ParsedLRC",
    "parse_lrc_file",
    "write_lrc_file",
    "split_artists",
    "match_artists",
    "parse_lrc_filename",
    "find_lrc_for_track",
]
