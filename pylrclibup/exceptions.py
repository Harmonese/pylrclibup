from __future__ import annotations


class PylrclibupError(Exception):
    """包内自定义异常的基类。"""


class NetworkError(PylrclibupError):
    """表示网络相关错误（如多次重试仍失败）。"""


class PublishTokenError(PylrclibupError):
    """获取或验证发布 Token 失败。"""


class PoWError(PylrclibupError):
    """PoW 求解失败或 challenge 数据异常。"""


class ApiResponseError(PylrclibupError):
    """LRCLIB API 返回了非预期的响应。"""


class LrcNotFoundError(PylrclibupError):
    """为某首歌找不到对应的 LRC 文件。"""

class ApiError(PylrclibupError):
    """API 调用相关异常"""
    pass

class ConfigError(PylrclibupError):
    """配置相关异常"""
    pass

class LrcParseError(PylrclibupError):
    """LRC 解析相关异常"""
    pass

class InstrumentalDetected(PylrclibupError):
    """
    标记解析过程中检测到纯音乐。
    在某些高级用法下，可能希望通过异常来中断普通歌词流程。
    """
