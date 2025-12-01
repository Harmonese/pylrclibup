# ===== api/http.py（完整 i18n 版本）=====

from __future__ import annotations

import random
import time
from typing import Optional, Dict, Any

import requests
from requests import RequestException

from ..config import AppConfig
from ..logging_utils import log_info, log_warn, log_error
from ..i18n import get_text as _


def _calculate_backoff(attempt: int, base: float = 1.0, max_delay: float = 30.0) -> float:
    """
    计算指数退避延迟时间（带抖动）
    
    Args:
        attempt: 当前重试次数（从 1 开始）
        base: 基础延迟时间
        max_delay: 最大延迟时间
    
    Returns:
        延迟秒数
    """
    delay = min(base * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)
    return delay


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
    - 对网络异常 / 5xx 做自动重试（使用指数退避）
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
            backoff = _calculate_backoff(attempt)
            log_warn(
                _("{label} 调用失败（第 {attempt}/{retries} 次），等待 {backoff:.1f}s 后重试: {error}").format(
                    label=label,
                    attempt=attempt,
                    retries=retries,
                    backoff=backoff,
                    error=str(e)
                )
            )
            if attempt == retries:
                return None
            time.sleep(backoff)
            continue

        # 特殊处理 404
        if resp.status_code == 404 and treat_404_as_none:
            return None

        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except ValueError as e:
                log_warn(
                    _("{label} 解析 JSON 失败: {error} (status={status}, body={body})").format(
                        label=label,
                        error=str(e),
                        status=resp.status_code,
                        body=resp.text[:200]
                    )
                )
                return None

        # 4xx 默认认为是参数/认证问题，不重试
        if 400 <= resp.status_code < 500:
            log_warn(
                _("{label} 请求失败：HTTP {status}, body={body}").format(
                    label=label,
                    status=resp.status_code,
                    body=resp.text[:200]
                )
            )
            return None

        # 5xx → 重试
        backoff = _calculate_backoff(attempt)
        log_warn(
            _("{label} 请求失败：HTTP {status}, body={body}（第 {attempt}/{retries} 次），等待 {backoff:.1f}s 后重试").format(
                label=label,
                status=resp.status_code,
                body=resp.text[:200],
                attempt=attempt,
                retries=retries,
                backoff=backoff
            )
        )
        if attempt == retries:
            return None
        time.sleep(backoff)

    return None
