#!/usr/bin/env node

/**
 * 批量创建品牌配置脚本
 * 为15个高尔夫品牌生成标准配置文件
 */

const fs = require('fs');
const path = require('path');

const brands = [
    {
        id: 'taylormade',
        name: 'TaylorMade Golf',
        domain: 'www.taylormadegolf.com',
        baseUrl: 'https://www.taylormadegolf.com',
        scheduleDay: 2,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'balls', 'apparel']
    },
    {
        id: 'titleist',
        name: 'Titleist',
        domain: 'www.titleist.com',
        baseUrl: 'https://www.titleist.com',
        scheduleDay: 3,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'balls', 'golf-bags', 'headcovers']
    },
    {
        id: 'ping',
        name: 'PING Golf',
        domain: 'www.ping.com',
        baseUrl: 'https://www.ping.com',
        scheduleDay: 4,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'bags', 'apparel']
    },
    {
        id: 'cobra',
        name: 'Cobra Golf',
        domain: 'www.cobragolf.com',
        baseUrl: 'https://www.cobragolf.com',
        scheduleDay: 5,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'apparel']
    },
    {
        id: 'bridgestone',
        name: 'Bridgestone Golf',
        domain: 'www.bridgestonegolf.com',
        baseUrl: 'https://www.bridgestonegolf.com',
        scheduleDay: 6,
        categories: ['balls', 'drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'apparel']
    },
    {
        id: 'mizuno',
        name: 'Mizuno Golf',
        domain: 'www.mizunogolf.com',
        baseUrl: 'https://www.mizunogolf.com',
        scheduleDay: 7,
        categories: ['drivers', 'irons', 'wedges', 'apparel', 'accessories']
    },
    {
        id: 'srixon',
        name: 'Srixon',
        domain: 'www.srixon.com',
        baseUrl: 'https://www.srixon.com',
        scheduleDay: 8,
        categories: ['balls', 'drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'apparel']
    },
    {
        id: 'pxg',
        name: 'PXG',
        domain: 'www.pxg.com',
        baseUrl: 'https://www.pxg.com',
        scheduleDay: 9,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'apparel', 'accessories']
    },
    {
        id: 'honma',
        name: 'Honma Golf',
        domain: 'www.honmagolf.com',
        baseUrl: 'https://www.honmagolf.com',
        scheduleDay: 10,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'apparel', 'balls']
    },
    {
        id: 'wilson',
        name: 'Wilson Staff',
        domain: 'www.wilson.com/golf',
        baseUrl: 'https://www.wilson.com/golf',
        scheduleDay: 1,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters', 'balls', 'bags']
    },
    {
        id: 'adams',
        name: 'Adams Golf',
        domain: 'www.adamsgolf.com',
        baseUrl: 'https://www.adamsgolf.com',
        scheduleDay: 2,
        categories: ['drivers', 'fairways', 'hybrids', 'irons', 'wedges', 'putters']
    },
    {
        id: 'cleveland',
        name: 'Cleveland Golf',
        domain: 'www.clevelandgolf.com',
        baseUrl: 'https://www.clevelandgolf.com',
        scheduleDay: 3,
        categories: ['wedges', 'putters', 'irons', 'apparel', 'accessories']
    },
    {
        id: 'scotty',
        name: 'Scotty Cameron',
        domain: 'www.scottycameron.com',
        baseUrl: 'https://www.scottycameron.com',
        scheduleDay: 4,
        categories: ['putters', 'headcovers', 'apparel', 'accessories']
    },
    {
        id: 'odyssey',
        name: 'Odyssey Golf',
        domain: 'www.odysseygolf.com',
        baseUrl: 'https://www.odysseygolf.com',
        scheduleDay: 5,
        categories: ['putters', 'balls', 'apparel', 'accessories']
    }
];

