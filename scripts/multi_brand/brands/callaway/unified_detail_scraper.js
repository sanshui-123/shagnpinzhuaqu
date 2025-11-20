#!/usr/bin/env node

/**
 * Callaway 统一详情页抓取器
 * 基于 scrape_product_detail.js 封装为类结构
 * 保持所有 DOM 选择器和抓取逻辑不变
 */

const { chromium } = require('playwright');
const { translateColorName } = require('./callaway_translations');

// 颜色翻译对照表
const COLOR_NAME_TRANSLATION = {
    // 基础颜色
    'White': '白色',
    'Black': '黑色',
    'Red': '红色',
    'Blue': '蓝色',
    'Green': '绿色',
    'Yellow': '黄色',
    'Pink': '粉色',
    'Purple': '紫色',
    'Orange': '橙色',
    'Brown': '棕色',
    'Gray': '灰色',
    'Grey': '灰色',

    // CallawayJP 特有颜色
    'Navy': '藏青色',
    'Royal': '宝蓝色',
    'Sky Blue': '天蓝色',
    'Light Blue': '浅蓝色',
    'Dark Blue': '深蓝色',
    'Turquoise': '绿松石色',
    'Teal': '青色',

    // 红色系
    'Burgundy': '酒红色',
    'Maroon': '栗色',
    'Coral': '珊瑚色',
    'Rose': '玫瑰色',
    'Fuchsia': '紫红色',
    'Magenta': '洋红色',

    // 绿色系
    'Olive': '橄榄色',
    'Khaki': '卡其色',
    'Lime': '青柠色',
    'Mint': '薄荷色',
    'Forest': '森林绿',
    'Emerald': '翡翠绿',

    // 灰色系
    'Charcoal': '炭灰色',
    'Silver': '银色',
    'Slate': '石板灰',
    'Heather': '麻灰色',

    // 棕色系
    'Tan': '棕褐色',
    'Beige': '米色',
    'Cream': '奶油色',
    'Ivory': '象牙色',
    'Ecrus': '米白色',
    'Camel': '驼色',

    // 紫色系
    'Lavender': '薰衣草紫',
    'Violet': '紫罗兰',
    'Plum': '梅子色',

    // 黄色系
    'Gold': '金色',
    'Mustard': '芥末黄',
    'Lemon': '柠檬黄',

    // 粉色系
    'Peach': '桃色',
    'Salmon': '鲑鱼粉',

    // 橙色系
    'Burnt Orange': '焦橙色',

    // 日文颜色（如果需要保留日文）
    'ホワイト': '白色',
    'ブラック': '黑色',
    'レッド': '红色',
    'ブルー': '蓝色',
    'ネイビー': '藏青色',
    'グレー': '灰色',
    'グリーン': '绿色',
    'イエロー': '黄色',
    'ピンク': '粉色',
    'パープル': '紫色',
    'オレンジ': '橙色',
    'ブラウン': '棕色',
    'ベージュ': '米色',
    'アイボリー': '象牙色',
    'カーキ': '卡其色',
    'オリーブ': '橄榄色',
    'ターコイズ': '绿松石色',
    'コーラル': '珊瑚色',
    'ローズ': '玫瑰色',
    'ラベンダー': '薰衣草紫',
    'ワイン': '酒红色',
    'モカ': '摩卡色',
    'チャコール': '炭灰色',
    'シルバー': '银色',
    'ゴールド': '金色'
};

class UnifiedDetailScraper {
    constructor(options = {}) {
        this.brandName = '卡拉威';
        this.options = {
            headless: options.headless !== false,
            timeout: options.timeout || 45000,
            debug: options.debug || false,
            ...options
        };
    }

