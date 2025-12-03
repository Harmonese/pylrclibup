# ===== processor/core.py（完整 i18n 版本，支持 YAML 元数据）=====

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Union

from ..config import AppConfig, SUPPORTED_AUDIO_EXTENSIONS
from ..model import TrackMeta, LyricsRecord, YamlTrackMeta, SUPPORTED_YAML_EXTENSIONS
from ..lrc import find_lrc_for_track, parse_lrc_file, cleanse_lrc_file, ParsedLRC
from ..lrc.yaml_matcher import find_lrc_for_yaml_meta
from ..api import ApiClient, upload_lyrics, upload_instrumental
from ..fs import move_with_dedup, cleanup_empty_dirs
from ..logging_utils import log_info, log_warn, log_error
from ..i18n import get_text as _


# -------------------- 预览辅助函数 --------------------


def _preview(label: str, text: str, max_lines: int) -> None:
    """预览歌词内容"""
    print(f"--- {label} ---")
    if not text:
        print(_("[空]"))
        print("-" * 40)
        return
    lines = text.splitlines()
    for ln in lines[:max_lines]:
        print(ln)
    if len(lines) > max_lines:
        print(_("... 共 {count} 行").format(count=len(lines)))
    print("-" * 40)


# -------------------- LRC 查找统一入口 --------------------


def _find_lrc_for_meta(
    meta: Union[TrackMeta, YamlTrackMeta],
    config: AppConfig,
    *,
    interactive: bool = True,
) -> Optional[Path]:
    """
    统一的 LRC 查找入口
    
    根据 meta 类型选择不同的查找策略：
    - YamlTrackMeta: 优先使用指定的 lrc_file，其次同名文件，最后降级到通用匹配
    - TrackMeta: 使用原有的匹配逻辑
    """
    if isinstance(meta, YamlTrackMeta):
        # YAML 元数据：优先使用指定的 lrc_file，其次同名文件
        lrc = find_lrc_for_yaml_meta(meta, config)
        if lrc:
            return lrc
        # 降级到通用匹配（需要转换为 TrackMeta）
        track_meta = TrackMeta.from_yaml(meta)
        return find_lrc_for_track(track_meta, config, interactive=interactive)
    else:
        # 音频文件元数据：使用原有匹配逻辑
        return find_lrc_for_track(meta, config, interactive=interactive)


# -------------------- 文件移动逻辑 --------------------


def move_files_after_processing(
    config: AppConfig,
    meta: Union[TrackMeta, YamlTrackMeta],
    lrc_path: Optional[Path],
) -> None:
    """
    处理完成后移动文件的统一逻辑
    
    注意：YAML 元数据文件本身不移动，只移动 LRC
    """
    is_yaml = isinstance(meta, YamlTrackMeta)
    
    # 步骤 1：移动音频文件（YAML 模式跳过）
    new_audio_path = meta.path
    
    if not is_yaml and config.done_tracks_dir:
        moved_audio = move_with_dedup(meta.path, config.done_tracks_dir)
        if moved_audio:
            new_audio_path = moved_audio
            log_info(_("音频文件已移动到：{path}").format(path=new_audio_path))
        else:
            log_warn(_("音频文件移动失败，将保持原地"))
    
    # 如果没有 LRC 文件，直接返回
    if not lrc_path or not lrc_path.exists():
        if not is_yaml:
            cleanup_empty_dirs(config.tracks_dir)
        return
    
    # 步骤 2：确定 LRC 的目标目录
    if config.done_lrc_dir:
        lrc_target_dir = config.done_lrc_dir
    elif config.follow_mp3 and not is_yaml:
        lrc_target_dir = new_audio_path.parent
    else:
        lrc_target_dir = lrc_path.parent
    
    # 步骤 3：确定 LRC 的目标文件名
    new_lrc_name = None
    if config.rename_lrc and not is_yaml:
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
                action.append(_("移动到 {dir}").format(dir=lrc_target_dir))
            if new_lrc_name and new_lrc_name != lrc_path.stem:
                action.append(_("重命名为 {name}").format(name=new_lrc_path.name))
            log_info(_("LRC 已{action}").format(action=_("、").join(action)))
        else:
            log_warn(_("LRC 移动失败"))
    else:
        log_info(_("LRC 保持原地不动"))
    
    # 步骤 5：清理空目录
    if not is_yaml:
        cleanup_empty_dirs(config.tracks_dir)
    cleanup_empty_dirs(config.lrc_dir)


