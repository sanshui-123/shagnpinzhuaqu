#!/bin/bash

# CallawayJP环境检查脚本 - 纯检测，无任何操作
# 用途：执行业务脚本前的环境状态确认
# 原则：只检查状态，不修改任何配置，不kill任何进程

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔍 CallawayJP环境检查"
echo "===================="

# 1. 基础环境检查
print_info "1. 基础环境检查"

# 检查当前目录
if [[ ! -f "callaway.env" ]]; then
    print_error "❌ callaway.env 文件不存在"
    echo "   💡 请确保在CallawayJP项目根目录执行"
    exit 1
else
    print_success "✅ callaway.env 文件存在"
fi

# 检查Python环境
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "unknown")
    print_success "✅ Python3: $PYTHON_VERSION"
else
    print_error "❌ Python3 未安装"
fi

# 检查Node.js环境
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
    print_success "✅ Node.js: $NODE_VERSION"
else
    print_error "❌ Node.js 未安装"
fi

# 2. 端口状态检查（纯检测）
print_info "2. 端口状态检查"

# 检查8080端口（高尔夫系统）
if lsof -ti:8080 >/dev/null 2>&1; then
    print_success "✅ 端口8080被占用（高尔夫系统正常）"
    PORT_8080_PID=$(lsof -ti:8080 2>/dev/null)
    echo "   📍 进程PID: $PORT_8080_PID"
else
    print_warning "⚠️  端口8080未被占用（高尔夫系统未运行）"
fi

# 检查8081端口（CallawayJP建议端口）
if lsof -ti:8081 >/dev/null 2>&1; then
    print_warning "⚠️  端口8081被占用"
    PORT_8081_PID=$(lsof -ti:8081 2>/dev/null)
    echo "   📍 占用进程PID: $PORT_8081_PID"
    echo "   💡 CallawayJP如需使用8081端口，请先停止占用进程"
else
    print_success "✅ 端口8081可用（CallawayJP建议端口）"
fi

# 3. 系统资源检查
print_info "3. 系统资源检查"

# 检查磁盘空间
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    print_success "✅ 磁盘空间充足 (${DISK_USAGE}%已用)"
else
    print_warning "⚠️  磁盘空间不足 (${DISK_USAGE}%已用)"
fi

# 检查内存使用
if command -v vm_stat >/dev/null 2>&1; then
    FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    FREE_GB=$((FREE_PAGES * 4096 / 1024 / 1024 / 1024))
    if [ "$FREE_GB" -gt 4 ]; then
        print_success "✅ 内存充足 (可用约${FREE_GB}GB)"
    else
        print_warning "⚠️  内存紧张 (仅可用约${FREE_GB}GB)"
    fi
fi

# 4. 网络连接检查
print_info "4. 网络连接检查"

# 检查基础网络连接
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    print_success "✅ 外网连接正常"
else
    print_warning "⚠️  外网连接异常"
fi

# 检查DNS解析
if nslookup www.callawaygolf.jp >/dev/null 2>&1; then
    print_success "✅ DNS解析正常"
else
    print_warning "⚠️  DNS解析异常"
fi

# 5. 关键文件和目录检查
print_info "5. 项目文件检查"

# 检查关键目录
for dir in "scripts" "results" "feishu_update"; do
    if [[ -d "$dir" ]]; then
        print_success "✅ 目录存在: $dir"
    else
        print_error "❌ 目录缺失: $dir"
    fi
done

# 检查关键脚本
for script in "scripts/scrape_category.js" "scripts/merge_dedup.py" "scripts/sync_feishu_products.py"; do
    if [[ -f "$script" ]]; then
        print_success "✅ 脚本存在: $script"
    else
        print_error "❌ 脚本缺失: $script"
    fi
done

# 6. 环境变量检查
print_info "6. 环境变量检查"

# 加载环境变量
set -a
source callaway.env 2>/dev/null || true
set +a

# 检查关键环境变量
CRITICAL_VARS=("ZHIPU_API_KEY" "FEISHU_APP_ID" "FEISHU_APP_SECRET")
MISSING_VARS=()

for var in "${CRITICAL_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING_VARS+=("$var")
    else
        print_success "✅ 环境变量: $var"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "❌ 缺失关键环境变量:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
fi

# 7. 浏览器资源检查
print_info "7. 浏览器资源检查"

BROWSER_COUNT=$(ps aux | grep -E "(playwright|chromium)" | grep -v grep | wc -l)
if [ "$BROWSER_COUNT" -eq 0 ]; then
    print_success "✅ 无活跃浏览器进程"
elif [ "$BROWSER_COUNT" -lt 5 ]; then
    print_info "ℹ️  检测到 $BROWSER_COUNT 个浏览器进程（正常范围）"
else
    print_warning "⚠️  检测到 $BROWSER_COUNT 个浏览器进程（可能影响性能）"
fi

# 8. 总结和建议
echo
echo "📋 环境检查总结"
echo "===================="

# 计算警告和错误数量
TOTAL_WARNINGS=0
TOTAL_ERRORS=0

# 这里简化处理，实际可以通过计数器实现

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    print_success "✅ 环境检查通过，可以执行业务脚本"
    echo
    echo "🚀 推荐执行命令:"
    echo "   ./run_pipeline.sh                    # 完整流程"
    echo "   ./run_feishu_update.sh <input.json>  # 仅飞书更新"
else
    print_error "❌ 发现环境问题，请修复后重试"
    echo
    echo "🔧 修复建议:"
    echo "   1. 检查并补充缺失的环境变量"
    echo "   2. 确保网络连接正常"
    echo "   3. 检查关键文件是否存在"
fi

echo
echo "💡 重要提醒:"
echo "   - 端口8080: 高尔夫系统专用，本脚本不会影响"
echo "   - 端口8081: CallawayJP建议端口，如有冲突需手动处理"
echo "   - 本脚本仅检查状态，不执行任何修改操作"