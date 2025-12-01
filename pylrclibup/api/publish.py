# ===== api/publish.py（完整 i18n 版本）=====

from __future__ import annotations

import random
import time
from typing import Optional, Dict, Any

import requests
from requests import RequestException

from ..config import AppConfig
from ..model import TrackMeta
from ..logging_utils import log_info, log_warn, log_error
from ..i18n import get_text as _
from .http import http_request_json
from .pow import solve_pow


# -------------------- Publish Token / PoW --------------------


def request_publish_token(config: AppConfig) -> Optional[str]:
    """
    调用 /api/request-challenge，执行 PoW，返回完整的
      X-Publish-Token = "{prefix}:{nonce}"
    """
    url = f"{config.lrclib_base}/request-challenge"
    data = http_request_json(
        config,
        "POST",
        url,
        _("请求发布令牌 (/api/request-challenge)"),
        treat_404_as_none=False,
    )
    if not data:
        return None

    prefix = data.get("prefix")
    target = data.get("target")
    if not prefix or not target:
        log_error(_("请求发布令牌返回异常数据：{data}").format(data=data))
        return None

    try:
        nonce = solve_pow(prefix, target)
    except Exception as e:
        log_error(_("PoW 求解失败：{error}").format(error=str(e)))
        return None

    return f"{prefix}:{nonce}"


# -------------------- Publish with retry --------------------


def _calculate_backoff(attempt: int, base: float = 1.0, max_delay: float = 30.0) -> float:
    """计算指数退避延迟时间（带抖动）"""
    return min(base * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)


def publish_with_retry(
    config: AppConfig,
    meta: TrackMeta,
    payload: Dict[str, Any],
    label: str,
) -> bool:
    """
    对 /api/publish 做一层自动重试：
      - 每次重试都会重新请求 challenge + 重新 PoW
      - 成功（201）即返回 True
      - 4xx 认为是参数或 Token 问题，不重试
    """
    url = f"{config.lrclib_base}/publish"
    retries = config.max_http_retries

    for attempt in range(1, retries + 1):
        token = request_publish_token(config)
        if not token:
            backoff = _calculate_backoff(attempt)
            log_warn(
                _("{label}：获取发布令牌失败（第 {attempt}/{retries} 次），等待 {backoff:.1f}s 后重试").format(
                    label=label,
                    attempt=attempt,
                    retries=retries,
                    backoff=backoff
                )
            )
            if attempt == retries:
                return False
            time.sleep(backoff)
            continue

        headers = {
            "X-Publish-Token": token,
            "Content-Type": "application/json",
            "User-Agent": config.user_agent,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        except RequestException as e:
            backoff = _calculate_backoff(attempt)
            log_warn(
                _("{label} (/api/publish) 调用失败（第 {attempt}/{retries} 次），等待 {backoff:.1f}s 后重试: {error}").format(
                    label=label,
                    attempt=attempt,
                    retries=retries,
                    backoff=backoff,
                    error=str(e)
                )
            )
            if attempt == retries:
                return False
            time.sleep(backoff)
            continue

        if resp.status_code == 201:
            return True

        # 4xx: 参数/Token 错误，不再重试
        if 400 <= resp.status_code < 500:
            log_error(
                _("{label} 失败：HTTP {status}, body={body}（4xx 错误，一般是参数或 Token 问题，不再重试）").format(
                    label=label,
                    status=resp.status_code,
                    body=resp.text[:200]
                )
            )
            return False

        # 5xx: 重试
        backoff = _calculate_backoff(attempt)
        log_warn(
            _("{label} 失败：HTTP {status}, body={body}（第 {attempt}/{retries} 次），等待 {backoff:.1f}s 后重试").format(
                label=label,
                status=resp.status_code,
                body=resp.text[:200],
                attempt=attempt,
                retries=retries,
                backoff=backoff
            )
        )
        if attempt == retries:
            return False
        time.sleep(backoff)

    return False


# -------------------- Payload 构造 --------------------


def build_payload_for_publish(
    meta: TrackMeta,
    plain: Optional[str],
    synced: Optional[str],
    *,
    force_instrumental: bool = False,
) -> Dict[str, Any]:
    """
    构造 /api/publish 的 JSON
    """
    base: Dict[str, Any] = {
        "trackName": meta.track,
        "artistName": meta.artist,
        "albumName": meta.album,
        "duration": meta.duration,
    }

    if force_instrumental:
        return base

    p = (plain or "").strip()
    s = (synced or "").strip()

    if not p and not s:
        return base

    base["plainLyrics"] = p
    base["syncedLyrics"] = s
    return base


# -------------------- 高阶上传函数 --------------------


def upload_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    plain: str,
    synced: str,
) -> bool:
    payload = build_payload_for_publish(meta, plain, synced, force_instrumental=False)
    return publish_with_retry(config, meta, payload, _("上传歌词"))


def upload_instrumental(config: AppConfig, meta: TrackMeta) -> bool:
    """按"纯音乐曲目"上传"""
    payload = build_payload_for_publish(meta, plain=None, synced=None, force_instrumental=True)
    return publish_with_retry(config, meta, payload, _("上传纯音乐标记"))
