from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config import AppConfig
from ..processor import process_all
from ..lrc import parse_lrc_file, write_lrc_file


def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}")

def _log_error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)

def parse_lrc_mode(target: Path) -> None:
    """
    -p/--parse 模式：标准化 LRC 文件或目录中的所有 LRC 文件
    
    Args:
        target: LRC 文件路径或包含 LRC 的目录
    """
    if not target.exists():
        _log_error(f"路径不存在：{target}")
        sys.exit(1)
    
    # 单个文件
    if target.is_file():
        if target.suffix.lower() != ".lrc":
            _log_error(f"不是 LRC 文件：{target}")
            sys.exit(1)
        
        _log_info(f"标准化 LRC 文件：{target}")
        try:
            parsed = parse_lrc_file(target)
            if write_lrc_file(target, parsed.synced):
                _log_info(f"✓ 成功标准化：{target.name}")
                if parsed.is_instrumental:
                    _log_info("  → 检测到纯音乐标记")
            else:
                _log_error(f"✗ 写入失败：{target.name}")
        except Exception as e:
            _log_error(f"✗ 处理失败：{target.name} - {e}")
        return
    
    # 目录：递归处理
    if target.is_dir():
        lrc_files = sorted(target.rglob("*.lrc"))
        if not lrc_files:
            _log_info(f"未找到任何 LRC 文件：{target}")
            return
        
        _log_info(f"找到 {len(lrc_files)} 个 LRC 文件，开始批量标准化...")
        
        success = 0
        failed = 0
        
        for lrc_path in lrc_files:
            try:
                parsed = parse_lrc_file(lrc_path)
                if write_lrc_file(lrc_path, parsed.synced):
                    success += 1
                    _log_info(f"✓ [{success}/{len(lrc_files)}] {lrc_path.name}")
                    if parsed.is_instrumental:
                        _log_info(f"  → 检测到纯音乐")
                else:
                    failed += 1
                    _log_error(f"✗ 写入失败：{lrc_path.name}")
            except Exception as e:
                failed += 1
                _log_error(f"✗ 处理失败：{lrc_path.name} - {e}")
        
        _log_info(f"\n标准化完成：成功 {success} 个，失败 {failed} 个")
        return
    
    _log_error(f"无效路径类型：{target}")
    sys.exit(1)


def run_cli():
    """
    pylrclibup 的命令行入口点。
    """

    parser = argparse.ArgumentParser(
        prog="pylrclibup",
        description="Upload lyrics or instrumental tags to LRCLIB with local files."
    )

    # 基础选项
    parser.add_argument("--yes", action="store_true",
                        help="不询问确认，默认选择上传或使用外部歌词")

    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不执行任何上传和移动")

    parser.add_argument("--single", type=str,
                        help="只处理指定文件（相对于 --tracks 目录），例如 'foo.mp3'")

    # ⭐ 新的路径参数（移除 --root，所有默认为 cwd）
    parser.add_argument("--tracks", type=str,
                        help="歌曲文件输入目录（默认：当前工作目录）")
    parser.add_argument("--lrc", type=str,
                        help="LRC 文件输入目录（默认：当前工作目录）")
    parser.add_argument("--done-tracks", type=str,
                        help="处理后歌曲文件移动到的目录（默认：与 --tracks 相同）")
    parser.add_argument("--done-lrc", type=str,
                        help="处理后 LRC 文件移动到的目录（默认：与 --lrc 相同）")

    parser.add_argument("--preview-lines", type=int, default=10,
                        help="预览歌词时显示的行数")

    # ⭐ -d/--default 模式
    parser.add_argument(
        "-d", "--default",
        nargs=2,
        metavar=("TRACKS_DIR", "LRC_DIR"),
        help=(
            "默认模式：使用指定歌曲目录和歌词目录，完整执行上传流程，"
            "但歌曲文件保持原地不动，匹配和使用过的 LRC 会被移动到对应歌曲文件所在目录。"
        ),
    )

    # ⭐ -p/--parse 模式
    parser.add_argument(
        "-p", "--parse",
        type=str,
        metavar="PATH",
        help=(
            "解析模式：对指定的 LRC 文件或目录中的所有 LRC 文件进行标准化处理。"
            "如果是文件，直接标准化该文件；如果是目录，递归处理所有 .lrc 文件。"
        ),
    )

    # ⭐ 新增：-m/--match 模式
    parser.add_argument(
        "-m", "--match",
        action="store_true",
        help=(
            "匹配模式：处理完成后，将 LRC 文件移动到 --done-tracks 目录"
            "（而不是 --done-lrc），并重命名为与歌曲文件相同的名称。"
        ),
    )

    args = parser.parse_args()

    # ========== 模式零：-p/--parse 解析模式 ==========
    if args.parse is not None:
        target_path = Path(args.parse).resolve()
        try:
            parse_lrc_mode(target_path)
        except KeyboardInterrupt:
            print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
            sys.exit(0)
        return

    # ========== 模式一：-d/--default 模式 ==========
    if args.default is not None:
        tracks_arg, lrc_arg = args.default

        # ⭐ 不再使用 --root，直接解析路径
        tracks_dir = Path(tracks_arg).resolve()
        lrc_dir = Path(lrc_arg).resolve()

        # 提示：-d 模式强制非 dry-run 且必须人工确认
        if args.dry_run or args.yes:
            print("[WARN] -d 模式下会忽略 --dry-run 和 --yes，始终进行真实上传并需要人工确认。")

        # 忽略 -m 参数
        if args.match:
            print("[WARN] -d 模式下会忽略 -m/--match 参数。")

        # 构建配置：注意这里开启 pair_lrc_with_track_dir
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tracks_dir,
            lrc_dir=lrc_dir,
            done_tracks_dir=Path.cwd(),  # -d 模式不使用 done 目录
            done_lrc_dir=Path.cwd(),
            preview_lines=args.preview_lines,
            pair_lrc_with_track_dir=True,  # ⭐ 核心
            match_mode=False,
        )

        try:
            # -d 模式：强制 auto_yes=False, dry_run=False
            process_all(
                config,
                auto_yes=False,
                dry_run=False,
                single=args.single,
            )
        except KeyboardInterrupt:
            print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
            sys.exit(0)

        return

    # ========== 模式二：普通模式 / -m 模式 ==========
    # ⭐ 新逻辑：done_*_dir 不再在 CLI 层设置默认值，交给 config 层处理

    tracks_dir = Path(args.tracks).resolve() if args.tracks else None
    lrc_dir = Path(args.lrc).resolve() if args.lrc else None
    done_tracks_dir = Path(args.done_tracks).resolve() if args.done_tracks else None
    done_lrc_dir = Path(args.done_lrc).resolve() if args.done_lrc else None

    config = AppConfig.from_env_and_defaults(
        tracks_dir=tracks_dir,
        lrc_dir=lrc_dir,
        done_tracks_dir=done_tracks_dir,
        done_lrc_dir=done_lrc_dir,
        preview_lines=args.preview_lines,
        match_mode=args.match,
    )

    try:
        process_all(config, auto_yes=args.yes, dry_run=args.dry_run, single=args.single)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
        sys.exit(0)
