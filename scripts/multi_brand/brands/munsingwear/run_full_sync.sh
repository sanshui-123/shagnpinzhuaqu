#!/bin/bash

###############################################################################
# Munsingwear / 万星威 完整同步流程自动化脚本
#
# 功能：
# - Step 1: 抓取商品列表（scrape_category.js）
# - Step 1.5: 导入基础记录到飞书（import_basic_products.py）
# - Step 2: 顺序抓详情并同步（sequential_sync.js）
#
# 使用方法：
#   ./run_full_sync.sh              # 运行完整流程
#   ./run_full_sync.sh --skip-step1 # 跳过 Step 1，使用已有的最新文件
#   ./run_full_sync.sh --limit 10   # Step 2 只处理 10 个产品（测试用）
###############################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/sanshui/Desktop/CallawayJP"
BRAND_DIR="$PROJECT_ROOT/scripts/multi_brand/brands/munsingwear"
OUTPUT_DIR="$BRAND_DIR/golf_content/munsingwear"
BRAND_NAME="万星威"

# 参数解析
SKIP_STEP1=false
LIMIT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-step1)
            SKIP_STEP1=true
            shift
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --help|-h)
            echo "使用方法："
            echo "  $0              # 运行完整流程"
            echo "  $0 --skip-step1 # 跳过 Step 1，使用已有的最新文件"
            echo "  $0 --limit N    # Step 2 只处理 N 个产品"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}  Munsingwear / 万星威 完整同步流程${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""

# Step 1: 抓取商品列表
if [ "$SKIP_STEP1" = false ]; then
    echo -e "${YELLOW}[Step 1] 抓取商品列表...${NC}"
    cd "$BRAND_DIR"
    node scrape_category.js
    echo -e "${GREEN}✅ Step 1 完成${NC}"
    echo ""
else
    echo -e "${YELLOW}[Step 1] 跳过抓取，使用已有文件${NC}"
    echo ""
fi

# 查找最新的产品文件
echo -e "${YELLOW}🔍 查找最新的产品文件...${NC}"
LATEST_FILE=$(ls -t "$OUTPUT_DIR"/munsingwear_products_*.json 2>/dev/null | head -1)

if [ -z "$LATEST_FILE" ]; then
    echo -e "${RED}❌ 错误: 未找到产品文件${NC}"
    echo -e "${RED}   请先运行 Step 1 或检查输出目录${NC}"
    exit 1
fi

FILENAME=$(basename "$LATEST_FILE")
RELATIVE_PATH="scripts/multi_brand/brands/munsingwear/golf_content/munsingwear/$FILENAME"

echo -e "${GREEN}✅ 找到文件: $FILENAME${NC}"
echo ""

# Step 1.5: 导入基础记录到飞书
echo -e "${YELLOW}[Step 1.5] 导入基础记录到飞书...${NC}"
echo -e "${BLUE}文件: $RELATIVE_PATH${NC}"
echo -e "${BLUE}品牌: $BRAND_NAME${NC}"
echo ""

cd "$PROJECT_ROOT"
python3 -m tongyong_feishu_update.tools.import_basic_products \
    --source "$RELATIVE_PATH" \
    --brand "$BRAND_NAME" \
    --verbose

echo -e "${GREEN}✅ Step 1.5 完成${NC}"
echo ""

# Step 2: 顺序抓详情并同步
echo -e "${YELLOW}[Step 2] 顺序抓详情并同步到飞书...${NC}"
echo -e "${BLUE}源文件: golf_content/munsingwear/$FILENAME${NC}"
if [ -n "$LIMIT" ]; then
    echo -e "${BLUE}限制: $LIMIT${NC}"
fi
echo ""

cd "$BRAND_DIR"
node sequential_sync.js \
    --source "golf_content/munsingwear/$FILENAME" \
    $LIMIT

echo ""
echo -e "${GREEN}✅ Step 2 完成${NC}"
echo ""

# 完成
echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}🎉 完整同步流程执行完成！${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""
echo -e "${YELLOW}📋 处理的文件: $FILENAME${NC}"
echo -e "${YELLOW}📁 文件路径: $LATEST_FILE${NC}"
echo ""
