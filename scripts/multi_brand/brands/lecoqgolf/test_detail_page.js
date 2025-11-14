#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 详情页测试抓取器
 * 用于分析单个商品详情页的数据结构
 */

const { chromium } = require('playwright');

class DetailPageTester {
    constructor() {
        this.url = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';
        this.results = {};
    }

    async analyze() {
        console.log('🔍 开始分析详情页:', this.url);

        const browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();

        try {
            // 访问页面
            await page.goto(this.url, {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });

            // 等待内容加载
            await page.waitForTimeout(5000);

            // 提取基础信息
            this.results.basic = await this.extractBasicInfo(page);

            // 提取商品图片
            this.results.images = await this.extractImages(page);

            // 提取价格信息
            this.results.pricing = await this.extractPricing(page);

            // 提取商品规格
            this.results.specifications = await this.extractSpecifications(page);

            // 提取库存信息
            this.results.inventory = await this.extractInventory(page);

            // 提取分类信息
            this.results.categories = await this.extractCategories(page);

            // 提取描述信息
            this.results.description = await this.extractDescription(page);

            // 输出结果
            this.printResults();

        } catch (error) {
            console.error('❌ 分析失败:', error.message);
        } finally {
            await browser.close();
        }
    }

    async extractBasicInfo(page) {
        return await page.evaluate(() => {
            const title = document.title || '';

            let metaDescription = '';
            const metaDescElement = document.querySelector('meta[name="description"]');
            if (metaDescElement) metaDescription = metaDescElement.content;

            let metaKeywords = '';
            const metaKeyElement = document.querySelector('meta[name="keywords"]');
            if (metaKeyElement) metaKeywords = metaKeyElement.content;

            let canonical = '';
            const canonElement = document.querySelector('link[rel="canonical"]');
            if (canonElement) canonical = canonElement.href;

            // 尝试提取商品名称
            let productTitle = '';
            const productNameEl = document.querySelector('.productName');
            if (productNameEl) productTitle = productNameEl.textContent.trim();
            else {
                const commodityNameEl = document.querySelector('.commodityName');
                if (commodityNameEl) productTitle = commodityNameEl.textContent.trim();
                else {
                    const h1El = document.querySelector('h1');
                    if (h1El) productTitle = h1El.textContent.trim();
                }
            }

            // 尝试提取商品编号
            let productCode = '';
            const productCodeEl = document.querySelector('.productCode');
            if (productCodeEl) productCode = productCodeEl.textContent.trim();
            else {
                const commodityCodeEl = document.querySelector('.commodityCode');
                if (commodityCodeEl) productCode = commodityCodeEl.textContent.trim();
                else {
                    const codeEl = document.querySelector('[class*="code"]');
                    if (codeEl) productCode = codeEl.textContent.trim();
                }
            }

            // 尝试提取品牌
            let brand = '';
            const brandNameEl = document.querySelector('.brandName');
            if (brandNameEl) brand = brandNameEl.textContent.trim();
            else {
                const brandEl = document.querySelector('[class*="brand"]');
                if (brandEl) brand = brandEl.textContent.trim();
            }

            return {
                title: title,
                metaDescription: metaDescription,
                metaKeywords: metaKeywords,
                canonical: canonical,
                productTitle: productTitle,
                productCode: productCode,
                brand: brand
            };
        });
    }

    async extractImages(page) {
        return await page.evaluate(() => {
            const images = [];

            // 主要图片区域
            const mainImage = document.querySelector('.mainImage img, .productImage img, .commodityImage img');
            if (mainImage) {
                images.push({
                    type: 'main',
                    src: mainImage.src,
                    alt: mainImage.alt
                });
            }

            // 缩略图
            const thumbnails = document.querySelectorAll('.thumbnail img, .thumb img, [class*="thumb"] img');
            thumbnails.forEach((thumb, index) => {
                if (thumb.src) {
                    images.push({
                        type: 'thumbnail',
                        index: index,
                        src: thumb.src,
                        alt: thumb.alt
                    });
                }
            });

            // 所有商品相关图片
            const productImages = document.querySelectorAll('img[src*="commodity"], img[src*="product"]');
            productImages.forEach((img, index) => {
                if (img.src) {
                    const exists = images.find(existing => existing.src === img.src);
                    if (!exists) {
                        images.push({
                            type: 'product',
                            index: index,
                            src: img.src,
                            alt: img.alt
                        });
                    }
                }
            });

            return images;
        });
    }

