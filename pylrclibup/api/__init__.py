"""
API 模块：与 LRCLIB 交互
"""

from .client import ApiClient
from .publish import upload_lyrics, upload_instrumental

__all__ = [
    "ApiClient",
    "upload_lyrics",
    "upload_instrumental",
]
