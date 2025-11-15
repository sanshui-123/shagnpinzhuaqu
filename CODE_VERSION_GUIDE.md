# CallawayJP 代码版本使用指南

## 📋 概述

本项目采用三步架构处理高尔夫产品数据。为避免版本混乱，请严格按照本指南使用指定的代码文件。

## 🏗️ 三步架构

### 第一步：数据抓取
**正确文件**：
- `scripts/multi_brand/brands/lecoqgolf/single_url_fixed_processor.js` - 单个产品抓取
- `scripts/multi_brand/brands/lecoqgolf/batch_detail_processor.js` - 批量产品抓取
- `scripts/multi_brand/brands/lecoqgolf/enhanced_detail_scraper.js` - 增强版抓取器

**功能**：
- 抓取产品基本信息
- 提取图片、颜色、尺码等数据
- 支持Le Coq公鸡乐卡克品牌特定规则

### 第二步：数据处理
**正确文件**：
- `callaway_13field_processor.py` - 13字段处理器

**功能**：
- AI标题生成
- 颜色翻译（日语→中文）
- 描述翻译
- 图片处理和分组

### 第三步：飞书同步
**正确文件**：
- `step3_feishu_sync.py` - 飞书多维表格同步

**功能**：
- 数据格式化
- 飞书API写入
- 字段映射处理

## 🚀 推荐使用流程

### 1. 单个产品测试
```bash
# 测试单个URL的完整流程
python3 test_full_pipeline_one_url.py
```

### 2. Le Coq公鸡乐卡克抓取
```bash
# 第一步：抓取单个产品
cd scripts/multi_brand/brands/lecoqgolf
node single_url_fixed_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872AM012332/"

# 第二步：处理抓取的数据
cd /Users/sanshui/Desktop/CallawayJP
python3 callaway_13field_processor.py --input scripts/multi_brand/brands/lecoqgolf/single_url_fixed_*.json --output step2_processed.json

# 第三步：同步到飞书
python3 step3_feishu_sync.py --input step2_processed.json

# 批量抓取
cd scripts/multi_brand/brands/lecoqgolf
node batch_detail_processor.js
```

### 3. Callaway品牌抓取
```bash
# Callaway使用不同的规则，不需要修改
cd scripts/multi_brand/brands/odyssey
node [callaway专用抓取脚本]
```

## ⚠️ 重要规则

### 1. Le Coq公鸡乐卡克品牌规则
- 品牌名：`Le Coq公鸡乐卡克`（硬编码）
- 性别判断：基于URL路径和内容
- 图片规则：只抓取第一个颜色，1100×1100尺寸，无数量限制
- 尺码规则：必须提取S, M, L, LL, 3L全部5个尺码

### 2. 字段映射
**第一步输出字段**（中文）：
- 商品链接、商品ID、商品标题、品牌名
- 价格、性别、颜色、尺码、图片链接
- 详情页文字、尺码表

**第二步输出字段**（处理后的中英混合）：
- 商品ID、生成标题、品牌、性别
- 服装类型、颜色、尺寸、描述翻译
- 图片链接（处理后）

**第三步输出字段**（飞书格式）：
- 商品链接、商品ID、商品标题、品牌名
- 价格、性别、衣服分类、图片URL
- 颜色、尺码、详情页文字、尺码表

### 3. 已删除的混乱文件
为避免版本混乱，以下文件已被删除：
- `test_*.py`（除`test_full_pipeline_one_url.py`外）
- `scripts/multi_brand/brands/lecoqgolf/test_*.js`
- `scripts/sync_feishu_products.py`
- `lecoqgolf_feishu_sync.js`
- 所有demo和example文件

## 🔧 配置要求

### 环境变量
确保`callaway.env`文件包含：
```
# GLM API（第二步需要）
GLM_API_KEY=your_glm_api_key

# 飞书配置（第三步需要）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_APP_TOKEN=your_app_token
FEISHU_TABLE_ID=your_table_id
```

### 依赖包
```bash
# Python依赖（第二步、第三步需要）
pip install playwright requests

# Node.js依赖（第一步需要）
npm install
```

## 🔄 完整生产流程示例

### 示例：处理单个Le Coq产品
```bash
# 第一步：抓取数据
cd scripts/multi_brand/brands/lecoqgolf
node single_url_fixed_processor.js "https://store.descente.co.jp/commodity/SDSC0140D/LE1872AM012332/"

# 输出：single_url_fixed_2025-11-14T15-07-05-621Z.json

# 第二步：处理数据
cd /Users/sanshui/Desktop/CallawayJP
python3 callaway_13field_processor.py --input scripts/multi_brand/brands/lecoqgolf/single_url_fixed_2025-11-14T15-07-05-621Z.json --output step2_result.json

# 输出：step2_result.json（包含AI标题、翻译等）

# 第三步：同步到飞书
python3 step3_feishu_sync.py --input step2_result.json

# 输出：成功写入飞书记录
```

## 🔧 配置要求

### 环境变量
确保`callaway.env`文件包含：
```
# GLM API（第二步需要）
GLM_API_KEY=your_glm_api_key

# 飞书配置（第三步需要）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_APP_TOKEN=your_app_token
FEISHU_TABLE_ID=your_table_id
```

### 依赖包
```bash
# Python依赖（第二步、第三步需要）
pip install playwright requests

# Node.js依赖（第一步需要）
npm install
```

## 🐛 故障排除

### 常见问题
1. **字段名不匹配**：检查是否使用了正确的代码版本
2. **图片数量限制**：确保使用`single_url_fixed_processor.js`而不是旧版本
3. **飞书写入失败**：检查环境变量和字段映射配置
4. **品牌识别错误**：确保第二步处理器支持中文字段名
5. **数据格式错误**：确保JSON文件格式正确

### 调试命令
```bash
# 检查飞书字段映射
python3 -c "from step3_feishu_sync import FeishuSync; fs = FeishuSync(); print(fs.feishu_field_mapping)"

# 测试抓取器
cd scripts/multi_brand/brands/lecoqgolf
node single_url_fixed_processor.js

# 测试处理器
python3 callaway_13field_processor.py --help

# 测试飞书同步（干运行）
python3 step3_feishu_sync.py --input your_data.json --dry-run
```

## 📝 更新记录

- 2025-11-14：清理所有混乱的测试文件，明确代码版本指南
- 2025-11-14：修复三步分离执行问题，支持独立命令行操作
- 2025-11-14：修复品牌识别和字段映射问题
- 修复字段映射问题，统一三步架构数据流
- 完善Le Coq公鸡乐卡克品牌特定规则

## 📞 支持

如有问题，请检查：
1. 是否使用了本指南指定的正确文件
2. 环境变量是否正确配置
3. 依赖包是否完整安装

**不要使用任何未在本指南中列出的文件！**