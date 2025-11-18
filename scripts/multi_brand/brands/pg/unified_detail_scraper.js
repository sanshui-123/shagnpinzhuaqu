#!/usr/bin/env node

/**
 * 统一详情页抓取器 - PEARLY GATES
 * 集成了所有高级功能，支持单个URL和批量处理
 * 包含高级尺码表抓取功能
 */

const { chromium } = require('playwright');
const fs = require('fs');

class UnifiedDetailScraper {
    constructor(options = {}) {
        this.brandName = 'PEARLY GATES';
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

            // 组装最终结果
            const result = {
                success: true,
                url: url,
                timestamp: new Date().toISOString(),
                ...basicInfo,
                ...colorsAndSizes,
                imageUrls: images,
                sizeChart: sizeChartData,
                _scraper_info: {
                    version: 'unified_v1.0',
                    debug_mode: this.options.debug,
                    size_chart_method: sizeChartData.method,
                    processing_time: new Date().toISOString()
                }
            };

            // 🔄 尺码 fallback - 如果sizes为空，尝试从sizeChart提取
            if ((!result.sizes || result.sizes.length === 0) && sizeChartData.text) {
                const sizeChartText = sizeChartData.text;
                const extractedSizes = new Set();

                // 匹配 FR、FREE、ONE SIZE、フリー 等关键字
                const frPatterns = [
                    /\bFR\b/gi,
                    /\bFREE\b/gi,
                    /\bONE\s*SIZE\b/gi,
                    /フリー/g
                ];

                for (const pattern of frPatterns) {
                    const matches = sizeChartText.match(pattern);
                    if (matches) {
                        // 标准化为 "FR"
                        extractedSizes.add('FR');
                        break;
                    }
                }

                // 也尝试匹配常规尺码 S/M/L 等
                const sizePattern = /\b(XS|S|M|L|XL|LL|3L|4L|5L)\b/g;
                const sizeMatches = sizeChartText.match(sizePattern);
                if (sizeMatches) {
                    sizeMatches.forEach(s => extractedSizes.add(s.toUpperCase()));
                }

                // 匹配日本数字尺码 (00/0/1/2 for women, 4/5/6/7 for men)
                // 在表格行开头匹配数字尺码
                const numericSizePattern = /(?:^|\s|>)(00|0|1|2|3|4|5|6|7)(?:\s|<|$)/gm;
                const numericMatches = sizeChartText.match(numericSizePattern);
                if (numericMatches) {
                    numericMatches.forEach(m => {
                        const size = m.trim().replace(/[<>]/g, '');
                        if (['00', '0', '1', '2', '3', '4', '5', '6', '7'].includes(size)) {
                            extractedSizes.add(size);
                        }
                    });
                }

                if (extractedSizes.size > 0) {
                    result.sizes = Array.from(extractedSizes);
                    console.log('📏 从尺码表提取尺码:', result.sizes);
                }
            }

            // 🎯 基于尺码体系的性别检测（核心信号）
            if (result._genderScores) {
                let menSizeScore = 0;
                let womenSizeScore = 0;
                const scores = result._genderScores;

                // 🔥 PG品牌尺码体系（强信号）：
                // - 男性尺码: 4, 5, 6, 7 (数字码系统)
                // - 女性尺码: 00, 0, 1, 2 (数字码系统)
                // - 共用: S, M, L, XL 等字母码
                if (result.sizes && result.sizes.length > 0) {
                    const menSizes = ['4', '5', '6', '7'];
                    const womenSizes = ['00', '0', '1', '2'];

                    let hasMenSize = false;
                    let hasWomenSize = false;

                    for (const size of result.sizes) {
                        const sizeStr = String(size).trim();
                        if (menSizes.includes(sizeStr)) {
                            hasMenSize = true;
                        }
                        if (womenSizes.includes(sizeStr)) {
                            hasWomenSize = true;
                        }
                    }

                    // 尺码体系是强信号
                    if (hasMenSize && !hasWomenSize) {
                        menSizeScore += 60; // 纯男性尺码体系
                    }
                    if (hasWomenSize && !hasMenSize) {
                        womenSizeScore += 60; // 纯女性尺码体系
                    }
                    if (hasMenSize && hasWomenSize) {
                        // 混合尺码，可能是中性或特殊情况
                        // 不加分，依赖其他信号
                    }
                }

                // 更新分数
                scores.men += menSizeScore;
                scores.women += womenSizeScore;

                // 最终决策
                if (scores.unisex >= 50) {
                    result.gender = '中性';
                } else if (scores.men > scores.women) {
                    result.gender = '男';
                } else if (scores.women > scores.men) {
                    result.gender = '女';
                } else if (scores.men === scores.women && scores.men > 0) {
                    // 平局时默认为中性
                    result.gender = '中性';
                }

                console.log(`👤 性别检测分数: 男=${scores.men}, 女=${scores.women}, 中性=${scores.unisex} -> ${result.gender}`);
            }

            // 清理临时数据
            delete result._genderScores;

            // 📦 分类检测 - 根据商品名称判断类别（按特异性排序，更具体的在前）
            if (result.productName) {
                const name = result.productName;
                if (name.includes('キャディバッグ') || name.includes('カート') || name.includes('スタンド')) {
                    result.category = '球包/球袋';
                } else if (name.includes('ポロ') || name.includes('POLO')) {
                    if (name.includes('長袖') || name.includes('ロングスリーブ')) {
                        result.category = '长袖POLO';
                    } else {
                        result.category = '短袖POLO';
                    }
                } else if (name.includes('ハイネック') || name.includes('タートル') || name.includes('モック')) {
                    // 高领在T恤之前检测，因为"ハイネックカットソー"应该是高领
                    if (name.includes('長袖')) {
                        result.category = '长袖高领';
                    } else {
                        result.category = '短袖高领';
                    }
                } else if (name.includes('カットソー') || name.includes('Tシャツ') || name.includes('T-shirt')) {
                    if (name.includes('長袖') || name.includes('ロングスリーブ')) {
                        result.category = '长袖T恤';
                    } else {
                        result.category = '短袖T恤';
                    }
                } else if (name.includes('ニット') || name.includes('セーター') || name.includes('プルオーバー')) {
                    result.category = '毛衣/针织衫';
                } else if (name.includes('ベスト')) {
                    result.category = '马甲/背心';
                } else if (name.includes('ブルゾン') || name.includes('ジャケット') || name.includes('アウター')) {
                    result.category = '外套/夹克';
                } else if (name.includes('パンツ') || name.includes('スカート')) {
                    if (name.includes('スカート')) {
                        result.category = '裙子';
                    } else {
                        result.category = '裤子';
                    }
                } else if (name.includes('キャップ') || name.includes('ハット') || name.includes('バイザー')) {
                    result.category = '帽子';
                } else if (name.includes('グローブ') || name.includes('手袋')) {
                    result.category = '手套';
                } else if (name.includes('シューズ') || name.includes('靴')) {
                    result.category = '球鞋';
                } else if (name.includes('ヘッドカバー')) {
                    result.category = '杆头套';
                } else if (name.includes('ボール')) {
                    result.category = '高尔夫球';
                }
            }

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

            // 🎯 商品标题选择器 - Shopify (mix.tokyo)
            const titleSelectors = [
                '.product__title h1',
                'h1.product__title',
                '.product-single__title',
                '.product__info h1',
                'h1[class*="product"]',
                '.product-meta h1',
                'h1:not(:empty)'
            ];

            for (const selector of titleSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim()) {
                    const title = element.textContent.trim();
                    if (title &&
                        title.length > 3 &&
                        !title.includes('mix.tokyo') &&
                        !title.includes('PEARLY GATES STORE')) {
                        result.productName = title;
                        break;
                    }
                }
            }

