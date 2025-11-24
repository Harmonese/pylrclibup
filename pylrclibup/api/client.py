from __future__ import annotations

from typing import Optional

from ..config import AppConfig
from ..model import TrackMeta, LyricsRecord
from .http import http_request_json
from .publish import (
    upload_lyrics as _upload_lyrics_impl,
    upload_instrumental as _upload_instrumental_impl,
)


def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _check_duration(meta: TrackMeta, record: dict, label: str) -> None:
    """
    打印 LRCLIB 返回的 duration 与本地 duration 的差值提示。
    逻辑与之前单文件脚本中的实现一致。
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
        _log_info(
            f"{label} 时长检查：LRCLIB={rec_dur_int}s, "
            f"本地={meta.duration}s, 差值={diff}s（<=2s，符合匹配条件）"
        )
    else:
        _log_warn(
            f"{label} 时长检查：LRCLIB={rec_dur_int}s, "
            f"本地={meta.duration}s, 差值={diff}s（>2s，可能不是同一首）"
        )


class ApiClient:
    """
    高层 API 封装：

    - get_cached()  : 调用 /api/get-cached，只查内部数据库
    - get_external(): 调用 /api/get，会触发 LRCLIB 外部抓取
    - upload_lyrics(): 语义化包装 /api/publish（带歌词）
    - upload_instrumental(): 语义化包装 /api/publish（纯音乐）

    说明：
      * 处理时长 ±2 秒的提示逻辑仍与早期脚本一致。
      * HTTP 重试、User-Agent、基地址等逻辑，全部由 AppConfig 控制，
        具体在 http_request_json() 和 publish.py 中实现。
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    # -------- 内部通用 GET 封装 --------

    def _api_get_common(
        self,
        meta: TrackMeta,
        endpoint: str,
        label: str,
    ) -> Optional[LyricsRecord]:
        """
        通用的 /api/get* 调用逻辑：

        - 使用 track / artist / album / duration 构造 query 参数
        - 调用 http_request_json（带自动重试）
        - 如有返回则包装为 LyricsRecord
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

    # -------- 公共方法：GET cached --------

    def get_cached(self, meta: TrackMeta) -> Optional[LyricsRecord]:
        """
        调用 /api/get-cached：
          - 只查 LRCLIB 内部数据库
          - 不触发外部抓取
          - 未命中返回 None
        """
        return self._api_get_common(meta, "get-cached", "内部数据库 (/api/get-cached)")

    # -------- 公共方法：GET external --------

    def get_external(self, meta: TrackMeta) -> Optional[LyricsRecord]:
        """
        调用 /api/get：
          - 若内部没有，会触发 LRCLIB 对外部来源的抓取
          - 未命中返回 None
        """
        return self._api_get_common(meta, "get", "外部抓取 (/api/get)")

    # -------- 公共方法：上传歌词 / 纯音乐（可选给库用户用） --------

    def upload_lyrics(self, meta: TrackMeta, plain: str, synced: str) -> bool:
        """
        高层包装：上传带 plain+synced 的歌词。
        （processor 层目前直接用 publish.upload_lyrics(config, meta, ...)，
         但如果你想在别处以面向对象方式使用，也可以通过 ApiClient 调用。）
        """
        return _upload_lyrics_impl(self.config, meta, plain, synced)

    def upload_instrumental(self, meta: TrackMeta) -> bool:
        """
        高层包装：以“纯音乐”方式上传（不包含任何歌词文本）。
        """
        return _upload_instrumental_impl(self.config, meta)
