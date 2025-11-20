# 库存巡检系统使用说明

## 概述

库存巡检系统用于定期检查商品库存状态并更新飞书。该系统复用现有的抓取逻辑（`unified_detail_scraper.js`），只更新库存相关字段（颜色/尺码/库存状态），不影响其他字段。

## 文件说明

| 文件 | 说明 |
|------|------|
| `check_inventory.js` | 库存巡检脚本，抓取商品库存 |
| `export_brand_products.py` | 从飞书导出指定品牌商品列表 |
| `run_inventory_sync.py` | 将库存数据同步到飞书 |

## 使用流程

### 完整流程（三步）

```bash
# 1. 从飞书导出 Le Coq 品牌商品列表
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
    --brand "Le Coq公鸡乐卡克" \
    --output "/tmp/lecoq_products.json" \
    --limit 50

# 2. 运行库存巡检
cd scripts/multi_brand/brands/lecoqgolf
node check_inventory.js \
    --input "/tmp/lecoq_products.json" \
    --output "/tmp/lecoq_inventory.json" \
    --limit 50

# 3. 同步库存到飞书
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
    "/tmp/lecoq_inventory.json" \
    --brand "Le Coq公鸡乐卡克"
```

## 各脚本详细说明

### 1. 导出商品列表

```bash
python3 -m tongyong_feishu_update.tools.export_brand_products [options]
```

**参数：**
- `--brand, -b`: 品牌名称（必需）
- `--output, -o`: 输出文件路径
- `--limit, -l`: 限制导出数量（默认: 全部）
- `--stdout`: 输出到标准输出

**输出格式：**
```json
{
  "brand": "Le Coq公鸡乐卡克",
  "timestamp": "2025-11-20T10:00:00",
  "total": 50,
  "products": [
    {
      "productId": "LG4FLP52M",
      "url": "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM009100/",
      "recordId": "rec_xxx"
    }
  ]
}
```

### 2. 库存巡检

```bash
node check_inventory.js [options]
```

**参数：**
- `--input, -i`: 输入文件路径（必需）
- `--output, -o`: 输出文件路径（必需）
- `--limit, -l`: 限制检查数量（默认: 全部）
- `--delay, -d`: 请求间隔毫秒（默认: 2000）
- `--brand, -b`: 品牌（默认: lecoqgolf）
- `--help, -h`: 显示帮助

**输出格式：**
```json
{
  "brand": "Le Coq Golf",
  "timestamp": "2025-11-20T10:05:00",
  "summary": {
    "total": 50,
    "success": 48,
    "failed": 2,
    "inStock": 10,
    "partialStock": 30,
    "outOfStock": 8
  },
  "products": [
    {
      "productId": "LG4FLP52M",
      "detailUrl": "https://...",
      "variantInventory": [
        {"color": "ベージュ", "size": "76", "inStock": true, "status": "little"},
        {"color": "グレー", "size": "76", "inStock": true, "status": "little"},
        {"color": "グレー", "size": "79", "inStock": false, "status": "oos"}
      ],
      "stockStatus": "partial_stock",
      "colors": ["ベージュ", "グレー", "ネイビー"],
      "sizes": ["76", "79", "82", "85", "88", "92", "96"]
    }
  ],
  "errors": []
}
```

### 3. 库存同步

```bash
python3 -m tongyong_feishu_update.run_inventory_sync <input_file> [options]
```

**参数：**
- `input_file`: 库存数据文件路径（必需）
- `--brand, -b`: 品牌名称（用于日志）
- `--dry-run`: 预览模式，不实际更新

**更新字段：**
- `颜色`: 只保留有货的颜色（翻译为中文）
- `尺码`: 只保留有货的尺码
- `库存状态`: 显示缺货信息
  - 全部缺货: `都缺货`
  - 部分缺货: `灰色(79/82/85) 没货`
  - 全部有货: `不缺货`

## 定时任务设置

### 使用 cron（每日巡检）

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨 3 点执行
0 3 * * * /path/to/inventory_check.sh >> /var/log/inventory_check.log 2>&1
```

### 示例脚本 inventory_check.sh

```bash
#!/bin/bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a

echo "$(date) - 开始 Le Coq 库存巡检"

# 导出商品列表
python3 -m tongyong_feishu_update.tools.export_brand_products \
    --brand "Le Coq公鸡乐卡克" \
    --output "/tmp/lecoq_products.json"

# 巡检库存
cd scripts/multi_brand/brands/lecoqgolf
node check_inventory.js \
    --input "/tmp/lecoq_products.json" \
    --output "/tmp/lecoq_inventory.json"

# 同步到飞书
cd /Users/sanshui/Desktop/CallawayJP
python3 -m tongyong_feishu_update.run_inventory_sync \
    "/tmp/lecoq_inventory.json"

echo "$(date) - 巡检完成"
```

## 扩展到其他品牌

### 1. 修改品牌配置

在 `check_inventory.js` 中添加品牌配置：

```javascript
const BRAND_CONFIG = {
    lecoqgolf: {
        name: 'Le Coq Golf',
        baseUrl: 'https://store.descente.co.jp',
        colorSelector: '#color-selector li, .color-selector li',
        sizeListSelector: '.shopping_cantrol.commoditySizelist, .commoditySizelist'
    },
    pg: {
        name: 'Pearly Gates',
        baseUrl: 'https://store.descente.co.jp',
        colorSelector: '...',  // PG 的选择器
        sizeListSelector: '...'
    },
    munsingwear: {
        name: 'Munsingwear',
        baseUrl: 'https://store.descente.co.jp',
        colorSelector: '...',
        sizeListSelector: '...'
    }
};
```

### 2. 复制并修改脚本

```bash
# 复制到新品牌目录
cp scripts/multi_brand/brands/lecoqgolf/check_inventory.js \
   scripts/multi_brand/brands/pg/check_inventory.js

# 修改默认品牌
# options.brand = 'pg'
```

## 注意事项

1. **请求间隔**: 默认 2 秒，避免请求过快被封
2. **并发控制**: 目前为串行处理，确保稳定性
3. **错误处理**: 单个商品失败不影响整体流程
4. **数据备份**: 建议在同步前备份飞书数据

## 常见问题

### Q: 巡检失败怎么办？

检查：
1. 网络连接是否正常
2. 商品 URL 是否有效
3. 页面结构是否变化

### Q: 如何只检查特定商品？

创建一个包含商品列表的 JSON 文件：
```json
{
  "products": [
    {"productId": "LG4FLP52M", "url": "https://..."}
  ]
}
```

### Q: 同步会覆盖其他字段吗？

不会。`run_inventory_sync.py` 只更新 颜色/尺码/库存状态 三个字段。
