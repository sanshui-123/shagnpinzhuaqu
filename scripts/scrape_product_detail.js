#!/usr/bin/env node

/**
 * CallawayJP 产品详情抓取脚本 - 精简版
 * 纯数据抓取，不含任何AI改写功能
 * 输出格式对齐 feishu_update/baseline/inputs/sample_product_details.json
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// 参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        url: null,
        productId: null,
        outputDir: 'CallawayJP/results'
    };

    for (let i = 0; i < args.length; i++) {
        switch(args[i]) {
            case '--url':
                options.url = args[++i];
                break;
            case '--product-id':
                options.productId = args[++i];
                break;
            case '--output-dir':
                options.outputDir = args[++i];
                break;
            case '--help':
                console.log(`
使用方法:
  node scrape_product_detail.js --url <产品URL> [选项]

参数:
  --url <url>              产品详情页URL (必需)
  --product-id <id>        产品ID (可选，从URL自动提取)
  --output-dir <path>      输出目录 (默认: CallawayJP/results)

示例:
  node scrape_product_detail.js --url "https://www.callawaygolf.jp/mens/tops/polo/C25128100_.html?pid=C25128100_0010_S"
                `);
                process.exit(0);
                break;
        }
    }

    if (!options.url) {
        console.error('错误: 需要提供 --url 参数');
        process.exit(1);
    }

    // 从URL自动提取productId
    if (!options.productId) {
        const match = options.url.match(/\/([A-Z]\d+)_\.html/);
        if (match) {
            options.productId = match[1];
        }
    }

    return options;
}

// 提取产品数据的主函数
async function extractProductData(page) {
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
            // 1. 优先尝试 __NEXT_DATA__
            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.pageProps) {
                console.log('✓ 找到 __NEXT_DATA__');
                const pageProps = window.__NEXT_DATA__.props.pageProps;
                if (pageProps.productDetail) {
                    result.productDetail = pageProps.productDetail;
                    result.dataSources.push('next_data');
                }
            }

            // 2. 搜索 __next_f 数据
            if (window.self && window.self.__next_f && Array.isArray(window.self.__next_f)) {
                console.log('🔍 正在搜索 __next_f 数据...');
                for (let i = 0; i < window.self.__next_f.length; i++) {
                    try {
                        const item = window.self.__next_f[i];
                        if (Array.isArray(item) && item.length > 1 && typeof item[1] === 'string') {
                            const jsonStr = item[1];
                            if (jsonStr.includes('productDetail') || jsonStr.includes('imageGroups')) {
                                const parsed = JSON.parse(jsonStr);
                                
                                // 递归查找productDetail
                                function findProductDetail(obj, path = '') {
                                    if (!obj || typeof obj !== 'object') return null;
                                    
                                    if (obj.productDetail) {
                                        console.log(`✓ 在 ${path} 找到 productDetail`);
                                        return obj.productDetail;
                                    }
                                    
                                    for (const [key, value] of Object.entries(obj)) {
                                        if (typeof value === 'object') {
                                            const found = findProductDetail(value, `${path}.${key}`);
                                            if (found) return found;
                                        }
                                    }
                                    return null;
                                }
                                
                                const foundDetail = findProductDetail(parsed, `__next_f[${i}]`);
                                if (foundDetail && !result.productDetail) {
                                    result.productDetail = foundDetail;
                                    result.dataSources.push('__next_f.productDetail');
                                }
                            }
                        }
                    } catch (e) {
                        // 忽略解析错误，继续下一个
                    }
                }
            }

            // 3. DOM数据提取策略 - 获取真实的颜色、图片、尺码
            console.log('🔍 开始DOM数据提取...');
            
            // 提取颜色选择器数据
            const colorElements = document.querySelectorAll('[data-color], [data-colorcode], .color-selector button, .variant-color');
            const extractedColors = [];
            const extractedImageGroups = [];
            
            // 尝试多种颜色选择器模式
            const colorSelectors = [
                '[data-color]',
                '[data-colorcode]', 
                '.color-selector button',
                '.variant-color',
                'button[class*="color"]',
                '[class*="swatch"]'
            ];
            
            console.log('🎨 搜索颜色选择器...');
            
            for (const selector of colorSelectors) {
                const elements = document.querySelectorAll(selector);
                console.log(`发现 ${elements.length} 个 ${selector} 元素`);
                
                elements.forEach((element, index) => {
                    const colorCode = element.getAttribute('data-color') || 
                                    element.getAttribute('data-colorcode') ||
                                    element.getAttribute('data-value') ||
                                    element.getAttribute('value') || 
                                    element.textContent?.trim();
                                    
                    const colorName = element.getAttribute('title') ||
                                    element.getAttribute('aria-label') ||
                                    element.textContent?.trim() ||
                                    colorCode;
                    
                    if (colorCode && colorName && !extractedColors.some(c => c.code === colorCode)) {
                        extractedColors.push({
                            code: colorCode,
                            name: colorName,
                            selector: selector
                        });
                        console.log(`✓ 找到颜色: ${colorName} (${colorCode})`);
                    }
                });
                
                if (extractedColors.length > 0) break; // 找到颜色就停止
            }
            
            // 提取尺码选择器数据
            const extractedSizes = [];
            const sizeSelectors = [
                '[data-size]',
                '.size-selector button',
                '.variant-size',
                'button[class*="size"]',
                'select[name*="size"] option',
                '[class*="size-option"]'
            ];
            
            console.log('📏 搜索尺码选择器...');
            
            for (const selector of sizeSelectors) {
                const elements = document.querySelectorAll(selector);
                console.log(`发现 ${elements.length} 个 ${selector} 元素`);
                
                elements.forEach(element => {
                    const sizeValue = element.getAttribute('data-size') ||
                                    element.getAttribute('data-value') ||
                                    element.getAttribute('value') ||
                                    element.textContent?.trim();
                    
                    if (sizeValue && !extractedSizes.includes(sizeValue)) {
                        extractedSizes.push(sizeValue);
                        console.log(`✓ 找到尺码: ${sizeValue}`);
                    }
                });
                
                if (extractedSizes.length > 0) break; // 找到尺码就停止
            }
            
            // 提取所有图片
            const allImages = [];
            const imageSelectors = [
                'img[src*="callawaygolf"]',
                'img[src*="webdamdb"]',
                '.product-images img',
                '.gallery img',
                '[class*="image"] img'
            ];
            
            console.log('🖼️ 搜索产品图片...');
            
            // 图片URL过滤函数 - 只保留1280尺寸商品图
            function isValidProductImage(imgSrc) {
                if (!imgSrc) return false;
                
                // 必须以指定格式开头
                const validPrefix = 'https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_';
                if (!imgSrc.startsWith(validPrefix)) {
                    return false;
                }
                
                // 排除追踪链接和缩略图
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
                console.log(`发现 ${images.length} 个 ${selector} 图片`);
                
                images.forEach(img => {
                    if (isValidProductImage(img.src) && !allImages.includes(img.src)) {
                        allImages.push(img.src);
                    }
                });
            }
            
            console.log(`✓ 总共提取到 ${allImages.length} 张过滤后的商品图`);
            
            // 构建imageGroups
            if (extractedColors.length > 0) {
                extractedColors.forEach(color => {
                    result.imageGroups.push({
                        colorCode: color.code,
                        colorName: color.name,
                        images: allImages // 为每个颜色分配所有图片
                    });
                });
            } else {
                // 没有颜色时创建默认组
                result.imageGroups.push({
                    colorCode: 'DEFAULT',
                    colorName: 'DEFAULT',
                    images: allImages
                });
            }
            
            // 构建variationAttributes
            if (extractedSizes.length > 0) {
                result.variationAttributes = {
                    size: extractedSizes.map(size => ({ value: size, name: size }))
                };
            }
            
            // 如果还没有productDetail，创建基础信息
            if (!result.productDetail) {
                const title = document.querySelector('h1')?.textContent?.trim() || 
                             document.querySelector('[class*="title"]')?.textContent?.trim() || 
                             document.querySelector('[class*="name"]')?.textContent?.trim() || '';
                
                const description = document.querySelector('[class*="description"]')?.textContent?.trim() || 
                                   document.querySelector('[class*="detail"]')?.textContent?.trim() || '';
                
                const mainImage = allImages.length > 0 ? allImages[0] : '';

                result.productDetail = {
                    name: title,
                    title: title,
                    longDescription: description,
                    description: description,
                    brand: 'Callaway Golf',
                    mainImage: mainImage
                };
            }
            
            result.dataSources.push('dom_enhanced');
            
            console.log(`✅ DOM提取完成: ${extractedColors.length}颜色, ${extractedSizes.length}尺码, ${allImages.length}图片`);

            // 4. 提取图片信息
            if (result.productDetail && result.productDetail.imageGroups) {
                result.imageGroups = result.productDetail.imageGroups;
            } else {
                // DOM回退 - 查找所有产品图片
                const images = Array.from(document.querySelectorAll('img[src*="callawaygolf"]'))
                    .map(img => img.src)
                    .filter(src => src && !src.includes('logo'));
                
                if (images.length > 0) {
                    result.imageGroups = [{
                        colorCode: 'DEFAULT',
                        images: images
                    }];
                }
            }

            // 5. 提取变体属性
            if (result.productDetail && result.productDetail.variationAttributes) {
                result.variationAttributes = result.productDetail.variationAttributes;
            }

            // 6. 提取尺码表
            if (result.productDetail && result.productDetail.sizeChart) {
                result.sizeChart = result.productDetail.sizeChart;
            }

        } catch (error) {
            console.log('❌ 数据提取过程中发生错误:', error.message);
            result.dataSources.push('error_fallback');
        }

        return result;
    });
}

// 构建最终产品数据
function buildFinalProductData(extractedData, productId, url) {
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
        
        // 使用多颜色抓取的结果
        colors.push(...extractedData.multiColorInfo.colors);
        
        // 处理imageGroups数据
        if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups)) {
            extractedData.imageGroups.forEach(group => {
                const colorCode = group.colorCode || group.code;
                
                if (group.images && Array.isArray(group.images)) {
                    images.variants[colorCode] = group.images;
                    images.product.push(...group.images);
                }
                
                console.log(`✓ 颜色 ${group.colorName} (${colorCode}): ${group.images?.length || 0}张图片`);
            });
        }
        
        // 去重product图片
        images.product = [...new Set(images.product)];
        
    } else if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups) && extractedData.imageGroups.length > 0) {
        console.log(`✓ 使用DOM提取的${extractedData.imageGroups.length}个颜色组`);
        
        extractedData.imageGroups.forEach(group => {
            const colorCode = group.colorCode || group.code || 'DEFAULT';
            const colorName = group.colorName || group.name || 'DEFAULT';
            
            // 只添加非DEFAULT的真实颜色
            if (colorCode !== 'DEFAULT' || colors.length === 0) {
                colors.push({
                    code: colorCode,
                    name: colorName
                });
                
                if (group.images && Array.isArray(group.images)) {
                    images.variants[colorCode] = group.images;
                    images.product.push(...group.images);
                }
                
                console.log(`✓ 添加颜色: ${colorName} (${colorCode}), ${group.images?.length || 0}张图片`);
            }
        });
    }
    
    // 如果DOM提取失败，尝试从URL和页面内容推断
    if (colors.length === 0 || colors.every(c => c.code === 'DEFAULT')) {
        console.log('🔍 DOM提取颜色失败，尝试从URL和页面内容推断...');
        
        const pageContent = (productDetail.longDescription || productDetail.description || '').toLowerCase();
        const urlContent = url.toLowerCase();
        
        // CallawayJP常见颜色关键词
        const commonColors = [
            { keywords: ['navy', 'ネイビー', '1031'], name: 'ネイビー', code: '1031' },
            { keywords: ['black', 'ブラック', '1040'], name: 'ブラック', code: '1040' },
            { keywords: ['white', 'ホワイト', '1000'], name: 'ホワイト', code: '1000' },
            { keywords: ['red', 'レッド', '1600'], name: 'レッド', code: '1600' },
            { keywords: ['blue', 'ブルー', '1030'], name: 'ブルー', code: '1030' },
            { keywords: ['gray', 'grey', 'グレー', '1900'], name: 'グレー', code: '1900' }
        ];
        
        const inferredColors = [];
        commonColors.forEach(color => {
            const found = color.keywords.some(keyword => 
                pageContent.includes(keyword) || urlContent.includes(keyword)
            );
            if (found) {
                inferredColors.push({
                    code: color.code,
                    name: color.name
                });
            }
        });
        
        if (inferredColors.length > 0) {
            console.log('✓ 推断出颜色:', inferredColors.map(c => c.name));
            colors.length = 0; // 清空原有的DEFAULT颜色
            colors.push(...inferredColors);
            
            // 更新images.variants以使用推断出的颜色
            if (images.product.length > 0) {
                images.variants = {};
                inferredColors.forEach(color => {
                    images.variants[color.code] = images.product;
                });
            }
        } else {
            console.log('❌ 推断颜色也失败，使用DEFAULT');
            // 确保至少有一个DEFAULT颜色
            if (colors.length === 0) {
                colors.push({ code: 'DEFAULT', name: 'DEFAULT' });
            }
        }
    } else {
        console.log(`✅ 成功提取到 ${colors.length} 种真实颜色: ${colors.map(c => c.name).join(', ')}`);
    }
    
    // 提取尺码信息
    const sizes = [];
    if (extractedData.variationAttributes && extractedData.variationAttributes.size) {
        extractedData.variationAttributes.size.forEach(size => {
            sizes.push(size.value || size.name || size);
        });
    } else {
        // 默认尺码
        sizes.push('S', 'M', 'L', 'LL');
    }
    
    // 生成变体（颜色×尺码笛卡尔积）
    if (colors.length > 0 && sizes.length > 0) {
        colors.forEach(color => {
            sizes.forEach(size => {
                variants.push({
                    variantId: `${productId}_${color.code}_${size}`,
                    colorName: color.name,
                    colorCode: color.code,
                    sizeName: size,
                    sizeCode: size,
                    availability: 'unknown',
                    sku: `${productId}_${color.code}_${size}`,
                    priceJPY: null
                });
            });
        });
    }
    
    // 处理尺码表
    let sizeChart = { headers: [], rows: [] };
    if (extractedData.sizeChart) {
        sizeChart = extractedData.sizeChart;
    }
    
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
            sizeChart: sizeChart
        },
        variants: variants,
        colors: colors,
        sizes: sizes,
        sizeChart: sizeChart,
        images: images,
        ossLinks: {
            productImages: [],
            variantImages: {}
        }
    };
    
    return finalData;
}

// 主函数
async function main() {
    const options = parseArgs();
    const startTime = Date.now();
    
    console.log('🚀 开始抓取产品详情...');
    console.log(`📍 URL: ${options.url}`);
    console.log(`🏷️  产品ID: ${options.productId}`);
    
    let browser = null;
    
    try {
        // 启动浏览器
        console.log('🌐 启动浏览器...');
        browser = await chromium.launch({
            headless: true,
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
        let pageLoaded = false;
        let attempts = 0;
        const maxAttempts = 3;
        
        while (!pageLoaded && attempts < maxAttempts) {
            attempts++;
            try {
                console.log(`🔄 尝试加载页面 (第${attempts}/${maxAttempts}次)...`);
                await page.goto(options.url, { 
                    waitUntil: 'domcontentloaded',  // 改为domcontentloaded策略
                    timeout: 120000  // 调整超时时间到120秒
                });
                
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
        
        // 首先进行多颜色抓取
        const multiColorData = await extractMultiColorData(page);
        
        // 提取产品数据
        const extractedData = await extractProductData(page);
        
        // 将多颜色数据合并到extractedData中
        if (multiColorData.colors.length > 0) {
            console.log(`🎨 使用多颜色抓取结果: ${multiColorData.colors.length}种颜色`);
            extractedData.imageGroups = multiColorData.imageGroups;
            extractedData.multiColorInfo = {
                colors: multiColorData.colors,
                totalImages: multiColorData.allImages.size
            };
        }
        
        // 构建最终数据
        const finalData = buildFinalProductData(extractedData, options.productId, options.url);
        
        // 确保输出目录存在
        if (!fs.existsSync(options.outputDir)) {
            fs.mkdirSync(options.outputDir, { recursive: true });
        }
        
        // 生成输出文件名
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputFile = path.join(options.outputDir, `product_details_${options.productId}_${timestamp}.json`);
        
        // 写入文件
        fs.writeFileSync(outputFile, JSON.stringify(finalData, null, 2), 'utf8');
        
        console.log('✅ 抓取完成!');
        console.log(`📁 输出文件: ${outputFile}`);
        console.log(`⏱️  处理时间: ${Date.now() - startTime}ms`);
        console.log(`📊 统计信息:`);
        console.log(`   - 变体数量: ${finalData.scrapeInfo.totalVariants}`);
        console.log(`   - 颜色数量: ${finalData.scrapeInfo.totalColors}`);
        console.log(`   - 尺码数量: ${finalData.scrapeInfo.totalSizes}`);
        console.log(`   - 图片数量: ${finalData.scrapeInfo.totalImages}`);
        console.log(`   - 数据来源: ${finalData.scrapeInfo.dataSources.join(', ')}`);
        
    } catch (error) {
        console.error('❌ 抓取失败:', error.message);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// 运行脚本
if (require.main === module) {
    main().catch(console.error);
}

// 多颜色抓取函数
async function extractMultiColorData(page) {
    console.log('🎨 开始多颜色抓取...');
    
    const multiColorData = {
        colors: [],
        imageGroups: [],
        allImages: new Set() // 用于去重
    };
    
    try {
        // 定位颜色按钮容器
        console.log('🔍 定位颜色按钮容器...');
        
        // 尝试多种可能的颜色按钮选择器
        const colorButtonSelectors = [
            '.d_flex.items_center.gap_2\\.5.flex_row.flex-wrap_wrap button',
            '[class*="d_flex"][class*="items_center"][class*="gap_2.5"] button',
            '[class*="color"] button',
            'button[aria-label*="色"]',
            'button[title*="色"]',
            '.variant-selector button',
            '.color-selector button'
        ];
        
        let colorButtons = [];
        
        for (const selector of colorButtonSelectors) {
            try {
                const buttons = await page.$$(selector);
                if (buttons.length > 0) {
                    console.log(`✓ 找到 ${buttons.length} 个颜色按钮 (${selector})`);
                    colorButtons = buttons;
                    break;
                }
            } catch (error) {
                console.log(`尝试选择器失败: ${selector}`);
            }
        }
        
        if (colorButtons.length === 0) {
            console.log('⚠️ 未找到颜色按钮，尝试通过文本查找...');
            
            // 通过文本内容查找可能的颜色按钮
            const allButtons = await page.$$('button');
            for (const button of allButtons) {
                try {
                    const text = await button.textContent();
                    const ariaLabel = await button.getAttribute('aria-label');
                    const title = await button.getAttribute('title');
                    
                    const content = `${text} ${ariaLabel || ''} ${title || ''}`.toLowerCase();
                    
                    // 检查是否包含颜色相关的日文词汇
                    if (content.includes('ネイビー') || content.includes('ブラック') || 
                        content.includes('ホワイト') || content.includes('ブルー') ||
                        content.includes('レッド') || content.includes('グレー') ||
                        content.includes('navy') || content.includes('black') ||
                        content.includes('white') || content.includes('blue')) {
                        colorButtons.push(button);
                    }
                } catch (e) {
                    // 跳过无法读取的按钮
                }
            }
            
            console.log(`✓ 通过文本找到 ${colorButtons.length} 个可能的颜色按钮`);
        }
        
        if (colorButtons.length === 0) {
            console.log('❌ 未找到任何颜色按钮，使用单颜色模式');
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
                
                // 等待页面更新 - 图片切换完成
                console.log('⏳ 等待页面更新...');
                await page.waitForTimeout(2000); // 等待2秒让图片加载
                
                // 尝试等待图片容器更新
                try {
                    await page.waitForFunction(() => {
                        const images = document.querySelectorAll('img[src*="callawaygolf"], img[src*="webdamdb"]');
                        return images.length > 0;
                    }, { timeout: 5000 });
                } catch (e) {
                    console.log('图片加载等待超时，继续执行...');
                }
                
                // 提取当前颜色信息
                const currentColorData = await page.evaluate((buttonInfo) => {
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
                        
                        // 必须以指定格式开头
                        const validPrefix = 'https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_';
                        if (!imgSrc.startsWith(validPrefix)) {
                            return false;
                        }
                        
                        // 排除追踪链接和缩略图
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
                }, {
                    text: buttonText,
                    ariaLabel,
                    title,
                    dataValue,
                    dataColor
                });
                
                console.log(`✓ 提取颜色: ${currentColorData.colorName} (${currentColorData.colorCode}), ${currentColorData.images.length}张图片`);
                
                // 实施图片保留策略：第一个颜色保留全部图片，其余颜色只保留前6张
                let finalImages = currentColorData.images;
                if (i === 0) {
                    // 第一个颜色：保留全部图片
                    console.log(`   📌 第一个颜色，保留全部 ${finalImages.length} 张图片`);
                } else {
                    // 其余颜色：只保留前6张
                    finalImages = currentColorData.images.slice(0, 6);
                    console.log(`   ✂️  非第一颜色，裁剪为前 6 张图片 (原${currentColorData.images.length}张 → ${finalImages.length}张)`);
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

module.exports = {
    extractProductData,
    buildFinalProductData,
    extractMultiColorData,
    main
};