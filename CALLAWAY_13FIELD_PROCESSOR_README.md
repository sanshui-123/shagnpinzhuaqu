# 卡拉威13字段改写逻辑完整提取

## 概述

基于CallawayJP项目的完整13字段改写系统，包含所有核心逻辑和配置。

## 核心功能

### 1. AI标题生成（title_v6.py完整版）
- **完整GLM提示词**：包含季节判断、品牌识别、性别判断、功能词选择、结尾词判断
- **智能优化规则**：长度控制（26-30字）、格式验证、重复检测
- **品牌识别**：支持11个主要高尔夫品牌（Callaway、Titleist、Puma等）
- **重试机制**：2次重试确保生成质量

### 2. 24种细分分类规则（classifiers.py完整版）
- **服装类**：羽绒服/棉服、卫衣/连帽衫、夹克、马甲/背心、风衣/防风外套、Polo衫、T恤、衬衫、针织衫/毛衣、长裤、短裤、裙装
- **鞋类**：高尔夫球鞋
- **配件类**：高尔夫手套、帽子/头饰、腰带、袜子、球杆头套、高尔夫球、球包、雨伞、毛巾、标记夹/果岭工具、其他高尔夫配件
- **智能匹配**：URL优先 + 产品名称关键词匹配

### 3. 产品描述翻译（translator_v2.py完整版）
- **结构化翻译**：【产品描述】+【产品亮点】+【材质信息】+【产地与洗涤】+【尺码对照表】
- **专业术语**：面料名称、工艺、营销文案
- **Markdown格式**：尺码表表格化显示
- **GLM-4.6模型**：高质量翻译保证

### 4. 图片处理规则（scrape_product_detail.js核心逻辑）
- **颜色翻译**：70+种颜色中英日文对照表
- **分配规则**：第一个颜色保留所有图片，其他颜色只保留前6张

## 环境要求

### 必需环境变量
```bash
export ZHIPU_API_KEY="your_zhipu_api_key"
```

### 可选环境变量
```bash
export GLM_MIN_INTERVAL=0.4    # API调用最小间隔（秒）
export GLM_MAX_RETRIES=3       # 最大重试次数
export GLM_BACKOFF_FACTOR=1.8  # 指数退避因子
```

### Python依赖
```bash
pip install requests
```

## 使用方法

### 1. 单个产品处理

```python
from callaway_13field_processor import Callaway13FieldProcessor

# 创建处理器实例
processor = Callaway13FieldProcessor()

# 验证环境配置
validation = processor.validate_environment()
if not validation['valid']:
    print("环境配置错误:", validation['errors'])
    exit(1)

# 处理单个产品
product_data = {
    'productId': 'C25128100',
    'productName': '25FW キャロウェイ メンズ ポロシャツ ストレッチ機能性',
    'brand': 'Callaway Golf',
    'description': '今シーズンのスターストレッチ採用のポロシャツ...',
    'colors': [{'code': '1031', 'name': 'ネイビー'}],
    'sizes': ['S', 'M', 'L', 'LL'],
    'images': {'product': ['image1.jpg', 'image2.jpg']},
    # ... 其他字段
}

result = processor.process_product(product_data)

# 查看处理结果
print("中文标题:", result['field_01_title_cn'])
print("性别:", result['field_02_gender'])
print("服装类型:", result['field_03_clothing_type'])
print("中文描述:", result['field_04_description_cn'])
```

### 2. 批量处理

```python
# 批量处理产品列表
products_list = [product1, product2, product3, ...]
results = processor.batch_process(products_list)

for result in results:
    print(f"产品 {result['product_id']}: {result['field_01_title_cn']}")
```

### 3. 直接调用功能模块

```python
# 直接调用标题生成
from callaway_13field_processor import generate_cn_title
title = generate_cn_title(product_data)

# 直接调用分类
from callaway_13field_processor import determine_gender, determine_clothing_type
gender = determine_gender(product_data)
clothing_type = determine_clothing_type(product_data)

# 直接调用翻译
from callaway_13field_processor import translate_description
description_cn = translate_description(product_data)
```

## 13字段说明

| 字段 | 名称 | 说明 |
|------|------|------|
| field_01_title_cn | 中文标题 | AI生成的26-30字中文标题 |
| field_02_gender | 性别分类 | 男/女/中性 |
| field_03_clothing_type | 服装类型 | 24种细分类型 |
| field_04_description_cn | 中文描述 | 结构化翻译的产品描述 |
| field_05_images_total | 图片总数 | 所有图片数量 |
| field_06_images_first_color | 第一个颜色图片数 | 第一个颜色的图片数量 |
| field_07_images_other_colors | 其他颜色图片数 | 其他颜色的图片总数 |
| field_08_color_names | 颜色名称列表 | 原始颜色名称 |
| field_09_color_names_cn | 中文颜色名称 | 翻译后的颜色名称 |
| field_10_sizes | 尺码列表 | 可用尺码 |
| field_11_price | 价格 | 商品价格 |
| field_12_category | 分类 | 商品分类 |
| field_13_tags | 标签 | 商品标签 |

## 测试

运行内置测试：

```bash
python callaway_13field_processor.py
```

测试将验证：
1. 环境配置正确性
2. AI标题生成功能
3. 长度控制（26-30字）
4. 关键词包含（"高尔夫"、品牌名）
5. 各个模块的基本功能

## 特性优势

### 🎯 完整性
- **100%复制**：所有逻辑、提示词、配置完整提取
- **无简化版本**：保持原系统的所有细节和规则
- **完整依赖**：包含所有必要的配置和映射表

### 🚀 高质量
- **AI标题生成**：基于GLM的智能标题，符合淘宝规范
- **专业翻译**：结构化产品描述翻译，保持营销吸引力
- **精确分类**：24种细分类别，准确识别产品类型

### 🛡️ 可靠性
- **重试机制**：API调用失败自动重试
- **错误处理**：完善的异常处理和日志记录
- **环境验证**：启动前检查所有必要配置

### 🔧 易用性
- **简单接口**：一个函数处理完整13个字段
- **批量处理**：支持批量处理多个产品
- **模块化设计**：可单独使用各个功能模块

## 技术架构

```
卡拉威13字段处理器
├── AI标题生成模块 (title_v6.py)
│   ├── 品牌识别
│   ├── 智能提示词构建
│   ├── GLM API调用
│   └── 标题优化验证
├── 分类系统 (classifiers.py)
│   ├── 性别分类
│   └── 24种服装类型细分
├── 翻译系统 (translator_v2.py)
│   ├── 描述清理
│   ├── 结构化翻译
│   └── 格式验证
├── 图片处理 (scrape_product_detail.js)
│   ├── 颜色翻译
│   ├── 分配规则
│   └── 图片过滤
└── 配置和常量
    ├── 品牌映射表
    ├── 颜色对照表
    └── API配置
```

## 注意事项

1. **API配额**：GLM API有调用频率限制，批量处理时注意添加适当延迟
2. **环境变量**：确保正确设置`ZHIPU_API_KEY`
3. **数据格式**：输入产品数据需要包含必要的字段（productName、description等）
4. **网络连接**：需要稳定的网络连接访问GLM API

## 版本信息

- **版本**: 1.0.0
- **基于**: CallawayJP项目完整提取
- **日期**: 2025-11-13
- **作者**: Claude Code

## 许可证

本代码基于CallawayJP项目提取，请遵循相应的开源许可证要求。