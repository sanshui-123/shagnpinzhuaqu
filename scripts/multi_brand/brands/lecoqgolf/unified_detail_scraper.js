#!/usr/bin/env node

/**
 * 统一详情页抓取器 - Le Coq Sportif Golf
 * 集成了所有高级功能，支持单个URL和批量处理
 * 包含高级尺码表抓取功能
 */

const { chromium } = require('playwright');
const fs = require('fs');

class UnifiedDetailScraper {
    constructor(options = {}) {
        this.brandName = 'Le Coq公鸡乐卡克';
        this.options = {
            headless: options.headless !== false, // 默认后台运行，可设置为false显示浏览器
            timeout: options.timeout || 45000,
            debug: options.debug || false,
            ...options
        };
        this.results = {};
    }

    /**
     * 主要的详情页抓取方法
     * @param {string} url - 商品详情页URL
     * @param {Object} extraData - 额外数据（如商品ID等）
     * @returns {Object} 抓取结果
     */
    async scrapeDetailPage(url, extraData = {}) {
        console.log('🎯 开始统一详情页抓取:', url);
        if (this.options.debug) {
            console.log('🐛 调试模式已开启');
        }

        const browser = await chromium.launch({
            headless: this.options.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        });

        try {
            const page = await browser.newPage();
            await page.setDefaultTimeout(this.options.timeout);

            // 访问页面
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: this.options.timeout
            });

            await page.waitForTimeout(3000);

            // 🎯 高级尺码表抓取 - 集成的核心功能
            console.log('🔍 开始高级尺码表抓取...');
            const sizeChartData = await this.extractAdvancedSizeChart(page);

            if (sizeChartData.success) {
                console.log('✅ 尺码表抓取成功:', sizeChartData.method);
            } else {
                console.log('⚠️ 尺码表抓取失败:', sizeChartData.reason);
            }

            // 📊 抓取基本商品信息
            console.log('📊 抓取基本商品信息...');
            const basicInfo = await this.extractBasicProductInfo(page, url, extraData);

            // 🖼️ 抓取图片
            console.log('🖼️ 抓取商品图片...');
            const images = await this.extractProductImages(page);

            // 🔴 抓取颜色和尺码信息
            console.log('🎨 抓取颜色和尺码...');
            const colorsAndSizes = await this.extractColorsAndSizes(page);

            // 📦 抓取库存状态信息
            console.log('📦 抓取库存状态...');
            const inventoryData = await this.extractVariantInventory(page);

            // 判断是否全部缺货
            let stockStatus = 'in_stock';
            let productNameFinal = basicInfo.productName;

            if (inventoryData.variantInventory && inventoryData.variantInventory.length > 0) {
                const hasAnyStock = inventoryData.variantInventory.some(v => v.inStock);
                if (!hasAnyStock) {
                    stockStatus = 'out_of_stock';
                    // 添加缺货前缀
                    if (productNameFinal && !productNameFinal.startsWith('【缺货】')) {
                        productNameFinal = '【缺货】' + productNameFinal;
                    }
                    console.log('⚠️ 该商品所有变体都已缺货');
                }
            }

            // 组装最终结果
            const result = {
                success: true,
                url: url,
                timestamp: new Date().toISOString(),
                ...basicInfo,
                productName: productNameFinal,
                ...colorsAndSizes,
                imageUrls: images,
                sizeChart: sizeChartData,
                variantInventory: inventoryData.variantInventory || [],
                stockStatus: stockStatus,
                _scraper_info: {
                    version: 'unified_v1.1',
                    debug_mode: this.options.debug,
                    size_chart_method: sizeChartData.method,
                    inventory_extracted: inventoryData.variantInventory ? inventoryData.variantInventory.length : 0,
                    processing_time: new Date().toISOString()
                }
            };