# -------------------- 单曲处理辅助函数 --------------------


def _handle_cached_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    cached: LyricsRecord,
    original_meta: Optional[Union[TrackMeta, YamlTrackMeta]] = None,
) -> None:
    """处理内部数据库已有歌词的情况"""
    log_info(_("内部数据库已存在歌词 → 自动移动音频文件+LRC 并跳过上传（不再重复提交）"))
    _preview(_("已有 plainLyrics"), cached.plain, config.preview_lines)
    _preview(_("已有 syncedLyrics"), cached.synced, config.preview_lines)
    
    # 使用原始 meta 查找 LRC（保留 YAML 的 lrc_file 信息）
    source_meta = original_meta if original_meta else meta
    lrc_path = _find_lrc_for_meta(source_meta, config, interactive=True)
    move_files_after_processing(config, source_meta, lrc_path)


def _handle_external_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    external: LyricsRecord,
    original_meta: Optional[Union[TrackMeta, YamlTrackMeta]] = None,
) -> bool:
    """
    处理外部抓取到歌词的情况
    
    Returns:
        True 表示已处理完成（无论成功失败），False 表示用户选择继续本地处理
    """
    plain_ext = external.plain
    synced_ext = external.synced
    instrumental_ext = external.instrumental
    
    log_info(_("外部抓取到歌词（仅供参考，可选择是否直接使用外部版本上传）："))
    _preview(_("外部 plainLyrics"), plain_ext, config.preview_lines)
    _preview(_("外部 syncedLyrics"), synced_ext, config.preview_lines)
    
    if instrumental_ext:
        log_info(_("外部记录中该曲被标记为 instrumental（或两种歌词字段均为空）。"))
    
    # 始终询问用户
    choice = input(_("是否直接使用外部版本上传？[y/N]: ")).strip().lower()
    use_ext = choice in ("y", "yes")
    
    if not use_ext:
        log_info(_("用户选择不直接使用外部歌词 → 继续尝试本地 LRC。"))
        return False
    
    # 执行上传
    if instrumental_ext:
        log_info(_("将使用“纯音乐”方式上传（不包含任何歌词内容，只标记为 instrumental）。"))
        ok = upload_instrumental(config, meta)
    else:
        log_info(_("将直接使用外部 plain+synced 歌词上传。"))
        ok = upload_lyrics(config, meta, plain_ext, synced_ext)
    
    if ok:
        log_info(_("外部歌词上传完成 ✓"))
        source_meta = original_meta if original_meta else meta
        lrc_path = _find_lrc_for_meta(source_meta, config, interactive=True)
        move_files_after_processing(config, source_meta, lrc_path)
    else:
        log_error(_("外部歌词上传失败 ×"))
    
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
            _("未找到本地 LRC，选择 [s] 跳过该歌曲 / [m] 手动指定歌词文件 / [i] 上传空歌词标记为纯音乐 / [q] 退出程序: ")
        ).strip().lower()
        
        if choice == "s":
            log_info(_("跳过该歌曲，不上传、不移动。"))
            return None
        
        elif choice == "m":
            lrc_path = _get_manual_lrc_path()
            if lrc_path:
                return lrc_path
            # 路径无效，继续循环
        
        elif choice == "i":
            log_info(_("将上传空歌词（标记为纯音乐）。"))
            ok = upload_instrumental(config, meta)
            if ok:
                log_info(_("纯音乐标记上传完成 ✓"))
                move_files_after_processing(config, meta, lrc_path=None)
            else:
                log_error(_("纯音乐标记上传失败 ×"))
            return None
        
        elif choice == "q":
            log_info(_("用户选择退出程序。"))
            sys.exit(1)
        
        else:
            print(_("无效输入，请重新选择。"))


