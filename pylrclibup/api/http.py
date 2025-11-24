from __future__ import annotations

import time
from typing import Optional, Dict, Any

import requests
from requests import RequestException

from ..config import AppConfig


def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _log_error(msg: str) -> None:
    print(f"[ERROR] {msg}")


def http_request_json(
    config: AppConfig,
    method: str,
    url: str,
    label: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 20,
    max_retries: Optional[int] = None,
    treat_404_as_none: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    封装 GET / POST JSON 请求的通用函数：

    - 遵循 config.max_http_retries 进行重试
    - 对网络异常 / 5xx 做自动重试
    - 404 可选视为 None
    - 其余 4xx 报错后不重试
    """
    retries = max_retries if max_retries is not None else config.max_http_retries

    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=timeout,
                headers={"User-Agent": config.user_agent},
            )
        except RequestException as e:
            _log_warn(f"{label} 调用失败（第 {attempt}/{retries} 次自动重试）: {e}")
            if attempt == retries:
                return None
            time.sleep(1)
            continue

        # 特殊处理 404
        if resp.status_code == 404 and treat_404_as_none:
            return None

        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except ValueError as e:
                _log_warn(
                    f"{label} 解析 JSON 失败: {e} "
                    f"(status={resp.status_code}, body={resp.text[:200]!r})"
                )
                return None

        # 4xx 默认认为是参数/认证问题，不重试
        if 400 <= resp.status_code < 500:
            _log_warn(
                f"{label} 请求失败：HTTP {resp.status_code}, body={resp.text[:200]!r}"
            )
            return None

        # 5xx → 重试
        _log_warn(
            f"{label} 请求失败：HTTP {resp.status_code}, "
            f"body={resp.text[:200]!r}（第 {attempt}/{retries} 次自动重试）"
        )
        if attempt == retries:
            return None
        time.sleep(1)

    return None
