# 库存巡检系统使用文档

本文档说明如何为不同品牌进行库存巡检。

## 支持的品牌

### 1. Le Coq Golf (公鸡乐卡克)
### 2. PEARLY GATES (PG)

---

## Le Coq Golf 库存巡检

### 步骤1：导出品牌商品列表

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "Le Coq公鸡乐卡克" \
  --output "/tmp/lecoq_products.json"
```

### 步骤2：运行库存巡检脚本

```bash
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf
node check_inventory.js \
  --input "/tmp/lecoq_products.json" \
  --output "/tmp/lecoq_inventory.json"
```

**可选参数：**
```bash
# 自定义并发数和延迟
node check_inventory.js \
  --input "/tmp/lecoq_products.json" \
  --output "/tmp/lecoq_inventory.json" \
  --concurrent 3 \
  --delay 500

# 限制检查数量（测试用）
node check_inventory.js \
  --input "/tmp/lecoq_products.json" \
  --output "/tmp/lecoq_inventory_test.json" \
  --limit 10
```

### 步骤3：同步库存结果到飞书

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/lecoq_inventory.json"
```

---

## PEARLY GATES (PG) 库存巡检

### 步骤1：导出品牌商品列表

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "PEARLY GATES" \
  --output "/tmp/pg_products.json"
```

### 步骤2：运行库存巡检脚本

```bash
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/pg
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json"
```

**可选参数：**
```bash
# 自定义并发数和延迟
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  --concurrent 3 \
  --delay 500

# 限制检查数量（测试用）
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory_test.json" \
  --limit 10
```

### 步骤3：同步库存结果到飞书

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/pg_inventory.json"
```

---

## 通用说明

### CLI 参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --input | -i | 输入文件路径（必需） | - |
| --output | -o | 输出文件路径（必需） | - |
| --limit | -l | 限制检查数量 | 0（全部） |
| --concurrent | -c | 并发数 | 3 |
| --delay | -d | 请求间隔（毫秒） | 500 |
| --brand | -b | 品牌标识 | 品牌默认值 |
| --help | -h | 显示帮助 | - |

### 性能调优

**推荐配置（已优化）：**
- 并发数：3
- 延迟：500ms
- 性能：约11分钟处理30个商品

**保守配置（稳定优先）：**
- 并发数：2
- 延迟：1000ms
- 性能：约14分钟处理30个商品

**激进配置（高速但可能不稳定）：**
- 并发数：5
- 延迟：300ms
- 风险：可能导致浏览器崩溃或网站限流

### 输出格式

库存巡检输出JSON格式：
```json
{
  "brand": "Le Coq Golf",
  "timestamp": "2025-11-20T07:00:00.000Z",
  "summary": {
    "total": 382,
    "success": 380,
    "failed": 2,
    "skipped": 5,
    "inStock": 100,
    "partialStock": 250,
    "outOfStock": 30
  },
  "products": [
    {
      "productId": "LG5FST81M",
      "detailUrl": "https://...",
      "variantInventory": [
        {
          "color": "ネイビー",
          "size": "M",
          "inStock": true
        }
      ],
      "stockStatus": "partial_stock",
      "colors": ["ネイビー", "グレー"],
      "sizes": ["S", "M", "L"],
      "timestamp": "2025-11-20T07:01:00.000Z"
    }
  ],
  "errors": [],
  "skipped": []
}
```

### 库存状态说明

- `in_stock`: 全部有货
- `partial_stock`: 部分缺货
- `out_of_stock`: 全部缺货
- `unknown`: 无法确定

### 监控和日志

**实时监控：**
```bash
# 监控巡检进度
tail -f /tmp/lecoq_inventory_check.log

# 检查进程状态
ps aux | grep check_inventory.js
```

**查看结果摘要：**
```bash
# 查看摘要信息
cat /tmp/lecoq_inventory.json | jq '.summary'

# 查看成功数量
cat /tmp/lecoq_inventory.json | jq '.summary.success'
```

---

## 添加新品牌

### 步骤1：复制脚本骨架

```bash
# 复制Le Coq的check_inventory.js到新品牌目录
cp scripts/multi_brand/brands/lecoqgolf/check_inventory.js \
   scripts/multi_brand/brands/<new_brand>/check_inventory.js
```

### 步骤2：修改品牌配置

在新品牌的`check_inventory.js`中修改`BRAND_CONFIG`：

```javascript
const BRAND_CONFIG = {
    newbrand: {
        name: '品牌中文名',
        baseUrl: 'https://品牌网站.com',
        colorSelector: '.color-selector-class',  // 需要根据实际DOM调整
        sizeListSelector: '.size-list-class'     // 需要根据实际DOM调整
    }
};
```

### 步骤3：修改默认brand值

```javascript
// 修改构造函数中的默认brand
this.brand = options.brand || 'newbrand';

// 修改CLI选项中的默认brand
options = {
    ...
    brand: 'newbrand'
};
```

### 步骤4：更新帮助文本

```javascript
console.log(`
库存巡检脚本 - 品牌中文名

使用方式:
  ...
`);
```

### 步骤5：测试

```bash
# 小批量测试
node check_inventory.js \
  --input test_products.json \
  --output test_inventory.json \
  --limit 5
```

### 步骤6：更新本文档

在本文档中添加新品牌的完整使用说明。

---

## 故障排除

### 问题1：进程崩溃或卡死

**症状**：脚本运行一段时间后突然停止，没有输出

**解决方案**：
```bash
# 降低并发数
node check_inventory.js --input ... --output ... --concurrent 1

# 增加延迟
node check_inventory.js --input ... --output ... --delay 2000

# 检查浏览器进程
ps aux | grep chromium
```

### 问题2：飞书同步失败

**症状**：库存巡检成功，但同步到飞书时失败

**解决方案**：
```bash
# 确保环境变量已加载
set -a && source callaway.env && set +a

# 检查飞书API凭证
echo $FEISHU_APP_ID
echo $FEISHU_APP_SECRET

# 手动验证飞书连接
python3 -m tongyong_feishu_update.clients.feishu_client
```

### 问题3：内存不足

**症状**：系统变慢，进程被杀死

**解决方案**：
```bash
# 分批处理
node check_inventory.js --input ... --output batch1.json --limit 100

# 监控内存使用
top -pid $(pgrep -f check_inventory.js)
```

### 问题4：网络超时

**症状**：频繁出现timeout错误

**解决方案**：
```bash
# 增加延迟，降低请求频率
node check_inventory.js --input ... --output ... --delay 3000

# 检查网络连接
ping store.descente.co.jp
```

---

## 最佳实践

1. **首次运行**：先用`--limit 10`测试，确认脚本正常工作
2. **生产环境**：使用推荐配置（并发3，延迟500ms）
3. **后台运行**：使用`nohup`或`screen`避免SSH断开
4. **定期监控**：每隔10分钟检查进度
5. **保存日志**：重定向输出到日志文件
6. **错误处理**：遇到错误时先查看错误日志，再考虑重新运行

---

## 版本历史

- 2025-11-20: 添加PEARLY GATES品牌支持
- 2025-11-19: 优化Le Coq性能配置（并发3，延迟500ms）
- 2025-11-18: 初始版本，支持Le Coq Golf
