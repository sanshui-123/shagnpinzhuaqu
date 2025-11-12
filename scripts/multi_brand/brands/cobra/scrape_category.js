#!/usr/bin/env node

/**
 * Cobra Golf 专用抓取器
 * 基于统一模板，根据具体网站结构调整选择器
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class CobraScraper {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.results = [];
        this.concurrencyLimit = config.constraints?.maxConcurrentPages || 3;
    }

    async scrape() {
        console.log('🚀 开始抓取 Cobra Golf 数据...');

        const browser = await puppeteer.launch({
            headless: this.config.scraper.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas'
            ]
        });

        try {
            // 抓取主页
            await this.scrapePage(browser, '/');

            // 抓取分类页面（并发控制）
            const categories = this.config.categories || [];
            for (let i = 0; i < categories.length; i += this.concurrencyLimit) {
                const batch = categories.slice(i, i + this.concurrencyLimit);

                const promises = batch.map(category =>
                    this.scrapePage(browser, `/${category}`).catch(err => {
                        console.warn(`⚠️ 分类 ${category} 抓取失败:`, err.message);
                        return null;
                    })
                );

                await Promise.all(promises);

                // 批次间延迟
                if (i + this.concurrencyLimit < categories.length) {
                    await this.delay(this.config.constraints?.requestDelay || 2000);
                }
            }

            return this.results;

        } catch (error) {
            console.error('抓取失败:', error);
            throw error;
        } finally {
            await browser.close();
        }
    }

    async scrapePage(browser, pagePath) {
        const page = await browser.newPage();
        const url = `${this.baseUrl}${pagePath}`;

        try {
            console.log(`📄 抓取页面: ${url}`);

            await page.setViewport(this.config.scraper.viewport);
            await page.setUserAgent(this.config.scraper.userAgent);
            await page.setDefaultTimeout(this.config.scraper.timeout);

            await page.goto(url, {
                waitUntil: 'networkidle2',
                timeout: this.config.scraper.timeout
            });

            // 等待内容加载
            await this.waitForContent(page);

            // 提取数据
            const products = await this.extractProducts(page);

            if (products.length > 0) {
                console.log(`✅ 页面 ${pagePath} 提取到 ${products.length} 个产品`);

                this.results.push({
                    page: pagePath,
                    url: url,
                    products: products,
                    timestamp: new Date().toISOString()
                });
            } else {
                console.warn(`⚠️ 页面 ${pagePath} 未找到产品`);
            }

        } catch (error) {
            console.error(`❌ 页面抓取失败 ${pagePath}:`, error.message);
            throw error;
        } finally {
            await page.close();
        }
    }

    async waitForContent(page) {
        try {
            // 等待主要内容容器
            const selectors = ['.product-grid', '.products-container', '.items-grid'];

            for (const selector of selectors) {
                try {
                    await page.waitForSelector(selector, { timeout: 5000 });
                    break;
                } catch (e) {
                    // 继续尝试下一个选择器
                }
            }

            // 等待图片加载
            await page.evaluate(() => {
                const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
                images.forEach(img => {
                    if (img.dataset.src) img.src = img.dataset.src;
                    if (img.loading === 'lazy') img.loading = 'eager';
                });
            });

            await page.waitForTimeout(2000);

        } catch (error) {
            console.warn('⚠️ 内容等待超时，继续执行');
        }
    }

    async extractProducts(page) {
        try {
            const products = await page.evaluate((config) => {
                // 多种可能的产品容器选择器
                const containerSelectors = config.selectors.productGrid.split(', ');
                let items = [];

                // 尝试不同的容器选择器
                for (const selector of containerSelectors) {
                    items = document.querySelectorAll(selector);
                    if (items.length > 0) break;
                }

                // 如果还是没找到，尝试通用选择器
                if (items.length === 0) {
                    const genericSelectors = [
                        '.product-item', '.product-card', '.item-card',
                        '.product', .item', '[data-product]'
                    ];

                    for (const selector of genericSelectors) {
                        items = document.querySelectorAll(selector);
                        if (items.length > 0) break;
                    }
                }

                return Array.from(items).map((item, index) => {
                    // 提取产品信息
                    const titleSelectors = config.selectors.productName.split(', ');
                    let title = '';

                    for (const selector of titleSelectors) {
                        const element = item.querySelector(selector);
                        if (element) {
                            title = element.textContent?.trim() || element.title?.trim() || '';
                            if (title) break;
                        }
                    }

                    // 提取URL
                    const linkElement = item.querySelector('a[href]');
                    const url = linkElement ? linkElement.href : '';

                    // 提取价格
                    const priceSelectors = config.selectors.productPrice.split(', ');
                    let price = '';

                    for (const selector of priceSelectors) {
                        const element = item.querySelector(selector);
                        if (element) {
                            price = element.textContent?.trim() || '';
                            if (price) break;
                        }
                    }

                    // 提取图片
                    const imageElement = item.querySelector('img');
                    const image = imageElement ?
                        (imageElement.src || imageElement.dataset.src || imageElement.dataset.lazy) : '';

                    // 提取分类
                    const categoryElement = item.querySelector(config.selectors.productCategory);
                    const category = categoryElement ? categoryElement.textContent.trim() : '';

                    // 过滤无效数据
                    if (!title || title.length < 2) return null;

                    return {
                        id: index + 1,
                        title: title,
                        url: url,
                        price: price,
                        image: image,
                        category: category,
                        brand: 'Cobra Golf',
                        sourceUrl: window.location.href,
                        scrapedAt: new Date().toISOString()
                    };
                }).filter(item => item !== null); // 移除无效项

            }, this.config);

            return products;

        } catch (error) {
            console.error('❌ 产品提取失败:', error.message);
            return [];
        }
    }

    async saveResults() {
        const outputPath = this.config.output.path;

        if (!fs.existsSync(outputPath)) {
            fs.mkdirSync(outputPath, { recursive: true });
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputFile = path.join(outputPath, `cobra_products_${timestamp}.json`);

        const outputData = {
            brand: 'Cobra Golf',
            brandId: 'cobra',
            scrapeTime: new Date().toISOString(),
            totalProducts: this.results.reduce((sum, page) => sum + page.products.length, 0),
            pagesScraped: this.results.length,
            results: this.results
        };

        fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2));
        console.log(`💾 结果已保存: ${outputFile}`);

        return outputFile;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const configPath = './config.json';

    if (!fs.existsSync(configPath)) {
        console.error('❌ 配置文件不存在:', configPath);
        process.exit(1);
    }

    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    const scraper = new CobraScraper(config);

    scraper.scrape()
        .then(() => scraper.saveResults())
        .then(() => console.log('✅ Cobra Golf 抓取完成'))
        .catch(error => {
            console.error('❌ Cobra Golf 抓取失败:', error);
            process.exit(1);
        });
}

module.exports = CobraScraper;
