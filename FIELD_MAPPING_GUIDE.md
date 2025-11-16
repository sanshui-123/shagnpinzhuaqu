# 字段映射说明和脚本一致性指南

## 概述

本文档说明CallawayJP项目中各脚本间的字段映射关系，确保从网页抓取到飞书同步的数据流转一致性。

## 数据流程概览

```
JavaScript抓取器 → 产品数据JSON → Python字段改写 → 飞书API同步
```

## 核心脚本文件

### JavaScript 抓取脚本
- `single_unified_processor.js` - 单个商品处理
- `batch_unified_processor.js` - 批量商品处理
- `unified_detail_scraper.js` - 统一详情页抓取器

### Python 处理脚本
- `tongyong_feishu_update/run_pipeline.py` - 主流水线入口
- `tongyong_feishu_update/services/title_v6.py` - 标题生成服务
- `tongyong_feishu_update/services/field_assembler.py` - 字段组装服务
- `tongyong_feishu_update/config/prompts.py` - 提示词模板

## 标准数据格式

### 输入格式（抓取器输出）
```json
{
  "products": {
    "PRODUCT_ID": {
      "productId": "商品ID",
      "productName": "商品标题（日文）",
      "detailUrl": "商品链接",
      "price": "价格",
      "brand": "品牌",
      "gender": "性别",
      "colors": ["颜色1", "颜色2"],
      "sizes": ["尺码1", "尺码2"],
      "imageUrls": ["图片URL1", "图片URL2"],
      "description": "商品描述",
      "sizeChart": {
        "html": "尺码表HTML",
        "text": "尺码表文本"
      },
      "_original_data": {
        "原始抓取数据": "保留所有原始信息"
      }
    }
  },
  "source_file": "生成的文件路径",
  "timestamp": "处理时间戳"
}
```

### 输出格式（飞书字段）
```json
{
  "records": [
    {
      "fields": {
        "商品ID": "商品唯一标识",
        "品牌名": "品牌名称（中文）",
        "商品标题": "AI生成的中文标题",
        "颜色": "翻译后的颜色，逗号分隔",
        "尺码": "可用尺码，逗号分隔",
        "性别": "商品性别分类",
        "价格": "商品价格信息",
        "商品链接": "原始商品详情页URL",
        "图片URL": "主要图片URL，换行分隔",
        "图片数量": "图片总数",
        "详情页文字": "翻译后的商品描述",
        "尺码表": "尺码表信息",
        "上传状态": "处理状态标识",
        "创建时间": "记录创建时间",
        "最近更新时间": "记录最后更新时间"
      }
    }
  ]
}
```

## 字段映射规则

### 基础字段
| 抓取器字段 | 飞书字段 | 处理说明 |
|-----------|---------|----------|
| `productId` | `商品ID` | 直接映射 |
| `brand` | `品牌名` | 映射为中文品牌名 |
| `productName` | `商品标题` | AI标题生成服务处理 |
| `detailUrl` | `商品链接` | 直接映射 |
| `price` | `价格` | 清理格式后映射 |
| `gender` | `性别` | 标准化性别分类 |

### 数组字段处理
| 抓取器字段 | 飞书字段 | 处理方式 |
|-----------|---------|----------|
| `colors[]` | `颜色` | 翻译颜色名，逗号连接 |
| `sizes[]` | `尺码` | 直接连接，逗号分隔 |
| `imageUrls[]` | `图片URL` | 取前6张，换行连接 |

### 复杂字段
| 抓取器字段 | 飞书字段 | 处理说明 |
|-----------|---------|----------|
| `description` | `详情页文字` | 日文转中文翻译 |
| `sizeChart.text` | `尺码表` | 提取并格式化尺码信息 |
| `imageUrls[0]` | `主图URL` | 第一张图片作为主图 |

## 标题生成规则

### 季节判断
- **优先级1**: 从表格数据中的`シーズン`字段提取
- **优先级2**: 从商品标题中的代码识别（如`25FW`→`25秋冬`）
- **优先级3**: 根据当前日期智能判断

### 品牌映射
```javascript
 BRAND_SHORT_NAME = {
    'callawaygolf': '卡拉威',
    'titleist': '泰特利斯',
    'puma': '彪马',
    'adidas': '阿迪达斯',
    'nike': '耐克',
    'lecoqgolf': '乐卡克'
 }
```

### 标题格式
```
[季节][品牌]高尔夫[性别][功能词][结尾词]
```

**示例**:
- `25秋冬卡拉威高尔夫男士保暖舒适夹克`
- `26春夏阿迪达斯高尔夫女士弹力全拉链上衣`

