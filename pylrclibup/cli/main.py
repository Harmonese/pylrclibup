from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config import AppConfig
from ..processor import process_all


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

    args = parser.parse_args()

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
