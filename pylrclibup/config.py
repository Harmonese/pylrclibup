# ===== config.py（新增常量 + 更新注释）=====

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

# 默认 User-Agent
DEFAULT_USER_AGENT = "pylrclibup (https://github.com/Harmonese/pylrclibup)"

# 支持的音频文件扩展名
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".flac", ".wav"}

# 支持的 YAML 元数据扩展名
SUPPORTED_YAML_EXTENSIONS = {".yaml", ".yml"}

# -------------------- AppConfig --------------------


@dataclass
class AppConfig:
    """
    全局配置对象：

    路径配置：
    - tracks_dir: 音频文件输入目录
    - lrc_dir: LRC 输入目录
    - done_tracks_dir: 音频文件输出目录（None = 原地不动）
    - done_lrc_dir: LRC 输出目录（None = 原地不动或跟随音频文件）

    行为配置（三个独立的布尔标志）：
    - follow_mp3: LRC 是否跟随音频文件到同一目录（保持旧名兼容性）
    - rename_lrc: 处理后是否将 LRC 重命名为与音频文件同名
    - cleanse_lrc: 处理前是否标准化 LRC 文件

    其他配置：
    - preview_lines: 预览歌词时显示的最大行数
    - max_http_retries: HTTP 自动重试次数
    - user_agent: 发送给 LRCLIB 的 User-Agent
    """

    tracks_dir: Path
    lrc_dir: Path
    done_tracks_dir: Optional[Path]
    done_lrc_dir: Optional[Path]

    follow_mp3: bool = False  # 保持旧名兼容性，实际含义是"跟随音频文件"
    rename_lrc: bool = False
    cleanse_lrc: bool = False

    preview_lines: int = PREVIEW_LINES_DEFAULT
    max_http_retries: int = MAX_HTTP_RETRIES_DEFAULT
    user_agent: str = DEFAULT_USER_AGENT

    lrclib_base: str = LRCLIB_BASE

    # -------------------- 便捷属性（向后兼容） --------------------

    @property
    def pair_lrc_with_track_dir(self) -> bool:
        """向后兼容：-d 模式 = follow + rename + cleanse"""
        return self.follow_mp3 and self.rename_lrc and self.cleanse_lrc

    @property
    def match_mode(self) -> bool:
        """向后兼容：-m 模式 = follow + rename + cleanse"""
        return self.follow_mp3 and self.rename_lrc and self.cleanse_lrc

    @property
    def keep_in_place(self) -> bool:
        """向后兼容：是否为原地模式"""
        return self.done_tracks_dir is None and self.done_lrc_dir is None and not self.follow_mp3

    # -------------------- 工厂方法 --------------------

    @classmethod
    def from_env_and_defaults(
        cls,
        *,
        tracks_dir: Optional[str | Path] = None,
        lrc_dir: Optional[str | Path] = None,
        done_tracks_dir: Optional[str | Path] = None,
        done_lrc_dir: Optional[str | Path] = None,
        follow_mp3: bool = False,
        rename_lrc: bool = False,
        cleanse_lrc: bool = False,
        preview_lines: Optional[int] = None,
        max_http_retries: Optional[int] = None,
        user_agent: Optional[str] = None,
    ) -> "AppConfig":
        """
        统一入口：综合考虑
        1. 显式传入（通常来自 CLI 参数）
        2. 环境变量
        3. 默认值

        优先级：参数 > 环境变量 > 默认
        """
        # 解析输入目录
        tracks, lrc = cls._resolve_input_dirs(tracks_dir, lrc_dir)
        
        # 解析输出目录
        done_tracks, done_lrc = cls._resolve_output_dirs(
            done_tracks_dir, done_lrc_dir
        )
        
        # 解析数值配置
        preview_lines_val, max_retries_val = cls._resolve_numeric_config(
            preview_lines, max_http_retries
        )
        
        # 解析 User-Agent
        ua = user_agent or os.getenv("PYLRCLIBUP_USER_AGENT") or DEFAULT_USER_AGENT

        return cls(
            tracks_dir=tracks,
            lrc_dir=lrc,
            done_tracks_dir=done_tracks,
            done_lrc_dir=done_lrc,
            follow_mp3=follow_mp3,
            rename_lrc=rename_lrc,
            cleanse_lrc=cleanse_lrc,
            preview_lines=preview_lines_val,
            max_http_retries=max_retries_val,
            user_agent=ua,
        )

    @staticmethod
    def _resolve_input_dirs(
        tracks_dir: Optional[str | Path],
        lrc_dir: Optional[str | Path],
    ) -> tuple[Path, Path]:
        """解析输入目录（tracks 和 lrc）"""
        cwd = Path.cwd()
        
        env_tracks = os.getenv("PYLRCLIBUP_TRACKS_DIR")
        env_lrc = os.getenv("PYLRCLIBUP_LRC_DIR")
        
        tracks = Path(tracks_dir or env_tracks or cwd)
        lrc = Path(lrc_dir or env_lrc or cwd)
        
        return tracks, lrc

    @staticmethod
    def _resolve_output_dirs(
        done_tracks_dir: Optional[str | Path],
        done_lrc_dir: Optional[str | Path],
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        解析输出目录
        
        返回 None 表示原地不动（或跟随音频文件，由 follow_mp3 决定）
        
        Returns:
            (done_tracks, done_lrc)
        """
        env_done_tracks = os.getenv("PYLRCLIBUP_DONE_TRACKS_DIR")
        env_done_lrc = os.getenv("PYLRCLIBUP_DONE_LRC_DIR")
        
        # 设置 done 目录（None 表示原地不动）
        done_tracks = None
        if done_tracks_dir:
            done_tracks = Path(done_tracks_dir)
        elif env_done_tracks:
            done_tracks = Path(env_done_tracks)
        
        done_lrc = None
        if done_lrc_dir:
            done_lrc = Path(done_lrc_dir)
        elif env_done_lrc:
            done_lrc = Path(env_done_lrc)
        
        return done_tracks, done_lrc

    @staticmethod
    def _resolve_numeric_config(
        preview_lines: Optional[int],
        max_http_retries: Optional[int],
    ) -> tuple[int, int]:
        """解析数值类配置"""
        # preview_lines
        if preview_lines is None:
            env_preview = os.getenv("PYLRCLIBUP_PREVIEW_LINES")
            if env_preview and env_preview.isdigit():
                preview_lines_val = int(env_preview)
            else:
                preview_lines_val = PREVIEW_LINES_DEFAULT
        else:
            preview_lines_val = preview_lines
        
        # max_http_retries
        if max_http_retries is None:
            env_retries = os.getenv("PYLRCLIBUP_MAX_HTTP_RETRIES")
            if env_retries and env_retries.isdigit():
                max_retries_val = int(env_retries)
            else:
                max_retries_val = MAX_HTTP_RETRIES_DEFAULT
        else:
            max_retries_val = max_http_retries
        
        return preview_lines_val, max_retries_val
