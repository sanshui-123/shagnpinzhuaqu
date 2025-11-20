# Callaway (卡拉威) 配置

## 基本信息
- **品牌ID**: callaway
- **品牌全名**: Callaway
- **品牌中文名**: 卡拉威
- **官网**: https://www.callawaygolf.jp
- **地区**: 日本
- **语言**: 日语
- **调度日**: 每月8号

## 当前状态
✅ 基础架构已迁移（从 lecoqgolf）
✅ 配置文件已更新
⏳ 13个字段抓取功能（使用旧版DOM逻辑）
⏳ 库存巡检功能（待提供DOM后补充）

## 网站特点

### 产品展示
- **产品容器**: `.c-productCard`, `[class*="product"]`
- **产品标题**: `.title`, `.name`, `h1`, `h2`, `h3`
- **产品链接**: `a[href*="?pid="]`
- **图片**: `img`
- **价格**: `[class*="price"]`

### URL结构
- **主页**: `/shop/men.html`
- **女士**: `/shop/women.html`
- **服装**: `/shop/apparel.html`

## 配置文件
- `config.json` - 主配置文件
- `scrape_category.js` - 列表抓取器（已迁移旧版DOM逻辑）
- `unified_detail_scraper.js` - 详情抓取器（已迁移旧版DOM逻辑）

## 使用方法

### 🚀 快速开始：一键运行（推荐）

```bash
# 进入 callaway 目录
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/callaway

# 运行完整流程（从抓取到同步）
./run_full_sync.sh

# 或者只处理部分产品（测试用）
./run_full_sync.sh --limit 10

# 或者跳过抓取，使用已有的最新文件
./run_full_sync.sh --skip-step1
```

**脚本自动完成：**
1. ✅ 抓取商品列表
2. ✅ 自动找到最新的 JSON 文件
3. ✅ 导入基础记录到飞书
4. ✅ 顺序抓详情并同步

**参数说明：**
- `--skip-step1`: 跳过抓取步骤，使用已有的最新文件
- `--limit N`: 限制 Step 2 只处理 N 个产品（测试用）
- `--help`: 显示帮助信息

---

### 📋 完整的三阶段流程（手动执行）

#### Stage 1: 抓取商品列表（scrape_category.js）
```bash
node scrape_category.js
```
- 输出文件：`golf_content/callaway/callaway_products_[时间戳].json`
- 包含：productId、url、brand 等基础信息

#### Stage 1.5: 导入基础记录到飞书
```bash
cd /Users/sanshui/Desktop/CallawayJP
python3 -m tongyong_feishu_update.tools.import_basic_products \
  --source "scripts/multi_brand/brands/callaway/golf_content/callaway/callaway_products_xxx.json" \
  --brand "卡拉威"
```
- 从 scrape_category.js 输出中提取 productId + url + brand
- 批量创建飞书基础记录（只填充品牌、商品ID、商品链接）

#### Stage 2: 顺序同步处理（sequential_sync.js）
```bash
node sequential_sync.js \
  --source "golf_content/callaway/callaway_products_xxx.json" \
  --limit 10
```
- 自动查询飞书中待处理的产品
- 逐个处理：抓取详情 → 立即同步到飞书
- 支持断点续传（自动保存进度到 `sequential_sync_status.json`）

#### 测试单个产品
```bash
node sequential_sync.js \
  --source "golf_content/callaway/callaway_products_xxx.json" \
  --limit 1
```

## 数据输出

抓取结果将保存到：
- 路径: `golf_content/callaway/`
- 文件格式: JSON
- 包含字段（13个基础字段）:
  - `productId`: 商品ID
  - `productName`: 商品名称
  - `brand`: 品牌
  - `price`: 价格
  - `originalPrice`: 原价
  - `image`: 主图片
  - `url`: 商品链接
  - `category`: 分类
  - `colors`: 颜色列表
  - `sizes`: 尺码列表
  - `gender`: 性别
  - `description`: 商品描述
  - `details`: 商品详情

## 库存巡检功能

⏳ **待补充** - 等提供 Callaway 库存 DOM 信息后实现：
- `check_inventory.js` - 库存检查脚本（待实现）
- `run_inventory_sync` - 库存同步功能（待实现）

## 注意事项

- 请遵守网站的robots.txt和使用条款
- 建议设置合理的请求间隔，避免给网站造成压力
- 定期检查和更新CSS选择器
- 监控抓取成功率，及时调整策略

## 常见问题

### Q: 为什么重新运行脚本后空字段仍未填充？
A: 这是因为断点续传机制。脚本会跳过已处理过的 product_id。
如果想重新填充空字段，请删除 `sequential_sync_status.json` 文件：
```bash
rm sequential_sync_status.json
./run_full_sync.sh
```

### Q: 如何只测试单个产品？
A: 使用 `--limit 1` 参数：
```bash
./run_full_sync.sh --limit 1
```