            console.log('✅ 详情页抓取完成');
            return result;

        } catch (error) {
            console.log('❌ 抓取过程出错:', error.message);
            return {
                success: false,
                url: url,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        } finally {
            await browser.close();
        }
    }

    /**
     * 🎯 高级尺码表抓取 - 集成所有成功的方法
     */
    async extractAdvancedSizeChart(page) {
        try {
            console.log('🔍 方法1: 检查尺码表相关链接...');
            const sizeLinks = await page.evaluate(() => {
                const links = document.querySelectorAll('a[href], button[onclick], div[onclick]');
                const result = [];

                for (const link of links) {
                    const text = link.textContent.trim();
                    const href = link.getAttribute('href') || link.getAttribute('onclick') || '';

                    if (text.includes('サイズガイド') ||
                        text.includes('サイズ') ||
                        href.includes('size') ||
                        href.includes('guide') ||
                        href.includes('chart')) {
                        result.push({
                            text: text,
                            href: href,
                            element: link.tagName,
                            visible: link.offsetParent !== null
                        });
                    }
                }
                return result;
            });

            console.log(`找到 ${sizeLinks.length} 个尺码表相关元素`);

            // 🎯 尝试点击找到的尺码表元素
            for (let i = 0; i < sizeLinks.length; i++) {
                const link = sizeLinks[i];
                if (!link.visible) continue;

                console.log(`尝试点击元素 ${i + 1}: ${link.text}`);

                try {
                    const clickResult = await page.evaluate((targetText) => {
                        const allElements = document.querySelectorAll('*');
                        for (const element of allElements) {
                            if (element.textContent.trim() === targetText &&
                                element.offsetParent !== null) {
                                try {
                                    element.scrollIntoView({ block: 'center' });
                                    setTimeout(() => element.click(), 500);
                                    return true;
                                } catch (e) {
                                    console.log('点击失败:', e.message);
                                }
                            }
                        }
                        return false;
                    }, link.text);

                    if (clickResult) {
                        console.log('✅ 点击成功，等待内容加载...');
                        await page.waitForTimeout(6000);

                        // 检查页面变化并提取尺码表
                        const sizeData = await this.extractSizeChartFromPage(page);
                        if (sizeData.hasContent) {
                            return {
                                success: true,
                                method: `点击元素: ${link.text}`,
                                html: sizeData.html,
                                text: sizeData.text,
                                tables: sizeData.tables
                            };
                        }
                    }
                } catch (error) {
                    console.log(`点击元素失败: ${error.message}`);
                }
            }

            // 🔍 深度搜索所有可能的尺码表内容
            console.log('🔍 方法2: 深度搜索尺码表内容...');
            const deepSearchResult = await this.deepSearchSizeCharts(page);
            if (deepSearchResult.found) {
                return {
                    success: true,
                    method: '深度搜索',
                    html: deepSearchResult.html,
                    text: deepSearchResult.text,
                    tables: deepSearchResult.tables
                };
            }

            // 🔍 最终检查 - 等待更长时间后重新检查
            console.log('🔍 方法3: 延长等待后最终检查...');
            await page.waitForTimeout(10000);
            const finalResult = await this.extractSizeChartFromPage(page);
            if (finalResult.hasContent) {
                return {
                    success: true,
                    method: '延长等待后找到',
                    html: finalResult.html,
                    text: finalResult.text,
                    tables: finalResult.tables
                };
            }

            return {
                success: false,
                method: 'none',
                reason: '所有方法都未找到详细尺码表',
                found_links: sizeLinks.length
            };

        } catch (error) {
            return {
                success: false,
                method: 'error',
                reason: error.message
            };
        }
    }

    /**
     * 从页面中提取尺码表内容
     */
    async extractSizeChartFromPage(page) {
        return await page.evaluate(() => {
            const result = {
                hasContent: false,
                html: '',
                text: '',
                tables: []
            };

            // 查找所有表格
            const tables = document.querySelectorAll('table');
            for (const table of tables) {
                const tableText = table.textContent.trim();

                // 检查是否包含尺码表特征
                const hasSizeKeywords = (
                    tableText.includes('身長') ||
                    tableText.includes('胸囲') ||
                    tableText.includes('着丈') ||
                    tableText.includes('肩幅') ||
                    tableText.includes('袖丈') ||
                    tableText.includes('ウエスト') ||
                    tableText.includes('ヒップ') ||
                    tableText.includes('サイズ')
                );

                const hasSizeNumbers = (
                    /\d+\.?\d*cm/i.test(tableText) ||
                    /S|M|L|LL|3L/.test(tableText) ||
                    tableText.length > 300
                );

                if (hasSizeKeywords || hasSizeNumbers) {
                    result.hasContent = true;
                    result.html = table.outerHTML;
                    result.text = tableText;
                    result.tables.push({
                        html: table.outerHTML,
                        text: tableText,
                        hasKeywords: hasSizeKeywords,
                        hasNumbers: hasSizeNumbers,
                        length: tableText.length
                    });
                }
            }

            return result;
        });
    }

    /**
     * 深度搜索尺码表内容
     */
    async deepSearchSizeCharts(page) {
        return await page.evaluate(() => {
            const result = {
                found: false,
                html: '',
                text: '',
                tables: []
            };

            // 搜索所有表格
            const allTables = document.querySelectorAll('table');
            for (let i = 0; i < allTables.length; i++) {
                const table = allTables[i];
                const tableText = table.textContent.trim();

                if (tableText.includes('cm') && tableText.length > 200) {
                    result.found = true;
                    result.html = table.outerHTML;
                    result.text = tableText;
                    result.tables.push({
                        index: i,
                        html: table.outerHTML,
                        text: tableText,
                        length: tableText.length
                    });
                }
            }

            // 搜索可能包含尺码信息的特殊div
            const sizeElements = document.querySelectorAll('div[class*="size"], div[id*="size"], .size-guide, .size-chart');
            for (const element of sizeElements) {
                const text = element.textContent.trim();
                if (text.length > 100 && (text.includes('cm') || text.includes('サイズ'))) {
                    result.found = true;
                    result.tables.push({
                        type: 'div',
                        className: element.className,
                        text: text.substring(0, 500)
                    });
                }
            }

            return result;
        });
    }

    /**
     * 抓取基本商品信息 - 改进版本，避免通用标题
     */
    async extractBasicProductInfo(page, url, extraData) {
        return await page.evaluate((params) => {
            const { url, extraData, brandName } = params;
            const result = {
                productId: '',
                productName: '',
                price: '',
                gender: '',
                description: '',
                detailUrl: url,
                brand: brandName
            };

            // 🎯 改进的商品标题选择器 - 优先选择具体产品名
            const titleSelectors = [
                '.product-name .name',
                '.item-detail .name',
                '.product-title',
                'h1.product-name',
                '.commodity-name',
                '.product-detail h1',
                '.item-info h1',
                'h1:not(:empty)'
            ];

            // 过滤掉通用标题
            for (const selector of titleSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim()) {
                    const title = element.textContent.trim();
                    // 过滤掉通用或过于简短的标题
                    if (title &&
                        title.length > 5 &&
                        !title.includes('DESCENTE STORE') &&
                        !title.includes('DESCENTE') &&
                        !title.includes('ストア') &&
                        !title === 'TOP' &&
                        !title === 'HOME') {
                        result.productName = title;
                        break;
                    }
                }
            }

            // 如果没找到合适的标题，尝试从h1中提取具体产品名
            if (!result.productName) {
                const h1Elements = document.querySelectorAll('h1');
                for (const h1 of h1Elements) {
                    const text = h1.textContent.trim();
                    if (text &&
                        text.length > 5 &&
                        !text.includes('DESCENTE STORE') &&
                        !text.includes('DESCENTE')) {
                        result.productName = text;
                        break;
                    }
                }
            }

            // 价格
            const priceSelectors = [
                '.price',
                '[class*="price"]',
                '.amount',
                '[class*="amount"]'
            ];

            for (const selector of priceSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim()) {
                    result.price = element.textContent.trim();
                    break;
                }
            }

            // 描述
            const descSelectors = [
                '.description',
                '[class*="description"]',
                '.detail',
                '[class*="detail"]'
            ];

            for (const selector of descSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim().length > 50) {
                    result.description = element.textContent.trim();
                    break;
                }
            }

            // 🎯 改进的商品ID提取 - 优先使用品牌货号而非商品番号
            // 查找表格中的商品番号和品牌货号
            const productCodeElements = document.querySelectorAll('table tr');
            let productItemCode = '';
            let productNumber = '';

            for (const tr of productCodeElements) {
                const th = tr.querySelector('th');
                const td = tr.querySelector('td');
                if (th && td) {
                    const thText = th.textContent.trim();
                    const tdText = td.textContent.trim();

                    if (thText.includes('商品番号')) {
                        productNumber = tdText;
                    } else if (thText.includes('ブランド商品番号') || thText.includes('品牌商品番号')) {
                        productItemCode = tdText;
                    }
                }
            }

            // 优先使用品牌货号，其次使用商品番号
            if (productItemCode && productItemCode.length > 0) {
                result.productId = productItemCode;
            } else if (productNumber && productNumber.length > 0) {
                result.productId = productNumber;
            } else if (extraData.productId) {
                result.productId = extraData.productId;
            }

            // 🎯 改进的性别判断 - 从页面的"性别类型"字段获取
            let genderFound = false;
            for (const tr of productCodeElements) {
                const th = tr.querySelector('th');
                const td = tr.querySelector('td');
                if (th && td) {
                    const thText = th.textContent.trim();
                    const tdText = td.textContent.trim();

                    if (thText.includes('性別タイプ') || thText.includes('性别类型')) {
                        if (tdText.includes('レディース') || tdText.includes('レディース') || tdText.includes('女')) {
                            result.gender = '女';
                            genderFound = true;
                            break;
                        } else if (tdText.includes('メンズ') || tdText.includes('男性') || tdText.includes('男')) {
                            result.gender = '男';
                            genderFound = true;
                            break;
                        }
                    }
                }
            }

            // 如果没有找到性别类型字段，回退到页面文本搜索
            if (!genderFound) {
                const pageText = document.body.textContent;
                if (pageText.includes('レディース') || pageText.includes('女性')) {
                    result.gender = '女';
                } else if (pageText.includes('メンズ') || pageText.includes('男性')) {
                    result.gender = '男';
                }
            }

            return result;
        }, { url, extraData, brandName: this.brandName });
    }

    /**
     * 抓取商品图片 - 改进版本，过滤品牌Logo和无关图片
     */
    async extractProductImages(page) {
        return await page.evaluate(() => {
            const images = [];
            const imgElements = document.querySelectorAll('img');

            for (const img of imgElements) {
                const src = img.getAttribute('src');
                const alt = img.getAttribute('alt') || '';
                const className = img.className || '';

                // 过滤掉明显的品牌Logo和无关图片
                if (src &&
                    !src.includes('logo') &&
                    !src.includes('brand') &&
                    !src.includes('header') &&
                    !src.includes('footer') &&
                    !src.includes('banner') &&
                    !alt.includes('logo') &&
                    !alt.includes('brand') &&
                    !alt.includes('DESCENTE') &&
                    !className.includes('logo') &&
                    !className.includes('brand') &&
                    (src.includes('locondo') ||
                     src.includes('product') ||
                     src.includes('item') ||
                     src.includes('commodity') ||
                     src.includes('jpg') ||
                     src.includes('png'))) {

                    // 获取高质量图片链接
                    let highQualitySrc = src;
                    if (src.includes('_thumb.jpg')) {
                        highQualitySrc = src.replace('_thumb.jpg', '.jpg');
                    } else if (src.includes('_s.jpg')) {
                        highQualitySrc = src.replace('_s.jpg', '.jpg');
                    } else if (src.includes('_m.jpg')) {
                        highQualitySrc = src.replace('_m.jpg', '.jpg');
                    }

                    // 只添加商品相关图片（通过尺寸和内容判断）
                    if (highQualitySrc &&
                        !highQualitySrc.includes('logo') &&
                        !images.includes(highQualitySrc)) {
                        images.push(highQualitySrc);
                    }
                }
            }

            // 去重并按优先级筛选图片：1100×1100 > _l.jpg > 前20张
            const uniqueImages = [...new Set(images)];
            const highResPattern = /(1100x1100|_1100x1100|_1100\.|\/1100\/)/;
            const highResImages = uniqueImages.filter(url => highResPattern.test(url));
            const largeFallback = uniqueImages.filter(url => url.endsWith('_l.jpg'));
            if (highResImages.length > 0) {
                return highResImages;
            }
            if (largeFallback.length > 0) {
                return largeFallback;
            }
            return uniqueImages.slice(0, 20);
        });
    }

    /**
     * 抓取颜色和尺码信息 - 修复版本，避免重复和无效值
     */
    async extractColorsAndSizes(page) {
        return await page.evaluate(() => {
            const result = {
                colors: [],
                sizes: []
            };

            try {
                // 🎨 提取颜色名称 - 避免重复和HTML污染
                const uniqueColors = new Set();

                // 方法1: 从alt属性提取带代码的颜色
                const images = document.querySelectorAll('img[alt]');
                images.forEach(img => {
                    const alt = img.getAttribute('alt');
                    if (alt &&
                        alt.includes('（') &&
                        alt.includes('）') &&
                        alt.match(/[（(][A-Z0-9]+[)）]/)) {
                        // 完整的颜色+代码组合，如：ネイビー（NV00）
                        uniqueColors.add(alt.trim());
                    }
                });

                // 方法2: 从颜色选择器提取
                const colorElements = document.querySelectorAll('.color-selector .colorName, .color-name');
                colorElements.forEach(el => {
                    const text = el.textContent.trim();
                    // 只提取纯颜色名称，不包含代码
                    if (text &&
                        text.length < 30 &&
                        text.length > 1 &&
                        !text.includes('\n') &&
                        !text.includes('バリエーション') &&
                        !text.includes('heading') &&
                        !text.includes('popup') &&
                        !text.includes('{{') &&
                        !text.includes('}}') &&
                        !text.includes('<') &&
                        !text.includes('>') &&
                        !text.includes('commodity') &&
                        !text.includes('image') &&
                        !text.includes('href')) {
                        uniqueColors.add(text);
                    }
                });

                // 转换为数组并去重
                result.colors = Array.from(uniqueColors);

                // 📏 提取尺码信息 - 过滤无效值
                const uniqueSizes = new Set();

                // 从尺码选择器提取
                const sizeElements = document.querySelectorAll('select[name*="size"] option, .size-selector option, .size-option, [class*="size"]');
                sizeElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text &&
                        text.length < 10 &&
                        text.trim().length > 0 &&
                        (/[SMLXL]/.test(text) || /^[0-9]+$/.test(text)) &&
                        !text.includes('選択') &&
                        !text.includes('サイズ') &&
                        !text.includes('--') &&
                        !text.includes('MLLL3L') && // 过滤无效组合
                        text !== 'MLLL3L' &&
                        text !== 'SMLLL' && // 🔥 过滤连接的尺码
                        text !== 'SML' &&
                        text !== 'SMLL' &&
                        !/^[SMLX]{3,}$/.test(text)) { // 🔥 过滤任何3个以上连续的SMLX字符
                        uniqueSizes.add(text);
                    }
                });

                result.sizes = Array.from(uniqueSizes).sort((a, b) => {
                    // 自定义排序：S M L LL 3L 4L 5L...
                    const order = {'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'XL': 4, 'LL': 5, '3L': 6, '4L': 7, '5L': 8};
                    return (order[a] || 99) - (order[b] || 99);
                });

            } catch (error) {
                console.warn('颜色尺码提取失败:', error);
            }

            return result;
        });
    }

    /**
     * 📦 抓取库存状态信息 - 遍历所有颜色和尺码组合
     */
    async extractVariantInventory(page) {
        try {
            const currentUrl = page.url();

            // 首先获取所有颜色选项（包括 URL）
            const colorOptions = await page.evaluate(() => {
                const colors = [];
                const colorItems = document.querySelectorAll('#color-selector li, .color-selector li');

                colorItems.forEach((item, index) => {
                    const img = item.querySelector('img');
                    const link = item.querySelector('a');
                    const colorName = img ? img.getAttribute('alt') : '';
                    const isCurrent = item.classList.contains('currentCommodityColor');
                    const href = link ? link.getAttribute('href') : '';

                    if (colorName) {
                        colors.push({
                            index: index,
                            colorName: colorName.replace(/[（(][A-Z0-9]+[)）]/g, '').trim(),
                            fullName: colorName,
                            isCurrent: isCurrent,
                            url: href
                        });
                    }
                });

                return colors;
            });

            console.log(`📦 发现 ${colorOptions.length} 个颜色选项`);

            const variantInventory = [];

            // 遍历每个颜色
            for (let i = 0; i < colorOptions.length; i++) {
                const colorOption = colorOptions[i];

                console.log(`🎨 选择颜色: ${colorOption.colorName}`);

                try {
                    // 如果不是当前颜色，需要导航到该颜色的页面
                    if (!colorOption.isCurrent && colorOption.url) {
                        const colorUrl = colorOption.url.startsWith('http')
                            ? colorOption.url
                            : `https://store.descente.co.jp${colorOption.url}`;
                        console.log(`  📍 导航到: ${colorUrl}`);
                        await page.goto(colorUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
                        await page.waitForTimeout(2000);
                    }
                } catch (e) {
                    console.log(`⚠️ 导航到颜色页面失败: ${e.message}`);
                    continue;
                }

                // 提取当前颜色的所有尺码库存状态
                const sizeStocks = await page.evaluate(() => {
                    const stocks = [];
                    let debugInfo = { method: 'none', found: false };

                    // 方法0: 从页面下方的尺码表格获取（切换颜色后会更新，最可靠）
                    const sizeList = document.querySelector('.shopping_cantrol.commoditySizelist, .commoditySizelist');
                    if (sizeList) {
                        const text = sizeList.innerText || sizeList.textContent;
                        // 分割成行或块
                        const lines = text.split(/\n/);
                        let currentSize = null;

                        lines.forEach(line => {
                            const trimmed = line.trim();
                            // 检查是否是尺码数字
                            const sizeMatch = trimmed.match(/^(\d{2,3}|[SMLX]+|LL|3L|4L|5L)$/);
                            if (sizeMatch) {
                                currentSize = sizeMatch[1];
                            } else if (currentSize && trimmed) {
                                // 检查库存状态
                                let inStock = true;
                                let status = 'normal';

                                if (/✕|×|なし|sold\s*out|品切/i.test(trimmed)) {
                                    inStock = false;
                                    status = 'oos';
                                } else if (/残りわずか|△/i.test(trimmed)) {
                                    status = 'little';
                                    inStock = true;
                                } else if (/○|在庫あり/i.test(trimmed)) {
                                    status = 'normal';
                                    inStock = true;
                                } else if (/カートに入れる|添加到购物车/i.test(trimmed)) {
                                    // 有购物车按钮说明有货
                                    if (!stocks.find(s => s.size === currentSize)) {
                                        stocks.push({ size: currentSize, inStock: true, status: status || 'normal' });
                                    }
                                    currentSize = null;
                                    return;
                                } else {
                                    return; // 跳过其他内容
                                }

                                if (!stocks.find(s => s.size === currentSize)) {
                                    stocks.push({ size: currentSize, inStock, status });
                                }
                            }
                        });

                        if (stocks.length > 0) {
                            debugInfo = { method: '方法0-commoditySizelist', found: true };
                        }
                    }

                    // 方法0.1: 查找悬浮弹出框 popupRelatedStock
                    if (stocks.length === 0) {
                        const popupStock = document.querySelector('.popupRelatedStock');
                        if (popupStock) {
                            const text = popupStock.textContent;
                            const stockPattern = /(\d{2,3}|[SMLX]+|LL|3L)\s*[:：]\s*([○△✕×✖])(?:\d*点)?/g;
                            let match;
                            while ((match = stockPattern.exec(text)) !== null) {
                                const size = match[1];
                                const symbol = match[2];
                                const inStock = symbol === '○' || symbol === '△';
                                const status = symbol === '○' ? 'normal' : (symbol === '△' ? 'little' : 'oos');

                                if (!stocks.find(s => s.size === size)) {
                                    stocks.push({ size, inStock, status });
                                }
                            }
                            if (stocks.length > 0) {
                                debugInfo = { method: '方法0.1-popupRelatedStock', found: true };
                            }
                        }
                    }

                    // 方法0.5: 查找任何包含 "の在庫" 的元素
                    if (stocks.length === 0) {
                        const stockSection = [...document.querySelectorAll('div, section, p')].find(el =>
                            el.textContent.includes('の在庫') && el.textContent.length < 500
                        );

                        if (stockSection) {
                            const text = stockSection.textContent;
                            // 匹配格式: 76: △2点 或 79: × (支持多种 × 字符)
                            const stockPattern = /(7[6-9]|8[0-9]|9[0-6])\s*[:：]\s*([○△✕×✖Xx])(?:\d*点)?/g;
                            let match;
                            while ((match = stockPattern.exec(text)) !== null) {
                                const size = match[1];
                                const symbol = match[2];
                                const inStock = symbol === '○' || symbol === '△';
                                const status = symbol === '○' ? 'normal' : (symbol === '△' ? 'little' : 'oos');

                                if (!stocks.find(s => s.size === size)) {
                                    stocks.push({ size, inStock, status });
                                }
                            }
                            if (stocks.length > 0) {
                                debugInfo = { method: '方法0.5-section', found: true };
                            }
                        }
                    }

                    // 方法1: 查找库存摘要行 "M:△2点 / L:△2点 / LL:✕" 或 "76: △2点 / 79: ×" 格式
                    if (stocks.length === 0) {
                        const allElements = document.querySelectorAll('div, p, span, li');
                        for (const el of allElements) {
                            const text = el.textContent.trim();
                            // 只在包含库存符号的短文本中匹配
                            if (text.length > 200 || !(/[○△✕×]/.test(text))) continue;

                            // 匹配格式: M:△ 或 L:○ 或 LL:✕ 或 76:△2点 或 79:×
                            // 支持字母尺码和数字尺码，支持多种 × 字符
                            const stockPattern = /([SMLX]+|LL|3L|4L|5L|7[6-9]|8[0-9]|9[0-6])\s*[:：]\s*([○△✕×✖Xx])(?:\d*点)?/g;
                            let match;
                            while ((match = stockPattern.exec(text)) !== null) {
                                const size = match[1];
                                const symbol = match[2];
                                const inStock = symbol === '○' || symbol === '△';
                                const status = symbol === '○' ? 'normal' : (symbol === '△' ? 'little' : 'oos');

                                // 避免重复添加
                                if (!stocks.find(s => s.size === size)) {
                                    stocks.push({ size, inStock, status });
                                }
                            }
                            if (stocks.length > 0) break; // 找到后退出
                        }
                    }

                    // 方法2: 查找包含 "残りわずか" 或 "なし" 的元素
                    if (stocks.length === 0) {
                        const sizeSection = [...document.querySelectorAll('section, div')].find(el =>
                            /サイズ/.test(el.textContent) && el.querySelectorAll('li, button').length > 0
                        );

                        if (sizeSection) {
                            const items = sizeSection.querySelectorAll('li, button, .option');
                            items.forEach(item => {
                                const text = item.textContent.trim();
                                // 提取尺码（支持字母和裤子尺码76-96）
                                const sizeMatch = text.match(/^([SMLX]+|LL|3L|4L|5L|7[6-9]|8[0-9]|9[0-6])\b/i);
                                if (sizeMatch) {
                                    const size = sizeMatch[1].toUpperCase ? sizeMatch[1].toUpperCase() : sizeMatch[1];
                                    const hasLowStock = /残りわずか|△/.test(text);
                                    const hasNoStock = /なし|sold\s*out|品切|✕|×/i.test(text);
                                    const inStock = !hasNoStock;
                                    const status = hasNoStock ? 'oos' : (hasLowStock ? 'little' : 'normal');

                                    if (!stocks.find(s => s.size === size)) {
                                        stocks.push({ size, inStock, status });
                                    }
                                }
                            });
                        }
                    }

                    // 方法3: 通用文本搜索 - 确保尺码和符号在同一匹配中
                    if (stocks.length === 0) {
                        const stockElements = [...document.querySelectorAll('li, div, span')].filter(el =>
                            /残りわずか|なし|○|△|✕|×/.test(el.textContent.trim()) &&
                            el.textContent.length < 100
                        );

                        stockElements.forEach(el => {
                            const text = el.textContent.trim();
                            // 必须同时包含尺码和符号，格式如: "76: ×" 或 "M △"
                            const combinedPattern = /([SMLX]+|LL|3L|4L|5L|7[6-9]|8[0-9]|9[0-6])\s*[:：]?\s*([○△✕×✖Xx])(?:\d*点)?/gi;
                            let match;
                            while ((match = combinedPattern.exec(text)) !== null) {
                                const size = match[1].toUpperCase ? match[1].toUpperCase() : match[1];
                                const symbol = match[2];
                                const inStock = symbol === '○' || symbol === '△';
                                const status = symbol === '○' ? 'normal' : (symbol === '△' ? 'little' : 'oos');

                                if (!stocks.find(s => s.size === size)) {
                                    stocks.push({ size, inStock, status });
                                }
                            }
                        });
                    }

                    return stocks;
                });

                // 添加到库存数组
                for (const stock of sizeStocks) {
                    variantInventory.push({
                        color: colorOption.colorName,
                        size: stock.size,
                        inStock: stock.inStock,
                        status: stock.status
                    });
                }

                console.log(`  颜色 ${colorOption.colorName}: ${sizeStocks.length} 个尺码, ${sizeStocks.filter(s => s.inStock).length} 个有货`);
            }

            // 如果没有找到任何库存信息，尝试备用方法
            if (variantInventory.length === 0) {
                console.log('⚠️ 未找到库存信息，尝试备用方法...');

                const fallbackStocks = await page.evaluate(() => {
                    const stocks = [];

                    // 查找任何包含库存状态的元素
                    const allElements = document.querySelectorAll('[class*="stock"], [class*="inventory"]');
                    allElements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text.includes('○') || text.includes('△') || text.includes('✕') || text.includes('×')) {
                            stocks.push({
                                text: text,
                                hasStock: text.includes('○') || text.includes('△')
                            });
                        }
                    });

                    return stocks;
                });

                if (fallbackStocks.length > 0) {
                    console.log(`📦 备用方法找到 ${fallbackStocks.length} 个库存元素`);
                }
            }

            return {
                variantInventory: variantInventory,
                totalVariants: variantInventory.length,
                inStockCount: variantInventory.filter(v => v.inStock).length,
                outOfStockCount: variantInventory.filter(v => !v.inStock).length
            };

        } catch (error) {
            console.log('❌ 库存信息提取失败:', error.message);
            return {
                variantInventory: [],
                error: error.message
            };
        }
    }
}

module.exports = UnifiedDetailScraper;