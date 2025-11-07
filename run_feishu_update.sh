#!/bin/bash
# 飞书强制更新便捷脚本 - 步骤1修改版本
# 用途：提供一键执行飞书更新的便捷方式，自动处理环境变量加载
# 特性：缺失即失败、一步执行、无兜底标题，环境/网络问题第一时间暴露

set -euo pipefail  # 严格错误处理：遇到错误立即退出，未定义变量报错，管道失败传递

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用帮助
show_help() {
    cat << EOF
飞书强制更新脚本

用法:
    $0 <输入文件> [选项]

参数:
    <输入文件>        JSON格式的产品数据文件路径（必需）

选项:
    --force-update    强制更新所有字段
    --title-only      仅更新标题字段
    --dry-run         干运行模式，不实际写入飞书
    --verbose         显示详细进度信息
    --help            显示此帮助信息

示例:
    # 基本用法
    $0 /tmp/dedup_top3.json

    # 强制更新所有字段
    $0 /tmp/dedup_top3.json --force-update

    # 仅更新标题
    $0 /tmp/dedup_top3.json --title-only

    # 干运行模式（测试）
    $0 /tmp/dedup_top3.json --dry-run --verbose

注意:
    - 确保项目根目录存在 .env 文件
    - .env 文件必须包含 ZHIPU_API_KEY 等必需的环境变量
    - 脚本会自动加载环境变量并调用 feishu_update 模块
EOF
}

# 检查参数
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 获取输入文件路径
INPUT_FILE="$1"
shift

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    print_error "输入文件不存在: $INPUT_FILE"
    exit 1
fi

# 确保在项目根目录执行（步骤1要求）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

print_info "切换到项目根目录: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# 检查是否在正确的目录（应该包含CallawayJP子目录）
if [ ! -d "CallawayJP" ]; then
    print_error "项目根目录不包含 CallawayJP 子目录，请检查脚本位置"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    print_error ".env 文件不存在，请确保项目根目录包含环境变量配置文件"
    exit 1
fi

print_info "正在加载环境变量..."

# 加载环境变量（使用正确的方式）
set -a
source .env
set +a

print_success "环境变量加载完成"

# 检查关键环境变量是否设置（步骤1修改 - 检查变量是否存在并提示）
if [ -z "${ZHIPU_API_KEY:-}" ]; then
    print_error "ZHIPU_API_KEY 环境变量未设置，请检查 .env 文件"
    exit 1
fi

# 检查代理设置并提示（不要 unset，改成检查变量是否存在）
if [ -n "${HTTPS_PROXY:-}" ] || [ -n "${https_proxy:-}" ] || [ -n "${HTTP_PROXY:-}" ] || [ -n "${http_proxy:-}" ]; then
    print_warning "检测到代理设置，如果连接智谱API时出现问题，请考虑临时关闭代理"
    print_info "当前代理设置："
    [ -n "${HTTPS_PROXY:-}" ] && print_info "  HTTPS_PROXY=$HTTPS_PROXY"
    [ -n "${https_proxy:-}" ] && print_info "  https_proxy=$https_proxy"
    [ -n "${HTTP_PROXY:-}" ] && print_info "  HTTP_PROXY=$HTTP_PROXY"
    [ -n "${http_proxy:-}" ] && print_info "  http_proxy=$http_proxy"
fi

print_info "环境变量校验完成"

# 构建命令参数
CMD_ARGS="--input $INPUT_FILE"

# 处理其他参数
while [ $# -gt 0 ]; do
    case $1 in
        --force-update|--title-only|--dry-run|--verbose)
            CMD_ARGS="$CMD_ARGS $1"
            ;;
        *)
            print_warning "未知参数: $1"
            ;;
    esac
    shift
done

print_info "准备执行飞书更新..."
print_info "输入文件: $INPUT_FILE"
print_info "命令参数: $CMD_ARGS"

# 注意：现在不再自动清理代理设置，由用户根据需要手动处理

# 执行 Python 模块
print_info "正在执行飞书更新..."
python3 -m CallawayJP.feishu_update.cli $CMD_ARGS

# 检查执行结果
if [ $? -eq 0 ]; then
    print_success "飞书更新执行完成"
else
    print_error "飞书更新执行失败"
    exit 1
fi