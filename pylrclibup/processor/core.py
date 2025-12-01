# ===== processor/core.py（支持多格式 + 更新日志）=====

# ===== processor/core.py =====

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from ..config import AppConfig, SUPPORTED_AUDIO_EXTENSIONS
from ..model import TrackMeta, LyricsRecord
from ..lrc import find_lrc_for_track, parse_lrc_file, cleanse_lrc_file, ParsedLRC
from ..api import ApiClient, upload_lyrics, upload_instrumental
from ..fs import move_with_dedup, cleanup_empty_dirs
from ..logging_utils import log_info, log_warn, log_error


# -------------------- 预览辅助函数 --------------------


def _preview(label: str, text: str, max_lines: int) -> None:
    """预览歌词内容"""
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


# -------------------- 文件移动逻辑 --------------------


def move_files_after_processing(
    config: AppConfig,
    meta: TrackMeta,
    lrc_path: Optional[Path],
) -> None:
    """
    处理完成后移动文件的统一逻辑
    """
    # 步骤 1：移动音频文件
    new_audio_path = meta.path
    
    if config.done_tracks_dir:
        moved_audio = move_with_dedup(meta.path, config.done_tracks_dir)
        if moved_audio:
            new_audio_path = moved_audio
            log_info(f"音频文件已移动到：{new_audio_path}")
        else:
            log_warn("音频文件移动失败，将保持原地")
    
    # 如果没有 LRC 文件，直接返回
    if not lrc_path or not lrc_path.exists():
        cleanup_empty_dirs(config.tracks_dir)
        return
    
    # 步骤 2：确定 LRC 的目标目录
    if config.done_lrc_dir:
        lrc_target_dir = config.done_lrc_dir
    elif config.follow_mp3:  # 保持旧名兼容性
        lrc_target_dir = new_audio_path.parent
    else:
        lrc_target_dir = lrc_path.parent
    
    # 步骤 3：确定 LRC 的目标文件名
    new_lrc_name = None
    if config.rename_lrc:
        new_lrc_name = new_audio_path.stem
    
    # 步骤 4：判断是否需要移动
    needs_move = (
        lrc_target_dir != lrc_path.parent or 
        (new_lrc_name and new_lrc_name != lrc_path.stem)
    )
    
    if needs_move:
        new_lrc_path = move_with_dedup(lrc_path, lrc_target_dir, new_name=new_lrc_name)
        if new_lrc_path:
            action = []
            if lrc_target_dir != lrc_path.parent:
                action.append(f"移动到 {lrc_target_dir}")
            if new_lrc_name and new_lrc_name != lrc_path.stem:
                action.append(f"重命名为 {new_lrc_path.name}")
            log_info(f"LRC 已{'、'.join(action)}")
        else:
            log_warn("LRC 移动失败")
    else:
        log_info("LRC 保持原地不动")
    
    # 步骤 5：清理空目录
    cleanup_empty_dirs(config.tracks_dir)
    cleanup_empty_dirs(config.lrc_dir)


# -------------------- 单曲处理辅助函数 --------------------


def _handle_cached_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    cached: LyricsRecord,
) -> None:
    """处理内部数据库已有歌词的情况"""
    log_info("内部数据库已存在歌词 → 自动移动音频文件+LRC 并跳过上传（不再重复提交）")
    _preview("已有 plainLyrics", cached.plain, config.preview_lines)
    _preview("已有 syncedLyrics", cached.synced, config.preview_lines)
    
    lrc_path = find_lrc_for_track(meta, config, interactive=True)
    move_files_after_processing(config, meta, lrc_path)


