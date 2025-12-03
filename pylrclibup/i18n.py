# ===== pylrclibup/i18n.py（智能默认语言版本）=====

"""
国际化 (i18n) 支持模块
"""

import gettext
import os
import locale as system_locale
from pathlib import Path
from typing import Optional, Callable

# 全局翻译函数（类型注解）
_translate: Callable[[str], str] = lambda x: x


def setup_i18n(
    locale: Optional[str] = None,
    localedir: Optional[Path] = None,
) -> None:
    """
    初始化国际化支持
    
    Args:
        locale: 语言代码（如 'en_US'、'zh_CN'），None 则自动检测
        localedir: 翻译文件目录，None 则使用默认位置
    """
    global _translate
    
    # 默认翻译文件位置
    if localedir is None:
        localedir = Path(__file__).parent / "locales"
    
    # 自动检测语言
    if locale is None:
        locale = _detect_locale()
    
    # 只有中文环境才使用源码（中文）
    if locale.startswith('zh'):
        _translate = lambda x: x
        return
    
    # 非中文环境：尝试加载英文翻译
    try:
        translation = gettext.translation(
            domain='pylrclibup',
            localedir=str(localedir),
            languages=[locale, 'en_US', 'en'],  # fallback chain
            fallback=False,
        )
        _translate = translation.gettext
    except (FileNotFoundError, OSError):
        # 翻译文件不存在，fallback 中文（返回原始 key）
        # 由于源码是中文，这里实际会显示中文
        # 所以我们需要确保 en_US 翻译文件存在
        _translate = lambda x: x


def _detect_locale() -> str:
    """
    自动检测系统语言
    
    检测策略（优先级从高到低）：
    1. 环境变量 PYLRCLIBUP_LANG（用户显式指定）
    2. 环境变量 LANG / LC_ALL / LC_MESSAGES（系统环境）
    3. Python locale 模块检测
    4. ⭐ 默认英语（国际化项目的最佳实践）
    
    Returns:
        语言代码（如 'en_US', 'zh_CN'）
    """
    # 1. 用户显式指定
    if pylrclib_lang := os.getenv('PYLRCLIBUP_LANG'):
        return pylrclib_lang
    
    # 2. 系统环境变量
    for var in ['LANG', 'LC_ALL', 'LC_MESSAGES']:
        if lang := os.getenv(var):
            # 处理格式：en_US.UTF-8 → en_US
            return lang.split('.')[0]
    
    # 3. 使用 Python locale 模块检测
    try:
        detected = system_locale.getdefaultlocale()[0]
        if detected:
            return detected
    except Exception:
        pass
    
    # 4. 默认英语
    return 'en_US'


def get_text(message: str) -> str:
    """获取翻译后的文本"""
    return _translate(message)


# 导出便捷别名
_ = get_text