function createConfigFile(brand) {
    const config = {
        name: brand.name,
        domain: brand.domain,
        baseUrl: brand.baseUrl,
        enabled: true,
        schedule: {
            interval: '10-days',
            dayOfMonth: brand.scheduleDay
        },
        scraper: {
            type: 'puppeteer',
            timeout: 30000,
            retries: 3,
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            headless: true,
            viewport: {
                width: 1920,
                height: 1080
            }
        },
        selectors: {
            productGrid: '.product-grid, .product-list, .items-grid, .catalog-items',
            productName: '.product-title, .product-name, .item-title, h3, h2',
            productUrl: 'a',
            productImage: '.product-image img, .item-image img, .product-photo img',
            productPrice: '.product-price, .price, .product-cost, .item-price',
            productCategory: '.product-category, .category, .item-category'
        },
        categories: brand.categories,
        output: {
            format: 'json',
            path: `golf_content/${brand.id}`,
            filename: `${brand.id}_products.json`
        },
        constraints: {
            minProductsPerPage: 5,
            maxPagesPerCategory: 5,
            requestDelay: 2000,
            maxConcurrentPages: 3
        }
    };

    return JSON.stringify(config, null, 2);
}

function createSelectorsFile(brand) {
    const selectors = {
        pages: {
            homepage: {
                url: '/',
                selectors: {
                    productContainer: '.new-arrivals, .featured-products, .products-container',
                    productItems: '.product-item, .product-card, .item'
                }
            },
            clubs: {
                url: '/clubs',
                selectors: {
                    productContainer: '.clubs-container, .products-grid',
                    productItems: '.club-item, .product-item'
                }
            },
            drivers: {
                url: '/clubs/drivers',
                selectors: {
                    productContainer: '.drivers-container',
                    productItems: '.driver-item, .product-item'
                }
            },
            apparel: {
                url: '/apparel',
                selectors: {
                    productContainer: '.apparel-container, .clothing-grid',
                    productItems: '.apparel-item, .clothing-item'
                }
            }
        },
        pagination: {
            nextButton: '.next-page, .pagination-next, [rel="next"]',
            itemSelector: '.product-item, .item-card',
            maxPages: 5
        },
        productDetails: {
            title: '.product-title, .product-name, h1',
            description: '.product-description, .product-details, .description',
            price: '.product-price, .price-current, .actual-price',
            originalPrice: '.price-original, .price-was, .compare-at-price',
            images: '.product-gallery img, .product-images img, .gallery-item img',
            specifications: '.product-specs, .specifications, .tech-specs',
            features: '.product-features, .key-features, .features-list',
            availability: '.stock-status, .availability, .in-stock'
        },
        waitFor: {
            productGrid: '.product-grid, .products-container',
            productImage: 'img[src]'
        }
    };

    return JSON.stringify(selectors, null, 2);
}

function createScraperFile(brand) {
    return `#!/usr/bin/env node

/**
 * ${brand.name} 专用抓取器
 * 基于统一模板，根据具体网站结构调整选择器
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ${brand.id.charAt(0).toUpperCase() + brand.id.slice(1)}Scraper {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.results = [];
        this.concurrencyLimit = config.constraints?.maxConcurrentPages || 3;
    }

    async scrape() {
        console.log('🚀 开始抓取 ${brand.name} 数据...');

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
                    this.scrapePage(browser, \`/\${category}\`).catch(err => {
                        console.warn(\`⚠️ 分类 \${category} 抓取失败:\`, err.message);
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
        const url = \`\${this.baseUrl}\${pagePath}\`;

        try {
            console.log(\`📄 抓取页面: \${url}\`);

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
                console.log(\`✅ 页面 \${pagePath} 提取到 \${products.length} 个产品\`);

                this.results.push({
                    page: pagePath,
                    url: url,
                    products: products,
                    timestamp: new Date().toISOString()
                });
            } else {
                console.warn(\`⚠️ 页面 \${pagePath} 未找到产品\`);
            }

        } catch (error) {
            console.error(\`❌ 页面抓取失败 \${pagePath}:\`, error.message);
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
                        brand: '${brand.name}',
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
        const outputFile = path.join(outputPath, \`${brand.id}_products_\${timestamp}.json\`);

        const outputData = {
            brand: '${brand.name}',
            brandId: '${brand.id}',
            scrapeTime: new Date().toISOString(),
            totalProducts: this.results.reduce((sum, page) => sum + page.products.length, 0),
            pagesScraped: this.results.length,
            results: this.results
        };

        fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2));
        console.log(\`💾 结果已保存: \${outputFile}\`);

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
    const scraper = new ${brand.id.charAt(0).toUpperCase() + brand.id.slice(1)}Scraper(config);

    scraper.scrape()
        .then(() => scraper.saveResults())
        .then(() => console.log('✅ ${brand.name} 抓取完成'))
        .catch(error => {
            console.error('❌ ${brand.name} 抓取失败:', error);
            process.exit(1);
        });
}

module.exports = ${brand.id.charAt(0).toUpperCase() + brand.id.slice(1)}Scraper;
`;
}

