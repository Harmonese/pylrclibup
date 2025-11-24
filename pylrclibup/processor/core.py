from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional

from ..config import AppConfig
from ..model import TrackMeta, LyricsRecord
from ..lrc import find_lrc_for_track, parse_lrc_file, ParsedLRC
from ..api import ApiClient, upload_lyrics, upload_instrumental
from ..fs import move_with_dedup, cleanup_empty_dirs


# -------------------- 日志 + 预览 --------------------


def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def _log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _log_error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


def _preview(label: str, text: str, max_lines: int) -> None:
    print(f"--- {label} ---")
    if not text:
        print("[空]")
        print("-" * 40)
        return
    lines = text.splitlines()
    for ln in lines[:max_lines]:
        print(ln)
    if len(lines) > max_lines:
        print(f"... 共 {len(lines)} 行")
    print("-" * 40)


# -------------------- 文件移动 & 清理 --------------------


def _move_after_done(
    config: AppConfig,
    meta: TrackMeta,
    lrc_path: Optional[Path],
) -> None:
    """
    在以下场景调用：
      - /api/get-cached 已有歌词
      - 上传成功（外部歌词 / 本地 LRC / 纯音乐）

    规则：
      - MP3 一定移动到 done_tracks_dir
      - LRC 如存在则移动到 done_lrc_dir
      - 移动后清理 tracks_dir 与 lrc_dir 下的空目录
    """
    if lrc_path and lrc_path.exists():
        new_lrc = move_with_dedup(lrc_path, config.done_lrc_dir)
        if new_lrc:
            _log_info(f"LRC 已移动到：{new_lrc}")

    if meta.path.exists():
        new_mp3 = move_with_dedup(meta.path, config.done_tracks_dir)
        if new_mp3:
            _log_info(f"MP3 已移动到：{new_mp3}")

    cleanup_empty_dirs(config.tracks_dir)
    cleanup_empty_dirs(config.lrc_dir)


# -------------------- 单曲处理逻辑 --------------------


def process_track(
    config: AppConfig,
    api_client: ApiClient,
    meta: TrackMeta,
    *,
    auto_yes: bool = False,
    dry_run: bool = False,
) -> None:
    """
    按你原来脚本的逻辑，处理一首歌：
      1. /api/get-cached 查内部数据库
      2. /api/get 查外部歌词（可选用）
      3. 本地 LRC（递归匹配）
      4. LRC 解析（删除 credit / 识别纯音乐）
      5. 上传（歌词 / 纯音乐）
      6. 移动文件 & 清理空目录
    """
    _log_info(f"处理：{meta}")

    # 1. 先查内部数据库（不触发外部抓取）
    cached: Optional[LyricsRecord] = api_client.get_cached(meta)
    if cached:
        _log_info("内部数据库已存在歌词 → 自动移动 MP3+LRC 并跳过上传（不再重复提交）")
        _preview("已有 plainLyrics", cached.plain, config.preview_lines)
        _preview("已有 syncedLyrics", cached.synced, config.preview_lines)

        lrc_path = find_lrc_for_track(meta, config.lrc_dir, interactive=True)
        _move_after_done(config, meta, lrc_path)
        return

    # 2. 再查外部抓取（仅供参考，可选是否直接使用）
    external: Optional[LyricsRecord] = api_client.get_external(meta)
    if external:
        plain_ext = external.plain
        synced_ext = external.synced
        instrumental_ext = external.instrumental

        _log_info("外部抓取到歌词（仅供参考，可选择是否直接使用外部版本上传）：")
        _preview("外部 plainLyrics", plain_ext, config.preview_lines)
        _preview("外部 syncedLyrics", synced_ext, config.preview_lines)

        if instrumental_ext:
            _log_info("外部记录中该曲被标记为 instrumental（或两种歌词字段均为空）。")

        if dry_run:
            _log_info("[dry-run] 模式下，仅展示外部结果，不上传，也不继续本地处理。")
            return

        use_ext = False
        if auto_yes:
            # 自动模式优先使用外部结果
            use_ext = True
        else:
            choice = input("是否直接使用外部版本上传？[y/N]: ").strip().lower()
            use_ext = choice in ("y", "yes")

        if use_ext:
            if instrumental_ext:
                _log_info("将使用“纯音乐”方式上传（不包含任何歌词内容，只标记为 instrumental）。")
                ok = upload_instrumental(config, meta)
            else:
                _log_info("将直接使用外部 plain+synced 歌词上传。")
                ok = upload_lyrics(config, meta, plain_ext, synced_ext)

            if ok:
                _log_info("外部歌词上传完成 ✓")
                lrc_path = find_lrc_for_track(meta, config.lrc_dir, interactive=True)
                _move_after_done(config, meta, lrc_path)
            else:
                _log_error("外部歌词上传失败 ×")
            return
        else:
            _log_info("用户选择不直接使用外部歌词 → 继续尝试本地 LRC。")

    # 3. 查找本地 LRC 文件
    lrc_path = find_lrc_for_track(meta, config.lrc_dir, interactive=True)
    if not lrc_path:
        _log_warn(f"⚠ 未找到本地 LRC 文件：{meta.track}")
        if dry_run:
            _log_info("[dry-run] 模式下，未找到 LRC，仅提示，不上传，不标记纯音乐。")
            return

        while True:
            choice = input(
                "未找到本地 LRC，选择 "
                "[s] 跳过该歌曲 / "
                "[i] 上传空歌词标记为纯音乐 / "
                "[q] 退出程序: "
            ).strip().lower()

            if choice == "s":
                _log_info("跳过该歌曲，不上传、不移动。")
                return
            elif choice == "i":
                _log_info("将上传空歌词（标记为纯音乐）。")
                ok = upload_instrumental(config, meta)
                if ok:
                    _log_info("纯音乐标记上传完成 ✓")
                    _move_after_done(config, meta, lrc_path=None)
                else:
                    _log_error("纯音乐标记上传失败 ×")
                return
            elif choice == "q":
                _log_info("用户选择退出程序。")
                sys.exit(1)
            else:
                print("无效输入，请重新选择。")

    # 4. 解析本地 LRC
    parsed: ParsedLRC = parse_lrc_file(lrc_path)

    if parsed.is_instrumental:
        _log_info("LRC 中检测到“纯音乐，请欣赏”等字样，将按纯音乐处理（不上传歌词内容）。")

    _preview("本地 plainLyrics（整理后，将上传）", parsed.plain, config.preview_lines)
    _preview("本地 syncedLyrics（整理后，将上传）", parsed.synced, config.preview_lines)

    if dry_run:
        _log_info("[dry-run] 模式，仅预览 LRC，不上传。")
        return

    # 判断是否按纯音乐上传
    treat_as_instrumental = parsed.is_instrumental or (
        not parsed.plain.strip() and not parsed.synced.strip()
    )

    if treat_as_instrumental:
        _log_info("根据解析结果：将按纯音乐曲目上传。")
        if not auto_yes:
            choice = input("确认以纯音乐方式上传？[y/N]: ").strip().lower()
            if choice not in ("y", "yes"):
                _log_info("用户取消上传。")
                return

        ok = upload_instrumental(config, meta)
        if ok:
            _log_info("纯音乐上传完成 ✓")
            _move_after_done(config, meta, lrc_path)
        else:
            _log_error("纯音乐上传失败 ×")
        return

    # 非纯音乐 → 正常上传 plain+synced
    if not auto_yes:
        choice = input("确认上传本地歌词？[y/N]: ").strip().lower()
        if choice not in ("y", "yes"):
            _log_info("用户取消上传。")
            return

    ok = upload_lyrics(config, meta, parsed.plain, parsed.synced)
    if ok:
        _log_info("上传完成 ✓")
        _move_after_done(config, meta, lrc_path)
    else:
        _log_error("上传失败 ×")


