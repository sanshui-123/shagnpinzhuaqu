# Odyssey Golf 配置

## 基本信息
- **品牌ID**: odyssey
- **官网**: https://www.odysseygolf.com
- **调度日**: 每月5号

## 配置文件
- `config.json` - 主配置文件
- `selectors.json` - CSS选择器配置
- `scrape_category.js` - 专用抓取器

## 使用方法

### 1. 测试抓取器
```bash
node scrape_category.js
```

### 2. 单独测试分类页面
```bash
node scrape_category.js --category drivers
```

### 3. 更新配置
编辑 `config.json` 文件后重新运行

## 调试说明

如果遇到抓取问题，请检查：
1. 网站是否有反爬虫保护
2. CSS选择器是否需要更新
3. 是否需要调整等待时间
4. 网站是否需要特殊的User-Agent

## 数据输出

抓取结果将保存到：
- 路径: `golf_content/odyssey/`
- 文件格式: JSON
- 包含字段: 标题、价格、图片、分类、URL等

## 注意事项

- 请遵守网站的robots.txt和使用条款
- 建议设置合理的请求间隔，避免给网站造成压力
- 定期检查和更新CSS选择器
