#!/bin/bash
# 编译翻译文件 (.po -> .mo)
cd "$(dirname "$0")/.."
echo "🔨 正在编译翻译文件..."
pybabel compile \
    --directory=pylrclibup/locales \
    --domain=pylrclibup \
    --statistics
if [ $? -eq 0 ]; then
    echo "✅ 翻译文件编译完成"
    echo "📦 .mo 文件已生成在 pylrclibup/locales/*/LC_MESSAGES/"
else
    echo "❌ 编译失败"
    exit 1
fi