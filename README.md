# Callaway JP 飞书更新系统 v2.0

**最新版本**: v2.0 (架构重构版)  
**分支**: refactor/feishu-update-v2  
**状态**: ✅ 阶段7验证完成，准备上线  

本项目是 Callaway 日本官网产品数据自动同步到飞书多维表格的现代化解决方案。v2.0版本采用模块化微服务架构，支持多种数据源格式，提供完整的CLI工具链。

---

## 🏗️ 系统架构

### v2.0 核心特性
- ✅ **模块化架构**: 从单脚本重构为分层微服务设计
- ✅ **多数据源支持**: 自动识别和处理3种不同的产品数据格式
- ✅ **智能标题生成**: 集成GLM API，支持fallback机制
- ✅ **并发处理**: 可配置的并发控制和性能优化
- ✅ **CLI工具链**: 完整的命令行界面，支持干运行模式
- ✅ **容错机制**: 完善的错误处理和自动恢复策略

### 架构概览
```
CLI 入口 → 数据加载器 → 服务层处理 → 管道编排 → 飞书更新
    ↓         ↓           ↓          ↓         ↓
  参数解析   格式识别    标题生成    并发控制   批量同步
            字段映射    翻译服务    进度追踪   结果汇总
```

---

## 📁 项目结构

```
CallawayJP/
├── feishu_update/              # v2.0 核心模块
│   ├── cli.py                  # CLI 入口
│   ├── loaders/                # 数据加载器
│   │   ├── detailed.py         # 详细产品数据加载器
│   │   ├── summarized.py       # 汇总产品数据加载器
│   │   └── link_only.py        # 链接数据加载器
│   ├── services/               # 服务层
│   │   ├── title_generator.py  # 标题生成服务
│   │   ├── field_assembler.py  # 字段组装服务
│   │   └── translator.py       # 翻译服务
│   ├── pipeline/               # 管道编排
│   │   ├── update_orchestrator.py  # 更新编排器
│   │   └── parallel_executor.py    # 并行执行器
│   ├── clients/                # 客户端层
│   │   ├── feishu_client.py    # 飞书API客户端
│   │   ├── glm_client.py       # GLM API客户端
│   │   └── dummy_feishu_client.py  # 测试模拟客户端
│   ├── models/                 # 数据模型
│   ├── config/                 # 配置管理
│   └── baseline/               # 测试基线数据
├── results/                    # 历史处理结果
├── guides/                     # 操作指南
└── docs/                       # 项目文档
```

---

## 🚀 快速开始

### 环境要求
- **Python**: 3.8+
- **依赖**: `pip install requests python-dotenv aiohttp`

### 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

环境变量配置：
```bash
# GLM API配置
ZHIPU_API_KEY=your_glm_api_key

# 飞书API配置  
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_APP_TOKEN=your_app_token
FEISHU_TABLE_ID=your_table_id

# 可选配置
FEISHU_CLIENT=real              # 或 dummy (测试模式)
```

### 基本使用

#### 1. 生产环境运行
```bash
# 处理产品数据并同步到飞书
python3 -m CallawayJP.feishu_update.cli \
  --input /path/to/products.json \
  --verbose
```

#### 2. 干运行测试
```bash
# 测试模式，不进行实际更新
python3 -m CallawayJP.feishu_update.cli \
  --input /path/to/products.json \
  --dry-run \
  --verbose
```

#### 3. 使用样本数据测试
```bash
# 使用内置样本数据进行测试
python3 -m CallawayJP.feishu_update.cli \
  --input CallawayJP/feishu_update/baseline/inputs/sample_all_products_dedup.json \
  --dry-run \
  --verbose
```

#### 4. 一键执行脚本 (完整流程)
```bash
# 一键执行完整流程: 抓取 → 去重 → 同步 → 标题生成
# 使用默认女装分类
./run_pipeline.sh

# 指定男装分类
./run_pipeline.sh mens_all https://www.callawaygolf.jp/apparel/mens

# 注意: 需要先配置 .env 文件中的必需环境变量
```

---

## 🔄 飞书强制更新流程

当需要无条件覆盖飞书中的产品数据时，可以使用强制更新模式。此模式会忽略现有数据，强制写入所有可写字段。

### 操作前准备

- **确认输入文件**: 确保已准备好要更新的产品数据文件（例如：`/tmp/dedup_top3.json`）
- **网络环境**: 确保能够正常访问智谱GLM API和飞书API
- **权限验证**: 确认飞书API配置具有数据表写入权限

### 执行步骤

按照以下指令序列执行强制更新：

```bash
cd /Users/sanshui/Desktop/cursor
unset HTTPS_PROXY https_proxy HTTP_PROXY http_proxy
set -a
source .env
set +a
export GLM_CLIENT=real
export FEISHU_CLIENT=real
export SKIP_FEISHU_SYNC=0
python3 -m CallawayJP.feishu_update.cli --input /tmp/dedup_top3.json --force-update --verbose
```

