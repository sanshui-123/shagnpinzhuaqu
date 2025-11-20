#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 数据抓取器
 * 阶段1: 纯数据抓取 - 不做任何数据处理
 * 输出标准化的原始数据格式，供universal_field_processor.js处理
 */

const puppeteer = require('puppeteer');

class LeCoqGolfDataScraper {
    constructor() {
        this.brand = 'le coq sportif golf';
    }

    /**
     * 抓取单个产品的原始数据
     * 只负责抓取，不做任何处理和判断
     */
    async scrapeProductData(url) {
        console.log(`🔍 开始抓取数据: ${url}`);

        const browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            const page = await browser.newPage();
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

            // 等待页面加载
            await page.waitForSelector('body', { timeout: 10000 });

            // 抓取所有原始数据
            const rawData = await page.evaluate(() => {
                return {
                    // 基础信息
                    url: window.location.href,
                    title: document.title,

                    // 商品信息
                    productCode: document.querySelector('[name*="itemCode"], [data-item-code]')?.textContent?.trim() || '',
                    originalPrice: document.querySelector('.price, [class*="price"]')?.textContent?.trim() || '',
                    brand: document.querySelector('[class*="brand"], .brand')?.textContent?.trim() || '',

                    // 图片数据 - 原始抓取，不做处理
                    images: {
                        all: Array.from(document.querySelectorAll('img')).map(img => ({
                            src: img.src,
                            alt: img.alt,
                            class: img.className
                        })).filter(img => img.src && (img.src.includes('jpg') || img.src.includes('jpeg') || img.src.includes('png'))),
                        productImages: Array.from(document.querySelectorAll('img[src*="LE/LE"], img[src*="commodity_image"]')).map(img => img.src)
                    },

                    // 颜色数据 - 原始抓取
                    colors: Array.from(document.querySelectorAll('[class*="color"], [class*="variation"]')).map(el => ({
                        name: el.textContent?.trim() || '',
                        value: el.value || '',
                        selected: el.classList.contains('selected') || el.selected
                    })),

                    // 尺码数据 - 原始抓取
                    sizes: Array.from(document.querySelectorAll('[class*="size"], [class*="size-option"]')).map(el => ({
                        size: el.textContent?.trim() || '',
                        value: el.value || '',
                        available: !el.classList.contains('unavailable') && !el.disabled
                    })),

                    // 分类信息 - 原始抓取
                    categories: Array.from(document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a, .breadcrumb li')).map(el => el.textContent?.trim()),

                    // 描述信息 - 原始抓取
                    description: document.querySelector('[class*="description"], .product-description')?.innerHTML || '',
                    detailText: document.querySelector('[class*="detail"], .product-detail')?.textContent?.trim() || '',

                    // 尺码表 - 完整原始HTML和文本
                    sizeChart: {
                        html: document.querySelector('.size-chart, [class*="size-table"], [class*="size"] table')?.outerHTML || '',
                        text: document.querySelector('.size-chart, [class*="size-table"], [class*="size"] table')?.textContent?.trim() || ''
                    }
                };
            });

            console.log(`✅ 抓取完成，获得原始数据`);
            return {
                brand: this.brand,
                scrapeTime: new Date().toISOString(),
                url: url,
                rawData: rawData
            };

        } catch (error) {
            console.error(`❌ 抓取失败: ${error.message}`);
            throw error;
        } finally {
            await browser.close();
        }
    }

    /**
     * 批量抓取产品数据
     */
    async batchScrape(urls) {
        console.log(`🚀 开始批量抓取 ${urls.length} 个产品`);

        const results = [];

        for (let i = 0; i < urls.length; i++) {
            const url = urls[i];
            console.log(`\n📋 抓取进度: ${i + 1}/${urls.length}`);

            try {
                const data = await this.scrapeProductData(url);
                results.push(data);

                // 避免请求过快
                if (i < urls.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            } catch (error) {
                console.error(`❌ 产品抓取失败: ${url}`, error.message);
                results.push({
                    brand: this.brand,
                    url: url,
                    error: error.message,
                    scrapeTime: new Date().toISOString()
                });
            }
        }

        console.log(`\n✅ 批量抓取完成！成功: ${results.filter(r => !r.error).length}/${urls.length}`);
        return results;
    }
}

module.exports = LeCoqGolfDataScraper;

// 如果直接运行此文件
if (require.main === module) {
    const scraper = new LeCoqGolfDataScraper();

    // 测试单个URL抓取
    const testUrl = process.argv[2] || 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';

    scraper.scrapeProductData(testUrl)
        .then(data => {
            console.log('\n📊 抓取结果:');
            console.log(JSON.stringify(data, null, 2));
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}