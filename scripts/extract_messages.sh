#!/usr/bin/env bash
# ===== scripts/extract_messages.sh =====

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📦 提取翻译字符串..."

# 提取 Python 源码中的 _() 包裹的字符串
xgettext \
    --language=Python \
    --keyword=_ \
    --keyword=get_text \
    --output=pylrclibup/locales/pylrclibup.pot \
    --from-code=UTF-8 \
    --add-comments=TRANSLATORS \
    --package-name="pylrclibup" \
    --package-version="0.3.0" \
    --msgid-bugs-address="https://github.com/Harmonese/pylrclibup/issues" \
    $(find pylrclibup -name "*.py" -not -path "*/tests/*")

echo "✅ 翻译模板已生成: pylrclibup/locales/pylrclibup.pot"
