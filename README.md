# pylrclibup

一个用于将本地 MP3/LRC 歌曲批量上传到 **LRCLIB.net** 的全自动增强工具。
比官方工具更强、更稳定、更智能——覆盖元数据解析、模糊匹配、本地/外部歌词整合、脚本自动化、网络重试、空目录清理与纯音乐识别等整套流程。

---

# ✨ 功能亮点

## 🎵 1. 自动从 MP3 读取真实 metadata

- 支持 ID3v2.3 / 2.4
- 自动读取：
  - `title`（曲名）
  - `artist`（艺人，多艺人自动拆分）
  - `album`（专辑名）
  - `duration`（时长）
- 完全不依赖文件名，提高准确性

## 🔍 2. 智能匹配本地 LRC（递归扫描 + 宽松模糊规则）

- 提取 LRC 文件名的结构：
  - `Artist - Title.lrc`
- 多艺人匹配仅需 **一个艺人命中** 即可
- 曲名 normalize 后严格一致（避免误匹配）
- 自动处理以下分隔符：
  - `,` `/` `;` `、` `&` `x` `×` `feat.` `featuring`
- 若匹配到多个 LRC → 自动进入选择模式

## 🧹 3. 自动清洗 LRC 内容

识别并移除所有常见“Credit 字段”，包括：

- 作词 / 作曲
- 编曲
- 录音 / 缩混 / 混音 / 母带
- 制作 / 监制
- 和声 / 配唱
- 等其他 NCM（网易云）格式字段

支持识别 credit 的各种变体：

```

[00:00.00] 作词 : XXX
[00:00.00] 作曲：XXX
[00:00.00] 混音  : XXX

```

## 🎼 4. 自动识别纯音乐

- 检测文本：
  - “纯音乐，请欣赏”等所有常见表达
- 或 LRC 内容为空
- 或用户手动选择
  → 自动上传为空歌词（instrumental）

## 🌐 5. 支持 /api/get-cached 与 /api/get 双查询

- **get-cached** → 查询内部数据库（0 外部请求）
- **get** → 若没有内部结果，会触发外部抓取
- 双查询可以判断：
  - 这首歌是否已经有人上传
  - 外部抓取得到的版本是否值得优先使用

## 🚀 6. 完整的上传流程（PoW 自实现）

- **自定义 PoW 求解器**（完全无外部依赖）
- 自动获取 challenge → nonce → publish token
- 最大化降低网络失败的影响

## 🔁 7. 智能重试机制

对网络不稳定环境特别优化：

- `/api/get` / `/api/get-cached`
- `/api/request-challenge`
- `/api/publish`
  均自动重试，最大 5 次

## 📦 8. 自动文件迁移 + 清理空目录

上传成功或发现已有歌词后：

- MP3 → moved 到 `done-tracks/`
- LRC → moved 到 `done-lrc-files/`
- 并自动递归删除空目录（包括子目录）

## 🖱 9. CLI 友好交互

- 单首文件上传
- 所有操作可交互式确认
- `--yes` 模式全自动
- `--dry-run` 不上传，不移动，全面预览
- Ctrl+C **优雅退出（无 traceback）**

## 🌍 10. 完全支持绝对路径 & 相对路径

所有路径都可以：

- 使用绝对路径
- 或相对 root 的路径
- 或完全依赖默认结构

---

# 📥 安装

## PyPI 版本

```bash
pip install pylrclibup
```

## 本地开发模式

```bash
pip install -e .
```

---

# 🧭 使用示例

## 1. 最快入门（使用默认目录）

```bash
pylrclibup
```

目录结构（自动创建）：

```
./tracks/
./lrc-files/
./done-tracks/
./done-lrc-files/
```

---

## 2. 使用-d（default）参数

```bash
pylrclibup -d "tracks/dir/" "lyrics/dir/"
```

默认参数行为：按非干跑、人工确认模式进行歌曲与歌词文件的匹配与上传，上传完毕后歌曲文件并不移动，歌词文件移动到与歌曲文件同一目录下。

## 3. 使用自定义根目录

```bash
pylrclibup --root /my/env
```

最终路径自动变为：

```
/my/env/tracks
/my/env/lrc-files
/my/env/done-tracks
/my/env/done-lrc-files
```

---

## 4. 使用绝对路径（忽略 root）

```bash
pylrclibup \
  --tracks "/mnt/music/tracks" \
  --lrc "/mnt/music/lrc" \
  --done-tracks "/mnt/music/ok_tracks" \
  --done-lrc "/mnt/music/ok_lrc"
```

---

## 5. 单首处理

```bash
pylrclibup --single "Lost & Found.mp3"
```

---

## 6. dry-run

```bash
pylrclibup --dry-run
```

---

## 7. 全自动上传（无任何询问）

```bash
pylrclibup --yes
```

---

# ⚙ 环境变量支持

所有 CLI 参数，都可以通过环境变量进行控制，以满足自动化部署场景。

示例：

```bash
export PYLRCLIBUP_ROOT=/data/lrcenv
export PYLRCLIBUP_TRACKS=/data/mp3
export PYLRCLIBUP_LRC=/data/lrc
export PYLRCLIBUP_DONE_TRACKS=/data/handled_mp3
export PYLRCLIBUP_DONE_LRC=/data/handled_lrc
export PYLRCLIBUP_PREVIEW_LINES=8

pylrclibup
```

优先级：

1. CLI 参数 >
2. 环境变量 >
3. 默认配置
