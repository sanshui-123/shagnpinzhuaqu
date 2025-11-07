# 飞书更新系统 v2.0 部署指南

**目标**: 将飞书更新系统v2.0安全可靠地部署到生产环境  
**适用版本**: v2.0+  
**更新日期**: 2025-11-04  

---

## 📋 部署概览

### 部署架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   执行环境      │───▶│   外部API服务   │───▶│   数据存储      │
│                 │    │                 │    │                 │
│ - Python 3.8+   │    │ - GLM API       │    │ - 飞书多维表格  │
│ - 系统依赖      │    │ - 飞书 API      │    │ - 日志文件      │
│ - 环境变量      │    │ - 网络连接      │    │ - 处理结果      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件
- **CLI应用**: 命令行界面和主要业务逻辑
- **数据处理**: 多格式数据加载和处理
- **外部集成**: GLM AI和飞书API集成
- **监控日志**: 结构化日志和性能监控

---

## 🔧 环境要求

### 系统要求
| 组件 | 最小要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux/macOS/Windows | Linux Server |
| Python | 3.8+ | 3.10+ |
| 内存 | 512MB | 1GB+ |
| 存储 | 100MB | 500MB+ |
| 网络 | 外网访问 | 稳定高速连接 |

### 软件依赖
```bash
# 核心依赖
requests>=2.28.0
python-dotenv>=1.0.0
aiohttp>=3.8.0

# 可选依赖 (开发环境)
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
```

### 外部服务
- **智谱AI (GLM)**: 标题生成服务
- **飞书开放平台**: 多维表格API
- **网络连接**: 稳定的HTTPS访问

---

## 🚀 部署步骤

### 1. 环境准备

#### 1.1 系统环境
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# CentOS/RHEL  
sudo yum install python3 python3-pip git

# macOS
brew install python3 git
```

#### 1.2 项目部署
```bash
# 1. 克隆项目
git clone <repository-url>
cd CallawayJP

# 2. 切换到生产分支
git checkout refactor/feishu-update-v2

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 4. 安装依赖
pip install -r requirements.txt
```

### 2. 配置管理

#### 2.1 环境变量配置
```bash
# 创建环境变量文件
cat > .env << 'EOF'
# GLM API配置
ZHIPU_API_KEY=your_actual_glm_api_key

# 飞书API配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=your_actual_app_secret
FEISHU_APP_TOKEN=your_actual_app_token
FEISHU_TABLE_ID=your_actual_table_id

# 系统配置
FEISHU_CLIENT=real
LOG_LEVEL=INFO
MAX_CONCURRENCY=5
TIMEOUT_SECONDS=300
EOF

# 设置权限
chmod 600 .env
```

#### 2.2 配置验证
```bash
# 验证环境变量
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['ZHIPU_API_KEY', 'FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_APP_TOKEN', 'FEISHU_TABLE_ID']
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f'❌ 缺少环境变量: {missing}')
    exit(1)
else:
    print('✅ 环境变量配置完成')
"
```

### 3. 功能验证

#### 3.1 干运行测试
```bash
# 使用样本数据测试
python3 -m CallawayJP.feishu_update.cli \
  --input CallawayJP/feishu_update/baseline/inputs/sample_all_products_dedup.json \
  --dry-run \
  --verbose

# 预期输出
# ✅ 成功加载 184 个产品
# ✅ 筛选出 184 个候选产品
# ✅ 标题生成完成
# ✅ 干运行完成，未进行实际更新
```

#### 3.2 连通性测试
```bash
# 测试GLM API连接
python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('ZHIPU_API_KEY')

headers = {'Authorization': f'Bearer {api_key}'}
try:
    response = requests.get('https://open.bigmodel.cn/api/paas/v4/models', headers=headers, timeout=10)
    if response.status_code == 200:
        print('✅ GLM API连接正常')
    else:
        print(f'❌ GLM API连接失败: {response.status_code}')
except Exception as e:
    print(f'❌ GLM API连接异常: {e}')
"

# 测试飞书API连接
python3 -c "
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')

try:
    response = requests.post('https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal', 
                           json={'app_id': app_id, 'app_secret': app_secret}, timeout=10)
    if response.status_code == 200:
        print('✅ 飞书API连接正常')
    else:
        print(f'❌ 飞书API连接失败: {response.status_code}')
except Exception as e:
    print(f'❌ 飞书API连接异常: {e}')
"
```

### 4. 生产部署

#### 4.1 生产环境执行
```bash
# 创建执行脚本
cat > run_feishu_update.sh << 'EOF'
#!/bin/bash

# 设置工作目录
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 加载环境变量
export $(grep -v '^#' .env | xargs)

# 记录执行时间
echo "开始执行时间: $(date)"

