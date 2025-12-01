# pylrclibup

[![PyPI version](https://badge.fury.io/py/pylrclibup.svg)](https://badge.fury.io/py/pylrclibup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A powerful CLI tool to upload local lyrics or instrumental markers to LRCLIB.net**

Upload your local LRC files to [LRCLIB](https://lrclib.net) with intelligent matching, multi-format audio support, automatic standardization, and robust error handling.

[English](#english) | [中文](#中文)

---

# English

## ✨ Features

### 🎵 Multi-Format Audio Support
- **Supported formats**: MP3, M4A, AAC, FLAC, WAV
- **Auto metadata extraction**: Title, Artist, Album, Duration
- Uses mutagen for universal tag reading across formats
- No reliance on filenames—uses actual embedded tags

### 🔍 Intelligent LRC Matching
- **Recursive scanning** of directories
- **Fuzzy artist matching** (supports multiple artists)
- **Normalized title comparison** (Unicode normalization, case-insensitive)
- **Multi-artist separators**: `,` `/` `;` `&` `x` `×` `feat.` `featuring` `和`
- **Interactive selection** when multiple matches found
- **Manual path input** when auto-match fails

### 🧹 Advanced LRC Standardization (`-c/--cleanse`)
- **Remove header content** before first timestamp
- **Strip credit lines**: 作词, 作曲, 编曲, 混音, etc.
- **Delete duplicate translations** (same timestamp, CJK detection)
- **Unicode normalization** (NFKC)
- **Fullwidth punctuation conversion**
- **Cyrillic character mapping** (ё→е, і→и, etc.)

### 🎼 Instrumental Track Detection
- Auto-detect "纯音乐，请欣赏" phrases
- Detect empty LRC content
- Manual instrumental marker upload option
- Uploads as empty lyrics with `instrumental: true`

### 🌐 Dual Query System
- **`/api/get-cached`**: Internal database only (fast, no external calls)
- **`/api/get`**: Triggers external scraping (Genius, Musixmatch, etc.)
- **Smart decision flow**:
  1. Check internal DB → auto-move if exists
  2. Check external sources → user chooses to use or skip
  3. Parse local LRC → upload with confirmation

### 🚀 Robust Upload Process
- **Custom PoW solver** (SHA-256 based, no external dependencies)
- **Auto challenge handling**: request → solve → publish
- **Token generation**: prefix + nonce calculation
- **Network-resilient**

### 🔁 Intelligent Retry Mechanism
- **Exponential backoff** with jitter (1s → 2s → 4s → 8s → 16s → 30s max)
- **5xx errors**: auto-retry
- **4xx errors**: fail immediately (parameter/token issues)
- **404**: treated as "not found" (expected, non-error)
- **Configurable**: `--max-retries` or `PYLRCLIBUP_MAX_HTTP_RETRIES`

### 📁 Flexible File Management
Three independent flags for complete control:

| Flag | Effect |
|------|--------|
| `-f` / `--follow` | LRC follows audio to same directory |
| `-r` / `--rename` | Rename LRC to match audio filename |
| `-c` / `--cleanse` | Standardize LRC before processing |

**Preset Modes**:
- **`-d/--default`** = `-f -r -c`: Quick setup (audio stays, LRC moves+renames+cleanses)
- **`-m/--match`** = `-f -r -c`: Match mode (same as default)

### 🌍 Internationalization (i18n)
- **Auto language detection**: Chinese for `zh_*` locales, English otherwise
- **Manual override**: `--lang en_US` or `--lang zh_CN`
- **Environment variable**: `PYLRCLIBUP_LANG=en_US`
- **Fully translated**: CLI help, logs, errors, prompts

### 🧪 Clean & Safe
- **Empty directory cleanup**: Auto-remove empty dirs after moving files
- **Duplicate handling**: Auto-rename with `_dup1`, `_dup2`, etc.
- **Non-destructive**: Original files preserved on failure
- **Graceful Ctrl+C**: Clean exit on user interrupt

---

## 📥 Installation

### From PyPI (Recommended)

```bash
pip install pylrclibup
```

### From Source (Development)

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e .
```

---

## 🚀 Quick Start

### Basic Usage (In-Place Mode)

Process all audio files in current directory without moving anything:

```bash
cd /path/to/music
pylrclibup
```

**Behavior**:
- ✅ Recursively scans for audio files (MP3, M4A, AAC, FLAC, WAV)
- ✅ Finds matching LRC files
- ✅ Uploads to LRCLIB
- ✅ Files stay in place

---

## 📖 Usage Examples

### 1. Quick Mode (`-d/--default`)

**Best for**: Moving LRC files from downloads to music library

```bash
pylrclibup -d "/music/tracks" "/downloads/lyrics"
```

**What it does**:
- Audio files: Stay in `/music/tracks`
- LRC files: Move to audio directory + rename to match + standardize
- Equivalent to: `--tracks /music/tracks --lrc /downloads/lyrics -f -r -c`

---

### 2. Match Mode (`-m/--match`)

**Best for**: Organizing lyrics to follow audio files

```bash
pylrclibup -m
```

**What it does**:
- Uses current directory for both audio and LRC
- LRC follows audio + renames + cleanses
- Equivalent to: `-f -r -c`

---

### 3. Custom Mode (Maximum Control)

**Example**: Separate input/output directories with selective options

```bash
pylrclibup \
  --tracks "/music/input" \
  --lrc "/lyrics/input" \
  --done-tracks "/music/output" \
  --done-lrc "/lyrics/output" \
  --rename --cleanse
```

**What it does**:
- Audio: `/music/input` → `/music/output`
- LRC: `/lyrics/input` → `/lyrics/output`
- LRC renamed to match audio (`--rename`)
- LRC standardized (`--cleanse`)
- LRC doesn't follow audio (no `--follow`)

---

### 4. Follow Mode Only

**Example**: Keep structure, just move LRC to audio directories

```bash
pylrclibup --follow
```

**What it does**:
- Audio: Stays in place
- LRC: Moves to audio directory (keeps original LRC filename)

---

### 5. Standardize LRC Only

**Example**: Clean up LRC files without uploading

```bash
pylrclibup --lrc "/path/to/lyrics" --cleanse
```

Or standardize then process:

```bash
# Step 1: Clean LRC files
pylrclibup --lrc "/lyrics" --cleanse

# Step 2: Upload
pylrclibup --tracks "/music" --lrc "/lyrics"
```

---

### 6. Preview Lyrics

Control how many lines are shown during confirmation:

```bash
pylrclibup --preview-lines 20
```

---

### 7. Language Selection

```bash
# Force English interface
pylrclibup --lang en_US

# Force Chinese interface
pylrclibup --lang zh_CN

# Auto-detect (default)
pylrclibup --lang auto
```

---

## 🎯 Common Scenarios

| Scenario | Command | Audio Behavior | LRC Behavior |
|----------|---------|----------------|--------------|
| **Upload only** | `pylrclibup` | In-place | In-place |
| **Organize lyrics to music lib** | `pylrclibup -d /music /downloads` | In-place | Move + rename + cleanse |
| **Match lyrics to audio** | `pylrclibup -m` | In-place | Move + rename + cleanse |
| **Separate outputs** | `pylrclibup --done-tracks /a --done-lrc /b` | Move to /a | Move to /b |
| **Clean LRC files** | `pylrclibup --lrc /lyrics -c` | N/A | Standardize in-place |
| **Custom workflow** | `pylrclibup -f -r` | In-place | Move + rename (no cleanse) |

---

## ⚙️ Environment Variables

Override defaults without CLI arguments:

```bash
# Input directories
export PYLRCLIBUP_TRACKS_DIR="/data/music"
export PYLRCLIBUP_LRC_DIR="/data/lyrics"

# Output directories
export PYLRCLIBUP_DONE_TRACKS_DIR="/data/processed/music"
export PYLRCLIBUP_DONE_LRC_DIR="/data/processed/lyrics"

# Configuration
export PYLRCLIBUP_PREVIEW_LINES=15
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
export PYLRCLIBUP_USER_AGENT="MyMusicApp/2.0"
export PYLRCLIBUP_LANG=en_US

# Run with env vars
pylrclibup
```

**Priority**: CLI args > Environment variables > Defaults

---

## 📋 Full CLI Reference

```
pylrclibup [OPTIONS]

Path Options:
  --tracks PATH          Audio files input directory (default: current dir)
  --lrc PATH             LRC files input directory (default: current dir)
  --done-tracks PATH     Move processed audio to this directory
  --done-lrc PATH        Move processed LRC to this directory

Behavior Options:
  -f, --follow           LRC follows audio to same directory
  -r, --rename           Rename LRC to match audio filename
  -c, --cleanse          Standardize LRC before processing

Preset Modes:
  -d, --default TRACKS LRC
                         Quick mode: audio stays, LRC moves+renames+cleanses
                         (equivalent to: --tracks TRACKS --lrc LRC -f -r -c)

  -m, --match            Match mode: LRC follows audio with rename+cleanse
                         (equivalent to: -f -r -c)

Other Options:
  --preview-lines N      Number of lyric lines to show (default: 10)
  --lang LANG            Interface language: zh_CN | en_US | auto (default: auto)
  -h, --help             Show this help message
  --version              Show version number

Conflicts:
  • --follow and --done-lrc cannot be used together
  • -d/--default and -m/--match cannot be used together
  • Preset modes cannot be combined with individual flags
```

---

## 🛠️ Advanced Usage

### Recursive Directory Processing

```bash
# Directory structure:
# /music/
#   Artist 1/
#     Album A/
#       01 - Song.mp3
#   Artist 2/
#     02 - Song.m4a

cd /music
pylrclibup -m
```

**Result**: Each LRC moves to its corresponding audio directory

---

### Manual LRC Path Input

When auto-matching fails:

```
未找到本地 LRC，选择 [s] 跳过该歌曲 / [m] 手动指定歌词文件 / [i] 上传空歌词标记为纯音乐 / [q] 退出程序: m
请输入 LRC 文件的完整路径: /path/to/lyrics/song.lrc
```

**Supports**:
- Absolute paths: `/home/user/lyrics/song.lrc`
- Relative paths: `../lyrics/song.lrc`
- Home expansion: `~/Music/lyrics/song.lrc`
- Quoted paths: `"/path/with spaces/song.lrc"`

---

### External Lyrics Integration

When LRCLIB finds external lyrics:

```
外部抓取到歌词（仅供参考，可选择是否直接使用外部版本上传）：
--- 外部 plainLyrics ---
[External lyrics content...]
--- 外部 syncedLyrics ---
[External synced lyrics...]

是否直接使用外部版本上传？[y/N]: y
```

**Options**:
- `y`: Upload external version directly (skip local LRC)
- `N`: Continue with local LRC (default)

---

### Instrumental Tracks

For tracks without lyrics:

```
未找到本地 LRC，选择 [s] 跳过该歌曲 / [m] 手动指定歌词文件 / [i] 上传空歌词标记为纯音乐 / [q] 退出程序: i
将上传空歌词（标记为纯音乐）。
```

**Or** auto-detected from LRC content:
```
[00:00.00]纯音乐，请欣赏
```

---

## 🔧 Configuration Tips

### Optimize Network Performance

For unstable connections:

```bash
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
pylrclibup
```

### Custom User-Agent

```bash
export PYLRCLIBUP_USER_AGENT="MyApp/1.0 (https://example.com)"
pylrclibup
```

### Batch Processing Script

```bash
#!/bin/bash
# process_library.sh

export PYLRCLIBUP_LANG=en_US
export PYLRCLIBUP_MAX_HTTP_RETRIES=5

# Process each artist directory
for dir in /music/*/; do
    echo "Processing: $dir"
    pylrclibup --tracks "$dir" --lrc "/downloads/lyrics" -f -r -c
done
```

---

## 🧪 Testing & Validation

### Test Language Detection

```bash
# English environment
LANG=en_US.UTF-8 pylrclibup -h

# Chinese environment
LANG=zh_CN.UTF-8 pylrclibup -h
```

### Verify Installation

```bash
pylrclibup --version
python -c "import pylrclibup; print(pylrclibup.__version__)"
```

---

## 🐛 Troubleshooting

### Issue: "No supported audio files found"

**Cause**: No MP3/M4A/AAC/FLAC/WAV files in directory

**Solution**: 
```bash
# Check file types
ls -la /path/to/music

# Use correct directory
pylrclibup --tracks /correct/path
```

---

### Issue: "LRC file not found"

**Cause**: Filename mismatch or wrong directory

**Solution**:
```bash
# Check LRC naming: "Artist - Title.lrc"
# Ensure artist/title match audio metadata

# Manual specification
pylrclibup  # then choose [m] and input path
```

---

### Issue: "HTTP request failed"

**Cause**: Network instability

**Solution**:
```bash
# Increase retries
pylrclibup --max-retries 10

# Or use environment variable
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
pylrclibup
```

---

### Issue: Translation not working

**Cause**: Missing compiled .mo files

**Solution**:
```bash
cd pylrclibup
./scripts/compile_translations.sh

# Or manually
msgfmt locales/en_US/LC_MESSAGES/pylrclibup.po \
       -o locales/en_US/LC_MESSAGES/pylrclibup.mo
```

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `pytest tests/`
4. **Commit**: `git commit -m "Add amazing feature"`
5. **Push**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Development Setup

```bash
# Clone repo
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
flake8 pylrclibup
mypy pylrclibup
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- [LRCLIB.net](https://lrclib.net) - Free lyrics API service
- [Mutagen](https://mutagen.readthedocs.io/) - Audio metadata library
- Community contributors and testers

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Harmonese/pylrclibup/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Harmonese/pylrclibup/discussions)
- **Email**: [your-email@example.com](mailto:your-email@example.com)

---

## 🗺️ Roadmap

- [ ] GUI application (Electron/Tauri)
- [ ] Batch processing progress bar
- [ ] Lyrics quality validation
- [ ] More language translations (日本語, 한국어, Español, etc.)
- [ ] Plugin system for custom processors

---

<div align="center">

**Made with ❤️ by [Harmonese](https://github.com/Harmonese)**

⭐ Star this repo if you find it helpful!

</div>

---

# 中文

## ✨ 功能特性

### 🎵 多格式音频支持
- **支持格式**: MP3, M4A, AAC, FLAC, WAV
- **自动提取元数据**: 标题、艺人、专辑、时长
- 使用 mutagen 库实现跨格式统一标签读取
- 不依赖文件名——使用真实的嵌入标签

### 🔍 智能 LRC 匹配
- **递归扫描**目录
- **模糊艺人匹配**（支持多艺人）
- **标准化曲名比较**（Unicode 规范化、忽略大小写）
- **多艺人分隔符**: `,` `/` `;` `&` `x` `×` `feat.` `featuring` `和`
- **交互式选择**（当匹配到多个文件时）
- **手动输入路径**（当自动匹配失败时）

### 🧹 高级 LRC 标准化 (`-c/--cleanse`)
- **删除歌词头部**（第一个时间戳之前的内容）
- **移除制作信息行**: 作词、作曲、编曲、混音等
- **删除重复翻译行**（相同时间戳、CJK 检测）
- **Unicode 规范化** (NFKC)
- **全角标点转换**
- **西里尔字母映射**（ё→е, і→и 等）

### 🎼 纯音乐识别
- 自动检测"纯音乐，请欣赏"等短语
- 检测空 LRC 内容
- 手动上传纯音乐标记选项
- 上传为空歌词并标记 `instrumental: true`

### 🌐 双查询系统
- **`/api/get-cached`**: 仅查询内部数据库（快速、无外部请求）
- **`/api/get`**: 触发外部抓取（Genius、Musixmatch 等）
- **智能决策流程**:
  1. 检查内部数据库 → 存在则自动移动
  2. 检查外部来源 → 用户选择是否使用
  3. 解析本地 LRC → 确认后上传

### 🚀 健壮的上传流程
- **自定义 PoW 求解器**（基于 SHA-256，无外部依赖）
- **自动 challenge 处理**: 请求 → 求解 → 发布
- **令牌生成**: prefix + nonce 计算
- **网络容错**

### 🔁 智能重试机制
- **指数退避 + 抖动**（1s → 2s → 4s → 8s → 16s → 30s 上限）
- **5xx 错误**: 自动重试
- **4xx 错误**: 立即停止（参数/令牌问题）
- **404**: 视为"未找到"（预期情况，非错误）
- **可配置**: `--max-retries` 或 `PYLRCLIBUP_MAX_HTTP_RETRIES`

### 📁 灵活的文件管理
三个独立标志实现完全控制:

| 标志 | 作用 |
|------|------|
| `-f` / `--follow` | LRC 跟随音频文件到同一目录 |
| `-r` / `--rename` | LRC 重命名为与音频文件相同 |
| `-c` / `--cleanse` | 处理前标准化 LRC |

**预设模式**:
- **`-d/--default`** = `-f -r -c`: 快速模式（音频不动，LRC 移动+重命名+标准化）
- **`-m/--match`** = `-f -r -c`: 匹配模式（同默认模式）

### 🌍 国际化 (i18n)
- **自动语言检测**: `zh_*` 显示中文，其他显示英文
- **手动覆盖**: `--lang en_US` 或 `--lang zh_CN`
- **环境变量**: `PYLRCLIBUP_LANG=en_US`
- **完整翻译**: CLI 帮助、日志、错误、提示

### 🧪 清洁安全
- **空目录清理**: 移动文件后自动删除空目录
- **重名处理**: 自动重命名为 `_dup1`, `_dup2` 等
- **非破坏性**: 失败时保留原始文件
- **优雅退出**: Ctrl+C 干净退出

---

## 📥 安装

### 从 PyPI 安装（推荐）

```bash
pip install pylrclibup
```

### 从源码安装（开发）

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e .
```

---

## 🚀 快速开始

### 基本用法（原地模式）

处理当前目录所有音频文件，不移动任何文件:

```bash
cd /path/to/music
pylrclibup
```

**行为**:
- ✅ 递归扫描音频文件（MP3、M4A、AAC、FLAC、WAV）
- ✅ 查找匹配的 LRC 文件
- ✅ 上传到 LRCLIB
- ✅ 文件保持原地

---

## 📖 使用示例

### 1. 快速模式（`-d/--default`）

**适用于**: 从下载目录整理 LRC 到音乐库

```bash
pylrclibup -d "/music/tracks" "/downloads/lyrics"
```

**效果**:
- 音频文件: 保持在 `/music/tracks`
- LRC 文件: 移动到音频目录 + 重命名匹配 + 标准化
- 等同于: `--tracks /music/tracks --lrc /downloads/lyrics -f -r -c`

---

### 2. 匹配模式（`-m/--match`）

**适用于**: 整理歌词跟随音频文件

```bash
pylrclibup -m
```

**效果**:
- 使用当前目录作为音频和 LRC 输入
- LRC 跟随音频 + 重命名 + 标准化
- 等同于: `-f -r -c`

---

### 3. 自定义模式（最大控制）

**示例**: 分别指定输入/输出目录，选择性选项

```bash
pylrclibup \
  --tracks "/music/input" \
  --lrc "/lyrics/input" \
  --done-tracks "/music/output" \
  --done-lrc "/lyrics/output" \
  --rename --cleanse
```

**效果**:
- 音频: `/music/input` → `/music/output`
- LRC: `/lyrics/input` → `/lyrics/output`
- LRC 重命名匹配音频（`--rename`）
- LRC 标准化（`--cleanse`）
- LRC 不跟随音频（无 `--follow`）

---

### 4. 仅跟随模式

**示例**: 保持结构，仅将 LRC 移动到音频目录

```bash
pylrclibup --follow
```

**效果**:
- 音频: 保持原地
- LRC: 移动到音频目录（保持原 LRC 文件名）

---

### 5. 仅标准化 LRC

**示例**: 清理 LRC 文件但不上传

```bash
pylrclibup --lrc "/path/to/lyrics" --cleanse
```

或先标准化再处理:

```bash
# 步骤 1: 清理 LRC 文件
pylrclibup --lrc "/lyrics" --cleanse

# 步骤 2: 上传
pylrclibup --tracks "/music" --lrc "/lyrics"
```

---

### 6. 预览歌词

控制确认时显示的行数:

```bash
pylrclibup --preview-lines 20
```

---

### 7. 语言选择

```bash
# 强制英文界面
pylrclibup --lang en_US

# 强制中文界面
pylrclibup --lang zh_CN

# 自动检测（默认）
pylrclibup --lang auto
```

---

## 🎯 常见场景

| 场景 | 命令 | 音频行为 | LRC 行为 |
|------|------|----------|----------|
| **仅上传** | `pylrclibup` | 原地 | 原地 |
| **整理歌词到音乐库** | `pylrclibup -d /music /downloads` | 原地 | 移动 + 重命名 + 标准化 |
| **歌词匹配音频** | `pylrclibup -m` | 原地 | 移动 + 重命名 + 标准化 |
| **分别输出** | `pylrclibup --done-tracks /a --done-lrc /b` | 移动到 /a | 移动到 /b |
| **清理 LRC** | `pylrclibup --lrc /lyrics -c` | N/A | 原地标准化 |
| **自定义工作流** | `pylrclibup -f -r` | 原地 | 移动 + 重命名（不标准化） |

---

## ⚙️ 环境变量

无需 CLI 参数即可覆盖默认值:

```bash
# 输入目录
export PYLRCLIBUP_TRACKS_DIR="/data/music"
export PYLRCLIBUP_LRC_DIR="/data/lyrics"

# 输出目录
export PYLRCLIBUP_DONE_TRACKS_DIR="/data/processed/music"
export PYLRCLIBUP_DONE_LRC_DIR="/data/processed/lyrics"

# 配置
export PYLRCLIBUP_PREVIEW_LINES=15
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
export PYLRCLIBUP_USER_AGENT="MyMusicApp/2.0"
export PYLRCLIBUP_LANG=zh_CN

# 使用环境变量运行
pylrclibup
```

**优先级**: CLI 参数 > 环境变量 > 默认值

---

## 📋 完整 CLI 参考

```
pylrclibup [选项]

路径选项:
  --tracks PATH          音频文件输入目录（默认：当前目录）
  --lrc PATH             LRC 文件输入目录（默认：当前目录）
  --done-tracks PATH     处理后音频文件移动目录
  --done-lrc PATH        处理后 LRC 文件移动目录

行为选项:
  -f, --follow           LRC 跟随音频文件到同一目录
  -r, --rename           LRC 重命名为与音频文件相同
  -c, --cleanse          处理前标准化 LRC

预设模式:
  -d, --default TRACKS LRC
                         快速模式：音频不动，LRC 移动+重命名+标准化
                         （等同于: --tracks TRACKS --lrc LRC -f -r -c）

  -m, --match            匹配模式：LRC 跟随音频并重命名+标准化
                         （等同于: -f -r -c）

其他选项:
  --preview-lines N      显示的歌词行数（默认：10）
  --lang LANG            界面语言: zh_CN | en_US | auto（默认：auto）
  -h, --help             显示此帮助信息
  --version              显示版本号

冲突规则:
  • --follow 与 --done-lrc 不能同时使用
  • -d/--default 与 -m/--match 不能同时使用
  • 预设模式不能与单独标志组合使用
```

---

## 🛠️ 高级用法

### 递归目录处理

```bash
# 目录结构:
# /music/
#   艺人 1/
#     专辑 A/
#       01 - 歌曲.mp3
#   艺人 2/
#     02 - 歌曲.m4a

cd /music
pylrclibup -m
```

**结果**: 每个 LRC 移动到对应的音频目录

---

### 手动输入 LRC 路径

当自动匹配失败时:

```
未找到本地 LRC，选择 [s] 跳过该歌曲 / [m] 手动指定歌词文件 / [i] 上传空歌词标记为纯音乐 / [q] 退出程序: m
请输入 LRC 文件的完整路径: /path/to/lyrics/song.lrc
```

**支持**:
- 绝对路径: `/home/user/lyrics/song.lrc`
- 相对路径: `../lyrics/song.lrc`
- Home 展开: `~/Music/lyrics/song.lrc`
- 引号路径: `"/path/with spaces/song.lrc"`

---

### 外部歌词整合

当 LRCLIB 找到外部歌词时:

```
外部抓取到歌词（仅供参考，可选择是否直接使用外部版本上传）：
--- 外部 plainLyrics ---
[外部歌词内容...]
--- 外部 syncedLyrics ---
[外部同步歌词...]

是否直接使用外部版本上传？[y/N]: y
```

**选项**:
- `y`: 直接上传外部版本（跳过本地 LRC）
- `N`: 继续使用本地 LRC（默认）

---

### 纯音乐曲目

对于无歌词的曲目:

```
未找到本地 LRC，选择 [s] 跳过该歌曲 / [m] 手动指定歌词文件 / [i] 上传空歌词标记为纯音乐 / [q] 退出程序: i
将上传空歌词（标记为纯音乐）。
```

**或**从 LRC 内容自动检测:
```
[00:00.00]纯音乐，请欣赏
```

---

## 🔧 配置技巧

### 优化网络性能

对于不稳定的连接:

```bash
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
pylrclibup
```

### 自定义 User-Agent

```bash
export PYLRCLIBUP_USER_AGENT="MyApp/1.0 (https://example.com)"
pylrclibup
```

### 批量处理脚本

```bash
#!/bin/bash
# process_library.sh

export PYLRCLIBUP_LANG=zh_CN
export PYLRCLIBUP_MAX_HTTP_RETRIES=5

# 处理每个艺人目录
for dir in /music/*/; do
    echo "正在处理: $dir"
    pylrclibup --tracks "$dir" --lrc "/downloads/lyrics" -f -r -c
done
```

---

## 🧪 测试与验证

### 测试语言检测

```bash
# 英文环境
LANG=en_US.UTF-8 pylrclibup -h

# 中文环境
LANG=zh_CN.UTF-8 pylrclibup -h
```

### 验证安装

```bash
pylrclibup --version
python -c "import pylrclibup; print(pylrclibup.__version__)"
```

---

## 🐛 故障排查

### 问题: "未找到任何支持的音频文件"

**原因**: 目录中没有 MP3/M4A/AAC/FLAC/WAV 文件

**解决方案**: 
```bash
# 检查文件类型
ls -la /path/to/music

# 使用正确的目录
pylrclibup --tracks /correct/path
```

---

### 问题: "未找到 LRC 文件"

**原因**: 文件名不匹配或目录错误

**解决方案**:
```bash
# 检查 LRC 命名: "艺人 - 标题.lrc"
# 确保艺人/标题匹配音频元数据

# 手动指定
pylrclibup  # 然后选择 [m] 并输入路径
```

---

### 问题: "HTTP 请求失败"

**原因**: 网络不稳定

**解决方案**:
```bash
# 增加重试次数
pylrclibup --max-retries 10

# 或使用环境变量
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
pylrclibup
```

---

### 问题: 翻译不工作

**原因**: 缺少编译的 .mo 文件

**解决方案**:
```bash
cd pylrclibup
./scripts/compile_translations.sh

# 或手动编译
msgfmt locales/en_US/LC_MESSAGES/pylrclibup.po \
       -o locales/en_US/LC_MESSAGES/pylrclibup.mo
```

---

## 🤝 贡献

欢迎贡献！流程如下:

1. **Fork 仓库**
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **修改并测试**: `pytest tests/`
4. **提交**: `git commit -m "添加某某功能"`
5. **推送**: `git push origin feature/amazing-feature`
6. **创建 Pull Request**

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup

# 以可编辑模式安装（含开发依赖）
pip install -e ".[dev]"

# 运行测试
pytest

# 运行代码检查
flake8 pylrclibup
mypy pylrclibup
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LRCLIB.net](https://lrclib.net) - 免费歌词 API 服务
- [Mutagen](https://mutagen.readthedocs.io/) - 音频元数据库
- 社区贡献者和测试者

---

## 📞 支持

- **问题反馈**: [GitHub Issues](https://github.com/Harmonese/pylrclibup/issues)
- **讨论**: [GitHub Discussions](https://github.com/Harmonese/pylrclibup/discussions)
- **邮件**: [your-email@example.com](mailto:your-email@example.com)

---

## 🗺️ 路线图

- [ ] GUI 应用程序（Electron/Tauri）
- [ ] 批量处理进度条
- [ ] 歌词质量验证
- [ ] 更多语言翻译（日本語、한국어、Español 等）
- [ ] 插件系统支持自定义处理器
- [ ] Docker 镜像
- [ ] Web API 封装
- [ ] 歌词同步编辑器集成

---

## 📚 附录

### A. 文件命名规范

**推荐的 LRC 文件命名格式**:

```
艺人 - 歌曲名.lrc
Artist - Song Title.lrc
艺人A & 艺人B - 歌曲名.lrc
Artist A feat. Artist B - Song.lrc
```

**支持的艺人分隔符**:
- `&` (和号)
- `,` (逗号)
- `/` (斜杠)
- `;` (分号)
- `、` (顿号)
- `x` / `×` (乘号)
- `feat.` / `featuring` (合作标记)
- `和` (中文"和")

---

### B. LRC 标准化详解

**标准化操作清单**:

1. **删除头部标签**:
   ```
   [ti:歌曲名]
   [ar:艺人]
   [al:专辑]
   ```

2. **移除制作信息**:
   ```
   [00:00.00]作词：张三
   [00:01.00]作曲：李四
   [00:02.00]编曲：王五
   ```

3. **删除翻译行**（相同时间戳）:
   ```
   [00:10.00]Hello world
   [00:10.00]你好世界  ← 删除此行
   ```

4. **Unicode 规范化**:
   - 全角 → 半角: `（` → `(`
   - 西里尔映射: `ё` → `е`
   - 空格规范化: 多个空格 → 单个空格

5. **纯音乐检测**:
   ```
   [00:00.00]纯音乐，请欣赏  ← 整行删除
   ```

---

### C. 环境变量完整列表

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `PYLRCLIBUP_TRACKS_DIR` | 路径 | 当前目录 | 音频文件输入目录 |
| `PYLRCLIBUP_LRC_DIR` | 路径 | 当前目录 | LRC 文件输入目录 |
| `PYLRCLIBUP_DONE_TRACKS_DIR` | 路径 | `None` | 音频文件输出目录 |
| `PYLRCLIBUP_DONE_LRC_DIR` | 路径 | `None` | LRC 文件输出目录 |
| `PYLRCLIBUP_PREVIEW_LINES` | 整数 | `10` | 预览歌词行数 |
| `PYLRCLIBUP_MAX_HTTP_RETRIES` | 整数 | `5` | HTTP 最大重试次数 |
| `PYLRCLIBUP_USER_AGENT` | 字符串 | `pylrclibup (...)` | 自定义 User-Agent |
| `PYLRCLIBUP_LANG` | 字符串 | `auto` | 界面语言（zh_CN/en_US/auto） |

---

### D. API 端点说明

**LRCLIB API 基础**: `https://lrclib.net/api`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/get-cached` | GET | 仅查询内部数据库 |
| `/get` | GET | 触发外部抓取 |
| `/request-challenge` | POST | 获取 PoW challenge |
| `/publish` | POST | 上传歌词（需 X-Publish-Token） |

**查询参数**:
- `track_name`: 歌曲名
- `artist_name`: 艺人名
- `album_name`: 专辑名
- `duration`: 时长（秒）

**上传参数**:
```json
{
  "trackName": "Song Title",
  "artistName": "Artist Name",
  "albumName": "Album Name",
  "duration": 180,
  "plainLyrics": "...",      // 可选
  "syncedLyrics": "[00:00.00]..."  // 可选
}
```

**纯音乐上传**（两种歌词字段均省略）:
```json
{
  "trackName": "Instrumental Track",
  "artistName": "Artist Name",
  "albumName": "Album Name",
  "duration": 180
}
```

---

### E. 常见问题 (FAQ)

**Q: 为什么我的 LRC 文件没有被匹配到？**

A: 检查以下几点:
1. LRC 文件名格式: `艺人 - 歌曲名.lrc`
2. 艺人名与音频文件标签一致（至少一个艺人匹配）
3. 歌曲名标准化后完全一致
4. LRC 文件在正确的搜索目录下

---

**Q: 可以批量处理多个目录吗？**

A: 可以，使用脚本循环处理:
```bash
for dir in /music/*/; do
    pylrclibup --tracks "$dir" -m
done
```

---

**Q: 如何处理已经上传过的歌曲？**

A: 程序会自动检测:
- 调用 `/api/get-cached` 查询内部数据库
- 如果已存在，自动跳过上传，只移动文件
- 不会重复提交相同歌词

---

**Q: 支持哪些音频格式？**

A: 支持以下格式（需要有元数据标签）:
- MP3 (ID3v2)
- M4A / AAC (iTunes MP4 tags)
- FLAC (Vorbis Comments)
- WAV (ID3 或 Vorbis Comments)

---

**Q: 为什么外部歌词与本地 LRC 不同？**

A: LRCLIB 的外部抓取来自:
- Genius
- Musixmatch
- 其他公开歌词源

这些来源可能与本地 LRC 有差异，程序会让你选择使用哪个版本。

---

**Q: 如何贡献翻译？**

A: 流程如下:
1. 复制 `locales/pylrclibup.pot` 为新语言 `locales/ja_JP/LC_MESSAGES/pylrclibup.po`
2. 编辑 `.po` 文件添加翻译
3. 编译: `msgfmt pylrclibup.po -o pylrclibup.mo`
4. 提交 Pull Request

---

**Q: 程序会修改原始音频文件吗？**

A: 不会。程序只:
- 读取音频文件的元数据标签
- 移动文件到目标目录（如果配置了）
- 不修改音频内容或标签

---

**Q: 如何处理网络代理？**

A: 设置环境变量:
```bash
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"
pylrclibup
```

---

### F. 性能优化建议

**大型音乐库处理**:

1. **分批处理**:
   ```bash
   # 每次处理 100 个文件
   find /music -name "*.mp3" | head -100 | while read file; do
       pylrclibup --tracks "$(dirname "$file")" -m
   done
   ```

2. **并行处理**（小心 API 限流）:
   ```bash
   # 使用 GNU parallel（谨慎使用）
   find /music -type d | parallel -j 4 'pylrclibup --tracks {} -m'
   ```

3. **预先标准化 LRC**:
   ```bash
   # 第一步：批量标准化
   pylrclibup --lrc /all/lyrics -c
 
   # 第二步：批量上传
   pylrclibup --tracks /music --lrc /all/lyrics -f -r
   ```

---

## 📖 参考资料

- [LRCLIB API 文档](https://lrclib.net/docs)
- [LRC 格式规范](https://en.wikipedia.org/wiki/LRC_(file_format))
- [Mutagen 文档](https://mutagen.readthedocs.io/)
- [Python gettext 文档](https://docs.python.org/3/library/gettext.html)

---

## 🔗 相关项目

- [LRCGET](https://github.com/tranxuanthang/lrcget) - LRCLIB 的 GUI 客户端
- [MusicBrainz Picard](https://picard.musicbrainz.org/) - 音乐元数据编辑器
- [beets](https://beets.io/) - 音乐库管理工具

---

## 📊 项目统计

```bash
# 代码统计
find pylrclibup -name "*.py" | xargs wc -l

# 测试覆盖率
pytest --cov=pylrclibup --cov-report=html

# 类型检查
mypy pylrclibup --strict
```

---

<div align="center">

**用 ❤️ 制作 by [Harmonese](https://github.com/Harmonese)**

⭐ 如果觉得有用，请给个 Star！

[![GitHub stars](https://img.shields.io/github/stars/Harmonese/pylrclibup.svg?style=social&label=Star)](https://github.com/Harmonese/pylrclibup)
[![GitHub forks](https://img.shields.io/github/forks/Harmonese/pylrclibup.svg?style=social&label=Fork)](https://github.com/Harmonese/pylrclibup/fork)

[报告 Bug](https://github.com/Harmonese/pylrclibup/issues) · [请求功能](https://github.com/Harmonese/pylrclibup/issues) · [贡献代码](https://github.com/Harmonese/pylrclibup/pulls)

</div>

---

## 🎉 更新日志

### v0.3.0 (Latest)
- ✨ 新增多格式音频支持（M4A, AAC, FLAC, WAV）
- ✨ 完整 i18n 支持（中文/英文自动切换）
- ✨ 智能语言检测（中文环境显示中文，其他显示英文）
- 🔧 重构配置系统（三个独立标志：-f/-r/-c）
- 🐛 修复银行家舍入导致的时长匹配问题
- 📝 完善文档和示例

### v0.2.0
- ✨ 新增双查询机制（内部数据库 + 外部抓取）
- ✨ 新增 LRC 标准化功能（-c/--cleanse）
- ✨ 新增手动指定歌词路径
- 🔧 改进重试机制（指数退避 + 抖动）
- 🐛 修复多艺人匹配问题

### v0.1.0
- 🎉 首次发布
- ✨ 基础上传功能
- ✨ 自动匹配本地 LRC
- ✨ PoW 求解器

---

**感谢使用 pylrclibup！**

如有问题或建议，欢迎在 [GitHub Issues](https://github.com/Harmonese/pylrclibup/issues) 反馈。