def _get_manual_lrc_path() -> Optional[Path]:
    """获取用户手动输入的 LRC 文件路径"""
    manual_path_raw = input(_("请输入 LRC 文件的完整路径: ")).strip()
    
    if not manual_path_raw:
        print(_("路径为空，请重新选择。"))
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
        print(_("文件不存在或不是有效文件：{path}").format(path=lrc_path))
        return None
    
    if lrc_path.suffix.lower() != ".lrc":
        confirm = input(_("警告：文件扩展名不是 .lrc，是否继续？[y/N]: ")).strip().lower()
        if confirm not in ("y", "yes"):
            return None
    
    log_info(_("使用手动指定的歌词文件：{path}").format(path=lrc_path))
    return lrc_path


def _upload_local_lyrics(
    config: AppConfig,
    meta: TrackMeta,
    lrc_path: Path,
    parsed: ParsedLRC,
    original_meta: Optional[Union[TrackMeta, YamlTrackMeta]] = None,
) -> None:
    """上传本地解析的歌词"""
    treat_as_instrumental = parsed.is_instrumental or (
        not parsed.plain.strip() and not parsed.synced.strip()
    )
    
    source_meta = original_meta if original_meta else meta
    
    if treat_as_instrumental:
        log_info(_("根据解析结果：将按纯音乐曲目上传。"))
        choice = input(_("确认以纯音乐方式上传？[y/N]: ")).strip().lower()
        if choice not in ("y", "yes"):
            log_info(_("用户取消上传。"))
            return
        
        ok = upload_instrumental(config, meta)
        if ok:
            log_info(_("纯音乐上传完成 ✓"))
            move_files_after_processing(config, source_meta, lrc_path)
        else:
            log_error(_("纯音乐上传失败 ×"))
        return
    
    # 非纯音乐 → 正常上传 plain+synced
    choice = input(_("确认上传本地歌词？[y/N]: ")).strip().lower()
    if choice not in ("y", "yes"):
        log_info(_("用户取消上传。"))
        return
    
    ok = upload_lyrics(config, meta, parsed.plain, parsed.synced)
    if ok:
        log_info(_("上传完成 ✓"))
        move_files_after_processing(config, source_meta, lrc_path)
    else:
        log_error(_("上传失败 ×"))


# -------------------- 单曲处理逻辑 --------------------


