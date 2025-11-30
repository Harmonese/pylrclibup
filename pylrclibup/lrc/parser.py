from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# -------------------- 文本规范化 --------------------


def normalize_name(s: str) -> str:
    """
    增强版规范化：支持多语言
      - 去首尾空白
      - 降为小写
      - 统一西里尔字母变体（如 Ё→Е）
      - Unicode 规范化（NFKC）
      - 替换全角标点
      - 移除零宽字符和控制字符
      - 合并多余空格
    """
    s = s.strip().lower()
    
    # Unicode 规范化
    s = unicodedata.normalize('NFKC', s)
    
    # 西里尔字母映射
    cyrillic_map = {
        'ё': 'е',  # 俄语
        'і': 'и',  # 乌克兰语
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

# 标准时间标签：[mm:ss.xx] 或 [mm:ss.xxx]
TIMESTAMP_RE = re.compile(
    r"\[\d{2}:\d{2}\.\d{2,3}\]"
)

# 扩展时间标签（支持特殊格式如 [00:00.00-1]）
EXTENDED_TIMESTAMP_RE = re.compile(
    r"\[\d{2}:\d{2}(?:\.\d{1,3}(?:-\d{1,3})?)?\]"
)

# LRC 头部标签，如 [ar:xxx] / [ti:xxx]
HEADER_TAG_RE = re.compile(r"^\[[a-zA-Z]{2,3}:.+\]$")

# NCM 常见 credit 关键字（扩展版）
CREDIT_KEYWORDS = (
    "作词", "作曲", "编曲", "混音", "缩混", "录音", "母带", "制作", "监制", "和声", 
    "配唱", "制作人", "演唱", "伴奏", "编配", "吉他", "贝斯", "鼓", "键盘", "弦乐", 
    "制作团队", "打击乐", "采样", "音效", "人声", "合成器", "录音师", "混音师", "编曲师",
    "出品", "发行", "企划", "统筹", "后期", "音乐总监"
)

# 匹配 credit 行：支持全角/半角冒号
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
    尝试多种编码读取文本文件：
      - utf-8-sig（带 BOM）
      - utf-8
      - gb18030（中文）
      - 最后使用 utf-8 并忽略错误
    """
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _contains_cjk(text: str) -> bool:
    """
    粗略判断文本是否包含中日韩文字
    使用 Unicode 范围：
      - 中日韩统一表意文字：\u4E00-\u9FFF
      - 中日韩扩展 A：\u3400-\u4DBF
      - 日文假名：\u3040-\u309F, \u30A0-\u30FF
    """
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]', text))


def parse_lrc_file(path: Path, *, remove_translations: bool = True) -> ParsedLRC:
    """
    增强版 LRC 解析：
    
    新增功能（来自 lrc-standardizer.sh）：
      1. ⭐ 删除歌词头：跳过第一个标准时间戳之前的所有内容
      2. ⭐ 删除中文翻译行：时间戳相同的连续中文行（可选）
    
    原有功能：
      - 保留 LRC 头部标签（[ar:] [ti:] 等）在 synced 中
      - 删除 NCM credit 行（作词/作曲等）
      - 检测"纯音乐，请欣赏"类提示
      - 支持扩展时间戳格式
    
    Args:
        path: LRC 文件路径
        remove_translations: 是否删除重复时间戳的翻译行（默认 True）
    
    Returns:
        ParsedLRC(synced, plain, is_instrumental)
    """
    raw = read_text_any(path)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    
    synced_lines: List[str] = []
    plain_lines: List[str] = []
    is_instrumental = False
    
    # ⭐ 新增：标记是否已遇到第一个标准时间戳
    started = False
    
    # ⭐ 新增：记录上一行的时间戳（用于检测翻译行）
    prev_timestamp: Optional[str] = None
    
    for line in raw.splitlines():
        s = line.strip()
        
        # ========== 阶段 1: 删除歌词头 ==========
        if not started:
            # 检查是否为标准时间戳行
            if TIMESTAMP_RE.match(s):
                started = True
            else:
                # 跳过第一个时间戳之前的所有内容（包括非标准标签）
                continue
        
        # ========== 阶段 2: 处理已开始的歌词内容 ==========
        
        # 空行：保留到 synced/plain（维持段落结构）
        if not s:
            synced_lines.append("")
            plain_lines.append("")
            prev_timestamp = None  # 重置时间戳记录
            continue
        
        # LRC 头部标签（出现在歌词中间的情况，罕见但存在）
        if HEADER_TAG_RE.match(s):
            synced_lines.append(line)
            prev_timestamp = None
            continue
        
        # 提取时间戳和歌词文本
        timestamp_match = EXTENDED_TIMESTAMP_RE.match(s)
        
        if timestamp_match:
            current_timestamp = timestamp_match.group(0)
            text_no_tag = s[len(current_timestamp):].strip()
            
            # ---------- 检测"纯音乐，请欣赏" ----------
            if text_no_tag and any(p in text_no_tag for p in PURE_MUSIC_PHRASES):
                is_instrumental = True
                prev_timestamp = None
                continue
            
            # ---------- 检测 credit 信息 ----------
            if text_no_tag and CREDIT_RE.match(text_no_tag):
                prev_timestamp = None
                continue
            
            # ⭐ ---------- 检测中文翻译行（新增） ----------
            if remove_translations and prev_timestamp == current_timestamp:
                # 时间戳与上一行相同，检查是否为中文
                if _contains_cjk(text_no_tag):
                    # 跳过这一行（视为翻译）
                    continue
            
            # ---------- 正常歌词行 ----------
            synced_lines.append(line)
            plain_lines.append(text_no_tag)
            prev_timestamp = current_timestamp
        
        else:
            # 无时间戳的行（理论上不应出现在标准 LRC 中）
            # 保留，但不记录时间戳
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
    
    Args:
        path: LRC 文件路径
        content: 要写入的内容
    
    Returns:
        bool: 写入成功返回 True，失败返回 False
    """
    try:
        # 统一使用 UTF-8 编码写入
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"[ERROR] 写入 LRC 文件失败 {path}: {e}")
        return False