    async extractPricing(page) {
        return await page.evaluate(() => {
            const pricing = {};

            // 当前价格
            let currentPrice = '';
            const priceEl = document.querySelector('.price');
            if (priceEl) currentPrice = priceEl.textContent.trim();
            else {
                const priceCurrentEl = document.querySelector('.price-current');
                if (priceCurrentEl) currentPrice = priceCurrentEl.textContent.trim();
                else {
                    const priceGenericEl = document.querySelector('[class*="price"]');
                    if (priceGenericEl) currentPrice = priceGenericEl.textContent.trim();
                }
            }

            // 原价
            let originalPrice = '';
            const originalPriceEl = document.querySelector('.price-original');
            if (originalPriceEl) originalPrice = originalPriceEl.textContent.trim();
            else {
                const priceBeforeEl = document.querySelector('.price-before');
                if (priceBeforeEl) originalPrice = priceBeforeEl.textContent.trim();
                else {
                    const originalGenericEl = document.querySelector('[class*="original"]');
                    if (originalGenericEl) originalPrice = originalGenericEl.textContent.trim();
                }
            }

            // 折扣价
            let salePrice = '';
            const salePriceEl = document.querySelector('.price-sale');
            if (salePriceEl) salePrice = salePriceEl.textContent.trim();
            else {
                const discountPriceEl = document.querySelector('.price-discount');
                if (discountPriceEl) salePrice = discountPriceEl.textContent.trim();
                else {
                    const saleGenericEl = document.querySelector('[class*="sale"]');
                    if (saleGenericEl) salePrice = saleGenericEl.textContent.trim();
                }
            }

            pricing.current = currentPrice;
            pricing.original = originalPrice;
            pricing.sale = salePrice;

            return pricing;
        });
    }

    async extractSpecifications(page) {
        return await page.evaluate(() => {
            const specs = {};

            // 尺寸信息
            const sizeElements = document.querySelectorAll('[class*="size"], .size-option');
            const sizes = [];
            sizeElements.forEach(el => {
                const text = el.textContent.trim();
                if (text) sizes.push(text);
            });
            specs.sizes = sizes;

            // 颜色信息
            const colorElements = document.querySelectorAll('[class*="color"], .color-option');
            const colors = [];
            colorElements.forEach(el => {
                const text = el.textContent.trim();
                if (text) colors.push(text);
            });
            specs.colors = colors;

            // 材质信息
            let material = '';
            const materialEl = document.querySelector('[class*="material"]');
            if (materialEl) material = materialEl.textContent.trim();
            else {
                const fabricEl = document.querySelector('[class*="fabric"]');
                if (fabricEl) material = fabricEl.textContent.trim();
            }
            specs.material = material;

            return specs;
        });
    }

    async extractInventory(page) {
        return await page.evaluate(() => {
            const inventory = {};

            // 库存状态
            let stockStatus = '';
            const stockEl = document.querySelector('[class*="stock"]');
            if (stockEl) stockStatus = stockEl.textContent.trim();
            else {
                const inventoryEl = document.querySelector('[class*="inventory"]');
                if (inventoryEl) stockStatus = inventoryEl.textContent.trim();
            }
            inventory.status = stockStatus;

            return inventory;
        });
    }

    async extractCategories(page) {
        return await page.evaluate(() => {
            const categories = [];

            // 面包屑导航
            const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a');
            breadcrumbs.forEach(el => {
                const text = el.textContent.trim();
                if (text) categories.push(text);
            });

            return categories;
        });
    }

    async extractDescription(page) {
        return await page.evaluate(() => {
            const description = {};

            // 商品描述
            const descElements = document.querySelectorAll('.description, .product-description, [class*="description"]');
            const descTexts = [];
            descElements.forEach(el => {
                const text = el.textContent.trim();
                if (text) descTexts.push(text);
            });
            description.text = descTexts.join('\n');

            return description;
        });
    }

    printResults() {
        console.log('\n=== 📊 详情页分析结果 ===\n');

        console.log('📝 基础信息:');
        console.log(JSON.stringify(this.results.basic, null, 2));

        console.log('\n🖼️ 图片信息:');
        console.log(`发现 ${this.results.images ? this.results.images.length : 0} 张图片`);
        if (this.results.images) {
            this.results.images.forEach((img, index) => {
                console.log(`  ${index + 1}. [${img.type}] ${img.src.substring(0, 80)}...`);
            });
        }

        console.log('\n💰 价格信息:');
        console.log(JSON.stringify(this.results.pricing, null, 2));

        console.log('\n📏 规格信息:');
        console.log(JSON.stringify(this.results.specifications, null, 2));

        console.log('\n📦 库存信息:');
        console.log(JSON.stringify(this.results.inventory, null, 2));

        console.log('\n🏷️ 分类信息:');
        console.log(JSON.stringify(this.results.categories, null, 2));

        console.log('\n📄 描述信息:');
        console.log(JSON.stringify(this.results.description, null, 2));
    }
}

// 运行测试
if (require.main === module) {
    const tester = new DetailPageTester();
    tester.analyze().catch(console.error);
}

module.exports = DetailPageTester;