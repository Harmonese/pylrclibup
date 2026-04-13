This project is deprecated and rebuilt in project `pylrclib` (see the github repository [here](https://github.com/Harmonese/pylrclib) and the PyPI release [here](https://pypi.org/project/pylrclib-cli/)). All the functions were rebuilt and improved in `pylrclib`.

Install `pylrclib` by
```bash
pip install pylrclib-cli
```

# English

# pylrclibup

[![PyPI version](https://badge.fury.io/py/pylrclibup.svg)](https://badge.fury.io/py/pylrclibup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A powerful CLI tool to upload local lyrics to LRCLIB.net**

[English](#english) | [中文](#中文)

---

## ✨ Features

- 🎵 **Multi-format audio support**: MP3, M4A, AAC, FLAC, WAV
- 🔍 **Intelligent LRC matching**: Fuzzy artist search, normalized title comparison
- 🧹 **Advanced LRC standardization**: Unicode normalization, duplicate removal, credit line stripping
- 🎼 **Instrumental track detection**: Auto-detect and upload empty lyrics
- 🔁 **Smart retry mechanism**: Exponential backoff with network resilience
- 🌍 **Bilingual interface**: Auto-detect locale or manual override (EN/CN)
- 📁 **Flexible file management**: Independent flags for complete control
- 🚀 **Robust upload**: Custom PoW solver with auto challenge handling
- 📄 **YAML metadata support**: Describe tracks without audio files and still upload lyrics

---

## 📥 Installation

### From PyPI (Recommended)

```bash
pip install pylrclibup
```

### From Source

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e .
```

---

## 🚀 Quick Start

### Basic Usage

Process audio files in current directory:

```bash
cd /path/to/music
pylrclibup
```

### Quick Mode

Move LRC files from downloads to music library:

```bash
pylrclibup -d "/music/tracks" "/downloads/lyrics"
```

This will:

- Keep audio files in `/music/tracks`
- Move LRC files to audio directories
- Rename LRC to match audio filenames
- Standardize LRC content

---

## 📖 Usage Examples

### 1. Upload Only (In-Place)

```bash
pylrclibup
```

Files stay in their original locations.

---

### 2. Match Mode

```bash
pylrclibup -m
```

LRC follows audio + renames + cleanses (equivalent to `-f -r -c`).

---

### 3. Custom Workflow

```bash
pylrclibup \
  --tracks "/music/input" \
  --lrc "/lyrics/input" \
  --done-tracks "/music/output" \
  --done-lrc "/lyrics/output" \
  --rename --cleanse
```

Separate input/output directories with selective options.

---

### 4. Cleanse Only

```bash
pylrclibup --lrc "/path/to/lyrics" --cleanse
```

Standardize LRC files without uploading.

---

### 5. Preview Control

```bash
pylrclibup --preview-lines 20
```

Show 20 lines during lyric confirmation.

---

### 6. Language Selection

```bash
# Force English
pylrclibup --lang en_US

# Force Chinese
pylrclibup --lang zh_CN

# Auto-detect (default)
pylrclibup --lang auto
```

---

### 7. YAML Metadata Usage

You can describe tracks using YAML files instead of real audio files. This is useful when:

- You only have metadata and LRC files
- You want to prepare uploads on a different machine from your music library

A minimal YAML file:

```yaml
# song.yaml
track: "Song Title"
artist: "Artist Name"
album: "Album Name"
duration: 180        # duration in seconds
lrc_file: "Song Title.lrc"  # optional, see below
```

Place `song.yaml` (and optionally the LRC) under `--tracks` directory:

```bash
pylrclibup --tracks "/path/with/yaml" --lrc "/path/to/lyrics"
```

The tool will:

- Read metadata from `*.yaml` / `*.yml` files
- Treat each YAML as a track (even without an audio file)
- Use the YAML info to query LRCLIB and upload lyrics / instrumental markers
- Apply the same interactive flow as for audio files

#### How YAML finds the LRC file

If `lrc_file` is set in YAML, lookup order is:

1. Relative to the YAML file directory
2. Under `--lrc` directory
3. As an absolute path (if `lrc_file` is absolute)

If `lrc_file` is **not** set, the tool will try:

1. `song.yaml` → `song.lrc` in the same directory
2. `song.lrc` under `--lrc` directory

---

## 🎯 Common Scenarios

| Scenario         | Command                                         | Audio Behavior | LRC Behavior            |
| ---------------- | ----------------------------------------------- | -------------- | ----------------------- |
| Upload only      | `pylrclibup`                                  | In-place       | In-place                |
| Organize lyrics  | `pylrclibup -d /music /downloads`             | In-place       | Move + rename + cleanse |
| Match mode       | `pylrclibup -m`                               | In-place       | Move + rename + cleanse |
| Separate outputs | `pylrclibup --done-tracks /a --done-lrc /b`   | Move to /a     | Move to /b              |
| Cleanse LRC      | `pylrclibup --lrc /lyrics -c`                 | N/A            | Standardize in-place    |
| YAML only        | `pylrclibup --tracks /yaml_dir --lrc /lyrics` | N/A            | Same logic as audio     |

---

## ⚙️ Options Reference

### Path Options

```bash
--tracks PATH          # Audio/YAML input directory (default: current dir)
--lrc PATH             # LRC input directory (default: current dir)
--done-tracks PATH     # Move processed audio to this directory
--done-lrc PATH        # Move processed LRC to this directory
```

### Behavior Options

```bash
-f, --follow           # LRC follows audio to same directory
-r, --rename           # Rename LRC to match audio filename
-c, --cleanse          # Standardize LRC before processing
```

### Preset Modes

```bash
-d, --default TRACKS LRC    # Quick mode: --tracks TRACKS --lrc LRC -f -r -c
-m, --match                 # Match mode: -f -r -c (current dir)
```

### Other Options

```bash
--preview-lines N      # Lyric preview lines (default: 10)
--lang LANG            # Interface language: zh_CN | en_US | auto
--max-retries N        # HTTP retry count (default: 5)
-h, --help             # Show help message
--version              # Show version number
```

---

## 🌍 Environment Variables

Override defaults without CLI arguments:

```bash
export PYLRCLIBUP_TRACKS_DIR="/data/music"
export PYLRCLIBUP_LRC_DIR="/data/lyrics"
export PYLRCLIBUP_DONE_TRACKS_DIR="/data/processed/music"
export PYLRCLIBUP_DONE_LRC_DIR="/data/processed/lyrics"
export PYLRCLIBUP_PREVIEW_LINES=15
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
export PYLRCLIBUP_USER_AGENT="MyMusicApp/2.0"
export PYLRCLIBUP_LANG=en_US

pylrclibup
```

**Priority**: CLI args > Environment variables > Defaults

---

## 🧹 LRC Standardization

When using `-c/--cleanse`, the following operations are performed:

- ✅ Remove header content before first timestamp
- ✅ Strip credit lines (作词, 作曲, 编曲, 混音, etc.)
- ✅ Delete duplicate translations (same timestamp, CJK detection)
- ✅ Unicode normalization (NFKC)
- ✅ Fullwidth punctuation conversion
- ✅ Cyrillic character mapping (ё→е, і→и, etc.)
- ✅ Instrumental phrase detection

---

## 🛠️ Advanced Usage

### Batch Processing

```bash
#!/bin/bash
for dir in /music/*/; do
    echo "Processing: $dir"
    pylrclibup --tracks "$dir" --lrc "/downloads/lyrics" -f -r -c
done
```

### Manual LRC Path Input

When auto-matching fails, choose `[m]` and input path:

```
Enter LRC file path: /path/to/lyrics/song.lrc
```

Supports:

- Absolute paths: `/home/user/lyrics/song.lrc`
- Relative paths: `../lyrics/song.lrc`
- Home expansion: `~/Music/lyrics/song.lrc`

### Instrumental Tracks

For tracks without lyrics, choose `[i]`:

```
Will upload empty lyrics (marked as instrumental).
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test: `pytest tests/`
4. Commit: `git commit -m "Add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

### Development Setup

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e ".[dev]"
pytest
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- [LRCLIB.net](https://lrclib.net) - Free lyrics API service
- [Mutagen](https://mutagen.readthedocs.io/) - Audio metadata library

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Harmonese/pylrclibup/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Harmonese/pylrclibup/discussions)

---

<div align="center">

**Made with ❤️ by [Harmonese](https://github.com/Harmonese)**

⭐ Star this repo if you find it helpful!

[![GitHub stars](https://img.shields.io/github/stars/Harmonese/pylrclibup.svg?style=social&label=Star)](https://github.com/Harmonese/pylrclibup)

</div>

---

# 中文

# pylrclibup

[![PyPI version](https://badge.fury.io/py/pylrclibup.svg)](https://badge.fury.io/py/pylrclibup)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**强大的本地歌词上传工具,支持自动匹配、标准化和智能管理**

[English](README.md) | [中文](README_CN.md)

---

## ✨ 功能特性

- 🎵 **多格式音频支持**: MP3, M4A, AAC, FLAC, WAV
- 🔍 **智能 LRC 匹配**: 模糊艺人搜索、标准化曲名比较
- 🧹 **高级 LRC 标准化**: Unicode 规范化、去重、移除制作信息
- 🎼 **纯音乐识别**: 自动检测并上传空歌词
- 🔁 **智能重试机制**: 指数退避与网络容错
- 🌍 **双语界面**: 自动检测语言环境或手动覆盖 (中/英)
- 📁 **灵活的文件管理**: 独立标志实现完全控制
- 🚀 **健壮的上传**: 自定义 PoW 求解器与自动 challenge 处理
- 📄 **YAML 元数据支持**: 无音频文件也可通过 YAML 描述曲目并上传歌词

---

## 📥 安装

### 从 PyPI 安装（推荐）

```bash
pip install pylrclibup
```

### 从源码安装

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e .
```

---

## 🚀 快速开始

### 基本用法

处理当前目录的音频文件:

```bash
cd /path/to/music
pylrclibup
```

### 快速模式

从下载目录整理 LRC 到音乐库:

```bash
pylrclibup -d "/music/tracks" "/downloads/lyrics"
```

效果:

- 音频文件保持在 `/music/tracks`
- LRC 文件移动到音频目录
- LRC 重命名匹配音频文件名
- 标准化 LRC 内容

---

## 📖 使用示例

### 1. 仅上传（原地模式）

```bash
pylrclibup
```

文件保持在原始位置。

---

### 2. 匹配模式

```bash
pylrclibup -m
```

LRC 跟随音频 + 重命名 + 标准化（等同于 `-f -r -c`）。

---

### 3. 自定义工作流

```bash
pylrclibup \
  --tracks "/music/input" \
  --lrc "/lyrics/input" \
  --done-tracks "/music/output" \
  --done-lrc "/lyrics/output" \
  --rename --cleanse
```

分别指定输入/输出目录，选择性选项。

---

### 4. 仅标准化

```bash
pylrclibup --lrc "/path/to/lyrics" --cleanse
```

标准化 LRC 文件但不上传。

---

### 5. 预览控制

```bash
pylrclibup --preview-lines 20
```

歌词确认时显示 20 行。

---

### 6. 语言选择

```bash
# 强制英文
pylrclibup --lang en_US

# 强制中文
pylrclibup --lang zh_CN

# 自动检测（默认）
pylrclibup --lang auto
```

---

### 7. YAML 元数据用法

你可以使用 YAML 文件描述曲目，而不依赖真实音频文件。适用于：

- 只有元数据和 LRC，音频不在当前机器
- 想先在一台机器准备好上传任务

一个最小 YAML 示例：

```yaml
# song.yaml
track: "歌曲名"
artist: "艺术家"
album: "专辑名"
duration: 180          # 时长（秒）
lrc_file: "歌曲名.lrc"  # 可选，见下
```

将 `song.yaml`（以及可选的 LRC）放在 `--tracks` 指定的目录下：

```bash
pylrclibup --tracks "/path/with/yaml" --lrc "/path/to/lyrics"
```

程序会：

- 扫描目录中的 `*.yaml` / `*.yml` 文件
- 将每个 YAML 视为一首歌曲（即使没有音频文件）
- 使用 YAML 中的元数据访问 LRCLIB 并上传歌词/纯音乐标记
- 流程与普通音频文件一致，同样支持交互确认

#### YAML 如何找到 LRC 文件

当 YAML 中设置了 `lrc_file` 字段时，查找顺序为：

1. 以 YAML 文件所在目录为基准的相对路径
2. `--lrc` 指定目录下的同名文件
3. 将 `lrc_file` 视为绝对路径（若本身为绝对路径）

如果 **未设置** `lrc_file`，则会尝试：

1. `song.yaml` → 同目录下的 `song.lrc`
2. `--lrc` 目录下的 `song.lrc`

---

## 🎯 常见场景

| 场景           | 命令                                            | 音频行为  | LRC 行为               |
| -------------- | ----------------------------------------------- | --------- | ---------------------- |
| 仅上传         | `pylrclibup`                                  | 原地      | 原地                   |
| 整理歌词       | `pylrclibup -d /music /downloads`             | 原地      | 移动 + 重命名 + 标准化 |
| 匹配模式       | `pylrclibup -m`                               | 原地      | 移动 + 重命名 + 标准化 |
| 分别输出       | `pylrclibup --done-tracks /a --done-lrc /b`   | 移动到 /a | 移动到 /b              |
| 清理 LRC       | `pylrclibup --lrc /lyrics -c`                 | N/A       | 原地标准化             |
| 仅 YAML 元数据 | `pylrclibup --tracks /yaml_dir --lrc /lyrics` | N/A       | 行为同音频模式         |

---

## ⚙️ 选项参考

### 路径选项

```bash
--tracks PATH          # 音频/YAML 输入目录（默认：当前目录）
--lrc PATH             # LRC 输入目录（默认：当前目录）
--done-tracks PATH     # 处理后音频移动目录
--done-lrc PATH        # 处理后 LRC 移动目录
```

### 行为选项

```bash
-f, --follow           # LRC 跟随音频到同一目录
-r, --rename           # LRC 重命名匹配音频文件名
-c, --cleanse          # 处理前标准化 LRC
```

### 预设模式

```bash
-d, --default TRACKS LRC    # 快速模式: --tracks TRACKS --lrc LRC -f -r -c
-m, --match                 # 匹配模式: -f -r -c（当前目录）
```

### 其他选项

```bash
--preview-lines N      # 歌词预览行数（默认：10）
--lang LANG            # 界面语言: zh_CN | en_US | auto
--max-retries N        # HTTP 重试次数（默认：5）
-h, --help             # 显示帮助信息
--version              # 显示版本号
```

---

## 🌍 环境变量

无需 CLI 参数即可覆盖默认值:

```bash
export PYLRCLIBUP_TRACKS_DIR="/data/music"
export PYLRCLIBUP_LRC_DIR="/data/lyrics"
export PYLRCLIBUP_DONE_TRACKS_DIR="/data/processed/music"
export PYLRCLIBUP_DONE_LRC_DIR="/data/processed/lyrics"
export PYLRCLIBUP_PREVIEW_LINES=15
export PYLRCLIBUP_MAX_HTTP_RETRIES=10
export PYLRCLIBUP_USER_AGENT="MyMusicApp/2.0"
export PYLRCLIBUP_LANG=zh_CN

pylrclibup
```

**优先级**: CLI 参数 > 环境变量 > 默认值

---

## 🧹 LRC 标准化

使用 `-c/--cleanse` 时执行以下操作:

- ✅ 删除第一个时间戳之前的头部内容
- ✅ 移除制作信息行（作词、作曲、编曲、混音等）
- ✅ 删除重复翻译行（相同时间戳、CJK 检测）
- ✅ Unicode 规范化 (NFKC)
- ✅ 全角标点转换
- ✅ 西里尔字母映射（ё→е, і→и 等）
- ✅ 纯音乐短语检测

---

## 🛠️ 高级用法

### 批量处理

```bash
#!/bin/bash
for dir in /music/*/; do
    echo "正在处理: $dir"
    pylrclibup --tracks "$dir" --lrc "/downloads/lyrics" -f -r -c
done
```

### 手动输入 LRC 路径

当自动匹配失败时，选择 `[m]` 并输入路径:

```
请输入 LRC 文件的完整路径: /path/to/lyrics/song.lrc
```

支持:

- 绝对路径: `/home/user/lyrics/song.lrc`
- 相对路径: `../lyrics/song.lrc`
- Home 展开: `~/Music/lyrics/song.lrc`

### 纯音乐曲目

对于无歌词的曲目，选择 `[i]`:

```
将上传空歌词（标记为纯音乐）。
```

---

## 🤝 贡献

1. Fork 仓库
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 修改并测试: `pytest tests/`
4. 提交: `git commit -m "添加某某功能"`
5. 推送: `git push origin feature/amazing-feature`
6. 创建 Pull Request

### 开发环境设置

```bash
git clone https://github.com/Harmonese/pylrclibup.git
cd pylrclibup
pip install -e ".[dev]"
pytest
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [LRCLIB.net](https://lrclib.net) - 免费歌词 API 服务
- [Mutagen](https://mutagen.readthedocs.io/) - 音频元数据库

---

## 📞 支持

- **问题反馈**: [GitHub Issues](https://github.com/Harmonese/pylrclibup/issues)
- **讨论**: [GitHub Discussions](https://github.com/Harmonese/pylrclibup/discussions)

---

<div align="center">

**用 ❤️ 制作 by [Harmonese](https://github.com/Harmonese)**

⭐ 如果觉得有用请给个 Star!

[![GitHub stars](https://img.shields.io/github/stars/Harmonese/pylrclibup.svg?style=social&label=Star)](https://github.com/Harmonese/pylrclibup)

</div>
