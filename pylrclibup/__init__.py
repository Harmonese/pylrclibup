"""
pylrclibup

A tool to upload local LRC lyrics / instrumental markers to LRCLIB.net,
based on track metadata from your music library (e.g. Jellyfin + MusicBrainz Picard).
"""

from .config import AppConfig

__all__ = ["AppConfig"]

__version__ = "0.1.0"
