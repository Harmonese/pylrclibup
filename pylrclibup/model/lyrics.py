from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LyricsRecord:
    """
    表示从 LRCLIB API（/api/get /api/get-cached 等）获得的歌词记录。
    """

    track_name: str
    artist_name: str
    album_name: str
    duration: int

    plain: str
    synced: str
    instrumental: bool

    @classmethod
    def from_api(cls, data: dict) -> "LyricsRecord":
        plain = data.get("plainLyrics") or ""
        synced = data.get("syncedLyrics") or ""
        instrumental = bool(data.get("instrumental")) or (not plain and not synced)

        return cls(
            track_name=data.get("trackName") or "",
            artist_name=data.get("artistName") or "",
            album_name=data.get("albumName") or "",
            duration=int(data.get("duration", 0)),
            plain=plain,
            synced=synced,
            instrumental=instrumental,
        )
