# ===== fs/mover.py（完整 i18n 版本）=====

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..logging_utils import log_warn
from ..i18n import get_text as _


def move_with_dedup(
    src: Path,
    dst_dir: Path,
    *,
    new_name: Optional[str] = None
) -> Optional[Path]:
    """
    将 src 移动到 dst_dir，若同名文件已存在，则自动添加 _dup 后缀。
    
    特殊处理：
      - 如果源文件已在目标目录且无需重命名 → 直接返回源路径
      - 如果目标文件存在且与源文件不同 → 添加 _dup 后缀

    返回最终路径；若失败返回 None。
    """
    try:
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        # 确定目标文件名
        if new_name:
            target = dst_dir / f"{new_name}{src.suffix}"
        else:
            target = dst_dir / src.name
        
        # 检查是否为原地移动
        src_resolved = src.resolve()
        target_resolved = target.resolve()
        
        if src_resolved == target_resolved:
            return src
        
        # 处理重名情况
        if target.exists():
            stem = target.stem
            suffix = target.suffix
            dedup = 1
            while True:
                candidate = dst_dir / f"{stem}_dup{dedup}{suffix}"
                if not candidate.exists():
                    target = candidate
                    break
                dedup += 1
        
        # 执行移动/重命名
        src.rename(target)
        return target

    except Exception as e:
        log_warn(_("移动文件失败：{src} → {dst}：{error}").format(src=src, dst=dst_dir, error=str(e)))
        return None
