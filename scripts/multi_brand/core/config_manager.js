/**
 * 多品牌配置管理系统
 * 负责品牌配置的加载、验证和管理
 */

const fs = require('fs');
const path = require('path');

class ConfigManager {
    constructor() {
        this.configs = new Map();
        this.baseDir = path.join(__dirname, '..', '..');
        this.brandsDir = path.join(this.baseDir, 'brands');
    }

    /**
     * 获取所有品牌列表
     */
    async getAllBrands() {
        try {
            const brandsPath = path.join(this.baseDir, 'brands');

            if (!fs.existsSync(brandsPath)) {
                return ['callaway']; // 默认只有卡拉威
            }

            const items = fs.readdirSync(brandsPath);
            return items
                .filter(item => {
                    const itemPath = path.join(brandsPath, item);
                    return fs.statSync(itemPath).isDirectory();
                })
                .sort();
        } catch (error) {
            console.error('获取品牌列表失败:', error.message);
            return ['callaway'];
        }
    }

    /**
     * 获取品牌配置
     */
    async getBrandConfig(brandName) {
        if (this.configs.has(brandName)) {
            return this.configs.get(brandName);
        }

        try {
            const configPath = path.join(this.baseDir, 'brands', brandName, 'config.json');

            if (!fs.existsSync(configPath)) {
                // 如果是callaway，使用现有系统配置
                if (brandName === 'callaway') {
                    return await this.getCallawayConfig();
                }
                return null;
            }

            const configData = fs.readFileSync(configPath, 'utf8');
            const config = JSON.parse(configData);

            // 验证配置完整性
            const validatedConfig = this.validateConfig(brandName, config);
            this.configs.set(brandName, validatedConfig);

            return validatedConfig;

        } catch (error) {
            console.error(`获取品牌 ${brandName} 配置失败:`, error.message);
            return null;
        }
    }

    /**
     * 同步获取品牌配置（带缓存）
     */
    getBrandConfigSync(brandName) {
        return this.configs.get(brandName);
    }

    /**
     * 获取Callaway配置（复用现有系统）
     */
    async getCallawayConfig() {
        return {
            name: 'Callaway Golf',
            domain: 'www.callawaygolf.com',
            baseUrl: 'https://www.callawaygolf.com',
            enabled: true,
            schedule: {
                interval: '10-days',
                dayOfMonth: 1 // 每月1号
            },
            scraper: {
                type: 'puppeteer',
                timeout: 30000,
                retries: 3
            },
            selectors: {
                // 复用现有的卡拉威选择器
                productGrid: '.product-grid .product-tile',
                productName: '.product-name',
                productUrl: 'a',
                productImage: '.product-image img',
                productPrice: '.product-price'
            },
            categories: [
                'drivers',
                'fairways',
                'hybrids',
                'irons',
                'wedges',
                'putters',
                'apparel',
                'accessories'
            ],
            output: {
                format: 'json',
                path: 'golf_content'
            }
        };
    }

    /**
     * 验证配置完整性
     */
    validateConfig(brandName, config) {
        const requiredFields = [
            'name',
            'domain',
            'baseUrl',
            'enabled',
            'schedule',
            'scraper',
            'selectors'
        ];

        const missing = requiredFields.filter(field => !config[field]);

        if (missing.length > 0) {
            throw new Error(`品牌 ${brandName} 配置缺少必需字段: ${missing.join(', ')}`);
        }

        // 设置默认值
        const validatedConfig = {
            ...config,
            schedule: {
                interval: config.schedule.interval || '10-days',
                dayOfMonth: config.schedule.dayOfMonth || 1,
                ...config.schedule
            },
            scraper: {
                type: config.scraper.type || 'puppeteer',
                timeout: config.scraper.timeout || 30000,
                retries: config.scraper.retries || 3,
                ...config.scraper
            },
            output: {
                format: config.output?.format || 'json',
                path: config.output?.path || 'golf_content',
                ...config.output
            }
        };

        return validatedConfig;
    }