## 颜色翻译映射

### 常用颜色
```javascript
const COLOR_MAPPING = {
    'ホワイト': '白色',
    'エメラルド': '翡翠绿',
    'ネイビー': '藏青色',
    'ブラック': '黑色',
    'グレー': '灰色',
    'NAVY': '藏青色',
    'BLACK': '黑色',
    'GREY': '灰色'
};
```

### 处理规则
1. 提取颜色名称（去掉括号内的代码）
2. 映射为中文颜色名
3. 逗号连接多个颜色

## 文件路径一致性

### 单品处理流程
```bash
# 1. 抓取单个商品
node single_unified_processor.js "URL" --output "/path/to/output.json"

# 2. 同步到飞书
python3 -m tongyong_feishu_update.run_pipeline "/path/to/output.json" --verbose
```

### 批量处理流程
```bash
# 1. 批量抓取（自动生成输出路径）
node batch_unified_processor.js --input "products.json"

# 2. 使用实际生成的文件路径
python3 -m tongyong_feishu_update.run_pipeline "实际生成的文件路径" --verbose
```

### 关键改进
- **batch_unified_processor.js**: `processAllProducts()` 现在返回实际文件路径
- **single_unified_processor.js**: `processSingleUrl()` 返回实际文件路径
- **run_pipeline.py**: 使用 argparse 完整参数解析
- **统一路径处理**: CLI命令指向实际存在的文件

## CLI 参数规范

### 单品处理器
```bash
node single_unified_processor.js <url> [productId] [选项]

选项:
  -o, --output <path>   输出文件路径
  -h, --help            显示帮助信息
```

### 批量处理器
```bash
node batch_unified_processor.js [选项]

选项:
  --input <path>        输入文件路径
  --output <path>       输出文件路径
  --headless           使用无头模式（默认）
  --debug              开启调试模式
  --timeout <ms>       设置超时时间
```

### Python 流水线
```bash
python3 -m tongyong_feishu_update.run_pipeline <input_path> [选项]

选项:
  --streaming          启用流式处理模式
  --force-update       强制更新所有字段
  --title-only         仅更新标题字段
  --dry-run            干运行模式
  --verbose, -v        显示详细进度信息
  --quiet, -q          静默模式
  --no-resume          禁用断点续传
  --timeout <SECONDS>  单个产品处理超时时间
  --save-interval <COUNT> 进度保存间隔
```

## 错误处理和重试机制

### JavaScript 抓取器
- **状态管理**: `batch_unified_status.json` 跟踪处理状态
- **断点续传**: 支持从失败位置继续处理
- **错误分类**: 区分网络错误、解析错误和处理错误

### Python 处理器
- **API重试**: GLM API 调用自动重试机制
- **标题验证**: 多层质量检查确保标题合规
- **渐进式处理**: 流式处理支持大批量数据

## 环境配置

### 必需的环境变量
```bash
# GLM API配置
export ZHIPU_API_KEY="your_api_key_here"

# 飞书配置
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_TABLE_ID="your_table_id"
```

### 依赖管理
- **JavaScript**: 使用内置模块，无外部依赖
- **Python**: 使用 requirements.txt 管理依赖
- **抓取器**: Playwright/Puppeteer 用于网页抓取

## 最佳实践

### 1. 数据一致性
- 所有脚本使用相同的字段定义
- 保持原始数据在`_original_data`字段中
- 统一的错误日志格式

### 2. 性能优化
- 批量处理优先使用流式模式
- 适当的请求间隔避免被封禁
- 并发控制防止资源耗尽

### 3. 质量保证
- 标题生成多层验证
- 图片数量限制（最多6张）
- 颜色和尺码标准化处理

### 4. 监控和调试
- 详细的进度日志
- 处理状态持久化
- 错误分类和报告

## 更新记录

### v2.1 (2025-11-16)
- 🔧 修复批量处理异常返回问题
  - processAllProducts() 异常时正确抛出错误而不是返回 undefined
  - 主函数区分"异常退出"和"无新文件生成"情况
  - 增强错误处理和用户反馈

### v2.0 (2025-11-16)
- ✅ 修复 batch_unified_processor.js 返回值问题
- ✅ 创建 prompts.py 模板化提示词
- ✅ 改进 CLI 参数解析一致性
- ✅ 增强文件路径处理可靠性
- ✅ 添加 run_pipeline.py argparse 支持

### v1.0 (初始版本)
- 基础抓取和处理功能
- 简单的字段映射
- 基本的错误处理

## 联系和支持

如有问题或建议，请查看项目文档或提交 Issue。