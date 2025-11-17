# Le Coq Sportif Golf 配置

## 基本信息
- **品牌ID**: lecoqgolf
- **品牌全名**: Le Coq Sportif Golf
- **官网**: https://store.descente.co.jp
- **地区**: 日本
- **语言**: 日语
- **调度日**: 每月6号

## 网站特点

### 技术栈
- **前端**: jQuery + Handlebars
- **网站类型**: 日本电商平台
- **反爬虫**: JavaScript检测 + CAPTCHA

### 产品展示
- **产品容器**: `.catalogList_item`
- **产品标题**: `.commodityName`
- **品牌信息**: `.brandName`
- **价格**: `.price`
- **图片**: `.catalogList_image img`
- **徽章**: `.badgeSale`, `.badgeNew`

### URL结构
- **男士系列**: `/brand/le%20coq%20sportif%20golf/ds_M`
- **女士系列**: `/brand/le%20coq%20sportif%20golf/ds_F`
- **分页**: `currentPage=N`

## 配置文件
- `config.json` - 主配置文件
- `selectors.json` - CSS选择器配置
- `scrape_category.js` - 专用抓取器

## 使用方法

### 完整的三阶段流程（推荐）

#### Stage 1: 抓取商品列表（scrape_category.js）
```bash
node scrape_category.js
```
- 输出文件：`golf_content/lecoqgolf/lecoqgolf_products_[时间戳].json`
- 包含：productId、url、brand 等基础信息
- 支持男士和女士系列分类抓取

#### Stage 1.5: 导入基础记录到飞书
```bash
cd /Users/sanshui/Desktop/CallawayJP
python3 -m tongyong_feishu_update.tools.import_basic_products \
  --source "scripts/multi_brand/brands/lecoqgolf/golf_content/lecoqgolf/lecoqgolf_products_xxx.json"
```
- 从 scrape_category.js 输出中提取 productId + url + brand
- 批量创建飞书基础记录（只填充品牌、商品ID、商品链接）
- 为后续详情补充做好准备

#### Stage 2: 顺序同步处理（sequential_sync.js）
```bash
node sequential_sync.js \
  --source "golf_content/lecoqgolf/lecoqgolf_products_xxx.json" \
  --limit 10
```
- 自动查询飞书中待处理的产品（通过 Python 工具）
- 逐个处理：抓取详情 → 立即同步到飞书
- 支持断点续传（自动保存进度到 `sequential_sync_status.json`）
- 支持限制处理数量（`--limit N`）
- 流程：
  1. 读取源文件，构建 productId → {url, name} 映射
  2. 调用 Python 工具获取待处理的 product_id 列表
  3. 对每个产品：
     - 运行 `single_unified_processor.js` 抓取详情
     - 调用 `python3 -m tongyong_feishu_update.run_pipeline` 同步飞书
     - 清理临时文件
  4. 自动保存进度

#### 测试单个产品
```bash
# 测试抓取单个产品
node sequential_sync.js \
  --source "golf_content/lecoqgolf/lecoqgolf_products_xxx.json" \
  --limit 1
```

#### 旧方法：通过主CLI运行
```bash
# 在 multi_brand 目录下
node core/cli.js run --brand lecoqgolf
```

### 更新配置
编辑 `config.json` 文件后重新运行

## 调试说明

如果遇到抓取问题，请检查：

1. **反爬虫机制**
   - 网站使用JavaScript检测
   - 可能触发CAPTCHA
   - 需要模拟真实用户行为

2. **网络问题**
   - 日本网站可能需要日本IP
   - 建议使用日本代理或VPN
   - 增加请求间隔时间

3. **选择器更新**
   - 定期检查CSS选择器是否变化
   - 关注页面结构更新
   - 验证数据提取逻辑

4. **分页处理**
   - 检查分页按钮状态
   - 验证最大页面数限制
   - 处理空页面情况

## 特殊处理

### 反检测措施
- 随机延迟
- 用户代理轮换
- 模拟鼠标移动
- 隐藏自动化特征

### 数据清理
- 去重处理
- 数据验证
- 空值过滤
- 格式标准化

## 数据输出

抓取结果将保存到：
- 路径: `golf_content/lecoqgolf/`
- 文件格式: JSON
- 包含字段:
  - `title`: 产品标题
  - `brand`: 品牌
  - `price`: 价格
  - `originalPrice`: 原价
  - `image`: 产品图片
  - `url`: 产品链接
  - `category`: 性别分类
  - `badges`: 徽章信息

## 注意事项

- 请遵守网站的robots.txt和使用条款
- 建议设置合理的请求间隔，避免给网站造成压力
- 定期检查和更新CSS选择器
- 监控抓取成功率，及时调整策略
- 考虑使用日本IP地址以提高成功率

## 常见问题

### Q: 为什么抓取失败率高？
A: 日本电商网站反爬虫较严格，建议：
- 增加请求间隔
- 使用日本代理
- 模拟真实用户行为

### Q: 如何处理JavaScript弹窗？
A: 抓取器已包含反检测机制，会自动处理
如仍有问题，可增加延迟时间

### Q: 数据不完整怎么办？
A: 检查选择器配置，更新CSS选择器
有些产品信息可能需要单独请求详情页