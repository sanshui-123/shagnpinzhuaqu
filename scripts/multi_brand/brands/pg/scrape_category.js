#!/usr/bin/env node

/**
 * PEARLY GATES 简化抓取器
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
        this.totalProductCount = null; // 从分页中提取的总商品数
    }

    async scrape() {
        console.log('🚀 开始抓取 PEARLY GATES 数据...');
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
        const maxPages = this.config.pagination?.maxPages || 15; // 从配置读取最大页数，默认15页

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

                // 检查页面是否有产品列表（支持 Boost 和通用选择器）
                const productSelectors = [
                    '.boost-sd__grid-item',
                    '.product-grid-item',
                    '.collection-grid-item',
                    'li.grid__item',
                    '.product-card'
                ];

                let hasProducts = 0;
                for (const selector of productSelectors) {
                    const count = await page.locator(selector).count();
                    if (count > 0) {
                        hasProducts = count;
                        console.log(`🔍 第${currentPage}页发现产品数量: ${hasProducts} (使用选择器: ${selector})`);
                        break;
                    }
                }

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
                // PEARLY GATES (Shopify + Boost) 产品容器选择器
                const containerSelectors = [
                    '.boost-sd__grid-item',      // Boost搜索网格（最优先）
                    '.product-grid-item',         // 通用产品网格
                    '.collection-grid-item',      // 集合网格
                    'li.grid__item',              // Shopify标准网格项
                    '.product-grid li',           // 产品网格中的列表项
                    '.card',                      // 卡片容器
                    '.product-card'               // 产品卡片
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
                        // === 商品链接 ===
                        const linkElement =
                            item.querySelector('a[href*="/products/"]') ||
                            item.querySelector('a[href*="mix.tokyo"]') ||
                            item.querySelector('a[href]') ||
                            item.closest('a[href]');

                        const url = linkElement ? linkElement.href : '';

                        // === 提取productId（Shopify格式）===
                        // Shopify URL格式: /products/product-handle
                        let productId = '';
                        if (url) {
                            const match = url.match(/\/products\/([^/?#]+)/);
                            productId = match ? match[1] : '';  // 例如: "polo-shirt-white"
                        }

                        // === 商品标题 ===
                        const titleElement =
                            item.querySelector('.product-title') ||
                            item.querySelector('.boost-sd__product-title') ||
                            item.querySelector('.card__title') ||
                            item.querySelector('.product-item__title') ||
                            item.querySelector('h3') ||
                            item.querySelector('h2') ||
                            (linkElement && (linkElement.querySelector('h3') || linkElement.querySelector('h2')));

                        let title = '';
                        if (titleElement) {
                            title = titleElement.getAttribute('title') || titleElement.textContent.trim();
                        } else if (linkElement) {
                            title = linkElement.getAttribute('title') || linkElement.textContent.trim();
                        }

                        const brand = 'PEARLY GATES';

                        // === 商品价格 ===
                        let price = '';
                        const priceSelectors = [
                            '.product-price',
                            '.price',
                            '.boost-sd__product-price',
                            '.card__price',
                            '[class*="price"]',
                            '[data-price]'
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

                        // === 商品图片 ===
                        let image = '';
                        const imageElement =
                            item.querySelector('img[alt][src]:not([src=""])') ||
                            item.querySelector('img[data-src]') ||
                            item.querySelector('img[data-original]') ||
                            item.querySelector('img[data-lazy]') ||
                            item.querySelector('img');

                        if (imageElement) {
                            image =
                                imageElement.getAttribute('src') ||
                                imageElement.getAttribute('data-src') ||
                                imageElement.getAttribute('data-original') ||
                                imageElement.getAttribute('data-lazy') ||
                                '';

                            // 转换为绝对URL
                            if (image && !image.includes('placeholder') && !image.includes('spacer')) {
                                if (image.startsWith('//')) {
                                    image = 'https:' + image;
                                } else if (image.startsWith('/')) {
                                    image = 'https://mix.tokyo' + image;
                                }
                            }
                        }

                        // === 提取徽章 ===
                        const saleBadge =
                            item.querySelector('.badge--sale') ||
                            item.querySelector('.product-badge--sale') ||
                            item.querySelector('[class*="sale"]') ||
                            item.querySelector('.on-sale');

                        const newBadge =
                            item.querySelector('.badge--new') ||
                            item.querySelector('.product-badge--new') ||
                            item.querySelector('[class*="new"]');

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
                            source: 'pg',
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
     * 检查是否有下一页（支持 Boost 分页组件）
     */
    async checkNextPage(page, currentPage) {
        try {
            // 🎯 优先检查 Boost 分页组件
            const boostPaginationExists = await page.locator('.boost-sd__pagination').count() > 0;

            if (boostPaginationExists) {
                console.log('🔍 检测到 Boost 分页组件');

                // 提取总商品数量（仅第一页时提取）
                if (currentPage === 1) {
                    const totalCountText = await page.locator('.boost-sd__product-count, .boost-sd__total-product, [class*="product-count"]').first().textContent().catch(() => '');
                    if (totalCountText) {
                        const match = totalCountText.match(/全?(\d+)件/);
                        if (match) {
                            const totalCount = parseInt(match[1]);
                            console.log(`📊 检测到总商品数量: ${totalCount} 件`);
                            this.totalProductCount = totalCount;
                        }
                    }
                }

                // 检查下一页按钮是否存在且可用
                const nextButtonSelectors = [
                    '.boost-sd__pagination-button--next:not(.boost-sd__pagination-button--disabled)',
                    '.boost-sd__pagination button[aria-label*="Next"]:not([disabled])',
                    '.boost-sd__pagination .boost-sd__pagination-button:last-child:not(.boost-sd__pagination-button--disabled)'
                ];

                for (const selector of nextButtonSelectors) {
                    const nextButton = page.locator(selector);
                    const count = await nextButton.count();
                    if (count > 0) {
                        console.log(`🔍 发现 Boost 下一页按钮 (${selector})`);
                        return true;
                    }
                }

                // 检查是否有下一页的页码按钮
                const nextPageNumber = page.locator(`.boost-sd__pagination-number:text("${currentPage + 1}")`);
                if (await nextPageNumber.count() > 0) {
                    console.log(`🔍 发现 Boost 第 ${currentPage + 1} 页按钮`);
                    return true;
                }

                console.log(`🔍 Boost 分页: 已到最后一页`);
                return false;
            }

            // 🔄 回退：通用分页选择器
            const paginationSelectors = [
                '.pagination a',
                '.pageNav a',
                '[class*="pager"] a',
                '[class*="page"] a'
            ];

            for (const selector of paginationSelectors) {
                const pageLinks = await page.locator(selector).count();
                if (pageLinks > 0) {
                    const nextPageLink = page.locator(`text=${currentPage + 1}`);
                    if (await nextPageLink.count() > 0) {
                        console.log(`🔍 发现第 ${currentPage + 1} 页链接`);
                        return true;
                    }
                }
            }

            // 检查通用"下一页"按钮
            const nextButtonSelectors = [
                '.next:not([disabled])',
                '.pagination-next:not([disabled])',
                '[class*="next"]:not([disabled])'
            ];

            for (const selector of nextButtonSelectors) {
                const nextButton = page.locator(selector);
                if (await nextButton.count() > 0) {
                    console.log(`🔍 发现可用的下一页按钮`);
                    return true;
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
     * 点击下一页（支持 Boost 分页组件）
     */
    async clickNextPage(page, targetPage) {
        try {
            // 🎯 优先尝试 Boost 分页组件
            const boostPaginationExists = await page.locator('.boost-sd__pagination').count() > 0;

            if (boostPaginationExists) {
                console.log(`🎯 使用 Boost 分页组件切换到第 ${targetPage} 页`);

                // 方法1：直接点击页码按钮
                const pageNumberSelectors = [
                    `.boost-sd__pagination-number:text("${targetPage}")`,
                    `.boost-sd__pagination button:text("${targetPage}")`,
                    `.boost-sd__pagination [data-page="${targetPage}"]`
                ];

                for (const selector of pageNumberSelectors) {
                    const pageButton = page.locator(selector);
                    if (await pageButton.count() > 0) {
                        await pageButton.first().click();
                        console.log(`✅ Boost: 点击第 ${targetPage} 页按钮成功`);
                        return true;
                    }
                }

                // 方法2：点击"下一页"按钮（如果页码不可见）
                const nextButtonSelectors = [
                    '.boost-sd__pagination-button--next:not(.boost-sd__pagination-button--disabled)',
                    '.boost-sd__pagination button[aria-label*="Next"]:not([disabled])',
                    '.boost-sd__pagination .boost-sd__pagination-button:last-child:not(.boost-sd__pagination-button--disabled)'
                ];

                for (const selector of nextButtonSelectors) {
                    const nextButton = page.locator(selector);
                    if (await nextButton.count() > 0) {
                        await nextButton.first().click();
                        console.log(`✅ Boost: 点击下一页按钮成功`);
                        return true;
                    }
                }

                console.log(`❌ Boost 分页: 无法找到可点击元素`);
                return false;
            }

            // 🔄 回退：通用分页选择器
            const pageLinkSelectors = [
                `.pagination a:text('${targetPage}')`,
                `a[href*="currentPage=${targetPage}"]`,
                `[class*="pager"] a:text('${targetPage}')`,
                `[class*="page"] a:text('${targetPage}')`
            ];

            for (const selector of pageLinkSelectors) {
                const pageLink = page.locator(selector);
                if (await pageLink.count() > 0) {
                    await pageLink.first().click();
                    console.log(`✅ 成功点击第 ${targetPage} 页 (选择器: ${selector})`);
                    return true;
                }
            }

            // 通用下一页按钮
            const nextButtonSelectors = [
                '.next:not([disabled])',
                '.pagination-next:not([disabled])',
                '[class*="next"]:not([disabled])'
            ];

            for (const selector of nextButtonSelectors) {
                const nextButton = page.locator(selector);
                if (await nextButton.count() > 0) {
                    await nextButton.click();
                    console.log(`✅ 成功点击下一页按钮`);
                    return true;
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
            const outputFile = path.join(outputPath, `pg_products_${timestamp}.json`);

            const totalProducts = this.results.reduce((sum, r) => sum + (r.products?.length || 0), 0);

            const outputData = {
                brand: 'PEARLY GATES',
                brandId: 'pg',
                scrapeTime: new Date().toISOString(),
                baseUrl: this.baseUrl,
                totalProducts: totalProducts,
                totalProductsFromPagination: this.totalProductCount, // 从分页显示提取的总数
                totalCollections: this.results.length,
                status: totalProducts > 0 ? 'success' : 'no_products',
                results: this.results
            };

            fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2));
            console.log(`💾 结果已保存: ${outputFile}`);
            console.log(`📊 总计抓取: ${totalProducts} 个产品`);

            if (this.totalProductCount) {
                console.log(`📈 网站显示总数: ${this.totalProductCount} 件商品`);
                const coverage = ((totalProducts / this.totalProductCount) * 100).toFixed(1);
                console.log(`📐 抓取覆盖率: ${coverage}%`);
            }

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
            .then(() => console.log('✅ PEARLY GATES 抓取完成'))
            .catch(error => {
                console.error('❌ PEARLY GATES 抓取失败:', error);
                process.exit(1);
            });

    } catch (error) {
        console.error('❌ 配置文件解析失败:', error);
        process.exit(1);
    }
}

module.exports = LeCoqGolfScraper;
