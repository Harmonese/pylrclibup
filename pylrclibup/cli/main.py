from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config import AppConfig
from ..processor import process_all, move_lrc_to_track_dirs


def run_cli():
    """
    pylrclibup 的命令行入口点。
    """

    parser = argparse.ArgumentParser(
        prog="pylrclibup",
        description="Upload lyrics or instrumental tags to LRCLIB with local files."
    )

    # 与你原脚本一致
    parser.add_argument("--yes", action="store_true",
                        help="不询问确认，默认选择“上传”或“使用外部歌词”")

    parser.add_argument("--dry-run", action="store_true",
                        help="仅预览，不执行任何上传和移动")

    parser.add_argument("--single", type=str,
                        help="只处理 tracks/ 中指定文件，例如 'foo.mp3'")

    # 新增：可自定义路径
    parser.add_argument("--root", default=".",
                        help="根目录（默认当前目录）")
    parser.add_argument("--tracks", default="tracks",
                        help="mp3 输入目录（相对 root）")
    parser.add_argument("--lrc", default="lrc-files",
                        help="lrc 输入目录（相对 root）")
    parser.add_argument("--done-tracks", default="done-tracks",
                        help="mp3 输出目录（相对 root）")
    parser.add_argument("--done-lrc", default="done-lrc-files",
                        help="lrc 输出目录（相对 root）")

    parser.add_argument("--preview-lines", type=int, default=10,
                        help="预览歌词时显示的行数")
    
    parser.add_argument(
        "-d",
        "--default-move",
        nargs=2,
        metavar=("TRACKS_DIR", "LRC_DIR"),
        help=(
            "仅进行本地匹配：第一个参数为歌曲根目录，第二个为 LRC 根目录；"
            "不会访问 LRCLIB，只在确认后将匹配到的 LRC 移动到对应歌曲目录。"
        ),
    )


    args = parser.parse_args()

    # ---------- 模式一：-d 本地匹配 & 移动 ----------
    if args.default_move:
        tracks_root_str, lrc_root_str = args.default_move
        tracks_root = Path(tracks_root_str).resolve()
        lrc_root = Path(lrc_root_str).resolve()

        if args.yes or args.dry_run or args.single:
            print("[WARN] -d 模式下会忽略 --yes / --dry-run / --single 这些参数。")

        try:
            move_lrc_to_track_dirs(tracks_root, lrc_root)
        except KeyboardInterrupt:
            print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
            sys.exit(0)
        return

    # ---------- 模式二：正常 LRCLIB 上传模式 ----------
    # 构建 AppConfig
    root = Path(args.root).resolve()

    config = AppConfig.from_env_and_defaults(
        tracks_dir=root / args.tracks,
        lrc_dir=root / args.lrc,
        done_tracks_dir=root / args.done_tracks,
        done_lrc_dir=root / args.done_lrc,
        preview_lines=args.preview_lines,
    )

    # 运行主流程
    try:
        process_all(
            config,
            auto_yes=args.yes,
            dry_run=args.dry_run,
            single=args.single,
        )
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
        sys.exit(0)
