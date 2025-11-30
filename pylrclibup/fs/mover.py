from __future__ import annotations

from pathlib import Path
from typing import Optional

def move_with_dedup(src: Path, dst_dir: Path, *, new_name: Optional[str] = None) -> Path | None:
    """
    将 src 移动到 dst_dir，若同名文件已存在，则自动添加 _dup 后缀。

    返回最终路径；若失败返回 None。
    """
    try:
        dst_dir.mkdir(parents=True, exist_ok=True)
        target = dst_dir / src.name

        if new_name:
            target = dst_dir / f"{new_name}{src.suffix}"
        else:
            target = dst_dir / src.name
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

        src.rename(target)
        return target

    except Exception as e:
        print(f"[WARN] 移动文件失败：{src} → {dst_dir}：{e}")
        return None
