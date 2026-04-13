# ===== pylrclibup/__init__.py =====

"""
pylrclibup

A tool to upload local LRC lyrics / instrumental markers to LRCLIB.net,
based on track metadata from your music library (e.g. Jellyfin + MusicBrainz Picard).
"""

from .config import AppConfig
from .logging_utils import get_logger, set_log_level, log_info, log_warn, log_error
from .i18n import setup_i18n, get_text as _  # 新增

__all__ = [
    "AppConfig",
    "get_logger",
    "set_log_level",
    "log_info",
    "log_warn",
    "log_error",
    "setup_i18n",  # 新增
    "_",            # 新增
]

__version__ = "0.5.5"

# 默认初始化 i18n（自动检测语言）
setup_i18n()
