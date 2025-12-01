from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class LyricsRecord:
    """
    表示从 LRCLIB API 返回的歌词记录
    """

    plain: str
    synced: str
    instrumental: bool

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "LyricsRecord":
        """
        从 API 返回的 JSON 构造 LyricsRecord
        
        API 返回格式：
        {
            "plainLyrics": "...",
            "syncedLyrics": "...",
            "instrumental": false,
            ...
        }
        """
        plain = data.get("plainLyrics") or ""
        synced = data.get("syncedLyrics") or ""
        instrumental = bool(data.get("instrumental", False))
        
        # 如果两个歌词字段都为空且没有明确标记 instrumental，
        # 也视为纯音乐
        if not plain.strip() and not synced.strip() and not instrumental:
            instrumental = True
        
        return cls(
            plain=plain,
            synced=synced,
            instrumental=instrumental,
        )

    def is_empty(self) -> bool:
        """判断歌词是否为空"""
        return not self.plain.strip() and not self.synced.strip()
