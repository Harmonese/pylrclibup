from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from ..config import AppConfig


@dataclass
class FsPaths:
    """
    根据 AppConfig 构建所有相关路径。

    使用：
        paths = FsPaths.from_config(config)
        paths.tracks_dir
        paths.lrc_dir
        paths.done_tracks_dir
        paths.done_lrc_dir
    """

    root: Path
    tracks_dir: Path
    lrc_dir: Path
    done_tracks_dir: Path
    done_lrc_dir: Path

    @classmethod
    def from_config(cls, config: AppConfig) -> "FsPaths":
        tracks = Path(config.tracks_dir).resolve()
        lrcs = Path(config.lrc_dir).resolve()
        done_tracks = Path(config.done_tracks_dir).resolve()
        done_lrcs = Path(config.done_lrc_dir).resolve()

        # 随便给 root 一个公共前缀（可选）
        root = tracks.parent

        for d in (tracks, lrcs, done_tracks, done_lrcs):
            d.mkdir(parents=True, exist_ok=True)

        return cls(
            root=root,
            tracks_dir=tracks,
            lrc_dir=lrcs,
            done_tracks_dir=done_tracks,
            done_lrc_dir=done_lrcs,
        )
