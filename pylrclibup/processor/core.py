from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional

from ..config import AppConfig
from ..model import TrackMeta, LyricsRecord
from ..lrc import find_lrc_for_track, parse_lrc_file, write_lrc_file, ParsedLRC
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

    普通模式（pair_lrc_with_track_dir=False）：
      - MP3 → done_tracks_dir
      - LRC → done_lrc_dir
      - 清理 tracks_dir / lrc_dir 下的空目录

    匹配模式（-m, match_mode=True）：
      - MP3 移动到 done_tracks_dir
      - LRC （如果存在）移动到 done_tracks_dir 并重命名为相同文件名
      - 清理 tracks_dir / lrc_dir 下的空目录

    默认模式（-d, pair_lrc_with_track_dir=True）：
      - MP3 保持原地不动
      - LRC（如果存在）移动到 MP3 所在目录并重命名为相同文件名
      - 不清理目录（避免误删）
    """

    # ⭐ 默认模式：LRC 跟随歌曲目录，歌曲不动
    if config.pair_lrc_with_track_dir:
        target_dir = meta.path.parent
        
        if lrc_path and lrc_path.exists():
            # ⭐ 重命名为和 MP3 相同的文件名（不包含扩展名）
            mp3_basename = meta.path.stem
            new_lrc = move_with_dedup(lrc_path, target_dir, new_name=mp3_basename)
            if new_lrc:
                _log_info(f"[pair-mode] LRC 已移动并重命名为：{new_lrc}")
        else:
            _log_info("[pair-mode] 没有 LRC 可移动。")
        # 歌曲文件不动，目录也不清理
        return

    # ⭐ 匹配模式：LRC 跟随 done_tracks_dir
    if config.match_mode:
        # 先移动 MP3
        new_mp3 = None
        if meta.path.exists():
            new_mp3 = move_with_dedup(meta.path, config.done_tracks_dir)
            if new_mp3:
                _log_info(f"MP3 已移动到：{new_mp3}")
        
        # 再移动 LRC 到 done_tracks_dir 并重命名
        if lrc_path and lrc_path.exists() and new_mp3:
            mp3_basename = new_mp3.stem
            new_lrc = move_with_dedup(lrc_path, config.done_tracks_dir, new_name=mp3_basename)
            if new_lrc:
                _log_info(f"[match-mode] LRC 已移动到歌曲目录并重命名为：{new_lrc}")
        elif lrc_path and lrc_path.exists():
            # MP3 移动失败但 LRC 存在
            _log_warn("[match-mode] MP3 移动失败，LRC 未移动")
        
        cleanup_empty_dirs(config.tracks_dir)
        cleanup_empty_dirs(config.lrc_dir)
        return

    # ⭐ 普通模式：分别移动到各自的 done 目录
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

        lrc_path = find_lrc_for_track(meta, config, interactive=True)
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
                lrc_path = find_lrc_for_track(meta, config, interactive=True)
                _move_after_done(config, meta, lrc_path)
            else:
                _log_error("外部歌词上传失败 ×")
            return
        else:
            _log_info("用户选择不直接使用外部歌词 → 继续尝试本地 LRC。")

    # 3. 查找本地 LRC 文件
    lrc_path = find_lrc_for_track(meta, config, interactive=True)
    if not lrc_path:
        _log_warn(f"⚠ 未找到本地 LRC 文件：{meta.track}")
        if dry_run:
            _log_info("[dry-run] 模式下，未找到 LRC，仅提示，不上传，不标记纯音乐。")
            return
        # ⭐ 新增：手动指定歌词文件选项
        while True:
            choice = input(
                "未找到本地 LRC，选择 "
                "[s] 跳过该歌曲 / "
                "[m] 手动指定歌词文件 / "
                "[i] 上传空歌词标记为纯音乐 / "
                "[q] 退出程序: "
            ).strip().lower()
            if choice == "s":
                _log_info("跳过该歌曲，不上传、不移动。")
                return
            elif choice == "m":
                # ⭐ 手动输入路径（支持绝对/相对路径、引号、转义符）
                manual_path_raw = input("请输入 LRC 文件的完整路径: ").strip()
                if not manual_path_raw:
                    print("路径为空，请重新选择。")
                    continue
                
                # ⭐ 处理引号（单引号/双引号）
                if (manual_path_raw.startswith("'") and manual_path_raw.endswith("'")) or \
                (manual_path_raw.startswith('"') and manual_path_raw.endswith('"')):
                    manual_path_raw = manual_path_raw[1:-1]
                
                # ⭐ 处理路径：支持绝对路径和相对路径
                lrc_path_manual = Path(manual_path_raw).expanduser()  # 展开 ~ 符号
                
                # 如果是相对路径，基于当前工作目录解析
                if not lrc_path_manual.is_absolute():
                    lrc_path_manual = Path.cwd() / lrc_path_manual
                
                lrc_path_manual = lrc_path_manual.resolve()  # 解析为绝对路径
                
                if not lrc_path_manual.exists() or not lrc_path_manual.is_file():
                    print(f"文件不存在或不是有效文件：{lrc_path_manual}")
                    continue
                
                if lrc_path_manual.suffix.lower() != ".lrc":
                    print(f"警告：文件扩展名不是 .lrc，是否继续？[y/N]: ", end="")
                    confirm = input().strip().lower()
                    if confirm not in ("y", "yes"):
                        continue
                
                lrc_path = lrc_path_manual
                _log_info(f"使用手动指定的歌词文件：{lrc_path}")
                break  # 退出循环，继续处理
                
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

    # 5. 写回标准化的 LRC 内容到原文件
    if not dry_run:
        if write_lrc_file(lrc_path, parsed.synced):
            _log_info(f"✓ LRC 文件已更新为标准化内容：{lrc_path.name}")
        else:
            _log_warn(f"⚠ LRC 文件写入失败，但将继续处理：{lrc_path.name}")
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

