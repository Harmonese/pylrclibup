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

    parser.add_argument(
        "-d",
        "--default",
        nargs=2,
        metavar=("TRACKS_DIR", "LRC_DIR"),
        help=(
            "default 模式：使用指定歌曲目录和歌词目录，完整执行上传流程，"
            "但歌曲文件保持原地不动，匹配和使用过的 LRC 会被移动到对应歌曲文件所在目录。"
        ),
    )


    args = parser.parse_args()

    # ---------- 模式一：-d default 模式 ----------
    if args.default is not None:
        tracks_arg, lrc_arg = args.default

        root = Path(args.root).resolve()

        # 允许传相对路径：相对 root 解析
        tracks_dir = Path(tracks_arg)
        if not tracks_dir.is_absolute():
            tracks_dir = (root / tracks_dir).resolve()

        lrc_dir = Path(lrc_arg)
        if not lrc_dir.is_absolute():
            lrc_dir = (root / lrc_dir).resolve()

        # 提示：-d 模式强制非 dry-run 且必须人工确认
        if args.dry_run or args.yes:
            print("[WARN] -d 模式下会忽略 --dry-run 和 --yes，始终进行真实上传并需要人工确认。")

        # 构建配置：注意这里开启 pair_lrc_with_track_dir
        config = AppConfig.from_env_and_defaults(
            tracks_dir=tracks_dir,
            lrc_dir=lrc_dir,
            done_tracks_dir=root / args.done_tracks,
            done_lrc_dir=root / args.done_lrc,
            preview_lines=args.preview_lines,
            pair_lrc_with_track_dir=True,  # ⭐ 核心
        )

        try:
            # -d 模式：强制 auto_yes=False, dry_run=False
            process_all(
                config,
                auto_yes=False,
                dry_run=False,
                single=args.single,  # 可以照常用 --single
            )
        except KeyboardInterrupt:
            print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
            sys.exit(0)

        return  # ⭐ 不再执行后面的“普通模式”逻辑

    # ---------- 模式二：普通模式（不带 -d） ----------
    root = Path(args.root).resolve()
    config = AppConfig.from_env_and_defaults(
        tracks_dir=root / args.tracks,
        lrc_dir=root / args.lrc,
        done_tracks_dir=root / args.done_tracks,
        done_lrc_dir=root / args.done_lrc,
        preview_lines=args.preview_lines,
    )

    try:
        process_all(config, auto_yes=args.yes, dry_run=args.dry_run, single=args.single)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断执行（Ctrl+C），已优雅退出。")
        sys.exit(0)
