from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


# -------------------- 文本规范化 --------------------


def normalize_name(s: str) -> str:
    """
    一般用于艺人名 / 歌曲名等的轻度规范化：
      - 去首尾空白
      - 降为小写
      - 将常见全角标点替换为半角
      - 合并多余空格
    """
    s = s.strip().lower()
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
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s)
    return s


# -------------------- LRC 内容解析 --------------------

# 时间标签：
#   [mm:ss.xxx] / [mm:ss.xx] / [mm:ss.x] / [mm:ss.xxx-1] 等
TIMESTAMP_RE = re.compile(
    r"\[\d{2}:\d{2}(?:\.\d{1,3}(?:-\d{1,3})?)?\]"
)

# LRC 头部标签，如 [ar:xxx] / [ti:xxx]
HEADER_TAG_RE = re.compile(r"^\[[a-zA-Z]{2,3}:.+\]$")

# NCM 常见 credit 关键字
CREDIT_KEYWORDS = (
    "作词", "作曲", "编曲",
    "混音", "缩混", "录音",
    "母带", "制作", "监制",
    "和声", "配唱",
)

# 匹配形如“作词 : xxx”/“作曲：xxx”等，注意支持全角/半角冒号
CREDIT_RE = re.compile(
    rf"^({'|'.join(CREDIT_KEYWORDS)})\s*[:：]\s*.+$"
)

# “纯音乐，请欣赏”类提示关键字
PURE_MUSIC_PHRASES = (
    "纯音乐，请欣赏",
    "纯音乐, 请欣赏",
    "纯音乐 请欣赏",
)


@dataclass
class ParsedLRC:
    """
    LRC 解析结果：
      - synced: 仍带时间戳的 LRC 内容（但已经去掉了 credit / 纯音乐提示等）
      - plain: 纯文本歌词（不包含时间标签）
      - is_instrumental: 是否从 LRC 中检测到“纯音乐”性质
    """

    synced: str
    plain: str
    is_instrumental: bool


def read_text_any(path: Path) -> str:
    """
    尝试多种编码读取文本文件：
      - utf-8-sig
      - utf-8
      - gb18030
    """
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_lrc_file(path: Path) -> ParsedLRC:
    """
    解析 LRC 文件：

    - 保留 LRC 头部标签（[ar:] [ti:] 等）在 synced 中，但不进入 plain
    - 删除 NCM credit 行（作词/作曲/缩混/母带等）
    - 检测包含“纯音乐，请欣赏”类提示 → 标记 is_instrumental=True，同时不保留该行
    - 支持特别格式的时间戳，例如 [00:00.00-1]

    返回 ParsedLRC(synced, plain, is_instrumental)
    """
    raw = read_text_any(path)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")

    synced_lines: List[str] = []
    plain_lines: List[str] = []
    is_instrumental = False

    for line in raw.splitlines():
        s = line.strip()

        # 空行：丢进 synced / plain 里，保持段落结构
        if not s:
            synced_lines.append("")
            plain_lines.append("")
            continue

        # LRC 头部标签：仅保留在 synced
        if HEADER_TAG_RE.match(s):
            synced_lines.append(line)
            continue

        # 去掉所有时间标签，得到纯文本部分
        text_no_tag = TIMESTAMP_RE.sub("", s).strip()

        # 检测“纯音乐，请欣赏”类提示
        if text_no_tag and any(p in text_no_tag for p in PURE_MUSIC_PHRASES):
            is_instrumental = True
            # 这类提示不用出现在 synced / plain 中
            continue

        # 检测 credit：作词/作曲/混音/母带/缩混/录音/制作/监制/和声/配唱 等
        if text_no_tag and CREDIT_RE.match(text_no_tag):
            # 整行丢弃，不保留到 synced / plain
            continue

        # 正常歌词行：保留原始行到 synced，将去掉 timestamp 的内容进入 plain
        synced_lines.append(line)
        plain_lines.append(text_no_tag)

    # 去掉 plain 顶部 / 尾部空行，使展示更干净
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
