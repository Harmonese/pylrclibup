# ===== __init__.py =====

"""
pylrclibup

A tool to upload local LRC lyrics / instrumental markers to LRCLIB.net,
based on track metadata from your music library (e.g. Jellyfin + MusicBrainz Picard).
"""

from .config import AppConfig
from .logging_utils import get_logger, set_log_level, log_info, log_warn, log_error

__all__ = [
    "AppConfig",
    "get_logger",
    "set_log_level",
    "log_info",
    "log_warn",
    "log_error",
]

__version__ = "0.3.0"