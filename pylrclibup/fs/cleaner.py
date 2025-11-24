from __future__ import annotations

from pathlib import Path


def cleanup_empty_dirs(root: Path) -> None:
    """
    从 root 开始向下递归删除空目录（保留 root 本身）。
    """

    if not root.exists():
        return

    # 按目录深度从深到浅排序
    dirs = sorted(
        (p for p in root.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )

    for d in dirs:
        try:
            # if empty
            if not any(d.iterdir()):
                d.rmdir()
        except Exception:
            # 非空或无权限，忽略
            pass
