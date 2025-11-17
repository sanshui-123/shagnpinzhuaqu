#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 简化抓取器
 * 专注于稳定性和基本数据提取
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

class LeCoqGolfScraper {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.results = [];
    }

    async scrape() {
        console.log('🚀 开始抓取 Le Coq Sportif Golf 数据...');
        console.log(`🌐 目标网站: ${this.baseUrl}`);

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            // 抓取男士系列（写死为 ds_apparel_m 路径）
            await this.scrapeCollection(
                browser,
                'mens',
                this.config.urls?.main ||
                    '/brand/le%2520coq%2520sportif%2520golf/ds_apparel_m?commercialType=0%7C2%7C3&groupByModel=1&currentPage=1&alignmentSequence=recommend_commodity_rank+asc'
            );

            // 抓取女士系列（写死为 ds_apparel_l 路径）
            await this.scrapeCollection(
                browser,
                'womens',
                this.config.urls?.womens ||
                    '/brand/le%2520coq%2520sportif%2520golf/ds_apparel_l?commercialType=0%7C2%7C3&currentPage=1&alignmentSequence=recommend_commodity_rank+asc&groupByModel=1'
            );

            return this.results;

        } catch (error) {
            console.error('❌ 抓取失败:', error);
            throw error;
        } finally {
            await browser.close();
        }
    }

    /**
     * 抓取指定系列（支持分页）
     */
    async scrapeCollection(browser, collectionType, url) {
        console.log(`\n👕 抓取${collectionType === 'mens' ? '男士' : '女士'}系列...`);

        const fullUrl = `${this.baseUrl}${url}`;
        console.log(`📄 访问页面: ${fullUrl}`);

        const page = await browser.newPage();
        let allProducts = [];
        let currentPage = 1;
        const maxPages = 10; // 安全限制，防止无限循环

        try {
            // 访问第一页
            await page.goto(fullUrl, {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });

            // 等待内容加载
            await page.waitForTimeout(5000);

            // 循环处理每一页
            while (currentPage <= maxPages) {
                console.log(`\n📖 正在处理第 ${currentPage} 页...`);

                // 调试：检查页面内容
                const pageTitle = await page.title();
                console.log(`📄 页面标题: ${pageTitle}`);

                // 检查页面是否有产品列表
                const hasProducts = await page.locator('.catalogList_item').count();
                console.log(`🔍 第${currentPage}页发现产品数量: ${hasProducts}`);

                if (hasProducts === 0) {
                    console.log(`⚠️ 第${currentPage}页没有产品，停止抓取`);
                    break;
                }

                // 🚀 借鉴卡拉威方案：添加本地Map去重机制
                if (currentPage === 1) {
                    // 第一页时初始化去重Map
                    this.productMap = new Map(); // key: productId, value: productInfo
                    this.uniqueProductIds = new Set();
                    console.log('🔄 初始化产品去重Map...');
                }

                // 提取当前页的产品数据
                const products = await page.evaluate(({collectionType, currentPage}) => {
                // 尝试多种产品容器选择器
                const containerSelectors = [
                    '.catalogList_item',
                    '.product-item',
                    '.item',
                    '[class*="item"]',
                    '[class*="product"]',
                    '.commodityItem',
                    '.catalog-item'
                ];

                let items = [];
                let usedSelector = '';

                for (const selector of containerSelectors) {
                    const foundItems = document.querySelectorAll(selector);
                    if (foundItems.length > 0) {
                        items = foundItems;
                        usedSelector = selector;
                        break;
                    }
                }

                if (items.length === 0) {
                    console.log(`⚠️ 未找到产品元素，页面可能已变化`);
                    return [];
                }

                console.log(`✅ 第${currentPage}页使用选择器 ${usedSelector} 找到 ${items.length} 个产品`);

                return Array.from(items).map((item, index) => {
                    try {
                        // 提取产品信息
                        const titleElement = item.querySelector('.commodityName');
                        const title = titleElement ? titleElement.textContent.trim() : '';

                        const brandElement = item.querySelector('.brandName');
                        const brand = brandElement ? brandElement.textContent.trim() : 'Le Coq Sportif Golf';

                        // 🚀 借鉴卡拉威：提取productId用于去重
                        const linkElement = item.querySelector('a[href*="/commodity/"]');
                        let productId = '';
                        if (linkElement) {
                            const href = linkElement.href;
                            const match = href.match(/\/([A-Z]\d+[A-Z\d]*)\/?$/);
                            productId = match ? match[1] : '';
                        }

                        // 尝试多种价格选择器
                        let price = '';
                        const priceSelectors = [
                            '.price',
                            '.price-current',
                            '.amount',
                            '.yen',
                            '.cost',
                            '.price1',
                            '.price2',
                            '.selling',
                            '.originalPrice',
                            '[class*="price"]',
                            '[class*="yen"]'
                        ];

                        for (const selector of priceSelectors) {
                            const priceElement = item.querySelector(selector);
                            if (priceElement && priceElement.textContent.trim()) {
                                price = priceElement.textContent.trim();
                                // 清理价格文本
                                price = price.replace(/[^\d￥,円]/g, '').trim();
                                if (price) break;
                            }
                        }

                        // 尝试多种图片选择器
                        let image = '';
                        const imageSelectors = [
                            '.catalogList_image img',
                            '.product-image img',
                            '.item-image img',
                            'img[src*="product"]',
                            'img[src*="item"]',
                            'img[src*="commodity"]',
                            'img[alt*="商品"]',
                            'img[alt*="product"]',
                            '.mainImage img',
                            '.thumbnail img'
                        ];

                        for (const selector of imageSelectors) {
                            const imageElement = item.querySelector(selector);
                            if (imageElement) {
                                image = imageElement.src || imageElement.dataset.src || imageElement.getAttribute('data-original') || '';
                                if (image && !image.includes('placeholder') && !image.includes('spacer')) {
                                    // 转换为绝对URL
                                    if (image.startsWith('//')) {
                                        image = 'https:' + image;
                                    } else if (image.startsWith('/')) {
                                        image = 'https://store.descente.co.jp' + image;
                                    }
                                    break;
                                }
                            }
                        }

                        const linkElement = item.querySelector('a[href]');
                        const url = linkElement ? linkElement.href : '';

                        // 提取徽章
                        const saleBadge = item.querySelector('.badgeSale');
                        const newBadge = item.querySelector('.badgeNew');

                        const badges = [];
                        if (saleBadge) badges.push('SALE');
                        if (newBadge) badges.push('NEW');

                        // 验证必要数据
                        if (!title || title.length < 2) {
                            return null;
                        }

                        return {
                            id: (currentPage - 1) * 100 + index + 1, // 基于页数计算唯一ID
                            productId: productId, // 🚀 借鉴卡拉威：添加productId用于去重
                            title: title,
                            brand: brand,
                            price: price,
                            image: image,
                            url: url,
                            category: collectionType === 'mens' ? '男性' : '女性',
                            badges: badges,
                            source: 'lecoqgolf',
                            scrapedAt: new Date().toISOString(),
                            page: currentPage // 记录页码
                        };

                    } catch (error) {
                        console.warn('产品提取错误:', error.message);
                        return null;
                    }
                }).filter(item => item !== null);

            }, {collectionType, currentPage});

                console.log(`✅ 第${currentPage}页提取到 ${products.length} 个产品`);

                // 🚀 借鉴卡拉威：去重逻辑
                let newItems = 0;
                let duplicateItems = 0;

                for (const product of products) {
                    if (!product.productId) {
                        // 没有productId的产品直接添加
                        allProducts.push(product);
                        newItems++;
                        continue;
                    }

                    const existingProduct = this.productMap.get(product.productId);
                    if (!existingProduct) {
                        // 新产品，添加到Map
                        this.productMap.set(product.productId, product);
                        allProducts.push(product);
                        newItems++;
                    } else {
                        // 重复产品，跳过
                        duplicateItems++;
                        console.log(`🔄 跳过重复产品: ${product.productId} - ${product.title}`);
                    }
                }

                console.log(`📊 第${currentPage}页统计: 新增 ${newItems} 个，重复 ${duplicateItems} 个`);

                // 检查是否需要继续翻页
                const hasNextPage = await this.checkNextPage(page, currentPage);

                if (!hasNextPage || currentPage >= maxPages) {
                    console.log(`📚 分页抓取完成，共处理 ${currentPage} 页`);
                    break;
                }

                // 点击下一页
                const success = await this.clickNextPage(page, currentPage + 1);
                if (!success) {
                    console.log(`❌ 无法翻转到第 ${currentPage + 1} 页，停止抓取`);
                    break;
                }

                currentPage++;

                // 等待新页面加载
                await page.waitForTimeout(3000);
            }

            console.log(`\n🎉 ${collectionType === 'mens' ? '男士' : '女士'}系列总计提取到 ${allProducts.length} 个产品`);

            if (allProducts.length > 0) {
                this.results.push({
                    collection: collectionType,
                    collectionName: collectionType === 'mens' ? '男士系列' : '女士系列',
                    url: fullUrl,
                    products: allProducts,
                    totalPages: currentPage,
                    timestamp: new Date().toISOString()
                });
            }

        } catch (error) {
            console.error(`❌ ${collectionType} 抓取失败:`, error.message);

            this.results.push({
                collection: collectionType,
                collectionName: collectionType === 'mens' ? '男士系列' : '女士系列',
                url: fullUrl,
                products: allProducts, // 即使出错也返回已抓取的产品
                error: error.message,
                totalPages: currentPage - 1,
                timestamp: new Date().toISOString()
            });

        } finally {
            await page.close();
        }
      }

    /**
     * 检查是否有下一页
     */
    async checkNextPage(page, currentPage) {
        try {
            // 查找分页导航
            const paginationSelectors = [
                '.pager_number a',
                '.pagination a',
                '.pageNav a',
                '[class*="pager"] a',
                '[class*="page"] a'
            ];

            for (const selector of paginationSelectors) {
                const pageLinks = await page.locator(selector).count();
                if (pageLinks > 0) {
                    // 检查是否存在当前页码+1的链接
                    const nextPageLink = page.locator(`text=${currentPage + 1}`);
                    if (await nextPageLink.count() > 0) {
                        console.log(`🔍 发现第 ${currentPage + 1} 页链接`);
                        return true;
                    }
                }
            }

            // 如果找不到明确的页码链接，检查"下一页"按钮
            const nextButtonSelectors = [
                '.pager_next a',
                '.next',
                '.pagination-next',
                '[class*="next"]'
            ];

            for (const selector of nextButtonSelectors) {
                const nextButton = page.locator(selector);
                if (await nextButton.count() > 0) {
                    const isEnabled = await nextButton.isEnabled();
                    if (isEnabled) {
                        console.log(`🔍 发现可用的下一页按钮`);
                        return true;
                    }
                }
            }

            console.log(`🔍 未找到下一页，当前为最后一页`);
            return false;

        } catch (error) {
            console.warn(`⚠️ 检查下一页时出错: ${error.message}`);
            return false;
        }
    }

    /**
     * 点击下一页
     */
    async clickNextPage(page, targetPage) {
        try {
            // 方法1：尝试点击具体页码（更精确的选择器）
            const pageLinkSelectors = [
                `.pager_number a:text('${targetPage}')`,
                `.pagination a:text('${targetPage}')`,
                `a[href*="currentPage=${targetPage}"]`,
                `[class*="pager"] a:text('${targetPage}')`,
                `[class*="page"] a:text('${targetPage}')`
            ];

            for (const selector of pageLinkSelectors) {
                const pageLink = page.locator(selector);
                if (await pageLink.count() > 0) {
                    await pageLink.first().click(); // 使用first()避免多匹配
                    console.log(`✅ 成功点击第 ${targetPage} 页 (选择器: ${selector})`);
                    return true;
                }
            }

            // 方法2：尝试点击下一页按钮
            const nextButtonSelectors = [
                '.pager_next a',
                '.next',
                '.pagination-next',
                '[class*="next"]'
            ];

            for (const selector of nextButtonSelectors) {
                const nextButton = page.locator(selector);
                if (await nextButton.count() > 0) {
                    const isEnabled = await nextButton.isEnabled();
                    if (isEnabled) {
                        await nextButton.click();
                        console.log(`✅ 成功点击下一页按钮`);
                        return true;
                    }
                }
            }

            console.log(`❌ 无法找到第 ${targetPage} 页的点击元素`);
            return false;

        } catch (error) {
            console.warn(`⚠️ 点击下一页时出错: ${error.message}`);
            return false;
        }
    }

    /**
     * 保存结果
     */
    async saveResults() {
        try {
            const outputPath = this.config.output.path;

            if (!fs.existsSync(outputPath)) {
                fs.mkdirSync(outputPath, { recursive: true });
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const outputFile = path.join(outputPath, `lecoqgolf_products_${timestamp}.json`);

            const totalProducts = this.results.reduce((sum, r) => sum + (r.products?.length || 0), 0);

            const outputData = {
                brand: 'Le Coq Sportif Golf',
                brandId: 'lecoqgolf',
                scrapeTime: new Date().toISOString(),
                baseUrl: this.baseUrl,
                totalProducts: totalProducts,
                totalCollections: this.results.length,
                status: totalProducts > 0 ? 'success' : 'no_products',
                results: this.results
            };

            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2));
            console.log(`💾 结果已保存: ${outputFile}`);
            console.log(`📊 总计抓取: ${totalProducts} 个产品`);

            return outputFile;

        } catch (error) {
            console.error('❌ 保存结果失败:', error.message);
            throw error;
        }
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const configPath = './config.json';

    if (!fs.existsSync(configPath)) {
        console.error('❌ 配置文件不存在:', configPath);
        process.exit(1);
    }

    try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        const scraper = new LeCoqGolfScraper(config);

        scraper.scrape()
            .then(() => scraper.saveResults())
            .then(() => console.log('✅ Le Coq Sportif Golf 抓取完成'))
            .catch(error => {
                console.error('❌ Le Coq Sportif Golf 抓取失败:', error);
                process.exit(1);
            });

    } catch (error) {
        console.error('❌ 配置文件解析失败:', error);
        process.exit(1);
    }
}

module.exports = LeCoqGolfScraper;