# 执行更新
python3 -m CallawayJP.feishu_update.cli \
  --input "$1" \
  --verbose \
  2>&1 | tee "logs/feishu_update_$(date +%Y%m%d_%H%M%S).log"

# 记录完成时间
echo "完成执行时间: $(date)"
EOF

chmod +x run_feishu_update.sh
```

#### 4.2 日志目录创建
```bash
# 创建日志目录
mkdir -p logs
mkdir -p data/backup
mkdir -p data/processed

# 设置日志轮转 (可选)
cat > /etc/logrotate.d/feishu-update << 'EOF'
/path/to/CallawayJP/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    copytruncate
}
EOF
```

---

## 📊 监控和运维

### 1. 性能监控

#### 1.1 关键指标
```bash
# 监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash

LOG_DIR="logs"
LATEST_LOG=$(ls -t ${LOG_DIR}/feishu_update_*.log | head -1)

if [ -f "$LATEST_LOG" ]; then
    echo "=== 最新执行状态 ==="
    echo "日志文件: $LATEST_LOG"
    echo "文件大小: $(du -h "$LATEST_LOG" | cut -f1)"
    echo "最后修改: $(stat -c %y "$LATEST_LOG")"
    
    echo -e "\n=== 处理统计 ==="
    grep "成功更新" "$LATEST_LOG" | tail -1
    grep "候选产品" "$LATEST_LOG" | tail -1  
    grep "处理时间" "$LATEST_LOG" | tail -1
    
    echo -e "\n=== 错误检查 ==="
    ERROR_COUNT=$(grep -c "ERROR" "$LATEST_LOG")
    WARN_COUNT=$(grep -c "WARN" "$LATEST_LOG")
    echo "错误数量: $ERROR_COUNT"
    echo "警告数量: $WARN_COUNT"
    
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "\n=== 最近错误 ==="
        grep "ERROR" "$LATEST_LOG" | tail -3
    fi
else
    echo "❌ 未找到日志文件"
fi
EOF

chmod +x monitor.sh
```

#### 1.2 健康检查
```bash
# 健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash

# 检查进程
if pgrep -f "feishu_update.cli" > /dev/null; then
    echo "✅ 进程运行中"
else
    echo "⚠️  未发现运行进程"
fi

# 检查依赖
python3 -c "
try:
    import requests, aiohttp
    from dotenv import load_dotenv
    print('✅ 依赖包正常')
except ImportError as e:
    print(f'❌ 依赖包缺失: {e}')
"

# 检查磁盘空间
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    echo "✅ 磁盘空间充足 (${DISK_USAGE}%)"
else
    echo "⚠️  磁盘空间不足 (${DISK_USAGE}%)"
fi

# 检查网络连接
if curl -s --connect-timeout 5 https://open.bigmodel.cn > /dev/null; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接异常"
fi
EOF

chmod +x health_check.sh
```

### 2. 自动化运维

#### 2.1 定时任务 (Cron)
```bash
# 编辑crontab
crontab -e

# 添加定时任务示例 (每天上午9点执行)
0 9 * * * /path/to/CallawayJP/run_feishu_update.sh /path/to/data/daily_products.json

# 每小时健康检查
0 * * * * /path/to/CallawayJP/health_check.sh >> /path/to/CallawayJP/logs/health.log 2>&1
```

#### 2.2 系统服务 (Systemd)
```bash
# 创建系统服务文件
sudo cat > /etc/systemd/system/feishu-update.service << 'EOF'
[Unit]
Description=Feishu Update Service
After=network.target

[Service]
Type=oneshot
User=feishu
Group=feishu
WorkingDirectory=/path/to/CallawayJP
Environment=PATH=/path/to/CallawayJP/venv/bin
ExecStart=/path/to/CallawayJP/run_feishu_update.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable feishu-update.service

# 手动执行
sudo systemctl start feishu-update.service

# 查看状态
sudo systemctl status feishu-update.service
```

### 3. 备份策略

#### 3.1 数据备份
```bash
# 备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="data/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份配置文件
cp .env "$BACKUP_DIR/env_$DATE"

# 备份重要日志
cp logs/feishu_update_*.log "$BACKUP_DIR/" 2>/dev/null || true

# 备份处理结果
cp -r results/ "$BACKUP_DIR/results_$DATE/" 2>/dev/null || true

# 清理老备份 (保留30天)
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "备份完成: $BACKUP_DIR"
EOF

chmod +x backup.sh
```

#### 3.2 数据恢复
```bash
# 恢复脚本
cat > restore.sh << 'EOF'
#!/bin/bash

if [ -z "$1" ]; then
    echo "用法: $0 <备份日期YYYYMMDD_HHMMSS>"
    echo "可用备份:"
    ls data/backup/env_* 2>/dev/null | sed 's/.*env_//'
    exit 1
