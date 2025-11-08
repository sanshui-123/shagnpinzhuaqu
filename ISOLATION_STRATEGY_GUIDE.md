# CallawayJP 完全隔离策略指南

## 🎯 设计原则

**完全隔离 + 无人为误杀** - 确保CallawayJP与高尔夫系统完全独立运行，避免任何交叉影响。

## 📁 推荐执行流程

### 标准操作顺序

```bash
# 终端1: 启动高尔夫系统（可选）
cd /Users/sanshui/Desktop/cursor
./safe_single_controller.sh

# 终端2: 启动CallawayJP系统
cd /Users/sanshui/Desktop/CallawayJP
./check_callaway_env.sh          # 1. 环境检查
./run_pipeline.sh                # 2. 执行业务流程
```

### 纯飞书更新操作

```bash
cd /Users/sanshui/Desktop/CallawayJP
./check_callaway_env.sh          # 环境检查
./run_feishu_update.sh input.json  # 飞书更新
```

## 🔌 端口策略

### 固定端口分配

| 系统 | 端口 | 用途 | 说明 |
|------|------|------|------|
| 高尔夫系统 | 8080 | Web服务器 | 固定使用，CallawayJP不得占用 |
| CallawayJP | 8081 | Web服务器(可选) | 建议端口，如有冲突需手动处理 |

### 重要规则

1. **CallawayJP永远不要使用8080端口**
2. **CallawayJP默认不需要Web服务器，除非有特殊需求**
3. **端口8081如需使用，显式设置环境变量**

```bash
# CallawayJP Web服务器设置
export CALLAWAYJP_PORT=8081
# 或在.env文件中添加
CALLAWAYJP_PORT=8081
```

## 🛡️ 隔离机制

### 脚本隔离

| 脚本类型 | 推荐使用 | 避免使用 | 原因 |
|----------|----------|----------|------|
| 环境检查 | `check_callaway_env.sh` | `start_callaway_system.sh` | 纯检测，无副作用 |
| 业务执行 | `run_pipeline.sh` | 任何含端口检查的脚本 | 纯业务，无交叉影响 |
| 飞书更新 | `run_feishu_update.sh` | 复合型脚本 | 单一职责 |

### 进程隔离

```bash
# 高尔夫系统进程标识
INTELLIGENT_CONTROLLER_AUTH=1
GOLF_SYSTEM_MODE=single_controller

# CallawayJP系统进程标识
CALLAWAYJP_SYSTEM=1
CALLAWAYJP_BASE_DIR=/Users/sanshui/Desktop/CallawayJP
```

### 资源隔离

- **浏览器进程**: 各自管理，不共享
- **内存使用**: 独立分配，互不影响
- **网络请求**: 独立连接，避免API冲突

## 🚫 禁止操作

### 高风险操作（不要执行）

```bash
# ❌ 不要在高尔夫系统目录执行CallawayJP脚本
cd /Users/sanshui/Desktop/cursor
./CallawayJP/run_pipeline.sh  # 危险！

# ❌ 不要执行可能检查8080端口的脚本
./start_callaway_system.sh     # 已弃用

# ❌ 不要运行通用资源清理脚本
./enhanced_resource_cleanup.sh  # 会影响两个系统
```

### 误操作识别

如果看到以下提示，**请输入N或直接Ctrl+C取消**：

```
是否停止占用进程并继续？(y/N)  # 输入N
端口8080被占用，是否清理？      # 输入N
检测到冲突进程，是否终止？      # 输入N
```

## ✅ 安全操作

### 推荐命令

```bash
# ✅ 安全的环境检查
./check_callaway_env.sh

# ✅ 安全的业务执行
./run_pipeline.sh
./run_feishu_update.sh input.json

# ✅ 安全的端口设置
export CALLAWAYJP_PORT=8081
```

### 系统监控

```bash
# 监控端口状态（纯查看）
lsof -i :8080  # 高尔夫系统
lsof -i :8081  # CallawayJP系统

# 监控进程状态（纯查看）
ps aux | grep -E "(node|callaway|golf)" | grep -v grep
```

## 📋 故障处理

### 常见问题

**Q: 执行CallawayJP脚本后，高尔夫8080端口无法访问？**
A: 不是脚本导致的，可能是：
- VSCode或其他工具重启了web_server.js
- 手动执行了影响8080端口的脚本
- 系统重启或其他操作

**Q: 看到端口冲突提示？**
A: 检查具体端口：
- 8080冲突：属于高尔夫系统问题，CallawayJP脚本不会影响
- 8081冲突：手动停止占用进程或更换端口

**Q: 资源占用过高？**
A: 两个系统同时运行时的正常现象，可以：
- 错峰运行（先完成一个再启动另一个）
- 监控资源使用，必要时重启清理

### 紧急恢复

```bash
# 紧急重启高尔夫系统
cd /Users/sanshui/Desktop/cursor
./safe_single_controller.sh

# 紧急清理CallawayJP进程（仅清理CallawayJP相关）
ps aux | grep CallawayJP | grep -v grep | awk '{print $2}' | xargs kill -TERM 2>/dev/null || true
```

## 🎯 最佳实践

### 日常使用流程

1. **启动阶段**:
   ```bash
   # 检查环境
   cd /Users/sanshui/Desktop/CallawayJP
   ./check_callaway_env.sh
   ```

2. **执行阶段**:
   ```bash
   # 选择执行模式
   ./run_pipeline.sh                    # 完整流程
   # 或
   ./run_feishu_update.sh data.json     # 飞书更新
   ```

3. **验证阶段**:
   ```bash
   # 检查结果
   ls -la results/
   ```

### 注意事项

1. **始终先执行环境检查**
2. **使用推荐的纯业务脚本**
3. **避免执行任何通用清理脚本**
4. **监控端口和进程状态**
5. **出现意外时优先检查操作日志**

## 📚 相关文件

- `check_callaway_env.sh` - 环境检查脚本
- `run_pipeline.sh` - 完整业务流程
- `run_feishu_update.sh` - 飞书更新脚本
- `callaway.env` - 环境变量配置

---

**核心原则**: CallawayJP系统完全独立运行，不依赖、不影响高尔夫系统。