# -------------------- 批量处理 --------------------


def process_all(
    config: AppConfig,
    *,
    auto_yes: bool = False,
    dry_run: bool = False,
    single: Optional[str] = None,
) -> None:
    """
    入口函数，等价于你之前脚本中的 main() 行为：

      - 如果 single 不为空 → 只处理指定文件
      - 否则递归扫描 tracks_dir 下所有 .mp3

    CLI 层只需要调用这一层。
    """
    api_client = ApiClient(config)

    metas: List[TrackMeta] = []

    if single:
        mp3 = config.tracks_dir / single
        if not mp3.is_file():
            _log_error(f"文件不存在：{mp3}")
            return
        tm = TrackMeta.from_mp3(mp3)
        if tm:
            metas.append(tm)
    else:
        for p in sorted(config.tracks_dir.rglob("*.mp3")):
            tm = TrackMeta.from_mp3(p)
            if tm:
                metas.append(tm)

    for meta in metas:
        process_track(
            config,
            api_client,
            meta,
            auto_yes=auto_yes,
            dry_run=dry_run,
        )
        print()

    _log_info("全部完成。")

def move_lrc_to_track_dirs(tracks_root: Path, lrc_root: Path) -> None:
    """
    “默认本地整理模式”（-d）：

    - 不访问 LRCLIB
    - 只做本地 mp3 ↔ lrc 匹配
    - 歌曲文件原地不动
    - 匹配到的 LRC 在用户确认后移动到对应歌曲所在目录

    参数：
      tracks_root: 歌曲根目录（递归扫描其中所有 .mp3）
      lrc_root   : 歌词根目录（递归扫描其中所有 .lrc，并参与匹配）
    """
    _log_info(f"默认匹配模式：歌曲根目录 = {tracks_root}, LRC 根目录 = {lrc_root}")

    if not tracks_root.is_dir():
        _log_error(f"歌曲目录不存在：{tracks_root}")
        return
    if not lrc_root.is_dir():
        _log_error(f"LRC 目录不存在：{lrc_root}")
        return

    mp3_paths = sorted(tracks_root.rglob("*.mp3"))
    if not mp3_paths:
        _log_warn("在指定歌曲目录下没有找到任何 .mp3 文件。")
        return

    for mp3 in mp3_paths:
        meta = TrackMeta.from_mp3(mp3)
        if not meta:
            continue

        _log_info(f"处理：{meta}")

        lrc_path = find_lrc_for_track(meta, lrc_root, interactive=True)
        if not lrc_path:
            _log_warn("未找到匹配的 LRC 文件，跳过。")
            print()
            continue

        _log_info(f"匹配到 LRC：{lrc_path}")
        target_dir = meta.path.parent
        prompt = f"是否将此 LRC 移动到歌曲目录 {target_dir}? [y/N]: "
        choice = input(prompt).strip().lower()
        if choice not in ("y", "yes"):
            _log_info("用户取消移动。")
            print()
            continue

        new_lrc = move_with_dedup(lrc_path, target_dir)
        if new_lrc:
            _log_info(f"LRC 已移动到：{new_lrc}")
        print()

    _log_info("默认匹配模式完成。")
