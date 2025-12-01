#!/bin/bash
# 初始化新语言的翻译文件
if [ -z "$1" ]; then
    echo "用法: $0 <语言代码>"
    echo "示例: $0 zh_CN"
    exit 1
fi
LOCALE=$1
cd "$(dirname "$0")/.."
echo "🌍 正在为 $LOCALE 初始化翻译..."
pybabel init \
    --input-file=pylrclibup/locales/pylrclibup.pot \
    --output-dir=pylrclibup/locales \
    --locale=$LOCALE \
    --domain=pylrclibup
if [ $? -eq 0 ]; then
    echo "✅ $LOCALE 翻译文件已创建"
    echo "📝 请编辑: pylrclibup/locales/$LOCALE/LC_MESSAGES/pylrclibup.po"
else
    echo "❌ 初始化失败"
    exit 1
fi