fi

BACKUP_DATE="$1"
BACKUP_DIR="data/backup"

# 恢复环境变量
if [ -f "$BACKUP_DIR/env_$BACKUP_DATE" ]; then
    cp "$BACKUP_DIR/env_$BACKUP_DATE" .env
    echo "✅ 环境变量已恢复"
else
    echo "❌ 备份文件不存在"
    exit 1
fi

# 恢复结果数据
if [ -d "$BACKUP_DIR/results_$BACKUP_DATE" ]; then
    cp -r "$BACKUP_DIR/results_$BACKUP_DATE"/* results/
    echo "✅ 结果数据已恢复"
fi
EOF

chmod +x restore.sh
```

---

## 🔒 安全配置

### 1. 访问控制

#### 1.1 文件权限
```bash
# 设置安全权限
chmod 600 .env                    # 环境变量文件
chmod 700 venv/                   # 虚拟环境目录
chmod 755 *.sh                    # 执行脚本
chmod 644 *.md *.py               # 文档和代码
```

#### 1.2 用户权限
```bash
# 创建专用用户 (推荐)
sudo useradd -m -s /bin/bash feishu
sudo usermod -G feishu feishu

# 切换到专用用户
sudo su - feishu
```

### 2. 网络安全

#### 2.1 防火墙配置
```bash
# 仅允许必要的出站连接
sudo ufw allow out 443/tcp    # HTTPS
sudo ufw allow out 80/tcp     # HTTP (重定向用)
sudo ufw deny out 22/tcp      # 禁止SSH出站
```

#### 2.2 SSL/TLS验证
```bash
# 验证证书有效性
python3 -c "
import ssl
import socket

def verify_ssl(hostname, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f'✅ {hostname} SSL证书有效')

verify_ssl('open.bigmodel.cn')
verify_ssl('open.feishu.cn')
"
```

### 3. 敏感信息保护

#### 3.1 环境变量加密 (可选)
```bash
# 使用gpg加密环境变量
gpg --symmetric --cipher-algo AES256 .env
mv .env.gpg .env.encrypted
rm .env

# 解密使用
gpg --decrypt .env.encrypted > .env
```

#### 3.2 API密钥轮换
```bash
# 密钥轮换脚本
cat > rotate_keys.sh << 'EOF'
#!/bin/bash

echo "⚠️  开始密钥轮换过程"
echo "1. 请在GLM平台生成新的API密钥"
echo "2. 请在飞书开放平台更新应用密钥"
echo "3. 更新.env文件中的密钥配置"
echo "4. 运行测试验证新密钥有效性"

read -p "确认完成上述步骤? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    ./health_check.sh
    echo "✅ 密钥轮换完成"
else
    echo "❌ 密钥轮换取消"
fi
EOF

chmod +x rotate_keys.sh
```

---

## 🚨 故障排除

### 1. 常见问题

#### 1.1 环境变量问题
```bash
# 问题: KeyError: 'ZHIPU_API_KEY'
# 解决方案:
echo "检查环境变量配置:"
cat .env | grep -v '^#' | grep -v '^$'

# 验证加载
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('ZHIPU_API_KEY:', 'SET' if os.getenv('ZHIPU_API_KEY') else 'NOT SET')
"
```

#### 1.2 API连接问题
```bash
# 问题: API调用失败
# 解决方案:
curl -v https://open.bigmodel.cn/api/paas/v4/models \
  -H "Authorization: Bearer $ZHIPU_API_KEY" \
  --connect-timeout 10

# 检查网络代理
echo "HTTP_PROXY: $HTTP_PROXY"
echo "HTTPS_PROXY: $HTTPS_PROXY"
```

#### 1.3 权限问题
```bash
# 问题: Permission denied
# 解决方案:
ls -la .env                           # 检查文件权限
whoami                               # 确认当前用户
groups                               # 检查用户组

# 修复权限
sudo chown $USER:$USER .env
chmod 600 .env
```

### 2. 日志分析

#### 2.1 错误日志分析
```bash
# 分析最近的错误
grep -n "ERROR\|FATAL\|Exception" logs/feishu_update_*.log | tail -10

# 统计错误类型
grep "ERROR" logs/feishu_update_*.log | \
  sed 's/.*ERROR.*: //' | \
  sort | uniq -c | sort -nr
```

#### 2.2 性能分析
```bash
# 分析处理时间
grep "处理时间" logs/feishu_update_*.log | \
  awk '{print $NF}' | \
  sed 's/[^0-9.]//g' | \
  awk '{sum+=$1; count++} END {print "平均处理时间:", sum/count, "秒"}'

# 分析API调用成功率
TOTAL_CALLS=$(grep -c "GLM API" logs/feishu_update_*.log)
SUCCESS_CALLS=$(grep -c "GLM API.*成功" logs/feishu_update_*.log)
echo "GLM API成功率: $(echo "scale=2; $SUCCESS_CALLS * 100 / $TOTAL_CALLS" | bc)%"
```

### 3. 紧急恢复

#### 3.1 服务恢复
```bash
# 快速恢复脚本
cat > emergency_recovery.sh << 'EOF'
#!/bin/bash

echo "🚨 开始紧急恢复程序"

# 1. 停止所有相关进程
pkill -f "feishu_update.cli"
echo "✅ 已停止运行进程"

# 2. 检查系统资源
df -h .
free -h
echo "✅ 系统资源检查完成"

# 3. 恢复最新备份
LATEST_BACKUP=$(ls -t data/backup/env_* | head -1)
if [ -f "$LATEST_BACKUP" ]; then
    cp "$LATEST_BACKUP" .env
    echo "✅ 配置文件已恢复"
fi

# 4. 健康检查
./health_check.sh

echo "🎉 紧急恢复完成"
EOF

chmod +x emergency_recovery.sh
```

#### 3.2 数据一致性检查
```bash
# 数据一致性验证
cat > data_integrity_check.sh << 'EOF'
#!/bin/bash

echo "📊 开始数据一致性检查"

# 检查处理结果文件
RESULT_COUNT=$(find results/ -name "*.json" | wc -l)
echo "结果文件数量: $RESULT_COUNT"

# 检查日志文件完整性
LOG_COUNT=$(find logs/ -name "*.log" -size +0c | wc -l)
echo "有效日志文件: $LOG_COUNT"

# 检查最近处理状态
LATEST_LOG=$(ls -t logs/feishu_update_*.log | head -1)
if [ -f "$LATEST_LOG" ]; then
    LAST_SUCCESS=$(grep "更新处理汇总" "$LATEST_LOG" | tail -1)
    if [ -n "$LAST_SUCCESS" ]; then
        echo "✅ 最近处理成功"
        echo "$LAST_SUCCESS"
    else
        echo "⚠️  最近处理可能异常"
    fi
fi

echo "📊 数据一致性检查完成"
EOF

chmod +x data_integrity_check.sh
```

---

## 📈 性能优化

### 1. 系统级优化

#### 1.1 内存优化
```bash
# Python内存限制
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=100000

# 调整虚拟内存
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

#### 1.2 网络优化
```bash
# TCP连接优化
echo 'net.ipv4.tcp_keepalive_time=120' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_keepalive_intvl=30' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_keepalive_probes=3' | sudo tee -a /etc/sysctl.conf

# 应用设置
sudo sysctl -p
```

### 2. 应用级优化

#### 2.1 并发调优
```bash
# 根据硬件配置调整并发数
CPU_CORES=$(nproc)
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')

# 建议配置
if [ $MEMORY_GB -ge 4 ] && [ $CPU_CORES -ge 4 ]; then
    echo "MAX_CONCURRENCY=8" >> .env
elif [ $MEMORY_GB -ge 2 ] && [ $CPU_CORES -ge 2 ]; then
    echo "MAX_CONCURRENCY=5" >> .env
else
    echo "MAX_CONCURRENCY=2" >> .env
fi
```

#### 2.2 缓存策略
```bash
# 配置Python字节码缓存
export PYTHONDONTWRITEBYTECODE=0
export PYTHONPYCACHEPREFIX=/tmp/pycache

# 创建缓存目录
mkdir -p /tmp/pycache
```

---

## 📝 维护计划

### 每日维护
- [ ] 检查应用运行状态
- [ ] 查看错误日志和警告
- [ ] 监控API调用成功率
- [ ] 验证处理结果完整性

### 每周维护  
- [ ] 执行完整健康检查
- [ ] 清理过期日志文件
- [ ] 更新系统安全补丁
- [ ] 备份重要配置和数据

### 每月维护
- [ ] 性能分析和优化
- [ ] API密钥安全检查
- [ ] 依赖包版本更新
- [ ] 容量规划评估

### 季度维护
- [ ] 全面安全审计
- [ ] API密钥轮换
- [ ] 架构优化评估
- [ ] 灾难恢复演练

---

## 📞 技术支持

### 联系方式
- **技术文档**: [项目README](README.md)
- **架构设计**: [技术架构文档](TECHNICAL_ARCHITECTURE.md)  
- **问题报告**: GitHub Issues
- **功能请求**: GitHub Feature Requests

### 支持范围
- ✅ 部署配置支持
- ✅ 常见问题排查
- ✅ 性能优化建议
- ✅ 安全配置指导

---

**部署指南版本**: v1.0  
**适用系统版本**: v2.0+  
**最后更新**: 2025-11-04  
**维护负责人**: Claude (AI Assistant)