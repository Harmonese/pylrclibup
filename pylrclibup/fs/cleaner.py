from __future__ import annotations

from pathlib import Path

from ..logging_utils import log_info, log_warn


def cleanup_empty_dirs(root: Path) -> None:
    """
    递归删除 root 下的空目录（不删除 root 本身）
    
    采用自底向上的方式，确保子目录先于父目录被检查
    """
    if not root.exists() or not root.is_dir():
        return
    
    # 收集所有子目录（自底向上排序）
    all_dirs = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    
    for d in all_dirs:
        if not d.is_dir():
            continue
        
        try:
            # 检查目录是否为空
            if not any(d.iterdir()):
                d.rmdir()
                log_info(f"已删除空目录：{d}")
        except PermissionError:
            log_warn(f"无权限删除目录：{d}")
        except OSError as e:
            log_warn(f"删除目录失败 {d}: {e}")