def _handle_external_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    external: LyricsRecord,
) -> bool:
    """
    处理外部抓取到歌词的情况
    
    Returns:
        True 表示已处理完成（无论成功失败），False 表示用户选择继续本地处理
    """
    plain_ext = external.plain
    synced_ext = external.synced
    instrumental_ext = external.instrumental
    
    log_info("外部抓取到歌词（仅供参考，可选择是否直接使用外部版本上传）：")
    _preview("外部 plainLyrics", plain_ext, config.preview_lines)
    _preview("外部 syncedLyrics", synced_ext, config.preview_lines)
    
    if instrumental_ext:
        log_info("外部记录中该曲被标记为 instrumental（或两种歌词字段均为空）。")
    
    # 始终询问用户
    choice = input("是否直接使用外部版本上传？[y/N]: ").strip().lower()
    use_ext = choice in ("y", "yes")
    
    if not use_ext:
        log_info("用户选择不直接使用外部歌词 → 继续尝试本地 LRC。")
        return False
    
    # 执行上传
    if instrumental_ext:
        log_info("将使用“纯音乐”方式上传（不包含任何歌词内容，只标记为 instrumental）。")
        ok = upload_instrumental(config, meta)
    else:
        log_info("将直接使用外部 plain+synced 歌词上传。")
        ok = upload_lyrics(config, meta, plain_ext, synced_ext)
    
    if ok:
        log_info("外部歌词上传完成 ✓")
        lrc_path = find_lrc_for_track(meta, config, interactive=True)
        move_files_after_processing(config, meta, lrc_path)
    else:
        log_error("外部歌词上传失败 ×")
    
    return True


def _prompt_for_missing_lrc(
    config: AppConfig,
    meta: TrackMeta,
) -> Optional[Path]:
    """
    当未找到本地 LRC 时，提示用户选择操作
    
    Returns:
        手动指定的 LRC 路径，或 None（跳过/退出/标记纯音乐）
    """
    while True:
        choice = input(
            "未找到本地 LRC，选择 "
            "[s] 跳过该歌曲 / "
            "[m] 手动指定歌词文件 / "
            "[i] 上传空歌词标记为纯音乐 / "
            "[q] 退出程序: "
        ).strip().lower()
        
        if choice == "s":
            log_info("跳过该歌曲，不上传、不移动。")
            return None
        
        elif choice == "m":
            lrc_path = _get_manual_lrc_path()
            if lrc_path:
                return lrc_path
            # 路径无效，继续循环
        
        elif choice == "i":
            log_info("将上传空歌词（标记为纯音乐）。")
            ok = upload_instrumental(config, meta)
            if ok:
                log_info("纯音乐标记上传完成 ✓")
                move_files_after_processing(config, meta, lrc_path=None)
            else:
                log_error("纯音乐标记上传失败 ×")
            return None
        
        elif choice == "q":
            log_info("用户选择退出程序。")
            sys.exit(1)
        
        else:
            print("无效输入，请重新选择。")


def _get_manual_lrc_path() -> Optional[Path]:
    """获取用户手动输入的 LRC 文件路径"""
    manual_path_raw = input("请输入 LRC 文件的完整路径: ").strip()
    
    if not manual_path_raw:
        print("路径为空，请重新选择。")
        return None
    
    # 处理引号（单引号/双引号）
    if (manual_path_raw.startswith("'") and manual_path_raw.endswith("'")) or \
       (manual_path_raw.startswith('"') and manual_path_raw.endswith('"')):
        manual_path_raw = manual_path_raw[1:-1]
    
    # 处理路径：支持绝对路径和相对路径
    lrc_path = Path(manual_path_raw).expanduser()
    
    if not lrc_path.is_absolute():
        lrc_path = Path.cwd() / lrc_path
    
    lrc_path = lrc_path.resolve()
    
    if not lrc_path.exists() or not lrc_path.is_file():
        print(f"文件不存在或不是有效文件：{lrc_path}")
        return None
    
    if lrc_path.suffix.lower() != ".lrc":
        confirm = input(f"警告：文件扩展名不是 .lrc，是否继续？[y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            return None
    
    log_info(f"使用手动指定的歌词文件：{lrc_path}")
    return lrc_path


def _upload_local_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    lrc_path: Path,
    parsed: ParsedLRC,
) -> None:
    """上传本地解析的歌词"""
    treat_as_instrumental = parsed.is_instrumental or (
        not parsed.plain.strip() and not parsed.synced.strip()
    )
    
    if treat_as_instrumental:
        log_info("根据解析结果：将按纯音乐曲目上传。")
        choice = input("确认以纯音乐方式上传？[y/N]: ").strip().lower()
        if choice not in ("y", "yes"):
            log_info("用户取消上传。")
            return
        
        ok = upload_instrumental(config, meta)
        if ok:
            log_info("纯音乐上传完成 ✓")
            move_files_after_processing(config, meta, lrc_path)
        else:
            log_error("纯音乐上传失败 ×")
        return
    
    # 非纯音乐 → 正常上传 plain+synced
    choice = input("确认上传本地歌词？[y/N]: ").strip().lower()
    if choice not in ("y", "yes"):
        log_info("用户取消上传。")
        return
    
    ok = upload_lyrics(config, meta, parsed.plain, parsed.synced)
    if ok:
        log_info("上传完成 ✓")
        move_files_after_processing(config, meta, lrc_path)
    else:
        log_error("上传失败 ×")