def process_track(
    config: AppConfig,
    api_client: ApiClient,
    meta: Union[TrackMeta, YamlTrackMeta],
) -> None:
    """
    处理一首歌（支持音频文件元数据或 YAML 元数据）：
      1. /api/get-cached 查内部数据库
      2. /api/get 查外部歌词（可选用）
      3. 查找本地 LRC
      4. [可选] 标准化 LRC（如果 config.cleanse_lrc=True）
      5. LRC 解析
      6. 上传（歌词 / 纯音乐）
      7. 移动文件 & 清理空目录
    """
    is_yaml = isinstance(meta, YamlTrackMeta)
    source_type = "YAML" if is_yaml else _("音频")
    
    log_info(_("处理（{source_type}）：{meta}").format(source_type=source_type, meta=meta))
    
    # 转换为 TrackMeta 用于 API 调用
    track_meta = TrackMeta.from_yaml(meta) if is_yaml else meta

    # 1. 先查内部数据库（不触发外部抓取）
    cached: Optional[LyricsRecord] = api_client.get_cached(track_meta)
    if cached:
        _handle_cached_lyrics(config, track_meta, cached, original_meta=meta)
        return

    # 2. 再查外部抓取（仅供参考，可选是否直接使用）
    external: Optional[LyricsRecord] = api_client.get_external(track_meta)
    if external:
        handled = _handle_external_lyrics(config, track_meta, external, original_meta=meta)
        if handled:
            return

    # 3. 查找本地 LRC 文件
    lrc_path = _find_lrc_for_meta(meta, config, interactive=True)
    
    if not lrc_path:
        log_warn(_("⚠ 未找到本地 LRC 文件：{track}").format(track=meta.track))
        lrc_path = _prompt_for_missing_lrc(config, track_meta)
        if not lrc_path:
            return
    
    # 4. [可选] 标准化 LRC 文件（在处理开始前）
    if config.cleanse_lrc:
        log_info(_("正在标准化 LRC 文件：{filename}").format(filename=lrc_path.name))
        if cleanse_lrc_file(lrc_path):
            log_info(_("✓ LRC 文件已标准化"))
        else:
            log_warn(_("⚠ LRC 文件标准化失败，将继续使用原始内容"))

    # 5. 解析本地 LRC（已经标准化过了，直接读取）
    parsed: ParsedLRC = parse_lrc_file(lrc_path)

    if parsed.is_instrumental:
        log_info(_("LRC 中检测到“纯音乐，请欣赏”等字样，将按纯音乐处理（不上传歌词内容）。"))

    _preview(_("本地 plainLyrics（将上传）"), parsed.plain, config.preview_lines)
    _preview(_("本地 syncedLyrics（将上传）"), parsed.synced, config.preview_lines)

    # 6. 上传歌词
    _upload_local_lyrics(config, track_meta, lrc_path, parsed, original_meta=meta)


# -------------------- 批量处理 --------------------


def process_all(config: AppConfig) -> None:
    """
    入口函数：递归扫描 tracks_dir 下所有支持的文件

    支持：
    - 音频文件（.mp3, .m4a, .aac, .flac, .wav）
    - YAML 元数据文件（.yaml, .yml）

    CLI 层只需要调用这一层。
    """
    api_client = ApiClient(config)

    metas: List[Union[TrackMeta, YamlTrackMeta]] = []
    
    # 扫描所有支持的音频格式
    audio_extensions_str = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
    log_info(_("扫描音频文件：{extensions}").format(extensions=audio_extensions_str))
    
    for ext in SUPPORTED_AUDIO_EXTENSIONS:
        pattern = f"*{ext}"
        for p in sorted(config.tracks_dir.rglob(pattern)):
            tm = TrackMeta.from_audio_file(p)
            if tm:
                metas.append(tm)
    
    # 扫描所有支持的 YAML 格式
    yaml_extensions_str = ", ".join(sorted(SUPPORTED_YAML_EXTENSIONS))
    log_info(_("扫描 YAML 元数据文件：{extensions}").format(extensions=yaml_extensions_str))
    
    for ext in SUPPORTED_YAML_EXTENSIONS:
        pattern = f"*{ext}"
        for p in sorted(config.tracks_dir.rglob(pattern)):
            ym = YamlTrackMeta.from_yaml_file(p)
            if ym:
                metas.append(ym)

    total = len(metas)
    
    if total == 0:
        all_extensions = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_YAML_EXTENSIONS))
        log_warn(_("未找到任何支持的文件（{extensions}）").format(extensions=all_extensions))
        return
    
    # 统计数量
    audio_count = sum(1 for m in metas if isinstance(m, TrackMeta))
    yaml_count = sum(1 for m in metas if isinstance(m, YamlTrackMeta))
    log_info(_("共找到 {total} 个文件（音频：{audio}，YAML：{yaml}）").format(
        total=total, audio=audio_count, yaml=yaml_count
    ))
    
    for idx, meta in enumerate(metas, 1):
        log_info(_("[{idx}/{total}] 开始处理...").format(idx=idx, total=total))
        process_track(config, api_client, meta)
        print()

    log_info(_("全部完成。"))
