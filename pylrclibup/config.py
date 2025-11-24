from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# -------------------- 常量（全局配置） --------------------

# LRCLIB API 根地址
LRCLIB_BASE = "https://lrclib.net/api"

# 预览歌词时显示的最大行数
PREVIEW_LINES_DEFAULT = 10

# HTTP 调用最大自动重试次数
MAX_HTTP_RETRIES_DEFAULT = 5

# 默认 User-Agent（可以在 CLI 里加个选项覆盖）
DEFAULT_USER_AGENT = "pylrclibup/0.1 (https://github.com/yourname/pylrclibup)"


# -------------------- AppConfig --------------------


@dataclass
class AppConfig:
    """
    全局配置对象：

    - tracks_dir: MP3 输入目录
    - lrc_dir: LRC 输入目录
    - done_tracks_dir: MP3 输出目录
    - done_lrc_dir: LRC 输出目录
    - preview_lines: 预览歌词时显示的最大行数
    - max_http_retries: HTTP 自动重试次数
    - user_agent: 发送给 LRCLIB 的 User-Agent
    """

    tracks_dir: Path
    lrc_dir: Path
    done_tracks_dir: Path
    done_lrc_dir: Path

    preview_lines: int = PREVIEW_LINES_DEFAULT
    max_http_retries: int = MAX_HTTP_RETRIES_DEFAULT
    user_agent: str = DEFAULT_USER_AGENT

    lrclib_base: str = LRCLIB_BASE

    pair_lrc_with_track_dir: bool = False

    @classmethod
    def from_env_and_defaults(
        cls,
        *,
        tracks_dir: Optional[str | Path] = None,
        lrc_dir: Optional[str | Path] = None,
        done_tracks_dir: Optional[str | Path] = None,
        done_lrc_dir: Optional[str | Path] = None,
        preview_lines: Optional[int] = None,
        max_http_retries: Optional[int] = None,
        user_agent: Optional[str] = None,
        pair_lrc_with_track_dir: bool = False,
    ) -> "AppConfig":
        """
        统一入口：综合考虑
          1. 显式传入（通常来自 CLI 参数）
          2. 环境变量
          3. 默认值

        优先级：参数 > 环境变量 > 默认
        """

        # ---- 路径类配置 ----
        # 默认基于当前工作目录（而不是包所在目录）
        cwd = Path.cwd()

        # 环境变量
        env_tracks = os.getenv("PYLRCLIBUP_TRACKS_DIR")
        env_lrc = os.getenv("PYLRCLIBUP_LRC_DIR")
        env_done_tracks = os.getenv("PYLRCLIBUP_DONE_TRACKS_DIR")
        env_done_lrc = os.getenv("PYLRCLIBUP_DONE_LRC_DIR")

        tracks = Path(
            tracks_dir
            or env_tracks
            or cwd / "tracks"
        )
        lrc = Path(
            lrc_dir
            or env_lrc
            or cwd / "lrc-files"
        )
        done_tracks = Path(
            done_tracks_dir
            or env_done_tracks
            or cwd / "done-tracks"
        )
        done_lrc = Path(
            done_lrc_dir
            or env_done_lrc
            or cwd / "done-lrc-files"
        )

        # ---- 数值配置 ----
        if preview_lines is None:
            # 若未显式指定，允许通过环境变量覆盖
            env_preview = os.getenv("PYLRCLIBUP_PREVIEW_LINES")
            if env_preview and env_preview.isdigit():
                preview_lines_val = int(env_preview)
            else:
                preview_lines_val = PREVIEW_LINES_DEFAULT
        else:
            preview_lines_val = preview_lines

        if max_http_retries is None:
            env_retries = os.getenv("PYLRCLIBUP_MAX_HTTP_RETRIES")
            if env_retries and env_retries.isdigit():
                max_http_retries_val = int(env_retries)
            else:
                max_http_retries_val = MAX_HTTP_RETRIES_DEFAULT
        else:
            max_http_retries_val = max_http_retries

        # ---- User-Agent ----
        ua = user_agent or os.getenv("PYLRCLIBUP_USER_AGENT") or DEFAULT_USER_AGENT

        return cls(
            tracks_dir=tracks,
            lrc_dir=lrc,
            done_tracks_dir=done_tracks,
            done_lrc_dir=done_lrc,
            preview_lines=preview_lines_val,
            max_http_retries=max_http_retries_val,
            user_agent=ua,
            pair_lrc_with_track_dir=pair_lrc_with_track_dir,
        )
