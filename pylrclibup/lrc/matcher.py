# ===== lrc/matcher.py（完整 i18n 版本）=====

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
import re

from ..config import AppConfig
from ..model import TrackMeta
from ..i18n import get_text as _
from .parser import normalize_name


# -------------------- 艺人拆分 & 匹配 --------------------


def split_artists(s: str) -> List[str]:
    """
    将艺人字符串拆分成多个 artist
    """
    s = s.lower()
    
    # 处理 feat/featuring
    s = re.sub(r'\bfeat\.?\s+', '<<<SEP>>>', s)
    s = re.sub(r'\bfeaturing\b', '<<<SEP>>>', s)
    
    # 拆分半角逗号
    s = re.sub(r'(?<!\s),(?!\s)', '<<<SEP>>>', s)
    
    # 处理其他分隔符
    for sep in [" x ", " X ", "×"]:
        s = s.replace(sep, '<<<SEP>>>')
    
    for sep in ["&", "和", "/", ";", "、", "，", "､"]:
        s = s.replace(sep, '<<<SEP>>>')
    
    artists = [a.strip() for a in s.split('<<<SEP>>>') if a.strip()]
    
    return list(dict.fromkeys(artists))


def match_artists(mp3_artists: List[str], lrc_artists: List[str]) -> bool:
    """艺人匹配策略"""
    mp3_norm = {normalize_name(a) for a in mp3_artists}
    lrc_norm = {normalize_name(a) for a in lrc_artists}
    return not mp3_norm.isdisjoint(lrc_norm)


# -------------------- LRC 文件名解析 & 匹配 --------------------


def parse_lrc_filename(path: Path) -> Tuple[List[str], str]:
    """从 LRC 文件名解析出 (artists_list, title_norm)"""
    stem = path.stem
    if " - " not in stem:
        return [], ""
    artist_raw, title_raw = stem.split(" - ", 1)
    artists = split_artists(artist_raw)
    title = normalize_name(title_raw)
    return artists, title


def find_lrc_for_track(
    meta: TrackMeta,
    config: AppConfig,
    *,
    interactive: bool = True,
) -> Optional[Path]:
    """
    在 config.lrc_dir 下递归寻找和某首歌曲匹配的 LRC 文件
    """
    meta_title_norm = normalize_name(meta.track)
    meta_artists = split_artists(meta.artist)

    candidates: List[Path] = []

    for p in config.lrc_dir.rglob("*.lrc"):
        lrc_artists, lrc_title_norm = parse_lrc_filename(p)
        if not lrc_title_norm:
            continue

        if lrc_title_norm != meta_title_norm:
            continue

        if match_artists(meta_artists, lrc_artists):
            candidates.append(p)

    if not candidates:
        return None

    if len(candidates) == 1 or not interactive:
        return candidates[0]

    # 多个候选 → 交互选择
    print("\n" + _("匹配到多个歌词文件，请选择："))
    for idx, c in enumerate(candidates, 1):
        print(f"{idx}) {c}")

    while True:
        choice = input(_("请输入 1-{max}: ").format(max=len(candidates))).strip()
        if choice.isdigit():
            i = int(choice)
            if 1 <= i <= len(candidates):
                return candidates[i - 1]
        print(_("输入无效，请重新输入。"))