# -------------------- 单曲处理逻辑 --------------------


def process_track(
    config: AppConfig,
    api_client: ApiClient,
    meta: TrackMeta,
) -> None:
    """
    处理一首歌：
      1. 查找本地 LRC
      2. [可选] 标准化 LRC（如果 config.cleanse_lrc=True）
      3. /api/get-cached 查内部数据库
      4. /api/get 查外部歌词（可选用）
      5. LRC 解析
      6. 上传（歌词 / 纯音乐）
      7. 移动文件 & 清理空目录
    """
    log_info(f"处理：{meta}")

    # 1. 查找本地 LRC 文件
    lrc_path = find_lrc_for_track(meta, config, interactive=True)
    
    if not lrc_path:
        log_warn(f"⚠ 未找到本地 LRC 文件：{meta.track}")
        lrc_path = _prompt_for_missing_lrc(config, meta)
        if not lrc_path:
            return
    
    # 2. [可选] 标准化 LRC 文件（在处理开始前）
    if config.cleanse_lrc:
        log_info(f"正在标准化 LRC 文件：{lrc_path.name}")
        if cleanse_lrc_file(lrc_path):
            log_info("✓ LRC 文件已标准化")
        else:
            log_warn("⚠ LRC 文件标准化失败，将继续使用原始内容")

    # 3. 先查内部数据库（不触发外部抓取）
    cached: Optional[LyricsRecord] = api_client.get_cached(meta)
    if cached:
        _handle_cached_lyrics(config, meta, cached)
        return

    # 4. 再查外部抓取（仅供参考，可选是否直接使用）
    external: Optional[LyricsRecord] = api_client.get_external(meta)
    if external:
        handled = _handle_external_lyrics(config, meta, external)
        if handled:
            return

    # 5. 解析本地 LRC（已经标准化过了，直接读取）
    parsed: ParsedLRC = parse_lrc_file(lrc_path)

    if parsed.is_instrumental:
        log_info("LRC 中检测到“纯音乐，请欣赏”等字样，将按纯音乐处理（不上传歌词内容）。")

    _preview("本地 plainLyrics（将上传）", parsed.plain, config.preview_lines)
    _preview("本地 syncedLyrics（将上传）", parsed.synced, config.preview_lines)

    # 6. 上传歌词
    _upload_local_lyrics(config, meta, lrc_path, parsed)


# -------------------- 批量处理 --------------------


def process_all(config: AppConfig) -> None:
    """
    入口函数：递归扫描 tracks_dir 下所有支持的音频文件

    CLI 层只需要调用这一层。
    """
    api_client = ApiClient(config)

    metas: List[TrackMeta] = []
    
    # 扫描所有支持的音频格式
    log_info(f"扫描音频文件：{', '.join(SUPPORTED_AUDIO_EXTENSIONS)}")
    
    for ext in SUPPORTED_AUDIO_EXTENSIONS:
        pattern = f"*{ext}"
        for p in sorted(config.tracks_dir.rglob(pattern)):
            tm = TrackMeta.from_audio_file(p)
            if tm:
                metas.append(tm)

    total = len(metas)
    
    if total == 0:
        log_warn(f"未找到任何支持的音频文件（{', '.join(SUPPORTED_AUDIO_EXTENSIONS)}）")
        return
    
    log_info(f"共找到 {total} 个音频文件")
    
    for idx, meta in enumerate(metas, 1):
        log_info(f"[{idx}/{total}] 开始处理...")
        process_track(config, api_client, meta)
        print()

    log_info("全部完成。")
