# ===== lrc/parser.py（完整 i18n 版本）=====

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..logging_utils import log_warn, log_error
from ..i18n import get_text as _


# -------------------- 文本规范化 --------------------


def normalize_name(s: str) -> str:
    """
    增强版规范化：支持多语言
    """
    s = s.strip().lower()
    
    # Unicode 规范化
    s = unicodedata.normalize('NFKC', s)
    
    # 西里尔字母映射
    cyrillic_map = {
        'ё': 'е',
        'і': 'и',
        'ї': 'и',
        'є': 'е',
        'ґ': 'г',
    }
    for old, new in cyrillic_map.items():
        s = s.replace(old, new)
    
    # 全角标点替换
    replacements = {
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "：": ":",
        "。": ".",
        "，": ",",
        "！": "!",
        "？": "?",
        "＆": "&",
        "／": "/",
        "；": ";",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    
    # 移除零宽字符和控制字符（保留空格）
    s = ''.join(ch for ch in s if unicodedata.category(ch)[0] not in ('C', 'Z') or ch == ' ')
    
    # 合并多余空格
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# -------------------- LRC 内容解析 --------------------

# 标准时间标签
TIMESTAMP_RE = re.compile(r"\[\d{2}:\d{2}\.\d{2,3}\]")

# 扩展时间标签
EXTENDED_TIMESTAMP_RE = re.compile(r"\[\d{2}:\d{2}(?:\.\d{1,3}(?:-\d{1,3})?)?\]")

# LRC 头部标签
HEADER_TAG_RE = re.compile(r"^\[[a-zA-Z]{2,3}:.+\]$")

# NCM 常见 credit 关键字
CREDIT_KEYWORDS = (
    "作词", "作曲", "编曲", "混音", "缩混", "录音", "母带", "制作", "监制", "和声", 
    "配唱", "制作人", "演唱", "伴奏", "编配", "吉他", "贝斯", "鼓", "键盘", "弦乐", 
    "制作团队", "打击乐", "采样", "音效", "人声", "合成器", "录音师", "混音师", "编曲师",
    "出品", "发行", "企划", "统筹", "后期", "音乐总监"
)

CREDIT_RE = re.compile(
    rf"^({'|'.join(re.escape(k) for k in CREDIT_KEYWORDS)})\s*[:：]\s*.+$"
)

# "纯音乐，请欣赏"类提示关键字
PURE_MUSIC_PHRASES = (
    "纯音乐，请欣赏",
    "纯音乐, 请欣赏",
    "纯音乐 请欣赏",
    "此歌曲为没有填词的纯音乐",
    "instrumental",
)


@dataclass
class ParsedLRC:
    """
    LRC 解析结果：
      - synced: 带时间戳的 LRC 内容（已标准化）
      - plain: 纯文本歌词（不包含时间标签）
      - is_instrumental: 是否检测到"纯音乐"性质
    """
    synced: str
    plain: str
    is_instrumental: bool


def read_text_any(path: Path) -> str:
    """
    尝试多种编码读取文本文件
    """
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _contains_cjk(text: str) -> bool:
    """粗略判断文本是否包含中日韩文字"""
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]', text))


def parse_lrc_file(path: Path, *, remove_translations: bool = True) -> ParsedLRC:
    """
    增强版 LRC 解析（带容错处理）
    
    Args:
        path: LRC 文件路径
        remove_translations: 是否删除重复时间戳的翻译行（默认 True）
    
    Returns:
        ParsedLRC(synced, plain, is_instrumental)
    """
    # 容错：读取文件失败
    try:
        raw = read_text_any(path)
    except Exception as e:
        log_error(_("读取 LRC 文件失败 {path}: {error}").format(path=path, error=str(e)))
        return ParsedLRC(synced="", plain="", is_instrumental=False)
    
    # 容错：检查是否有有效时间戳
    if not TIMESTAMP_RE.search(raw):
        log_warn(_("LRC 文件无有效时间戳: {path}").format(path=path))
        return ParsedLRC(synced="", plain="", is_instrumental=False)
    
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    
    synced_lines: List[str] = []
    plain_lines: List[str] = []
    is_instrumental = False
    
    started = False
    prev_timestamp: Optional[str] = None
    
    for line in raw.splitlines():
        s = line.strip()
        
        # 阶段 1: 删除歌词头
        if not started:
            if TIMESTAMP_RE.match(s):
                started = True
            else:
                continue
        
        # 阶段 2: 处理已开始的歌词内容
        
        # 空行
        if not s:
            synced_lines.append("")
            plain_lines.append("")
            prev_timestamp = None
            continue
        
        # LRC 头部标签
        if HEADER_TAG_RE.match(s):
            synced_lines.append(line)
            prev_timestamp = None
            continue
        
        # 提取时间戳和歌词文本
        timestamp_match = EXTENDED_TIMESTAMP_RE.match(s)
        
        if timestamp_match:
            current_timestamp = timestamp_match.group(0)
            text_no_tag = s[len(current_timestamp):].strip()
            
            # 检测"纯音乐，请欣赏"
            if text_no_tag and any(p in text_no_tag for p in PURE_MUSIC_PHRASES):
                is_instrumental = True
                prev_timestamp = None
                continue
            
            # 检测 credit 信息
            if text_no_tag and CREDIT_RE.match(text_no_tag):
                prev_timestamp = None
                continue
            
            # 检测中文翻译行
            if remove_translations and prev_timestamp == current_timestamp:
                if _contains_cjk(text_no_tag):
                    continue
            
            # 正常歌词行
            synced_lines.append(line)
            plain_lines.append(text_no_tag)
            prev_timestamp = current_timestamp
        
        else:
            synced_lines.append(line)
            if s:
                plain_lines.append(s)
            prev_timestamp = None
    
    # 清理 plain 顶部/尾部的空行
    while plain_lines and not plain_lines[0]:
        plain_lines.pop(0)
    while plain_lines and not plain_lines[-1]:
        plain_lines.pop()
    
    synced = "\n".join(synced_lines)
    plain = "\n".join(plain_lines)
    
    return ParsedLRC(
        synced=synced,
        plain=plain,
        is_instrumental=is_instrumental,
    )


def write_lrc_file(path: Path, content: str) -> bool:
    """
    将标准化后的 LRC 内容写回文件（使用 UTF-8 编码）
    """
    try:
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        log_error(_("写入 LRC 文件失败 {path}: {error}").format(path=path, error=str(e)))
        return False


def cleanse_lrc_file(path: Path) -> bool:
    """
    标准化 LRC 文件（in-place）
    
    等价于：
        parsed = parse_lrc_file(path)
        write_lrc_file(path, parsed.synced)
    
    Args:
        path: LRC 文件路径
    
    Returns:
        是否成功标准化
    """
    try:
        parsed = parse_lrc_file(path)
        return write_lrc_file(path, parsed.synced)
    except Exception as e:
        log_error(_("标准化 LRC 文件失败 {path}: {error}").format(path=path, error=str(e)))
        return False
