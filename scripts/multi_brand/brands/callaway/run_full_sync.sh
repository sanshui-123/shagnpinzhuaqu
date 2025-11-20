#!/bin/bash

###############################################################################
# Callaway 完整同步流程自动化脚本
#
# 功能：
# - Step 1: 抓取商品列表（scrape_category.js）
# - Step 1.5: 导入基础记录到飞书（import_basic_products.py）
# - Step 2: 顺序抓详情并同步（sequential_sync.js）
# - Step 3: 库存巡检并同步（导出产品→check_inventory→同步库存状态）
#
# 使用方法：
#   ./run_full_sync.sh              # 运行完整流程（包含库存巡检）
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
CALLAWAY_DIR="$PROJECT_ROOT/scripts/multi_brand/brands/callaway"
OUTPUT_DIR="$CALLAWAY_DIR/golf_content/callaway"
BRAND_NAME="卡拉威"

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
echo -e "${BLUE}  Callaway 完整同步流程${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""

# Step 1: 抓取商品列表
if [ "$SKIP_STEP1" = false ]; then
    echo -e "${YELLOW}[Step 1] 抓取商品列表...${NC}"
    cd "$CALLAWAY_DIR"
    node scrape_category.js
    echo -e "${GREEN}✅ Step 1 完成${NC}"
    echo ""
else
    echo -e "${YELLOW}[Step 1] 跳过抓取，使用已有文件${NC}"
    echo ""
fi

# 查找最新的产品文件
echo -e "${YELLOW}🔍 查找最新的产品文件...${NC}"
LATEST_FILE=$(ls -t "$OUTPUT_DIR"/callaway_products_*.json 2>/dev/null | head -1)

if [ -z "$LATEST_FILE" ]; then
    echo -e "${RED}❌ 错误: 未找到产品文件${NC}"
    echo -e "${RED}   请先运行 Step 1 或检查输出目录${NC}"
    exit 1
fi

FILENAME=$(basename "$LATEST_FILE")
RELATIVE_PATH="scripts/multi_brand/brands/callaway/golf_content/callaway/$FILENAME"

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
echo -e "${BLUE}源文件: golf_content/callaway/$FILENAME${NC}"
if [ -n "$LIMIT" ]; then
    echo -e "${BLUE}限制: $LIMIT${NC}"
fi
echo ""

# 检测断点续传状态文件
cd "$CALLAWAY_DIR"
if [ -f "sequential_sync_status.json" ]; then
    echo -e "${YELLOW}⚠️  检测到断点续传状态文件 (sequential_sync_status.json)${NC}"
    echo -e "${YELLOW}   已处理的 product_id 会被跳过；如需对所有记录重跑，${NC}"
    echo -e "${YELLOW}   请删除该文件或运行时带 --no-resume 参数。${NC}"
    echo ""
fi
node sequential_sync.js \
    --source "golf_content/callaway/$FILENAME" \
    $LIMIT

echo ""
echo -e "${GREEN}✅ Step 2 完成${NC}"
echo ""

# Step 3: 库存巡检（自动执行）
echo -e "${YELLOW}[Step 3] 库存巡检并同步...${NC}"
echo -e "${BLUE}这将更新飞书中的 颜色/尺码/库存状态 三个字段${NC}"
echo ""

# Step 3.1: 从飞书导出当前品牌的所有商品
echo -e "${YELLOW}[Step 3.1] 从飞书导出商品列表...${NC}"
cd "$PROJECT_ROOT"
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
    --brand "$BRAND_NAME" \
    --output "/tmp/lecoq_inventory_products.json"

PRODUCT_COUNT=$(cat /tmp/lecoq_inventory_products.json | grep -o '"productId"' | wc -l | tr -d ' ')
echo -e "${GREEN}✅ 已导出 $PRODUCT_COUNT 个商品${NC}"
echo ""

# Step 3.2: 运行库存巡检脚本
echo -e "${YELLOW}[Step 3.2] 运行库存巡检...${NC}"
echo -e "${BLUE}输入: /tmp/lecoq_inventory_products.json${NC}"
echo -e "${BLUE}输出: /tmp/lecoq_inventory_result.json${NC}"
echo -e "${BLUE}配置: 并发3, 延迟500ms${NC}"
echo ""

cd "$CALLAWAY_DIR"
node check_inventory.js \
    --input "/tmp/lecoq_inventory_products.json" \
    --output "/tmp/lecoq_inventory_result.json"

echo ""
echo -e "${GREEN}✅ 库存巡检完成，结果已保存到 /tmp/lecoq_inventory_result.json${NC}"
echo ""

# Step 3.3: 同步库存结果到飞书
echo -e "${YELLOW}[Step 3.3] 同步库存到飞书...${NC}"
cd "$PROJECT_ROOT"
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
    "/tmp/lecoq_inventory_result.json"

echo ""
echo -e "${GREEN}✅ Step 3 完成（库存已同步）${NC}"
echo ""

# 完成
echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}🎉 完整同步流程执行完成！${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""
echo -e "${YELLOW}📋 处理的文件: $FILENAME${NC}"
echo -e "${YELLOW}📁 文件路径: $LATEST_FILE${NC}"
echo -e "${YELLOW}📦 库存巡检: /tmp/lecoq_inventory_result.json${NC}"
echo ""