            // 从h1中提取
            if (!result.productName) {
                const h1Elements = document.querySelectorAll('h1');
                for (const h1 of h1Elements) {
                    const text = h1.textContent.trim();
                    if (text && text.length > 3 && !text.includes('mix.tokyo')) {
                        result.productName = text;
                        break;
                    }
                }
            }

            // 🎯 标题规范化 - 确保以 PEARLY GATES 品牌开头
            if (result.productName) {
                // 移除原有的PG前缀（如 "PG is PG"）
                let normalizedTitle = result.productName
                    .replace(/^PG\s+is\s+PG\s*/i, '')
                    .replace(/^PEARLY\s*GATES\s*/i, '')
                    .trim();
                // 添加标准品牌前缀
                result.productName = 'PEARLY GATES ' + normalizedTitle;
            }

            // 价格 - Shopify（提取数字价格）
            const priceSelectors = [
                '.product__price .money',
                '.price .money',
                '.product-price .money',
                '.price-item--regular',
                '[class*="price"] .money',
                '.price'
            ];

            for (const selector of priceSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim()) {
                    const priceText = element.textContent.trim();
                    // 提取数字价格（如 "¥70,400" -> "70400"）
                    const match = priceText.match(/[\d,]+/);
                    if (match) {
                        result.price = match[0].replace(/,/g, '');
                    } else {
                        result.price = priceText;
                    }
                    break;
                }
            }

            // 描述 - Shopify
            const descSelectors = [
                '.product__description',
                '.product-description',
                '.product__info-description',
                '[class*="description"]',
                '.rte'
            ];

            for (const selector of descSelectors) {
                const element = document.querySelector(selector);
                if (element && element.textContent.trim().length > 30) {
                    result.description = element.textContent.trim();
                    break;
                }
            }

            // 🎯 商品ID从URL提取 - PG规则：10位数字截断为8位
            const urlMatch = url.match(/\/products\/(\d+)/);
            if (urlMatch && urlMatch[1]) {
                const rawId = urlMatch[1];
                // 如果是10位数字，去掉后两位
                if (rawId.length >= 10) {
                    result.productId = rawId.slice(0, -2);
                } else {
                    result.productId = rawId;
                }
            } else if (extraData.productId) {
                result.productId = extraData.productId;
            }

            // 🎯 性别判断 - 多信号评分算法
            const pageText = document.body.textContent;
            const urlLower = url.toLowerCase();

            // 评分系统
            let menScore = 0;
            let womenScore = 0;
            let unisexScore = 0;

            // ========== 强规则 (直接决定) ==========

            // 1. 商品标题中的性别标签 (最高优先级)
            const titleUpper = result.productName.toUpperCase();
            if (titleUpper.includes('(UNISEX)') || titleUpper.includes('（UNISEX）') ||
                titleUpper.includes('UNISEX') || result.productName.includes('ユニセックス')) {
                unisexScore += 100;
            }
            if (titleUpper.includes('(MENS)') || titleUpper.includes('（MENS）') ||
                titleUpper.includes('(MEN)') || titleUpper.includes('（MEN）')) {
                menScore += 100;
            }
            if (titleUpper.includes('(LADIES)') || titleUpper.includes('（LADIES）') ||
                titleUpper.includes('(WOMEN)') || titleUpper.includes('（WOMEN）')) {
                womenScore += 100;
            }

            // 2. 导航/面包屑路径检测
            const breadcrumbs = document.querySelectorAll('nav a, .breadcrumb a, [class*="breadcrumb"] a, .nav-link');
            for (const crumb of breadcrumbs) {
                const text = crumb.textContent.toUpperCase().trim();
                if (text === 'MEN' || text === 'MENS' || text === 'メンズ') {
                    menScore += 50;
                }
                if (text === 'WOMEN' || text === 'LADIES' || text === 'レディース') {
                    womenScore += 50;
                }
                if (text === 'UNISEX' || text === 'ユニセックス') {
                    unisexScore += 50;
                }
            }

            // 3. URL路径检测
            if (urlLower.includes('/men/') || urlLower.includes('/mens/')) {
                menScore += 40;
            }
            if (urlLower.includes('/women/') || urlLower.includes('/ladies/')) {
                womenScore += 40;
            }
            if (urlLower.includes('/unisex/')) {
                unisexScore += 40;
            }

            // ========== 中规则 (信心增强) ==========

            // 4. 产品区域关键词检测 - 只检测产品信息区域，避免导航/页脚噪音
            const productArea = document.querySelector('.product__info, .product-info, [class*="product"], main') || document.body;
            const productText = productArea.textContent;

            // 男性关键词 - 限制最大加分
            const menKeywords = ['メンズ', '男性', '紳士'];
            let menKeywordScore = 0;
            for (const kw of menKeywords) {
                const regex = new RegExp(kw, 'gi');
                const matches = productText.match(regex);
                if (matches) {
                    menKeywordScore += Math.min(matches.length * 5, 15); // 每个关键词最多15分
                }
            }
            menScore += Math.min(menKeywordScore, 30); // 关键词总分最多30分

            // 女性关键词 - 限制最大加分
            const womenKeywords = ['レディース', '女性', '婦人'];
            let womenKeywordScore = 0;
            for (const kw of womenKeywords) {
                const regex = new RegExp(kw, 'gi');
                const matches = productText.match(regex);
                if (matches) {
                    womenKeywordScore += Math.min(matches.length * 5, 15);
                }
            }
            womenScore += Math.min(womenKeywordScore, 30);

            // 中性关键词 - 限制最大加分
            const unisexKeywords = ['UNISEX', 'ユニセックス', '男女兼用'];
            let unisexKeywordScore = 0;
            for (const kw of unisexKeywords) {
                const regex = new RegExp(kw, 'gi');
                const matches = productText.match(regex);
                if (matches) {
                    unisexKeywordScore += Math.min(matches.length * 10, 30);
                }
            }
            unisexScore += Math.min(unisexKeywordScore, 50);

            // 5. 相关商品标签检测
            const relatedProducts = document.querySelectorAll('.related-products a, .product-recommendations a, [class*="related"] a, [class*="recommend"] a');
            let relatedMen = 0, relatedWomen = 0, relatedUnisex = 0;
            for (const link of relatedProducts) {
                const text = link.textContent.toUpperCase();
                if (text.includes('(MENS)') || text.includes('（MENS）')) relatedMen++;
                if (text.includes('(LADIES)') || text.includes('（LADIES）')) relatedWomen++;
                if (text.includes('(UNISEX)') || text.includes('（UNISEX）')) relatedUnisex++;
            }
            if (relatedMen > relatedWomen && relatedMen > relatedUnisex) {
                menScore += 20;
            }
            if (relatedWomen > relatedMen && relatedWomen > relatedUnisex) {
                womenScore += 20;
            }
            if (relatedUnisex > relatedMen && relatedUnisex > relatedWomen) {
                unisexScore += 20;
            }

            // ========== 弱规则 (尺码模式) ==========

            // 6. 尺码模式检测 - 需要结合后面提取的尺码信息
            // 男性尺码模式: 4, 5, 6, 7
            // 女性尺码模式: 00, 0, 1, 2
            // 这个会在尺码提取后再做一次检测

            // ========== 决策 ==========

            // 如果有强信号(>=50分)，直接使用
            if (unisexScore >= 50) {
                result.gender = '中性';
            } else if (menScore >= 50 && menScore > womenScore) {
                result.gender = '男';
            } else if (womenScore >= 50 && womenScore > menScore) {
                result.gender = '女';
            } else if (menScore > 0 || womenScore > 0 || unisexScore > 0) {
                // 使用分数最高的
                if (unisexScore > menScore && unisexScore > womenScore) {
                    result.gender = '中性';
                } else if (menScore > womenScore) {
                    result.gender = '男';
                } else if (womenScore > menScore) {
                    result.gender = '女';
                }
            }

            // 保存分数供后续尺码检测使用
            result._genderScores = { men: menScore, women: womenScore, unisex: unisexScore };

            return result;
        }, { url, extraData, brandName: this.brandName });
    }

    /**
     * 抓取商品图片 - 只收集1280宽度的Shopify CDN图片
     */
    async extractProductImages(page) {
        return await page.evaluate(() => {
            const images = [];
            const imgElements = document.querySelectorAll('img');

            for (const img of imgElements) {
                let src = img.getAttribute('src') || img.getAttribute('data-src') || '';

                // 只处理 mix.tokyo/cdn/shop/files 的图片
                if (!src.includes('mix.tokyo/cdn/shop/files')) continue;

                // 过滤掉 _MAIN.jpg 图片
                if (src.includes('_MAIN.jpg')) continue;

                // 过滤掉 logo、banner、应用商店等无关图片
                if (src.includes('logo') || src.includes('banner') || src.includes('icon') ||
                    src.includes('appstore') || src.includes('googleplay') ||
                    src.includes('pearlygates.jpg') || src.includes('.png')) continue;

                // 只收集产品图片（包含产品ID的文件名）
                const productIdPattern = /\d{10}-\d{3}_[A-Z]\.jpg/i;
                if (!productIdPattern.test(src)) continue;

                // 确保是1280宽度的图片
                // 如果没有width参数，添加width=1280
                if (!src.includes('width=')) {
                    src = src + (src.includes('?') ? '&' : '?') + 'width=1280';
                } else {
                    // 替换为1280宽度
                    src = src.replace(/width=\d+/, 'width=1280');
                }

                // 确保URL有协议前缀
                if (src.startsWith('//')) {
                    src = 'https:' + src;
                }

                // 收集所有非_MAIN的CDN图片
                if (!images.includes(src)) {
                    images.push(src);
                }
            }

            // 🔄 图片去重 - 使用文件名作为唯一标识
            const uniqueImages = [];
            const seenFiles = new Set();

            for (const imgUrl of images) {
                // 提取文件名部分作为唯一标识 (如 0536980121-130_A.jpg)
                const fileMatch = imgUrl.match(/\/([^\/]+\.jpg)/i);
                if (fileMatch) {
                    const fileName = fileMatch[1].split('?')[0]; // 去掉query参数
                    if (!seenFiles.has(fileName)) {
                        seenFiles.add(fileName);
                        uniqueImages.push(imgUrl);
                    }
                } else if (!uniqueImages.includes(imgUrl)) {
                    uniqueImages.push(imgUrl);
                }
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

                // 📏 提取尺码信息 - 从Shopify变体数据获取
                const uniqueSizes = new Set();

                // 方法1: 从Shopify变体input/label提取
                const variantSelectors = [
                    'input[name*="Size"]',
                    'input[name*="size"]',
                    'label[for*="Size"]',
                    'label[for*="size"]',
                    '.variant-input input',
                    'select[name*="size"] option',
                    '.size-selector option'
                ];

                for (const selector of variantSelectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        let value = el.getAttribute('value') || el.textContent.trim();
                        if (value &&
                            value.length < 10 &&
                            (value === 'FR' || /^[SMLXL]+$/.test(value) || /^\d+$/.test(value) ||
                             value === 'XS' || value === 'LL' || value === '3L' || value === '4L' || value === '5L') &&
                            !value.includes('選択')) {
                            uniqueSizes.add(value.trim());
                        }
                    });
                }

                // 方法2: 从页面JSON数据提取（Shopify常用）
                const scripts = document.querySelectorAll('script[type="application/json"]');
                scripts.forEach(script => {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data.variants) {
                            data.variants.forEach(v => {
                                if (v.option1) uniqueSizes.add(v.option1);
                                if (v.option2) uniqueSizes.add(v.option2);
                            });
                        }
                    } catch (e) {}
                });

                // 方法3: 检查页面文本中的尺码信息
                const pageText = document.body.textContent;
                const frMatch = pageText.match(/サイズ[：:]\s*(FR|S|M|L|LL|3L)/);
                if (frMatch) {
                    uniqueSizes.add(frMatch[1]);
                }

                result.sizes = Array.from(uniqueSizes).sort((a, b) => {
                    const order = {'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'XL': 4, 'LL': 5, '3L': 6, '4L': 7, '5L': 8, 'FR': 9};
                    return (order[a] || 99) - (order[b] || 99);
                });

            } catch (error) {
                console.warn('颜色尺码提取失败:', error);
            }

            return result;
        });
    }
}

module.exports = UnifiedDetailScraper;