function createReadmeFile(brand) {
    return `# ${brand.name} 配置

## 基本信息
- **品牌ID**: ${brand.id}
- **官网**: ${brand.baseUrl}
- **调度日**: 每月${brand.scheduleDay}号

## 配置文件
- \`config.json\` - 主配置文件
- \`selectors.json\` - CSS选择器配置
- \`scrape_category.js\` - 专用抓取器

## 使用方法

### 1. 测试抓取器
\`\`\`bash
node scrape_category.js
\`\`\`

### 2. 单独测试分类页面
\`\`\`bash
node scrape_category.js --category drivers
\`\`\`

### 3. 更新配置
编辑 \`config.json\` 文件后重新运行

## 调试说明

如果遇到抓取问题，请检查：
1. 网站是否有反爬虫保护
2. CSS选择器是否需要更新
3. 是否需要调整等待时间
4. 网站是否需要特殊的User-Agent

## 数据输出

抓取结果将保存到：
- 路径: \`golf_content/${brand.id}/\`
- 文件格式: JSON
- 包含字段: 标题、价格、图片、分类、URL等

## 注意事项

- 请遵守网站的robots.txt和使用条款
- 建议设置合理的请求间隔，避免给网站造成压力
- 定期检查和更新CSS选择器
`;
}

// 主执行函数
async function main() {
    const baseDir = path.join(__dirname);
    console.log('🏗️ 开始创建15个品牌配置...');

    for (const brand of brands) {
        const brandDir = path.join(baseDir, brand.id);

        // 创建品牌目录
        if (!fs.existsSync(brandDir)) {
            fs.mkdirSync(brandDir, { recursive: true });
        }

        try {
            // 创建配置文件
            const configContent = createConfigFile(brand);
            fs.writeFileSync(path.join(brandDir, 'config.json'), configContent);

            // 创建选择器文件
            const selectorsContent = createSelectorsFile(brand);
            fs.writeFileSync(path.join(brandDir, 'selectors.json'), selectorsContent);

            // 创建抓取器文件
            const scraperContent = createScraperFile(brand);
            fs.writeFileSync(path.join(brandDir, 'scrape_category.js'), scraperContent);

            // 创建README文件
            const readmeContent = createReadmeFile(brand);
            fs.writeFileSync(path.join(brandDir, 'README.md'), readmeContent);

            // 设置抓取器执行权限
            fs.chmodSync(path.join(brandDir, 'scrape_category.js'), '755');

            console.log(`✅ ${brand.name} 配置创建完成`);

        } catch (error) {
            console.error(`❌ 创建 ${brand.name} 配置失败:`, error.message);
        }
    }

    console.log('\n🎉 所有品牌配置创建完成！');
    console.log('\n📁 配置文件位置:');
    console.log('- 主配置: scripts/multi_brand/brands/');
    console.log('- 每个品牌都有独立的配置目录');
    console.log('- 包含 config.json, selectors.json, scrape_category.js 三个文件');
}

// 如果直接运行此脚本
if (require.main === module) {
    main().catch(error => {
        console.error('❌ 脚本执行失败:', error);
        process.exit(1);
    });
}

module.exports = { brands, createConfigFile, createSelectorsFile, createScraperFile };