**步骤说明**：
- `cd /Users/sanshui/Desktop/cursor` - 切换到项目根目录
- `unset HTTPS_PROXY ...` - 清除代理设置，避免网络连接问题
- `set -a` - 开启变量自动导出模式
- `source .env` - 加载环境变量文件（包含API密钥等配置）
- `set +a` - 关闭变量自动导出模式
- `export GLM_CLIENT=real` - 启用真实GLM API客户端
- `export FEISHU_CLIENT=real` - 启用真实飞书API客户端
- `export SKIP_FEISHU_SYNC=0` - 确保不跳过飞书同步操作
- `python3 -m CallawayJP.feishu_update.cli --input /tmp/dedup_top3.json --force-update --verbose` - 执行强制更新命令

### 成功标识

**重要**: 终端输出中必须看到以下信息才算执行成功：
```
批次 1/1: ✓ 成功更新 3 条
============================================================
📈 更新处理汇总
============================================================
✓ 成功更新: 3 条
```

如果看到此输出，说明数据已成功强制写入飞书数据表。

### 可选优化：一键命令

为了简化操作，可以将上述步骤封装为函数。在 `~/.zshrc` 中添加：

```bash
feishu_force_update() {
  cd /Users/sanshui/Desktop/cursor || return 1
  unset HTTPS_PROXY https_proxy HTTP_PROXY http_proxy
  set -a
  source .env
  set +a
  export GLM_CLIENT=real
  export FEISHU_CLIENT=real
  export SKIP_FEISHU_SYNC=0
  python3 -m CallawayJP.feishu_update.cli \
    --input /tmp/dedup_top3.json \
    --force-update \
    --verbose
}
```

保存后执行 `source ~/.zshrc` 重新加载配置。之后只需运行：

```bash
feishu_force_update
```

即可完成整套强制更新流程。

### 注意事项

- **数据备份**: 强制更新会覆盖现有数据，建议操作前备份重要数据
- **API配额**: 确保GLM API和飞书API有足够配额
- **错误处理**: 如遇到网络错误或API限流，系统会自动重试或使用fallback机制

---

## 📊 支持的数据格式

### 1. 详细产品格式 (DetailedProductLoader)
```json
{
  "productId": "C25215200",
  "productName": "商品名称", 
  "detailUrl": "https://...",
  "price": "¥12,000",
  "colors": ["黑色", "白色"],
  "sizes": ["S", "M", "L"]
}
```

### 2. 汇总产品格式 (SummarizedProductLoader)
```json
{
  "products": [
    {
      "productId": "C25215200",
      "productName": "商品名称",
      "detailUrl": "https://..."
    }
  ]
}
```

### 3. 原始链接格式 (LinkOnlyProductLoader)
```json
{
  "links": [
    {
      "url": "https://...",
      "priceText": "¥12,000",
      "productId": "C25215200"
    }
  ]
}
```

系统会自动识别输入数据格式，并选择合适的加载器进行处理。

---

## 🔧 CLI 命令参考

### 基本选项
```bash
python3 -m CallawayJP.feishu_update.cli [OPTIONS]
```

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--input` | ✅ | 输入数据文件路径 | `--input products.json` |
| `--dry-run` | ❌ | 干运行模式，不执行实际更新 | `--dry-run` |
| `--verbose` | ❌ | 详细输出模式 | `--verbose` |
| `--config` | ❌ | 自定义配置文件路径 | `--config custom.json` |

### 使用示例
```bash
# 1. 完整生产环境执行
python3 -m CallawayJP.feishu_update.cli \
  --input results/all_products_dedup_latest.json \
  --verbose

# 2. 开发测试模式  
FEISHU_CLIENT=dummy python3 -m CallawayJP.feishu_update.cli \
  --input test_data.json \
  --dry-run \
  --verbose

# 3. 静默批处理模式
python3 -m CallawayJP.feishu_update.cli \
  --input products.json 2>&1 | tee update.log
```

---

## 📈 处理流程

### 完整处理管道
```
1. 数据加载 → 2. 格式识别 → 3. 产品解析 → 4. 候选筛选
                    ↓
