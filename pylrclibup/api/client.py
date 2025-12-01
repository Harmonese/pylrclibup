# ===== api/client.py（完整 i18n 版本）=====

from __future__ import annotations

from typing import Optional

from ..config import AppConfig
from ..model import TrackMeta, LyricsRecord
from ..logging_utils import log_info, log_warn
from ..i18n import get_text as _
from .http import http_request_json
from .publish import (
    upload_lyrics as _upload_lyrics_impl,
    upload_instrumental as _upload_instrumental_impl,
)


def _check_duration(meta: TrackMeta, record: dict, label: str) -> None:
    """
    打印 LRCLIB 返回的 duration 与本地 duration 的差值提示。
    """
    rec_dur = record.get("duration")
    if rec_dur is None:
        return

    try:
        rec_dur_int = int(round(float(rec_dur)))
    except Exception:
        return

    diff = abs(rec_dur_int - meta.duration)
    if diff <= 2:
        log_info(
            _("{label} 时长检查：LRCLIB={rec_dur}s, 本地={local_dur}s, 差值={diff}s（<=2s，符合匹配条件）").format(
                label=label,
                rec_dur=rec_dur_int,
                local_dur=meta.duration,
                diff=diff
            )
        )
    else:
        log_warn(
            _("{label} 时长检查：LRCLIB={rec_dur}s, 本地={local_dur}s, 差值={diff}s（>2s，可能不是同一首）").format(
                label=label,
                rec_dur=rec_dur_int,
                local_dur=meta.duration,
                diff=diff
            )
        )


class ApiClient:
    """
    高层 API 封装：

    - get_cached()  : 调用 /api/get-cached，只查内部数据库
    - get_external(): 调用 /api/get，会触发 LRCLIB 外部抓取
    - upload_lyrics(): 语义化包装 /api/publish（带歌词）
    - upload_instrumental(): 语义化包装 /api/publish（纯音乐）
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def _api_get_common(
        self,
        meta: TrackMeta,
        endpoint: str,
        label: str,
    ) -> Optional[LyricsRecord]:
        """
        通用的 /api/get* 调用逻辑
        """
        params = {
            "track_name": meta.track,
            "artist_name": meta.artist,
            "album_name": meta.album,
            "duration": meta.duration,
        }

        url = f"{self.config.lrclib_base}/{endpoint}"

        data = http_request_json(
            self.config,
            method="GET",
            url=url,
            label=label,
            params=params,
        )
        if not data:
            return None

        _check_duration(meta, data, label)
        return LyricsRecord.from_api(data)

    def get_cached(self, meta: TrackMeta) -> Optional[LyricsRecord]:
        """
        调用 /api/get-cached：只查 LRCLIB 内部数据库
        """
        return self._api_get_common(meta, "get-cached", _("内部数据库 (/api/get-cached)"))

    def get_external(self, meta: TrackMeta) -> Optional[LyricsRecord]:
        """
        调用 /api/get：会触发 LRCLIB 对外部来源的抓取
        """
        return self._api_get_common(meta, "get", _("外部抓取 (/api/get)"))

    def upload_lyrics(self, meta: TrackMeta, plain: str, synced: str) -> bool:
        """高层包装：上传带 plain+synced 的歌词"""
        return _upload_lyrics_impl(self.config, meta, plain, synced)

    def upload_instrumental(self, meta: TrackMeta) -> bool:
        """高层包装：以"纯音乐"方式上传"""
        return _upload_instrumental_impl(self.config, meta)
