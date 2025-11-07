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

            // 3. DOM回退策略 - 提取基础信息
            if (!result.productDetail) {
                console.log('⚠️ 未找到 productDetail，使用 DOM 回退策略');
                
                // 提取基础产品信息
                const title = document.querySelector('h1')?.textContent?.trim() || 
                             document.querySelector('[class*="title"]')?.textContent?.trim() || 
                             document.querySelector('[class*="name"]')?.textContent?.trim() || '';
                
                const description = document.querySelector('[class*="description"]')?.textContent?.trim() || 
                                   document.querySelector('[class*="detail"]')?.textContent?.trim() || '';
                
                // 查找主图
                const mainImageElement = document.querySelector('img[class*="main"]') || 
                                        document.querySelector('img[class*="product"]') ||
                                        document.querySelector('.product-image img') ||
                                        document.querySelector('img[src*="callawaygolf"]');
                const mainImage = mainImageElement ? mainImageElement.src : '';

                result.productDetail = {
                    name: title,
                    title: title,
                    longDescription: description,
                    description: description,
                    brand: 'Callaway Golf',
                    mainImage: mainImage
                };
                result.dataSources.push('dom_enhanced');
            }

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
    
    if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups)) {
        extractedData.imageGroups.forEach(group => {
            const colorCode = group.colorCode || group.code || 'DEFAULT';
            const colorName = group.colorName || group.name || 'DEFAULT';
            
            colors.push({
                code: colorCode,
                name: colorName
            });
            
            if (group.images && Array.isArray(group.images)) {
                images.variants[colorCode] = group.images;
                images.product.push(...group.images);
            }
        });
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
            args: ['--no-sandbox', '--disable-setuid-sandbox']
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
        
        // 提取产品数据
        const extractedData = await extractProductData(page);
        
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

module.exports = {
    extractProductData,
    buildFinalProductData,
    main
};