    /**
     * 创建品牌配置模板
     */
    async createBrandTemplate(brandName) {
        const brandDir = path.join(this.baseDir, 'brands', brandName);

        // 创建目录
        if (!fs.existsSync(brandDir)) {
            fs.mkdirSync(brandDir, { recursive: true });
        }

        // 创建配置文件模板
        const configTemplate = {
            name: brandName.charAt(0).toUpperCase() + brandName.slice(1),
            domain: `${brandName.toLowerCase()}.com`,
            baseUrl: `https://${brandName.toLowerCase()}.com`,
            enabled: true,
            schedule: {
                interval: '10-days',
                dayOfMonth: this.calculateScheduleDay(brandName)
            },
            scraper: {
                type: 'puppeteer',
                timeout: 30000,
                retries: 3,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                headless: true,
                viewport: {
                    width: 1920,
                    height: 1080
                }
            },
            selectors: {
                // 需要根据每个网站具体配置
                productGrid: '.product-grid .product-item',
                productName: '.product-title',
                productUrl: 'a',
                productImage: '.product-image img',
                productPrice: '.price',
                productCategory: '.category'
            },
            categories: [
                'drivers',
                'fairways',
                'hybrids',
                'irons',
                'wedges',
                'putters',
                'apparel',
                'shoes',
                'accessories'
            ],
            output: {
                format: 'json',
                path: `golf_content/${brandName}`,
                filename: `${brandName}_products.json`
            }
        };

        const configPath = path.join(brandDir, 'config.json');
        fs.writeFileSync(configPath, JSON.stringify(configTemplate, null, 2));

        // 创建选择器配置文件模板
        const selectorsTemplate = {
            pages: {
                homepage: {
                    url: '/',
                    selectors: {
                        productContainer: '.products-container',
                        productItems: '.product-item'
                    }
                },
                clubs: {
                    url: '/clubs',
                    selectors: {
                        productContainer: '.clubs-container',
                        productItems: '.club-item'
                    }
                },
                apparel: {
                    url: '/apparel',
                    selectors: {
                        productContainer: '.apparel-container',
                        productItems: '.apparel-item'
                    }
                }
            },
            pagination: {
                nextButton: '.next-page',
                itemSelector: '.product-item',
                maxPages: 5
            },
            productDetails: {
                title: '.product-title',
                description: '.product-description',
                price: '.product-price',
                images: '.product-gallery img',
                specifications: '.product-specs'
            }
        };

        const selectorsPath = path.join(brandDir, 'selectors.json');
        fs.writeFileSync(selectorsPath, JSON.stringify(selectorsTemplate, null, 2));

        // 创建抓取器模板
        const scraperTemplate = this.generateScraperTemplate(brandName);
        const scraperPath = path.join(brandDir, 'scrape_category.js');
        fs.writeFileSync(scraperPath, scraperTemplate);

        console.log(`✅ 品牌模板已创建: ${brandDir}`);
        console.log(`📝 请编辑以下文件完成配置:`);
        console.log(`   - ${configPath}`);
        console.log(`   - ${selectorsPath}`);
        console.log(`   - ${scraperPath}`);
    }

    /**
     * 计算品牌调度日（避免所有品牌同一天运行）
     */
    calculateScheduleDay(brandName) {
        const brands = [
            'callaway', 'taylormade', 'titleist', 'ping', 'cobra',
            'bridgestone', 'mizuno', 'srixon', 'pxg', 'honma',
            'wilson', 'adams', 'cleveland', 'scotty', 'odyssey'
        ];

        const index = brands.indexOf(brandName.toLowerCase());
        return index >= 0 ? (index % 10) + 1 : 1;
    }

    /**
     * 生成抓取器模板
     */
    generateScraperTemplate(brandName) {
        return `#!/usr/bin/env node

/**
 * ${brandName} 品牌专用抓取器
 * 基于统一模板，需要根据具体网站结构调整选择器
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ${brandName.charAt(0).toUpperCase() + brandName.slice(1)}Scraper {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.results = [];
    }

    async scrape() {
        console.log('🚀 开始抓取 ${brandName} 数据...');

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
                await this.scrapePage(page, \`/\${category}\`);
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
            const url = \`\${this.baseUrl}\${path}\`;
            console.log(\`📄 抓取页面: \${url}\`);

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
            console.error(\`页面抓取失败 \${path}:\`, error.message);
        }
    }

    async saveResults() {
        if (!fs.existsSync(this.config.output.path)) {
            fs.mkdirSync(this.config.output.path, { recursive: true });
        }

        const outputFile = path.join(this.config.output.path, this.config.output.filename);
        fs.writeFileSync(outputFile, JSON.stringify(this.results, null, 2));

        console.log(\`💾 结果已保存: \${outputFile}\`);
        return outputFile;
    }
}

// 如果直接运行此文件
if (require.main === module) {
    const config = JSON.parse(fs.readFileSync('./config.json', 'utf8'));
    const scraper = new ${brandName.charAt(0).toUpperCase() + brandName.slice(1)}Scraper(config);

    scraper.scrape()
        .then(() => scraper.saveResults())
        .then(() => console.log('✅ 抓取完成'))
        .catch(error => {
            console.error('❌ 抓取失败:', error);
            process.exit(1);
        });
}

module.exports = ${brandName.charAt(0).toUpperCase() + brandName.slice(1)}Scraper;
`;
    }

    /**
     * 更新品牌配置
     */
    async updateBrandConfig(brandName, updates) {
        try {
            const config = await this.getBrandConfig(brandName);
            if (!config) {
                throw new Error(`品牌 ${brandName} 不存在`);
            }

            const updatedConfig = { ...config, ...updates };
            const configPath = path.join(this.baseDir, 'brands', brandName, 'config.json');

            fs.writeFileSync(configPath, JSON.stringify(updatedConfig, null, 2));

            // 清除缓存
            this.configs.delete(brandName);

            console.log(`✅ 品牌 ${brandName} 配置已更新`);
            return updatedConfig;

        } catch (error) {
            console.error(`更新品牌 ${brandName} 配置失败:`, error.message);
            throw error;
        }
    }

    /**
     * 检查品牌是否启用
     */
    async isBrandEnabled(brandName) {
        const config = await this.getBrandConfig(brandName);
        return config && config.enabled;
    }

    /**
     * 获取启用的品牌列表
     */
    async getEnabledBrands() {
        const allBrands = await this.getAllBrands();
        const enabled = [];

        for (const brand of allBrands) {
            if (await this.isBrandEnabled(brand)) {
                enabled.push(brand);
            }
        }

        return enabled;
    }
}

module.exports = ConfigManager;