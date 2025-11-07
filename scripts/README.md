# CallawayJP 产品详情抓取脚本

## 概述

这是一个精简版的CallawayJP产品详情抓取脚本，使用Playwright进行页面抓取，支持多种数据提取方法。

## 功能特性

- ✅ 支持 `--url`、`--product-id`、`--output-dir` 参数
- ✅ 使用 Playwright headless 模式
- ✅ 等待页面 networkidle/domcontentloaded
- ✅ 三层数据提取策略：
  1. `window.__NEXT_DATA__?.props?.pageProps?.productDetail`
  2. 遍历 `self.__next_f` 的JSON数据  
  3. DOM选择器回退策略
- ✅ 提取产品基础信息（name、description、brand）
- ✅ 处理图片、颜色、尺码、变体等数据
- ✅ 输出JSON格式对齐 `feishu_update/baseline/inputs/sample_product_details.json`
- ✅ 完整的错误处理和日志记录

## 安装依赖

```bash
npm install playwright
```

## 使用方法

### 基本用法

```bash
node scrape_product_detail.js --url "https://www.callawaygolf.jp/womens/tops/outer/C25215200_.html?pid=C25215200_1031_S"
```

### 完整参数

```bash
node scrape_product_detail.js \
  --url "https://www.callawaygolf.jp/womens/tops/outer/C25215200_.html?pid=C25215200_1031_S" \
  --product-id "C25215200" \
  --output-dir "CallawayJP/results"
```

### 查看帮助

```bash
node scrape_product_detail.js --help
```

## 输出格式

脚本输出标准的JSON格式，包含以下结构：

```json
{
  "scrapeInfo": {
    "timestamp": "2025-11-05T15:00:26.896Z",
    "version": "1.0.0", 
    "url": "...",
    "productId": "...",
    "totalVariants": 0,
    "totalColors": 0,
    "totalSizes": 0,
    "totalImages": 0,
    "processingTimeMs": 8167,
    "dataSources": ["dom_enhanced"]
  },
  "product": {
    "productId": "C25215200",
    "title": "2WAYハーフジップフーディーブルゾン (WOMENS)",
    "productUrl": "...", 
    "description": "...",
    "brand": "Callaway Golf",
    "detailUrl": "...",
    "mainImage": "...",
    "sizeChart": { "headers": [...], "rows": [...] }
  },
  "variants": [...],
  "colors": [...], 
  "sizes": [...],
  "sizeChart": { ... },
  "images": {
    "product": [...],
    "variants": { "1031": [...], ... }
  },
  "ossLinks": { "productImages": [], "variantImages": {} }
}
```

## 数据提取策略

### 1. Next.js 数据优先
- 检查 `window.__NEXT_DATA__.props.pageProps.productDetail`
- 这是最可靠的数据源

### 2. Next.js SSR 数据  
- 遍历 `window.self.__next_f` 数组
- 查找包含 `productDetail` 的JSON字符串

### 3. DOM选择器回退
- 使用多种选择器提取基础信息
- 包括标题、描述、颜色、尺码、图片

## 环境变量

脚本支持从 `.env` 文件读取GLM API配置（虽然当前版本未使用AI处理）：

```bash
ZHIPU_API_KEY=your_api_key
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions  
ZHIPU_MODEL=glm-4.6
```

## 错误处理

- 超时：60秒页面加载超时
- 网络错误：自动记录错误信息
- 数据提取失败：保存错误日志到输出目录

## 性能数据

- 页面加载：约3-8秒
- 数据提取：几乎实时
- 总处理时间：通常在10秒以内

## 文件输出

### 成功输出
```
CallawayJP/results/product_detail_C25215200_2025-11-05T15-00-26-896Z.json
```

### 错误输出
```  
CallawayJP/results/error_C25215200_2025-11-05T15-00-26-896Z.json
```

## 注意事项

1. **Playwright依赖**：需要安装chromium浏览器
2. **网络连接**：需要能访问CallawyGolf JP网站
3. **动态内容**：某些产品页面可能使用JavaScript动态加载
4. **反爬虫**：网站可能有反爬虫保护，建议适当延时

## 扩展建议

如需要更高级的功能，可以考虑：

1. 添加代理支持
2. 集成GLM API进行内容智能处理  
3. 支持批量处理多个URL
4. 添加图片下载功能
5. 实现缓存机制避免重复抓取