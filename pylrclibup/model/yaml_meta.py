# ===== model/yaml_meta.py =====

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from ..logging_utils import log_warn, log_error
from ..i18n import get_text as _


SUPPORTED_YAML_EXTENSIONS = {".yaml", ".yml"}


@dataclass
class YamlTrackMeta:
    """
    从 YAML 文件读取的音频元数据（用于无音频文件场景）
  
    YAML 格式：
    ```yaml
    track: "歌曲名"
    artist: "艺术家"
    album: "专辑名"
    duration: 180
    lrc_file: "example.lrc"  # 可选，指定关联的 LRC 文件
    ```
    """
    path: Path
    track: str
    artist: str
    album: str
    duration: int
    lrc_file: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.artist} - {self.track} ({self.album}, {self.duration}s) [YAML]"

    @classmethod
    def from_yaml_file(cls, yaml_path: Path) -> Optional["YamlTrackMeta"]:
        """从 YAML 文件读取元数据"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
          
            if not isinstance(data, dict):
                log_warn(_("YAML 文件格式错误（非字典）：{path}").format(path=yaml_path))
                return None
          
            track = data.get('track')
            artist = data.get('artist')
            album = data.get('album')
            duration = data.get('duration')
          
            if not all([track, artist, album, duration]):
                log_warn(_("YAML 文件缺少必需字段（track/artist/album/duration）：{path}").format(path=yaml_path))
                return None
          
            try:
                duration_int = int(duration)
                if duration_int <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                log_warn(_("YAML 文件 duration 字段无效：{path}").format(path=yaml_path))
                return None
          
            lrc_file = data.get('lrc_file')
          
            return cls(
                path=yaml_path,
                track=str(track),
                artist=str(artist),
                album=str(album),
                duration=duration_int,
                lrc_file=str(lrc_file) if lrc_file else None,
            )
      
        except yaml.YAMLError as e:
            log_error(_("解析 YAML 文件失败 {path}: {error}").format(path=yaml_path, error=str(e)))
            return None
        except Exception as e:
            log_error(_("读取 YAML 文件异常 {path}: {error}").format(path=yaml_path, error=str(e)))
            return None