8. 结果汇总 ← 7. 批量更新 ← 6. 字段组装 ← 5. 标题生成
```

### 详细步骤说明
1. **数据加载**: 读取输入文件，验证JSON格式
2. **格式识别**: 自动识别数据格式，选择合适的加载器
3. **产品解析**: 将原始数据转换为标准Product对象
4. **候选筛选**: 查询飞书现有数据，识别需要更新的新产品
5. **标题生成**: 调用GLM API生成产品标题(支持fallback)
6. **字段组装**: 将产品数据转换为飞书字段格式
7. **批量更新**: 并发调用飞书API进行批量更新
8. **结果汇总**: 生成处理报告和统计信息

---

## 🎯 监控和日志

### 输出示例
```bash
[INFO] 开始加载产品数据...
[INFO] 检测到数据格式: SummarizedProductLoader
[INFO] 成功加载 184 个产品
[INFO] 筛选出 184 个候选产品 (100% 为新产品)
[INFO] 开始并发生成标题...
[WARN] GLM API调用失败，使用fallback策略
[INFO] 标题生成完成，成功率: 95%
[INFO] 开始批量更新飞书...
[INFO] 飞书更新完成，成功: 180, 失败: 4

============================================================
📈 更新处理汇总  
============================================================
✓ 成功更新: 180 条
📊 候选产品: 184 个
⏱️ 处理时间: 3分42秒
============================================================
```

### 日志级别
- **INFO**: 正常处理流程信息
- **WARN**: 警告信息(如API fallback)
- **ERROR**: 错误信息和异常详情
- **DEBUG**: 详细调试信息(使用--verbose启用)

---

## 🔧 高级配置

### 性能调优
```python
# config/settings.py 中的关键配置
MAX_CONCURRENCY = 5        # 最大并发数
TIMEOUT_SECONDS = 300      # 超时时间
BATCH_SIZE = 100           # 批处理大小
```

### 自定义翻译
```python
# config/translation.py
COLOR_TRANSLATIONS = {
    'black': '黑色',
    'white': '白色',
    # 添加更多翻译...
}
```

### GLM提示词定制
```python
# config/settings.py
TITLE_PROMPT_TEMPLATE = """
基于以下信息生成简洁的产品标题:
品牌: {brand_name}
产品: {product_name}
分类: {category}
要求: 不超过50字符，突出品牌和产品特色
"""
```

---

## 🧪 测试和验证

### 单元测试
```bash
# 运行加载器测试
python3 CallawayJP/tests/test_stage3_integration.py

# 运行价格字段测试  
python3 CallawayJP/tests/test_linkonly_price.py
```

### 回归测试
```bash
# 运行完整回归测试
python3 -m CallawayJP.feishu_update.cli \
  --input CallawayJP/feishu_update/baseline/inputs/sample_all_products_dedup.json \
  --dry-run \
  --verbose
```

### 验证清单
- [ ] 数据加载成功率 100%
- [ ] 候选筛选逻辑正确
- [ ] 标题生成或fallback正常
- [ ] 飞书字段映射完整
- [ ] 更新结果准确统计

---

## 📚 相关文档

- [V2.0实施方案总结](V2_IMPLEMENTATION_SUMMARY.md) - 项目概览和成果总结
- [技术架构文档](TECHNICAL_ARCHITECTURE.md) - 详细技术设计和实现
- [阶段7验证报告](../STAGE7_REGRESSION_VALIDATION_REPORT.md) - 回归测试结果
- [操作指南](guides/category_scrape_checklist.md) - 分类抓取工作流

## 🚧 故障排除

### 常见问题

#### 1. 环境变量未配置
```bash
# 错误: KeyError: 'ZHIPU_API_KEY'
# 解决: 检查.env文件是否正确配置
export ZHIPU_API_KEY=your_api_key
```

#### 2. 数据格式无法识别
```bash
# 错误: ValueError: 无法找到合适的数据加载器
# 解决: 检查输入文件格式是否为支持的三种格式之一
```

#### 3. GLM API配额不足
```bash
# 警告: GLM API调用失败，使用fallback策略
# 系统会自动使用fallback标题，无需人工干预
```

#### 4. 飞书API限流
```bash
# 系统自动处理API限流，会降低并发度并重试
# 如持续失败，检查API配额和权限
```

### 调试模式
```bash
# 启用详细调试信息
python3 -m CallawayJP.feishu_update.cli \
  --input products.json \
  --verbose \
  --dry-run
```

---

## 📞 支持和反馈

### 获取帮助
- **项目文档**: 查看 `docs/` 目录下的详细文档
- **技术支持**: 创建 GitHub Issue 描述问题
- **功能请求**: 提交 Feature Request 到项目仓库

### 贡献指南
1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -m 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建 Pull Request

---

## 📋 更新日志

### v2.0.0 (2025-11-04) - 架构重构版
- ✅ 重构为模块化微服务架构
- ✅ 新增3种数据加载器支持多格式
- ✅ 集成GLM API智能标题生成
- ✅ 实现完整的CLI工具链
- ✅ 添加并发处理和性能优化
- ✅ 完善错误处理和容错机制
- ✅ 新增干运行模式和测试支持

### v1.x (历史版本)
- 基础抓取和同步功能
- 单脚本架构实现
- 分类页面抓取系统

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**项目维护**: Claude (AI Assistant)  
**最后更新**: 2025-11-04  
**版本**: v2.0
