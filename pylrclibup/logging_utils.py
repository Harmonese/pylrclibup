"""
pylrclibup 统一日志模块

提供全局统一的日志输出接口，替代各模块分散定义的 _log_* 函数。
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


# 全局 logger 实例
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
    """
    初始化并配置 logger
    
    Args:
        name: logger 名称
        level: 日志级别
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # stdout handler（INFO 及以下）
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    
    # stderr handler（ERROR 及以上）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    
    # 阻止向上传播
    logger.propagate = False
    
    return logger


def set_log_level(level: int) -> None:
    """动态设置日志级别"""
    get_logger().setLevel(level)


# -------------------- 便捷函数（保持向后兼容） --------------------


def log_info(msg: str) -> None:
    """输出 INFO 级别日志"""
    get_logger().info(msg)


def log_warn(msg: str) -> None:
    """输出 WARNING 级别日志"""
    get_logger().warning(msg)


def log_error(msg: str) -> None:
    """输出 ERROR 级别日志"""
    get_logger().error(msg)


def log_debug(msg: str) -> None:
    """输出 DEBUG 级别日志"""
    get_logger().debug(msg)
