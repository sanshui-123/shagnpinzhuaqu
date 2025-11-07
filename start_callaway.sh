#!/usr/bin/env bash
set -euo pipefail

# ====================================================
# Callaway Japan 商品抓取系统独立启动脚本
# 完全隔离于文章系统，使用独立配置和依赖
# ====================================================

# 进入CallawayJP目录
CALLAWAY_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$CALLAWAY_DIR"

echo "🏌️ Callaway Japan 商品抓取系统"
echo "======================================="
echo "📂 工作目录: $CALLAWAY_DIR"

# 检查配置文件
if [[ ! -f "callaway.env" ]]; then
  echo "❌ 配置文件不存在: callaway.env"
  echo "请先创建配置文件并填写必要的API密钥"
  exit 1
fi

# 检查Node.js依赖
if [[ ! -d "node_modules" ]]; then
  echo "📦 安装Node.js依赖..."
  npm install
fi

# 加载配置
set -a
source callaway.env
set +a

echo "✅ 配置加载完成"

# 显示使用选项
echo ""
echo "🚀 启动选项："
echo "  1. 完整流程 (推荐) - 抓取商品并同步到飞书"
echo "  2. 仅抓取商品数据"
echo "  3. 仅同步到飞书"
echo "  4. 流式测试"
echo ""

# 获取用户选择
read -p "请选择操作 (1-4): " choice

case $choice in
  1)
    echo "🔄 执行完整流程..."
    category="${1:-mens_all}"
    echo "分类: $category"
    ./run_pipeline.sh "$category"
    ;;
  2)
    echo "📊 仅抓取商品数据..."
    category="${1:-mens_all}"
    url="${2:-https://www.callawaygolf.jp/apparel/mens}"
    node scripts/scrape_category.js --url "$url" --category "$category" --overwrite-latest
    python3 scripts/merge_dedup.py --category "$category"
    ;;
  3)
    echo "📤 仅同步到飞书..."
    if [[ -z "${1:-}" ]]; then
      echo "请指定数据文件路径"
      exit 1
    fi
    python3 scripts/sync_feishu_products.py --input "$1"
    ;;
  4)
    echo "🧪 运行流式测试..."
    python3 test_streaming.py
    ;;
  *)
    echo "❌ 无效选择"
    exit 1
    ;;
esac

echo ""
echo "✅ 操作完成！"
echo "📊 查看结果: $CALLAWAY_DIR/results/"
echo "📝 查看日志: $CALLAWAY_DIR/sync_logs/"