    /**
     * 主要的详情页抓取方法
     * @param {string} url - 商品详情页URL
     * @param {Object} extraData - 额外数据（如商品ID等）
     * @returns {Object} 抓取结果
     */
    async scrapeDetailPage(url, extraData = {}) {
        console.log('🚀 开始抓取产品详情...');
        console.log(`📍 URL: ${url}`);

        const startTime = Date.now();
        let browser = null;

        try {
            // 启动浏览器
            console.log('🌐 启动浏览器...');
            browser = await chromium.launch({
                headless: this.options.headless,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--no-first-run',
                    '--no-default-browser-check'
                ]
            });

            const context = await browser.newContext({
                userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale: 'ja-JP',
                timezone: 'Asia/Tokyo'
            });

            const page = await context.newPage();

            // 加载页面（带重试机制）
            console.log('📄 加载页面...');
            await this.loadPageWithRetry(page, url);

            // 首先进行多颜色抓取
            const multiColorData = await this.extractMultiColorData(page);

            // 提取产品数据（包含价格信息）
            const extractedData = await this.extractProductData(page);

            // 将多颜色数据合并到extractedData中
            if (multiColorData.colors.length > 0) {
                console.log(`🎨 使用多颜色抓取结果: ${multiColorData.colors.length}种颜色`);
                extractedData.imageGroups = multiColorData.imageGroups;
                extractedData.multiColorInfo = {
                    colors: multiColorData.colors,
                    totalImages: multiColorData.allImages.size
                };
            }

            // 提取价格信息（使用extractedData中已提取的价格）
            const priceInfo = {
                currentPrice: extractedData.currentPrice || null,
                originalPrice: extractedData.originalPrice || null,
                priceText: extractedData.priceText || ''
            };

            console.log(`💰 价格信息: ${priceInfo.priceText || '未找到'}`);

            // 尝试使用增强的下拉菜单方式提取尺码
            let dropdownSizes = [];
            if (multiColorData.colors.length > 0) {
                console.log('📏 尝试从下拉菜单提取尺码（第一优先级）...');
                dropdownSizes = await this.extractSizesFromDropdown(page);
            }

            // 提取商品ID
            const productId = extraData.productId || this.extractProductIdFromUrl(url);
            console.log(`🏷️  产品ID: ${productId}`);

            // 构建最终数据（传递下拉菜单提取的尺码）
            const finalData = this.buildFinalProductData(
                extractedData,
                productId,
                url,
                priceInfo,
                dropdownSizes
            );

            console.log('✅ 抓取完成!');
            console.log(`⏱️  处理时间: ${Date.now() - startTime}ms`);
            console.log(`📊 统计信息:`);
            console.log(`   - 颜色数量: ${finalData.scrapeInfo.totalColors}`);
            console.log(`   - 尺码数量: ${finalData.scrapeInfo.totalSizes}`);
            console.log(`   - 图片数量: ${finalData.scrapeInfo.totalImages}`);
            console.log(`   - 数据来源: ${finalData.scrapeInfo.dataSources.join(', ')}`);

            // 转换为统一格式返回
            return this.convertToUnifiedFormat(finalData);

        } catch (error) {
            console.error('❌ 抓取失败:', error.message);
            return {
                success: false,
                url: url,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        } finally {
            if (browser) {
                await browser.close();
            }
        }
    }

    /**
     * 从URL提取产品ID
     */
    extractProductIdFromUrl(url) {
        const match = url.match(/\/([A-Z]\d+)_\.html/);
        return match ? match[1] : '';
    }

    /**
     * 加载页面（带重试机制）
     */
    async loadPageWithRetry(page, url) {
        let pageLoaded = false;
        let attempts = 0;
        const maxAttempts = 3;

        while (!pageLoaded && attempts < maxAttempts) {
            attempts++;
            try {
                console.log(`🔄 尝试加载页面 (第${attempts}/${maxAttempts}次)...`);
                await page.goto(url, {
                    waitUntil: 'domcontentloaded',
                    timeout: 120000
                });

                // 测试：检查页面是否正确加载并包含我们期望的内容
                const hasExpectedContent = await page.evaluate(() => {
                    const bodyText = document.body.textContent || '';
                    return bodyText.includes('今シーズンの') || bodyText.includes('Callaway') || bodyText.includes('Golf');
                });

                console.log(`📄 页面内容检查: ${hasExpectedContent ? '✅ 找到期望内容' : '⚠️ 未找到期望内容'}`);

                // 等待页面完全加载
                await page.waitForTimeout(5000);
                pageLoaded = true;
                console.log('✅ 页面加载成功');

            } catch (error) {
                console.log(`❌ 第${attempts}次加载失败: ${error.message}`);
                if (attempts < maxAttempts) {
                    console.log(`⏱️  等待5秒后重试...`);
                    await page.waitForTimeout(5000);
                } else {
                    throw new Error(`页面加载失败，已重试${maxAttempts}次: ${error.message}`);
                }
            }
        }
    }

