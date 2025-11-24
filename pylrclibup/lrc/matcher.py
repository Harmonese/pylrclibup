from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from ..config import AppConfig
from ..model import TrackMeta
from .parser import normalize_name


# -------------------- 艺人拆分 & 匹配 --------------------


def split_artists(s: str) -> List[str]:
    """
    将艺人字符串拆分成多个 artist：
      - 支持 "feat." / "featuring" 作为分隔符
      - 支持 "&"、"和"、"/"、";"、"、"、" x " / " X " / "×"
      - 将各种逗号/间隔统一整理
    """
    import re

    s = s.lower()
    # 把 feat/featuring 先转成逗号
    s = re.sub(r"\bfeat\.?\b", ",", s)
    s = re.sub(r"\bfeaturing\b", ",", s)

    # 其他分隔符也统一转成逗号
    for sep in ["&", "和", "/", ";", "、", " x ", " X ", "×"]:
        s = s.replace(sep, ",")

    # 一些特殊逗号/间隔
    for sep in ["，", "､"]:
        s = s.replace(sep, ",")

    artists = [a.strip() for a in s.split(",") if a.strip()]
    # 去重保持顺序
    return list(dict.fromkeys(artists))


def match_artists(mp3_artists: List[str], lrc_artists: List[str]) -> bool:
    """
    艺人匹配策略：
      - 对双方艺人列表 normalize
      - 只要有任意一个艺人名相等 → 认为匹配成功
    """
    mp3_norm = {normalize_name(a) for a in mp3_artists}
    lrc_norm = {normalize_name(a) for a in lrc_artists}
    return not mp3_norm.isdisjoint(lrc_norm)


# -------------------- LRC 文件名解析 & 匹配 --------------------


def parse_lrc_filename(path: Path) -> Tuple[List[str], str]:
    """
    从 LRC 文件名解析出 (artists_list, title_norm)。

    约定格式为：
      "Artist - Title.lrc"

    例如：
      "A & B - Song.lrc"
    会解析为：
      (["a", "b"], "song")

    注意：这里不对 " - " 做任何过滤，这个分隔符是稳定可靠的。
    """
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
    在 config.lrc_dir 下递归寻找和某首歌曲匹配的 LRC 文件。

    匹配规则：
      1. 从 MP3 的 meta.track / meta.artist 获取歌名和艺人
      2. 将歌名 normalize 后，与 LRC 文件名中 parse 出的 title_norm 做完全匹配
      3. 艺人名使用 split_artists 拆分，只要任一艺人 match_artists 成功即视为匹配

    行为：
      - 若无匹配 → 返回 None
      - 若匹配到 1 个 → 直接返回
      - 若匹配到多个且 interactive=True → 让用户选择
      - 若匹配到多个且 interactive=False → 返回第一个匹配的路径
    """
    meta_title_norm = normalize_name(meta.track)
    meta_artists = split_artists(meta.artist)

    candidates: List[Path] = []

    for p in config.lrc_dir.rglob("*.lrc"):
        lrc_artists, lrc_title_norm = parse_lrc_filename(p)
        if not lrc_title_norm:
            continue

        # 1) 歌曲名必须完全相等（在 normalize 之后）
        if lrc_title_norm != meta_title_norm:
            continue

        # 2) 艺人名任意一个成功匹配即可
        if match_artists(meta_artists, lrc_artists):
            candidates.append(p)

    if not candidates:
        return None

    if len(candidates) == 1 or not interactive:
        # 单一匹配 or 非交互模式
        return candidates[0]

    # 多个候选 → 交互选择
    print("\n匹配到多个歌词文件，请选择：")
    for idx, c in enumerate(candidates, 1):
        print(f"{idx}) {c}")

    while True:
        choice = input(f"请输入 1-{len(candidates)}: ").strip()
        if choice.isdigit():
            i = int(choice)
            if 1 <= i <= len(candidates):
                return candidates[i - 1]
        print("输入无效，请重新输入。")
