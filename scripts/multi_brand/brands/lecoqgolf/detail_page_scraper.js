#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 详情页抓取器 - 针对飞书数据优化版
 * 根据用户要求优化数据提取规则
 */

const { chromium } = require('playwright');

class DetailPageScraper {
    constructor() {
        this.url = '';
        this.results = {};
    }

    async scrapeDetailPage(url) {
        this.url = url;
        console.log('🔍 开始抓取详情页:', url);

        const browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        try {
            // 访问页面
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });

            // 等待内容加载
            await page.waitForTimeout(5000);

            // 按照飞书要求提取数据
            this.results = {
                url: url,
                productCode: await this.extractProductCode(page),
                title: await this.extractTitle(page),
                brand: await this.extractBrand(page),
                price: await this.extractPrice(page),
                gender: await this.extractGender(page),
                colors: await this.extractColors(page),
                images: await this.extractImages(page),
                sizes: await this.extractSizes(page),
                inventoryStats: await this.extractInventoryStats(page),
                categories: await this.extractCategories(page),
                description: await this.extractDescription(page),
                scrapedAt: new Date().toISOString()
            };

            return this.results;

        } catch (error) {
            console.error('❌ 抓取失败:', error.message);
            throw error;
        } finally {
            await browser.close();
        }
    }

    async extractProductCode(page) {
        return await page.evaluate(() => {
            // 尝试多种方式提取商品编号
            const selectors = [
                '.productCode',
                '.commodityCode',
                '.itemCode',
                '[class*="code"]',
                '.code'
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const text = element.textContent.trim();
                    // 清理文本，只保留字母数字
                    const cleanCode = text.replace(/[^A-Z0-9]/gi, '');
                    if (cleanCode && cleanCode.length > 3) {
                        return cleanCode;
                    }
                }
            }

            // 从URL中提取商品编号 (如 LE1872EM012989)
            const urlMatch = window.location.pathname.match(/\/([A-Z0-9]+\/[A-Z0-9]+)\/?$/);
            if (urlMatch) {
                return urlMatch[1].replace('/', '');
            }

            return '';
        });
    }

    async extractTitle(page) {
        return await page.evaluate(() => {
            // 优先提取商品标题，而不是页面标题
            const selectors = [
                '.productName',
                '.commodityName',
                '.productTitle',
                'h1',
                '.product-name'
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const title = element.textContent.trim();
                    if (title && title.length > 5) {
                        return title;
                    }
                }
            }

            return document.title || '';
        });
    }

    async extractBrand(page) {
        return await page.evaluate(() => {
            const selectors = [
                '.brandName',
                '.brand',
                '[class*="brand"]'
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const brand = element.textContent.trim();
                    if (brand) {
                        return brand;
                    }
                }
            }

            return 'le coq sportif golf'; // 默认品牌
        });
    }

    async extractPrice(page) {
        return await page.evaluate(() => {
            const selectors = [
                '.price',
                '.price-current',
                '[class*="price"]',
                '.amount'
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const price = element.textContent.trim();
                    // 提取价格数字和货币符号
                    const priceMatch = price.match(/[￥¥$]\s*[\d,]+/);
                    if (priceMatch) {
                        return priceMatch[0];
                    }
                }
            }

            return '';
        });
    }

    async extractGender(page) {
        return await page.evaluate(() => {
            const url = window.location.href;
            const title = document.title.toLowerCase();
            const metaKeywords = document.querySelector('meta[name="keywords"]')?.content.toLowerCase() || '';

            // 多种方式判断性别
            const mensIndicators = ['mens', 'men\'s', 'メンズ', '男性', 'ds_m'];
            const womensIndicators = ['womens', 'women\'s', 'ウィメンズ', '女性', 'ds_f', 'ds_l'];

            // 检查URL
            if (mensIndicators.some(indicator => url.includes(indicator))) return '男性';
            if (womensIndicators.some(indicator => url.includes(indicator))) return '女性';

            // 检查标题
            if (mensIndicators.some(indicator => title.includes(indicator))) return '男性';
            if (womensIndicators.some(indicator => title.includes(indicator))) return '女性';

            // 检查关键词
            if (mensIndicators.some(indicator => metaKeywords.includes(indicator))) return '男性';
            if (womensIndicators.some(indicator => metaKeywords.includes(indicator))) return '女性';

            // 检查面包屑导航
            const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a');
            for (const breadcrumb of breadcrumbs) {
                const text = breadcrumb.textContent.toLowerCase();
                if (mensIndicators.some(indicator => text.includes(indicator))) return '男性';
                if (womensIndicators.some(indicator => text.includes(indicator))) return '女性';
            }

            return 'Unisex'; // 默认为中性
        });
    }

    async extractColors(page) {
        return await page.evaluate(() => {
            const colors = [];

            // 查找颜色选择器
            const colorSelectors = [
                '#color-selector .colorName',
                '.color-selector .colorName',
                '[class*="color"] .colorName',
                '.color-option',
                '[class*="color"]'
            ];

            let colorElements = [];
            for (const selector of colorSelectors) {
                colorElements = document.querySelectorAll(selector);
                if (colorElements.length > 0) break;
            }

            colorElements.forEach((element, index) => {
                const colorName = element.textContent.trim();
                if (colorName && !colors.includes(colorName)) {
                    colors.push({
                        name: colorName,
                        code: `COLOR_${index + 1}`,
                        isFirstColor: index === 0
                    });
                }
            });

            // 如果没有找到颜色元素，尝试从文本中提取
            if (colors.length === 0) {
                const colorPatterns = [
                    /ネイビー[^）]*/g,
                    /ブラック[^）]*/g,
                    /ブルー[^）]*/g,
                    /グレー[^）]*/g,
                    /ベージュ[^）]*/g,
                    /（[A-Z0-9]+）\s*[）〕]/g
                ];

                const bodyText = document.body.textContent;
                colorPatterns.forEach(pattern => {
                    const matches = bodyText.match(pattern);
                    if (matches) {
                        matches.forEach(match => {
                            const cleanColor = match.replace(/[（）〕\s]/g, '').trim();
                            if (cleanColor && !colors.find(c => c.name === cleanColor)) {
                                colors.push({
                                    name: cleanColor,
                                    code: cleanColor,
                                    isFirstColor: colors.length === 0
                                });
                            }
                        });
                    }
                });
            }

            return colors;
        });
    }

    async extractImages(page) {
        return await page.evaluate(() => {
            const images = {
                total: 0,
                urls: [],
                firstColorImages: [],
                otherColorsImages: []
            };

            // 查找所有商品图片
            const imgSelectors = [
                'img[src*="commodity_image"]',
                'img[src*="LE/LE"]',
                '.product-image img',
                '.mainImage img',
                '.thumbnail img'
            ];

            let allImages = [];
            imgSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el.src && !allImages.find(img => img.src === el.src)) {
                        allImages.push({
                            src: el.src,
                            alt: el.alt || ''
                        });
                    }
                });
            });

            // 筛选1100*1100尺寸的图片
            const sizeImages = allImages.filter(img => {
                return img.src.includes('_1100x1100_') ||
                       img.src.includes('_1100x1100.') ||
                       img.src.includes('1100x1100');
            });

            // 如果没有找到1100x1100的，尝试其他大尺寸
            if (sizeImages.length === 0) {
                const largeImages = allImages.filter(img => {
                    return img.src.includes('_l.') ||
                           img.src.includes('_large') ||
                           img.src.includes('_big');
                });
                sizeImages.push(...largeImages);
            }

            // 如果还是没有，使用所有图片
            if (sizeImages.length === 0) {
                sizeImages.push(...allImages);
            }

            // 分类图片：第一个颜色的所有图片，其他颜色的前6张
            const firstColorImages = sizeImages.slice(0, 6); // 默认前6张作为第一个颜色
            const otherColorsImages = sizeImages.slice(0, 6);  // 其他颜色也取前6张

            images.total = sizeImages.length;
            images.urls = sizeImages.map(img => img.src);
            images.firstColorImages = firstColorImages.map(img => img.src);
            images.otherColorsImages = otherColorsImages.map(img => img.src);

            return images;
        });
    }

    async extractSizes(page) {
        return await page.evaluate(() => {
            const sizes = [];

            // 查找尺码信息
            const sizeElements = document.querySelectorAll('[class*="size"], .size-option');

            // 简单的尺码模式匹配
            const sizePatterns = [/^[SML][L]*$/, /^[SML][L]?$/, /^[X][SML][L]*$/];

            sizeElements.forEach(element => {
                const text = element.textContent.trim();

                // 匹配标准尺码
                const sizeMatch = text.match(/[SML][L0-9]*/);
                if (sizeMatch) {
                    const size = sizeMatch[0];
                    if (!sizes.find(s => s.size === size)) {
                        // 检查库存状态
                        const hasStock = text.includes('あり') || text.includes('残りわずか');
                        const stockStatus = hasStock ? '有库存' : '无库存';

                        sizes.push({
                            size: size,
                            stockStatus: stockStatus,
                            canOrder: hasStock
                        });
                    }
                }
            });

            // 如果没有找到，尝试从文本中提取
            if (sizes.length === 0) {
                const standardSizes = ['S', 'M', 'L', 'LL', '3L'];
                const bodyText = document.body.textContent;

                standardSizes.forEach(size => {
                    const regex = new RegExp(size + '[^\\w]', 'i');
                    if (regex.test(bodyText)) {
                        sizes.push({
                            size: size,
                            stockStatus: '未知',
                            canOrder: true
                        });
                    }
                });
            }

            return sizes;
        });
    }

    async extractInventoryStats(page) {
        return await page.evaluate(() => {
            const stats = {
                totalSizes: 0,
                availableSizes: 0,
                soldOutSizes: 0,
                lowStockSizes: 0,
                stockPercentage: 0
            };

            // 统计各种库存状态
            const bodyText = document.body.textContent;

            // 计数有库存的尺寸
            const availableMatches = bodyText.match(/あり|残りわずか|○/g) || [];
            stats.availableSizes = availableMatches.length;

            // 计数缺货的尺寸
            const soldOutMatches = bodyText.match(/なし|✕/g) || [];
            stats.soldOutSizes = soldOutMatches.length;

            // 少量库存
            const lowStockMatches = bodyText.match(/残りわずか|△/g) || [];
            stats.lowStockSizes = lowStockMatches.length;

            stats.totalSizes = stats.availableSizes + stats.soldOutSizes;

            if (stats.totalSizes > 0) {
                stats.stockPercentage = Math.round((stats.availableSizes / stats.totalSizes) * 100);
            }

            return stats;
        });
    }

    async extractCategories(page) {
        return await page.evaluate(() => {
            const categories = [];

            // 面包屑导航
            const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a');
            breadcrumbs.forEach(el => {
                const text = el.textContent.trim();
                if (text && !categories.includes(text)) {
                    categories.push(text);
                }
            });

            return categories;
        });
    }

    async extractDescription(page) {
        return await page.evaluate(() => {
            const description = {
                features: [],
                materials: [],
                functions: []
            };

            // 提取商品描述
            const descElements = document.querySelectorAll('.description, .product-description, [class*="description"]');
            let fullText = '';

            descElements.forEach(el => {
                const text = el.textContent.trim();
                if (text) {
                    fullText += text + '\n';
                }
            });

            // 提取功能特性
            const featurePatterns = [
                /■([^■\n]+)/g,  // ■开头的特性
                /【([^】]+)】/g,  // 【】括号的内容
                /(HEAT NAVI|MOTION 3D|はっ水|防風|蓄熱保温|デタッチャブル|ストレッチ)/g
            ];

            featurePatterns.forEach(pattern => {
                const matches = fullText.match(pattern);
                if (matches) {
                    matches.forEach(match => {
                        const cleanFeature = match.replace(/[■【】]/g, '').trim();
                        if (cleanFeature && !description.features.includes(cleanFeature)) {
                            description.features.push(cleanFeature);
                        }
                    });
                }
            });

            // 提取材质信息
            const materialMatch = fullText.match(/素材[:：]([^\n]+)/);
            if (materialMatch) {
                description.materials = materialMatch[1].trim().split(/[、，]/).map(m => m.trim());
            }

            description.fullText = fullText.trim();

            return description;
        });
    }

    printResults() {
        console.log('\n=== 📊 优化版详情页抓取结果 ===\n');
        console.log('🔗 URL:', this.results.url);
        console.log('🏷️ 商品编号:', this.results.productCode);
        console.log('📝 标题:', this.results.title);
        console.log('🏷️ 品牌:', this.results.brand);
        console.log('👕 性别:', this.results.gender);
        console.log('💰 价格:', this.results.price);

        console.log('\n🎨 颜色信息:');
        this.results.colors.forEach((color, index) => {
            console.log(`  ${index + 1}. ${color.name} (${color.isFirstColor ? '首个颜色' : '其他颜色'})`);
        });

        console.log('\n🖼️ 图片统计:');
        console.log(`  总数: ${this.results.images.total}张`);
        console.log(`  首个颜色: ${this.results.images.firstColorImages.length}张`);
        console.log(`  其他颜色: ${this.results.images.otherColorsImages.length}张`);

        console.log('\n📏 尺码信息:');
        this.results.sizes.forEach((size, index) => {
            console.log(`  ${index + 1}. ${size.size} - ${size.stockStatus}`);
        });

        console.log('\n📦 库存统计:');
        console.log(JSON.stringify(this.results.inventoryStats, null, 2));

        console.log('\n🏷️ 分类信息:');
        this.results.categories.forEach((cat, index) => {
            console.log(`  ${index + 1}. ${cat}`);
        });

        console.log('\n⚡ 功能特性:');
        this.results.description.features.forEach((feature, index) => {
            console.log(`  ${index + 1}. ${feature}`);
        });
    }
}

// 运行测试
if (require.main === module) {
    const testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';
    const scraper = new DetailPageScraper();

    scraper.scrapeDetailPage(testUrl)
        .then(results => {
            scraper.results = results;
            scraper.printResults();

            // 保存结果到文件
            const fs = require('fs');
            const outputPath = './golf_content/lecoqgolf/';

            if (!fs.existsSync(outputPath)) {
                fs.mkdirSync(outputPath, { recursive: true });
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const outputFile = `${outputPath}detail_test_${timestamp}.json`;

            fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
            console.log(`\n💾 结果已保存: ${outputFile}`);
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
        });
}

module.exports = DetailPageScraper;