    /**
     * 多颜色抓取函数
     */
    async extractMultiColorData(page) {
        console.log('🎨 开始多颜色抓取...');

        const multiColorData = {
            colors: [],
            imageGroups: [],
            allImages: new Set()
        };

        try {
            console.log('🔍 使用优化的颜色按钮检测逻辑...');

            // Callaway 专用颜色选择器（从旧版 DOM 逻辑迁移 - 使用实际工作的选择器）
            const colorButtonSelectors = [
                '.d_flex.items_center.gap_2\\.5.flex_row.flex-wrap_wrap button',  // Callaway 实际使用的选择器
                '[data-color]',
                '[data-colorcode]'
            ];

            let colorButtons = [];

            // CSS选择器检测（添加属性验证，从旧版逻辑迁移）
            for (const selector of colorButtonSelectors) {
                try {
                    const buttons = await page.$$(selector);
                    if (buttons.length > 0) {
                        console.log(`✓ 选择器 "${selector}" 找到 ${buttons.length} 个元素`);

                        // 对于 Callaway 的第一个选择器（.d_flex...），非常specific，无需验证
                        // 对于其他选择器，验证是否有颜色相关属性
                        if (selector.includes('d_flex')) {
                            // Callaway 专用选择器，直接使用
                            console.log(`   ✓ 使用 Callaway 专用选择器，找到 ${buttons.length} 个颜色按钮`);
                            colorButtons = buttons;
                            break;
                        } else {
                            // 其他选择器需要验证
                            const validButtons = [];
                            for (const button of buttons) {
                                const hasColorAttr = await button.evaluate(el => {
                                    const dataColor = el.getAttribute('data-color');
                                    const dataColorCode = el.getAttribute('data-colorcode');
                                    const dataValue = el.getAttribute('data-value');
                                    const title = el.getAttribute('title');
                                    const ariaLabel = el.getAttribute('aria-label');
                                    const text = el.textContent?.trim();

                                    // 颜色按钮通常有这些特征之一
                                    return dataColor || dataColorCode || dataValue || title || ariaLabel || (text && text.length > 0 && text.length < 50);
                                });

                                if (hasColorAttr) {
                                    validButtons.push(button);
                                }
                            }

                            if (validButtons.length > 0) {
                                console.log(`   ✓ 验证后有效颜色按钮: ${validButtons.length} 个`);
                                colorButtons = validButtons;
                                break;
                            } else {
                                console.log(`   ⚠️ 未找到有效颜色属性，尝试下一个选择器...`);
                            }
                        }
                    }
                } catch (error) {
                    console.log(`⚠️ 选择器 "${selector}" 执行失败:`, error.message);
                }
            }

            console.log(`🎯 找到 ${colorButtons.length} 个颜色按钮`);

            // 如果没有找到颜色按钮，使用默认颜色
            if (colorButtons.length === 0) {
                console.log('⚠️ 未找到颜色按钮，使用默认颜色继续执行...');
                multiColorData.colors.push({
                    code: 'DEFAULT',
                    name: 'DEFAULT'
                });
                return multiColorData;
            }

            // 逐个点击颜色按钮并抓取数据
            for (let i = 0; i < colorButtons.length; i++) {
                const button = colorButtons[i];

                try {
                    // 获取按钮信息
                    const buttonText = await button.textContent();
                    const ariaLabel = await button.getAttribute('aria-label');
                    const title = await button.getAttribute('title');
                    const dataValue = await button.getAttribute('data-value');
                    const dataColor = await button.getAttribute('data-color');

                    console.log(`🔘 点击颜色按钮 ${i + 1}/${colorButtons.length}: ${buttonText || ariaLabel || title || '未知'}`);

                    // 点击按钮
                    await button.click();

                    // 等待页面更新
                    console.log('⏳ 等待页面更新...');
                    await page.waitForTimeout(2000);

                    // 提取当前颜色信息
                    const currentColorData = await this.extractCurrentColorData(page, {
                        text: buttonText,
                        ariaLabel,
                        title,
                        dataValue,
                        dataColor
                    });

                    console.log(`✓ 提取颜色: ${currentColorData.colorName} (${currentColorData.colorCode}), ${currentColorData.images.length}张图片`);

                    // 图片抓取规则：第一个颜色保留所有图片，其他颜色只保留前6张
                    let finalImages;
                    if (i === 0) {
                        finalImages = currentColorData.images;
                        console.log(`   📌 第一个颜色保留全部 ${finalImages.length} 张图片`);
                    } else {
                        finalImages = currentColorData.images.slice(0, 6);
                        console.log(`   📌 其他颜色保留前6张图片（共${finalImages.length}张）`);
                    }

                    // 添加到结果中
                    multiColorData.colors.push({
                        code: currentColorData.colorCode,
                        name: currentColorData.colorName
                    });

                    multiColorData.imageGroups.push({
                        colorCode: currentColorData.colorCode,
                        colorName: currentColorData.colorName,
                        images: finalImages
                    });

                    // 将图片添加到总集合中
                    finalImages.forEach(img => multiColorData.allImages.add(img));

                } catch (error) {
                    console.log(`❌ 处理颜色按钮 ${i + 1} 时出错: ${error.message}`);
                }
            }

            console.log(`✅ 多颜色抓取完成: ${multiColorData.colors.length}种颜色, 总计${multiColorData.allImages.size}张图片`);

        } catch (error) {
            console.log(`❌ 多颜色抓取失败: ${error.message}`);
        }

        return multiColorData;
    }

