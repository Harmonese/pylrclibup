# ===== lrc/yaml_matcher.py =====

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..config import AppConfig
from ..model import YamlTrackMeta
from ..logging_utils import log_info
from ..i18n import get_text as _


def find_lrc_for_yaml_meta(
    yaml_meta: YamlTrackMeta,
    config: AppConfig,
) -> Optional[Path]:
    """
    为 YAML 元数据查找对应的 LRC 文件
    
    策略顺序：
    1. YAML 中指定的 lrc_file（相对于 YAML 文件或 lrc_dir）
    2. 与 YAML 文件同名的 .lrc 文件
    3. 在 lrc_dir 中查找同名 .lrc 文件
    """
    # 策略 1：YAML 中指定的 lrc_file
    if yaml_meta.lrc_file:
        # 尝试相对于 YAML 文件目录
        lrc_rel = yaml_meta.path.parent / yaml_meta.lrc_file
        if lrc_rel.exists() and lrc_rel.is_file():
            return lrc_rel
        
        # 尝试相对于 lrc_dir
        lrc_in_dir = config.lrc_dir / yaml_meta.lrc_file
        if lrc_in_dir.exists() and lrc_in_dir.is_file():
            return lrc_in_dir
        
        # 尝试绝对路径
        lrc_abs = Path(yaml_meta.lrc_file)
        if lrc_abs.is_absolute() and lrc_abs.exists() and lrc_abs.is_file():
            return lrc_abs
    
    # 策略 2：与 YAML 文件同名的 .lrc
    lrc_same_dir = yaml_meta.path.with_suffix('.lrc')
    if lrc_same_dir.exists() and lrc_same_dir.is_file():
        return lrc_same_dir
    
    # 策略 3：在 lrc_dir 中查找同名 .lrc
    lrc_in_lrc_dir = config.lrc_dir / (yaml_meta.path.stem + '.lrc')
    if lrc_in_lrc_dir.exists() and lrc_in_lrc_dir.is_file():
        return lrc_in_lrc_dir
    
    return None
