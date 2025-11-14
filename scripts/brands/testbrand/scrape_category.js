#!/usr/bin/env node

/**
 * testbrand 品牌专用抓取器
 * 基于统一模板，需要根据具体网站结构调整选择器
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class TestbrandScraper {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.results = [];
    }

    async scrape() {
        console.log('🚀 开始抓取 testbrand 数据...');

        const browser = await puppeteer.launch({
            headless: this.config.scraper.headless,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            const page = await browser.newPage();
            await page.setViewport(this.config.scraper.viewport);
            await page.setUserAgent(this.config.scraper.userAgent);

            // 抓取主页
            await this.scrapePage(page, '/');

            // 抓取分类页面
            for (const category of this.config.categories) {
                await this.scrapePage(page, `/${category}`);
            }

            return this.results;

        } catch (error) {
            console.error('抓取失败:', error);
            throw error;
        } finally {
            await browser.close();
        }
    }

    async scrapePage(page, path) {
        try {
            const url = `${this.baseUrl}${path}`;
            console.log(`📄 抓取页面: ${url}`);

            await page.goto(url, { waitUntil: 'networkidle2' });

            // 根据实际网站结构调整选择器
            const products = await page.evaluate((selectors) => {
                const items = document.querySelectorAll(selectors.productGrid);
                return Array.from(items).map(item => ({
                    name: item.querySelector(selectors.productName)?.textContent?.trim(),
                    url: item.querySelector(selectors.productUrl)?.href,
                    price: item.querySelector(selectors.productPrice)?.textContent?.trim(),
                    image: item.querySelector(selectors.productImage)?.src
                }));
            }, this.config.selectors);

            this.results.push({
                page: path,
                url: url,
                products: products.filter(p => p.name && p.url),
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error(`页面抓取失败 ${path}:`, error.message);
        }
    }

    async saveResults() {
        if (!fs.existsSync(this.config.output.path)) {
            fs.mkdirSync(this.config.output.path, { recursive: true });
        }

        const outputFile = path.join(this.config.output.path, this.config.output.filename);
        fs.writeFileSync(outputFile, JSON.stringify(this.results, null, 2));

        console.log(`💾 结果已保存: ${outputFile}`);
        return outputFile;
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
    const scraper = new TestbrandScraper(config);

    scraper.scrape()
        .then(() => scraper.saveResults())
        .then(() => console.log('✅ 抓取完成'))
        .catch(error => {
            console.error('❌ 抓取失败:', error);
            process.exit(1);
        });
}

module.exports = TestbrandScraper;
