#!/bin/bash
# 更新现有翻译文件（代码变更后使用）
cd "$(dirname "$0")/.."
echo "🔄 正在更新翻译文件..."
# 先提取最新的文本
./scripts/extract_messages.sh
# 更新所有语言的 .po 文件
pybabel update \
    --input-file=pylrclibup/locales/pylrclibup.pot \
    --output-dir=pylrclibup/locales \
    --domain=pylrclibup \
    --update-header-comment
if [ $? -eq 0 ]; then
    echo "✅ 翻译文件已更新"
    echo "📝 请检查并完成新增的翻译"
else
    echo "❌ 更新失败"
    exit 1
fi