    /**
     * 提取当前颜色数据
     */
    async extractCurrentColorData(page, buttonInfo) {
        return await page.evaluate((buttonInfo) => {
            // 从按钮信息中提取颜色名称和代码
            let colorName = buttonInfo.text || buttonInfo.ariaLabel || buttonInfo.title || 'Unknown';
            let colorCode = buttonInfo.dataValue || buttonInfo.dataColor;

            // 如果没有明确的颜色代码，尝试生成一个
            if (!colorCode) {
                const colorMap = {
                    'ネイビー': '1031', 'navy': '1031',
                    'ブラック': '1040', 'black': '1040',
                    'ホワイト': '1000', 'white': '1000',
                    'ブルー': '1030', 'blue': '1030',
                    'レッド': '1600', 'red': '1600',
                    'グレー': '1900', 'gray': '1900', 'grey': '1900'
                };

                const lowerName = colorName.toLowerCase();
                for (const [key, value] of Object.entries(colorMap)) {
                    if (lowerName.includes(key.toLowerCase())) {
                        colorCode = value;
                        break;
                    }
                }

                if (!colorCode) {
                    colorCode = `AUTO_${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
                }
            }

            // 抓取当前显示的图片
            const currentImages = [];
            const imageSelectors = [
                'img[src*="callawaygolf"]',
                'img[src*="webdamdb"]',
                '.product-images img',
                '.gallery img',
                '[class*="image"] img'
            ];

            // 图片URL过滤函数 - 只保留1280尺寸商品图
            function isValidProductImage(imgSrc) {
                if (!imgSrc) return false;

                const validPrefix = 'https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_';
                if (!imgSrc.startsWith(validPrefix)) {
                    return false;
                }

                const blockedPatterns = [
                    't.co/',
                    'analytics.twitter.com',
                    'bat.bing.com',
                    '100th_sm_',
                    '220th_sm_',
                    'logo',
                    'icon',
                    'favicon'
                ];

                for (const pattern of blockedPatterns) {
                    if (imgSrc.includes(pattern)) {
                        return false;
                    }
                }

                return true;
            }

            for (const selector of imageSelectors) {
                const images = document.querySelectorAll(selector);
                images.forEach(img => {
                    if (isValidProductImage(img.src) && !currentImages.includes(img.src)) {
                        currentImages.push(img.src);
                    }
                });
            }

            console.log(`过滤后图片数量: ${currentImages.length}`);

            return {
                colorName,
                colorCode,
                images: currentImages
            };
        }, buttonInfo);
    }

    /**
     * 提取产品数据的主函数
     */
    async extractProductData(page) {
        console.log('🔍 开始提取产品数据...');

        return await page.evaluate(() => {
            const result = {
                productDetail: null,
                imageGroups: [],
                variationAttributes: null,
                variants: [],
                sizeChart: null,
                dataSources: []
            };

            try {
                // 尝试 __NEXT_DATA__
                if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.pageProps) {
                    const pageProps = window.__NEXT_DATA__.props.pageProps;
                    if (pageProps.productDetail) {
                        result.productDetail = pageProps.productDetail;
                        result.dataSources.push('next_data');
                    }
                }

                // 如果还没有productDetail，创建基础信息
                if (!result.productDetail) {
                    const title = document.querySelector('h1')?.textContent?.trim() ||
                                 document.querySelector('[class*="title"]')?.textContent?.trim() ||
                                 document.querySelector('[class*="name"]')?.textContent?.trim() || '';

                    // 增强的描述抓取
                    let description = '';

                    // 策略1: 查找常见的描述选择器
                    const descriptionSelectors = [
                        '[class*="description"]',
                        '[class*="detail"]',
                        '[class*="product"]',
                        '[class*="info"]',
                        '[class*="spec"]',
                        '[id*="description"]',
                        '[id*="detail"]',
                        'meta[name="description"]',
                        'meta[property="og:description"]'
                    ];

                    for (const selector of descriptionSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            const text = element.getAttribute('content') || element.textContent;
                            if (text && text.length > 50) {
                                description = text.trim();
                                console.log(`✓ 策略1成功 - 找到描述内容 (${selector}, ${text.length}字符)`);
                                break;
                            }
                        }
                    }

                    // 策略2: 如果没找到，查找包含特定关键词的段落
                    if (!description) {
                        console.log('🔍 策略2开始 - 搜索包含关键词的元素...');
                        const textElements = Array.from(document.querySelectorAll('p, div, span, section, article'));

                        for (const element of textElements) {
                            const text = element.textContent.trim();
                            if (text && text.length > 100 && (
                                text.includes('素材') ||
                                text.includes('MADE IN') ||
                                text.includes('バスト') ||
                                text.includes('着丈') ||
                                text.includes('ポリエステル') ||
                                text.includes('ストレッチ') ||
                                text.includes('デタッチャブル')
                            )) {
                                description = text;
                                console.log(`✓ 策略2成功 - 通过关键词找到描述内容 (${text.length}字符)`);
                                break;
                            }
                        }
                    }

                    // 策略3: 查找页面标题之外的较长文本
                    if (!description) {
                        console.log('🔍 策略3开始 - 提取页面长文本...');
                        const allText = document.body.textContent || '';
                        const title = document.querySelector('h1')?.textContent?.trim() || '';
                        const cleanText = allText.replace(title, '').replace(/\s+/g, ' ').trim();

                        if (cleanText.length > 200) {
                            description = cleanText.substring(0, 1000);
                            console.log(`✓ 策略3成功 - 使用页面文本 (${description.length}字符)`);
                        } else {
                            console.log('✗ 策略3失败 - 页面文本太短');
                        }
                    }

                    result.productDetail = {
                        name: title,
                        title: title,
                        longDescription: description,
                        description: description,
                        brand: 'Callaway Golf',
                        mainImage: ''
                    };
                }

                result.dataSources.push('dom_enhanced');

                // 提取尺码表
                const sizeSection = document.querySelector('#size .product-html');
                if (sizeSection) {
                    const sizeSectionHtml = sizeSection.innerHTML.trim();
                    const sizeSectionText = sizeSection.innerText
                        .replace(/\u00a0/g, ' ')
                        .replace(/\r\n/g, '\n')
                        .replace(/\r/g, '\n')
                        .replace(/\t/g, ' ')
                        .replace(/\s+\n/g, '\n')
                        .replace(/\n{2,}/g, '\n')
                        .trim();

                    if (sizeSectionText.length > 0) {
                        result.sizeSectionHtml = sizeSectionHtml;
                        result.sizeSectionText = sizeSectionText;
                    }
                }

                // 提取价格信息
                try {
                    const priceSelectors = [
                        '[data-testid="price"]',
                        '.price_wrapper span',
                        '.monica-translate-translate',
                        '.product-price',
                        '.price-value',
                        '[class*="price"]'
                    ];

                    let priceText = '';

                    for (const selector of priceSelectors) {
                        const priceElement = document.querySelector(selector);
                        if (priceElement) {
                            const text = priceElement.textContent.trim();
                            if (text && text.length > 0) {
                                priceText = text;
                                break;
                            }
                        }
                    }

                    if (priceText) {
                        result.productDetail.priceText = priceText;
                        result.productDetail.price = priceText;
                        result.currentPrice = priceText;
                        result.priceText = priceText;
                    }

                } catch (priceError) {
                    console.log('❌ 价格提取失败:', priceError.message);
                }

            } catch (error) {
                console.log('❌ 数据提取过程中发生错误:', error.message);
                result.dataSources.push('error_fallback');
            }

            return result;
        });
    }

    /**
     * 增强的尺码提取函数 - 使用下拉菜单方式
     */
    async extractSizesFromDropdown(page) {
        console.log('🎯 开始增强的尺码下拉菜单提取...');
        const extractedSizes = [];

        const primarySelectors = [
            'button[id^="headlessui-listbox-button"]',
            'button[aria-haspopup="listbox"]',
            '.size-selector button',
            '[data-testid*="size"] button'
        ];

        for (const selector of primarySelectors) {
            try {
                await page.waitForSelector(selector, { timeout: 2000 });
                const button = await page.$(selector);

                if (button) {
                    console.log(`📏 找到下拉按钮: ${selector}`);

                    await button.evaluate(el => el.scrollIntoView({ block: 'center' }));
                    await page.waitForTimeout(500);
                    await button.hover();
                    await page.waitForTimeout(300);

                    let clickAttempts = 0;
                    const maxAttempts = 3;

                    while (clickAttempts < maxAttempts && extractedSizes.length === 0) {
                        clickAttempts++;
                        console.log(`🖱️ 第 ${clickAttempts} 次点击尝试...`);

                        try {
                            await button.click();
                            console.log('⏳ 等待下拉列表出现...');

                            try {
                                await page.waitForSelector('ul[id^="headlessui-listbox-options"] li', {
                                    visible: true,
                                    timeout: 1500
                                });

                                const sizes = await page.evaluate(() => {
                                    const optionSelectors = [
                                        'ul[id^="headlessui-listbox-options"] li',
                                        '[role="option"]',
                                        'ul li[data-headlessui-state]'
                                    ];

                                    let foundOptions = [];
                                    for (const optSelector of optionSelectors) {
                                        const options = document.querySelectorAll(optSelector);
                                        if (options.length > 0) {
                                            foundOptions = Array.from(options);
                                            break;
                                        }
                                    }

                                    if (foundOptions.length > 0) {
                                        const sizes = [];
                                        foundOptions.forEach(option => {
                                            const sizeText = option.textContent?.trim();
                                            if (sizeText && !sizes.includes(sizeText)) {
                                                sizes.push(sizeText);
                                            }
                                        });
                                        return sizes;
                                    }
                                    return [];
                                });

                                if (sizes && sizes.length > 0) {
                                    extractedSizes.push(...sizes);
                                    console.log(`✅ 成功提取 ${sizes.length} 个尺码: ${sizes.join(', ')}`);
                                    break;
                                }

                            } catch (waitError) {
                                console.log('⚠️ 下拉列表未出现，继续尝试...');
                            }

                            if (clickAttempts < maxAttempts) {
                                await page.waitForTimeout(1000);
                            }

                        } catch (clickError) {
                            console.log(`⚠️ 点击失败: ${clickError.message}`);
                        }
                    }

                    if (extractedSizes.length > 0) {
                        console.log(`🎉 下拉菜单方式成功提取 ${extractedSizes.length} 个尺码`);
                        return extractedSizes;
                    }
                }

            } catch (error) {
                console.log(`⚠️ 选择器 "${selector}" 处理失败: ${error.message}`);
            }
        }

        console.log('❌ 所有下拉菜单尝试都失败了');
        return extractedSizes;
    }

    /**
     * 构建最终产品数据
     */
    buildFinalProductData(extractedData, productId, url, priceInfo = {}, dropdownSizes = []) {
        console.log('🔄 构建最终产品数据...');

        const startTime = Date.now();
        const productDetail = extractedData.productDetail || {};

        // 提取颜色信息
        const colors = [];
        const variants = [];
        const images = { product: [], variants: {} };

        // 优先使用多颜色抓取的数据
        if (extractedData.multiColorInfo && extractedData.multiColorInfo.colors.length > 0) {
            console.log(`✓ 使用多颜色抓取的${extractedData.multiColorInfo.colors.length}种颜色`);

            colors.push(...extractedData.multiColorInfo.colors);

            if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups)) {
                extractedData.imageGroups.forEach(group => {
                    const colorCode = group.colorCode || group.code;

                    if (group.images && Array.isArray(group.images)) {
                        images.variants[colorCode] = group.images;
                        images.product.push(...group.images);
                    }
                });
            }

            images.product = [...new Set(images.product)];
        }

        // 如果没有颜色，添加默认颜色
        if (colors.length === 0) {
            colors.push({ code: 'DEFAULT', name: 'DEFAULT' });
        }

        // 提取尺码信息
        const sizes = [];

        if (dropdownSizes && dropdownSizes.length > 0) {
            sizes.push(...dropdownSizes);
            console.log(`✅ 使用下拉菜单提取的尺码: ${sizes.join(', ')}`);
        } else if (extractedData.variationAttributes && extractedData.variationAttributes.size) {
            extractedData.variationAttributes.size.forEach(size => {
                sizes.push(size.value || size.name || size);
            });
            console.log(`✅ 从variationAttributes提取到 ${sizes.length} 个尺码`);
        }

        // 处理尺码表
        let sizeChart = { headers: [], rows: [] };
        if (extractedData.sizeChart) {
            sizeChart = extractedData.sizeChart;
        }

        const sizeSectionHtml = extractedData.sizeSectionHtml || '';
        const sizeSectionText = extractedData.sizeSectionText || '';

        // 生成颜色翻译文本
        const colorsCnText = this.generateColorsCnText(colors);

        // 构建最终数据结构
        const finalData = {
            scrapeInfo: {
                timestamp: new Date().toISOString(),
                version: "1.0.0",
                url: url,
                productId: productId,
                totalVariants: variants.length,
                totalColors: colors.length,
                totalSizes: sizes.length,
                totalImages: images.product.length,
                processingTimeMs: Date.now() - startTime,
                dataSources: extractedData.dataSources || []
            },

            product: {
                productId: productId,
                title: productDetail.name || productDetail.title || '',
                productUrl: url,
                description: productDetail.longDescription || productDetail.description || '',
                brand: productDetail.brand || 'Callaway Golf',
                category: '',
                tags: [],
                mainImage: productDetail.mainImage || (images.product.length > 0 ? images.product[0] : ''),
                detailUrl: url,
                sizeChart: sizeChart,
                sizeSectionHtml: sizeSectionHtml,
                sizeSectionText: sizeSectionText,
                currentPrice: priceInfo.currentPrice || null,
                originalPrice: priceInfo.originalPrice || null,
                priceText: priceInfo.priceText || ''
            },
            variants: variants,
            colors: colors,
            sizes: sizes,
            sizeChart: sizeChart,
            sizeSection: {
                text: sizeSectionText,
                html: sizeSectionHtml
            },
            images: images,
            colors_cn_text: colorsCnText,
            ossLinks: {
                productImages: [],
                variantImages: {}
            }
        };

        return finalData;
    }

    /**
     * 生成多行中文颜色文本
     */
    generateColorsCnText(colors) {
        if (!colors || colors.length === 0) {
            return '';
        }

        const colorLines = [];

        colors.forEach(color => {
            const englishName = color.name || '';
            const chineseName = this.translateColorNameInternal(englishName);

            if (chineseName) {
                colorLines.push(chineseName);
            } else if (englishName) {
                colorLines.push(englishName);
            }
        });

        return colorLines.join('\n');
    }

    /**
     * 颜色翻译函数
     */
    translateColorNameInternal(englishColor) {
        if (!englishColor) return '';

        const colorName = englishColor.trim();

        if (COLOR_NAME_TRANSLATION[colorName]) {
            return COLOR_NAME_TRANSLATION[colorName];
        }

        const lowerColorName = colorName.toLowerCase();
        for (const [english, chinese] of Object.entries(COLOR_NAME_TRANSLATION)) {
            if (lowerColorName.includes(english.toLowerCase())) {
                return chinese;
            }
        }

        return colorName;
    }

    /**
     * 转换为统一格式
     */
    convertToUnifiedFormat(finalData) {
        return {
            success: true,
            url: finalData.product.detailUrl,
            productId: finalData.product.productId,
            productName: finalData.product.title,
            price: finalData.product.priceText || finalData.product.currentPrice || '',
            gender: '',
            brand: finalData.product.brand,
            description: finalData.product.description,
            colors: finalData.colors,
            sizes: finalData.sizes,
            imageUrls: finalData.images.product,
            sizeChart: {
                success: !!finalData.sizeSection.text,
                text: finalData.sizeSection.text,
                html: finalData.sizeSection.html,
                method: 'callaway_scraper'
            },
            timestamp: finalData.scrapeInfo.timestamp,
            _scraper_info: {
                version: 'unified_callaway_v1.0',
                debug_mode: this.options.debug,
                size_chart_method: 'callaway_scraper',
                processing_time: finalData.scrapeInfo.processingTimeMs
            }
        };
    }
}

module.exports = UnifiedDetailScraper;
