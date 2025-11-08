#!/bin/bash

# CallawayJP系统启动脚本 - 已弃用推荐版本
#
# ⚠️  重要提示：此脚本已被更专业的方案替代
#
# 推荐使用方案：
#   ./check_callaway_env.sh     # 环境检查（纯检测）
#   ./run_pipeline.sh           # 业务执行（纯业务）
#   ./run_feishu_update.sh data.json  # 飞书更新（纯业务）
#
# 为什么弃用此脚本：
# - 包含端口检查逻辑，容易引起用户混淆
# - 混合了检测和交互逻辑，不符合单一职责原则
# - 新的完全隔离策略更安全、更清晰
#
# 如果仍需使用此脚本，请了解：
# - 8080端口检查仅打印信息，不会影响服务
# - 8081端口冲突需要用户确认才会清理
# - 推荐使用上述新的纯业务脚本

echo "⚠️  使用已弃用脚本 - 建议改用 run_pipeline.sh"

# 检查是否在高尔夫系统目录中运行
if [ -f "./resource_isolation_config.json" ] && [ -f "./golf_content" ]; then
    echo "❌ 错误：当前目录似乎是高尔夫系统目录"
    echo "💡 请在CallawayJP项目目录中运行此脚本"
    echo "   正确的目录应该包含：scripts/, results/, CallawayJP/ 等文件夹"
    exit 1
fi

# 1. 资源冲突检查
echo "🔍 执行资源冲突检查..."

# 检查是否有高尔夫系统的处理进程在运行
GOLF_PROCESSING=$(ps aux | grep -E 'node.*(batch_process|intelligent_concurrent|auto_scrape)' | grep -v grep | grep -v 'CallawayJP' | wc -l)
if [ $GOLF_PROCESSING -gt 0 ]; then
    echo "⚠️  检测到高尔夫文章处理系统正在运行"
    echo "   建议等待高尔夫系统处理完成后再启动CallawayJP系统"
    echo "   或者可以继续，但可能影响系统性能"
    read -p "是否继续启动CallawayJP系统？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 用户取消启动"
        exit 1
    fi
fi

# 2. 端口检查
echo "🔌 检查端口占用..."

# 检查8080端口（高尔夫系统）
# 注意：此段代码仅打印状态信息，不会停止或影响8080端口的任何服务
# CallawayJP系统与8080端口完全隔离，无需担心冲突
echo "ℹ️  端口状态检查："
if lsof -ti:8080 >/dev/null 2>&1; then
    echo "    - 端口8080：被高尔夫系统占用（正常状态，无需处理）"
else
    echo "    - 端口8080：未被占用（高尔夫系统未运行）"
fi
echo "    📌 提醒：CallawayJP不会使用8080端口，请放心"

# 检查8081端口（CallawayJP建议端口）
if lsof -ti:8081 >/dev/null 2>&1; then
    echo "⚠️  端口8081已被占用"
    echo "   CallawayJP系统需要使用其他端口或停止占用进程"
    PORT_8081_PID=$(lsof -ti:8081)
    echo "   占用进程PID: $PORT_8081_PID"
    read -p "是否停止占用进程并继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -TERM $PORT_8081_PID 2>/dev/null || true
        sleep 2
        lsof -ti:8081 | xargs kill -KILL 2>/dev/null || true
        echo "✅ 端口8081已清理"
    else
        echo "❌ 端口冲突，无法启动"
        exit 1
    fi
fi

# 3. 浏览器进程检查
echo "🌐 检查浏览器资源..."
BROWSER_COUNT=$(ps aux | grep -E "(playwright|chromium)" | grep -v grep | wc -l)
if [ $BROWSER_COUNT -gt 5 ]; then
    echo "⚠️  检测到较多浏览器进程 ($BROWSER_COUNT个)"
    echo "   这可能影响CallawayJP抓取性能"
    echo "   建议在系统负载较低时运行"
fi

# 4. 清理CallawayJP相关遗留进程
echo "🧹 清理CallawayJP遗留进程..."
CALLAWAY_PIDS=$(ps aux | grep -E 'node.*CallawayJP' | grep -v grep | awk '{print $2}')
if [ -n "$CALLAWAY_PIDS" ]; then
    echo "  发现遗留CallawayJP进程，正在清理..."
    echo "$CALLAWAY_PIDS" | while read pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "    终止进程 PID $pid"
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    sleep 2
    echo "  ✅ CallawayJP进程清理完成"
else
    echo "  ✅ 没有发现遗留CallawayJP进程"
fi

# 5. 环境变量设置
echo "🔧 设置CallawayJP环境变量..."
export CALLAWAYJP_SYSTEM=1
export CALLAWAYJP_PORT=8081
export CALLAWAYJP_BASE_DIR=$(pwd)

# 6. 系统信息显示
echo -e "\n📊 CallawayJP系统信息:"
echo "  系统类型: CallawayJP产品抓取系统"
echo "  建议端口: 8081"
echo "  工作目录: $(pwd)"
echo "  环境标识: CALLAWAYJP_SYSTEM=1"

echo -e "\n🚀 CallawayJP系统准备完成！"
echo ""
echo "💡 使用建议:"
echo "   1. 运行产品详情抓取:"
echo "      node scripts/scrape_product_detail.js --url '产品URL' --output-dir results/"
echo ""
echo "   2. 运行分类抓取:"
echo "      node scripts/scrape_category.js --category '分类名' --output-dir results/"
echo ""
echo "   3. 查看结果:"
echo "      ls -la results/"
echo ""
echo "   4. 监控系统资源:"
echo "      ps aux | grep -E '(playwright|CallawayJP)' | grep -v grep"
echo ""
echo "⚠️  重要提醒:"
echo "   - CallawayJP系统使用独立的资源管理"
echo "   - 不会影响高尔夫文章处理系统"
echo "   - 建议在高尔夫系统空闲时运行"
echo "   - 完成后会自动清理浏览器资源"