# ===== pylrclibup/logging_utils.py（移除 translate 参数）=====

"""
pylrclibup 统一日志模块
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取或创建全局 logger 实例"""
    global _logger
    if _logger is None:
        _logger = _setup_logger()
    return _logger


def _setup_logger(
    name: str = "pylrclibup",
    level: int = logging.INFO,
) -> logging.Logger:
    """初始化并配置 logger"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    logger.propagate = False
    
    return logger


def set_log_level(level: int) -> None:
    """动态设置日志级别"""
    get_logger().setLevel(level)


# -------------------- 便捷函数（调用方需自行翻译）--------------------


def log_info(msg: str) -> None:
    """输出 INFO 级别日志（调用方需使用 _() 包裹中文）"""
    get_logger().info(msg)


def log_warn(msg: str) -> None:
    """输出 WARNING 级别日志（调用方需使用 _() 包裹中文）"""
    get_logger().warning(msg)


def log_error(msg: str) -> None:
    """输出 ERROR 级别日志（调用方需使用 _() 包裹中文）"""
    get_logger().error(msg)


def log_debug(msg: str) -> None:
    """输出 DEBUG 级别日志（调用方需使用 _() 包裹中文）"""
    get_logger().debug(msg)
