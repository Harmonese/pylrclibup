# ===== pylrclibup/cli/main.py（完整修复版）=====

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..config import AppConfig
from ..processor import process_all
from ..logging_utils import log_info, log_error
from ..i18n import setup_i18n, get_text as _


def _detect_lang_from_argv() -> str:
    """
    从命令行参数中提前检测 --lang 参数
    
    在创建 ArgumentParser 之前调用，以便正确显示多语言 help
    """
    args = sys.argv[1:]
    
    # 检查 --lang 或 --language
    for i, arg in enumerate(args):
        if arg in ('--lang', '--language'):
            if i + 1 < len(args):
                return args[i + 1]
        elif arg.startswith('--lang='):
            return arg.split('=', 1)[1]
        elif arg.startswith('--language='):
            return arg.split('=', 1)[1]
    
    # 未指定，返回 'auto'
    return 'auto'


def validate_args(args) -> None:
    """验证命令行参数的冲突规则"""
    # 规则 1：--follow 与 --done-lrc 冲突
    if args.follow and args.done_lrc:
        log_error(_("错误：--follow 与 --done-lrc 不能同时使用"))
        log_error(_("提示：--follow 表示 LRC 跟随音频文件，不应指定独立的 LRC 输出目录"))
        sys.exit(1)
    
    # 规则 2：-d 与 -m 冲突
    if args.default and args.match:
        log_error(_("错误：-d/--default 与 -m/--match 不能同时使用"))
        sys.exit(1)
    
    # 规则 3 & 4：快捷模式与其他参数冲突
    if args.default:
        conflicts = []
        if args.follow:
            conflicts.append("-f/--follow")
        if args.rename:
            conflicts.append("-r/--rename")
        if args.cleanse:
            conflicts.append("-c/--cleanse")
        if args.tracks or args.lrc or args.done_tracks or args.done_lrc:
            conflicts.append(_("路径参数"))
        
        if conflicts:
            log_error(_("错误：-d/--default 模式不能与以下参数同时使用：{conflicts}").format(
                conflicts=', '.join(conflicts)
            ))
            sys.exit(1)
    
    if args.match:
        conflicts = []
        if args.follow:
            conflicts.append("-f/--follow")
        if args.rename:
            conflicts.append("-r/--rename")
        if args.cleanse:
            conflicts.append("-c/--cleanse")
        
        if conflicts:
            log_error(_("错误：-m/--match 模式不能与以下参数同时使用：{conflicts}").format(
                conflicts=', '.join(conflicts)
            ))
            sys.exit(1)


def run_cli():
    """
    pylrclibup 的命令行入口点。
    """
    
    # ========== 🌍 提前初始化 i18n ==========
    detected_lang = _detect_lang_from_argv()
    if detected_lang != 'auto':
        setup_i18n(locale=detected_lang)
    else:
        setup_i18n()  # 自动检测系统语言
    
    # ========== 创建 ArgumentParser ==========
    parser = argparse.ArgumentParser(
        prog="pylrclibup",
        description=_("将本地歌词文件或纯音乐标记上传到 LRCLIB。")
    )

    # -------------------- 路径参数 --------------------
    parser.add_argument(
        "--tracks",
        type=str,
        help=_("音频文件输入目录（默认：当前工作目录）")
    )
    parser.add_argument(
        "--lrc",
        type=str,
        help=_("LRC 文件输入目录（默认：当前工作目录）")
    )
    parser.add_argument(
        "--done-tracks",
        type=str,
        help=_("处理后音频文件移动到的目录（默认：原地不动）")
    )
    parser.add_argument(
        "--done-lrc",
        type=str,
        help=_("处理后 LRC 文件移动到的目录（默认：原地不动/跟随音频，取决于 --follow 设置）")
    )

    # -------------------- 行为控制参数 --------------------
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help=_("LRC 文件跟随音频文件到同一目录（与 --done-lrc 冲突）")
    )
    parser.add_argument(
        "-r", "--rename",
        action="store_true",
        help=_("处理后将 LRC 重命名为与音频文件同名")
    )
    parser.add_argument(
        "-c", "--cleanse",
        action="store_true",
        help=_("处理前标准化 LRC 文件（移除制作信息、翻译等）")
    )

    # -------------------- 其他参数 --------------------
    parser.add_argument(
        "--preview-lines",
        type=int,
        default=10,
        help=_("预览歌词时显示的行数")
    )

    # -------------------- 快捷模式 --------------------
    parser.add_argument(
        "-d", "--default",
        nargs=2,
        metavar=("TRACKS_DIR", "LRC_DIR"),
        help=_(
            "快捷模式：等价于 --tracks TRACKS_DIR --lrc LRC_DIR --follow --rename --cleanse。"
            "音频文件保持原地不动，LRC 移动到音频目录并重命名，且会标准化 LRC 文件。"
        ),
    )

    parser.add_argument(
        "-m", "--match",
        action="store_true",
        help=_(
            "匹配模式：等价于 --follow --rename --cleanse。"
            "处理完成后，LRC 移动到音频目录并重命名为与音频文件相同的名称，且会标准化 LRC 文件。"
        ),
    )

    # -------------------- 语言选项 --------------------
    parser.add_argument(
        "--lang", "--language",
        type=str,
        choices=["zh_CN", "en_US", "auto"],
        default="auto",
        help=_("界面语言：zh_CN（简体中文）/ en_US（English）/ auto（自动检测）"),
    )

    args = parser.parse_args()

    # ========== 参数冲突检查 ==========
    validate_args(args)

    # ========== 统一处理所有模式 ==========
    
    # 处理 -d/--default 模式
    if args.default:
        tracks_arg, lrc_arg = args.default
        
        tracks_dir = Path(tracks_arg).resolve()
        lrc_dir = Path(lrc_arg).resolve()
        done_tracks_dir = None
        done_lrc_dir = None
        follow_mp3 = True
        rename_lrc = True
        cleanse_lrc = True
    
    # 处理 -m/--match 模式
    elif args.match:
        tracks_dir = Path(args.tracks).resolve() if args.tracks else None
        lrc_dir = Path(args.lrc).resolve() if args.lrc else None
        done_tracks_dir = Path(args.done_tracks).resolve() if args.done_tracks else None
        done_lrc_dir = None
        follow_mp3 = True
        rename_lrc = True
        cleanse_lrc = True
    
    # 普通模式
    else:
        tracks_dir = Path(args.tracks).resolve() if args.tracks else None
        lrc_dir = Path(args.lrc).resolve() if args.lrc else None
        done_tracks_dir = Path(args.done_tracks).resolve() if args.done_tracks else None
        done_lrc_dir = Path(args.done_lrc).resolve() if args.done_lrc else None
        follow_mp3 = args.follow
        rename_lrc = args.rename
        cleanse_lrc = args.cleanse

    # 创建配置
    config = AppConfig.from_env_and_defaults(
        tracks_dir=tracks_dir,
        lrc_dir=lrc_dir,
        done_tracks_dir=done_tracks_dir,
        done_lrc_dir=done_lrc_dir,
        follow_mp3=follow_mp3,
        rename_lrc=rename_lrc,
        cleanse_lrc=cleanse_lrc,
        preview_lines=args.preview_lines,
    )

    # 执行处理
    try:
        process_all(config)
    except KeyboardInterrupt:
        print("\n" + _("[信息] 用户中断执行（Ctrl+C），已优雅退出。"))
        sys.exit(0)
