# ===== model/track.py（完整 i18n 版本）=====

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from mutagen import File as MutaFile
from mutagen.id3 import ID3NoHeaderError

from ..logging_utils import log_warn, log_error, log_debug
from ..i18n import get_text as _

# 各格式标签键映射（统一到 title, artist, album）
TAG_MAPPINGS: Dict[str, Dict[str, list[str]]] = {
    # MP3 (ID3v2)
    "mp3": {
        "title": ["TIT2"],
        "artist": ["TPE1"],
        "album": ["TALB"],
    },
    # M4A/AAC (iTunes MP4)
    "m4a": {
        "title": ["©nam", "\xa9nam"],
        "artist": ["©ART", "\xa9ART"],
        "album": ["©alb", "\xa9alb"],
    },
    "aac": {  # 同 m4a
        "title": ["©nam", "\xa9nam"],
        "artist": ["©ART", "\xa9ART"],
        "album": ["©alb", "\xa9alb"],
    },
    # FLAC (Vorbis Comments)
    "flac": {
        "title": ["TITLE", "title"],
        "artist": ["ARTIST", "artist"],
        "album": ["ALBUM", "album"],
    },
    # WAV (通常使用 ID3 或无标签)
    "wav": {
        "title": ["TIT2", "TITLE", "title"],
        "artist": ["TPE1", "ARTIST", "artist"],
        "album": ["TALB", "ALBUM", "album"],
    },
}


@dataclass
class TrackMeta:
    """
    表示一首歌曲的元数据（从音频文件读取）
    """

    path: Path
    track: str
    artist: str
    album: str
    duration: int  # 秒

    def __str__(self) -> str:
        return f"{self.artist} - {self.track} ({self.album}, {self.duration}s)"

    @staticmethod
    def _get_universal_tag(audio: Any, field: str, ext: str) -> Optional[str]:
        """
        统一的标签读取接口（支持多种音频格式）
        
        Args:
            audio: Mutagen 音频对象
            field: 字段名（title/artist/album）
            ext: 文件扩展名（不含点，如 "mp3"）
        
        Returns:
            标签值字符串，如果不存在则返回 None
        """
        if not audio or not audio.tags:
            return None
        
        # 获取该格式对应的标签键列表
        mapping = TAG_MAPPINGS.get(ext, {})
        possible_keys = mapping.get(field, [])
        
        # 尝试所有可能的键
        for key in possible_keys:
            try:
                value = audio.tags.get(key)
                if value is None:
                    continue
                
                # 处理不同格式的返回值
                if isinstance(value, list) and value:
                    return str(value[0])
                elif hasattr(value, "text") and value.text:
                    return str(value.text[0])
                elif isinstance(value, str):
                    return value
                else:
                    # 尝试直接转字符串
                    result = str(value)
                    if result:
                        return result
            except Exception as e:
                log_debug(_("读取标签 {key} 失败: {error}").format(key=key, error=str(e)))
                continue
        
        return None

    @classmethod
    def from_audio_file(cls, audio_path: Path) -> Optional["TrackMeta"]:
        """
        从音频文件读取元数据（支持 MP3, M4A, AAC, FLAC, WAV）
        
        出现异常/标签不完整时返回 None。
        """
        ext = audio_path.suffix.lower().strip(".")
        
        try:
            audio = MutaFile(audio_path)
            if audio is None:
                log_warn(_("无法读取音频文件：{filename}").format(filename=audio_path.name))
                return None
        except ID3NoHeaderError:
            log_warn(_("音频文件无标签：{filename}").format(filename=audio_path.name))
            return None
        except Exception as e:
            log_error(_("读取音频文件异常 {filename}: {error}").format(filename=audio_path.name, error=str(e)))
            return None

        # 使用统一接口读取标签
        track = cls._get_universal_tag(audio, "title", ext)
        artist = cls._get_universal_tag(audio, "artist", ext)
        album = cls._get_universal_tag(audio, "album", ext)

        if not track or not artist or not album:
            log_warn(_("音频文件标签不完整：{filename}").format(filename=audio_path.name))
            return None

        # 读取时长
        duration = 0
        if hasattr(audio, "info") and hasattr(audio.info, "length"):
            duration = int(round(audio.info.length))
        
        if duration <= 0:
            log_warn(_("音频文件时长无效：{filename}").format(filename=audio_path.name))
            return None

        return cls(
            path=audio_path,
            track=track,
            artist=artist,
            album=album,
            duration=duration,
        )

    @classmethod
    def from_mp3(cls, mp3_path: Path) -> Optional["TrackMeta"]:
        """
        向后兼容的方法（调用 from_audio_file）
        
        ⚠️ 已弃用，请使用 from_audio_file()
        """
        return cls.from_audio_file(mp3_path)

    @classmethod
    def from_yaml(cls, yaml_meta: "YamlTrackMeta") -> "TrackMeta":
        from .yaml_meta import YamlTrackMeta  # 避免循环导入
        """从 YamlTrackMeta 转换为 TrackMeta"""
        return cls(
            path=yaml_meta.path,
            track=yaml_meta.track,
            artist=yaml_meta.artist,
            album=yaml_meta.album,
            duration=yaml_meta.duration,
        )