from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mutagen import File as MutaFile
from mutagen.id3 import ID3NoHeaderError

from ..exceptions import PylrclibupError


@dataclass
class TrackMeta:
    """
    表示一首歌曲的元数据（从 MP3 文件读取）：
      - path: MP3 文件路径
      - track: 歌曲名
      - artist: 艺术家名（可能含 feat. 等）
      - album: 专辑名
      - duration: 秒数
    """

    path: Path
    track: str
    artist: str
    album: str
    duration: int  # 秒

    def __str__(self) -> str:
        return f"{self.artist} - {self.track} ({self.album}, {self.duration}s)"

    # --------------------------------------------------

    @staticmethod
    def _get_tag(tags, key: str) -> Optional[str]:
        """从 Mutagen 的 tag 对象中安全获取 text 字段"""
        field = tags.get(key)
        return field.text[0] if field and getattr(field, "text", None) else None

    # --------------------------------------------------

    @classmethod
    def from_mp3(cls, mp3_path: Path) -> Optional["TrackMeta"]:
        """
        从 MP3 文件读取元数据。
        出现异常/标签不完整时返回 None（processor 决定如何处理）。
        """

        try:
            audio = MutaFile(mp3_path)
            if audio is None or audio.tags is None:
                print(f"[WARN] 无法读取标签：{mp3_path.name}")
                return None
        except ID3NoHeaderError:
            print(f"[WARN] 无 ID3 标签：{mp3_path.name}")
            return None
        except Exception as e:
            print(f"[ERROR] 读取标签异常 {mp3_path.name}: {e}")
            return None

        tags = audio.tags

        track = cls._get_tag(tags, "TIT2")
        artist = cls._get_tag(tags, "TPE1")
        album = cls._get_tag(tags, "TALB")

        if not track or not artist or not album:
            print(f"[WARN] 标签不完整：{mp3_path.name}")
            return None

        duration = int(round(getattr(audio.info, "length", 0)))
        if duration <= 0:
            print(f"[WARN] 时长无效：{mp3_path.name}")
            return None

        return cls(
            path=mp3_path,
            track=track,
            artist=artist,
            album=album,
            duration=duration,
        )
