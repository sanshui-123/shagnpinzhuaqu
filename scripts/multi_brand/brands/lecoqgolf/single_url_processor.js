#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 完整版单URL处理器
 * 合并基础抓取 + 智能增强功能
 * 特点：
 * 1. 基础数据抓取（稳定）
 * 2. 智能尺码表检测（按需增强）
 * 3. 错误容错机制
 * 4. 统一品牌处理
 */

const { chromium } = require('playwright');
const fs = require('fs');

class SingleURLProcessor {
    constructor() {
        this.results = {};
        this.brandName = 'Le Coq公鸡乐卡克'; // 硬编码品牌名
    }

    async processSingleURL(url) {
        console.log('🔍 开始完整版抓取单URL:', url);

        const browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        });

        try {
            const page = await browser.newPage();
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 60000
            });

            await page.waitForTimeout(3000);

            // 智能增强：尝试点击尺码表按钮
            await this.tryEnhanceSizeChart(page);

            // 抓取所有数据
            this.results = await page.evaluate(() => {
                return {
                    // 基础信息
                    "商品链接": window.location.href,
                    "商品ID": (() => {
                        // 优先从尺码表中提取品牌商品编号
                        const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');
                        if (sizeChartArea) {
                            const chartText = sizeChartArea.textContent;
                            const afterBrandCodeText = chartText.split('ブランド商品番号※店舗お問い合わせ用')[1];
                            if (afterBrandCodeText) {
                                const brandCodeMatch = afterBrandCodeText.match(/\b([A-Z]{2,}\d{4,})\b/);
                                if (brandCodeMatch) return brandCodeMatch[1];
                            }
                        }

                        // 备用方法：从页面其他位置提取
                        const selectors = [
                            '.product-id',
                            '[data-product-id]',
                            '.item-number',
                            '.product-number'
                        ];

                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const text = element.textContent.trim();
                                const match = text.match(/\b([A-Z]{2,}\d{4,})\b/);
                                if (match) return match[1];
                            }
                        }

                        // 最后尝试从URL提取
                        const urlMatch = window.location.href.match(/\/([A-Z]{2,}\d{4,})\//);
                        return urlMatch ? urlMatch[1] : '';
                    })(),

                    "商品标题": (() => {
                        const selectors = [
                            'h1',
                            '.product-name',
                            '.item-name',
                            '[data-product-name]'
                        ];

                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                return element.textContent.trim();
                            }
                        }
                        return document.title.trim();
                    })(),

                    "品牌名": "Le Coq公鸡乐卡克", // 硬编码品牌名

                    "价格": (() => {
                        const priceSelectors = [
                            '.price',
                            '.product-price',
                            '[data-price]',
                            '.current-price'
                        ];

                        for (const selector of priceSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const priceText = element.textContent.trim();
                                const priceMatch = priceText.match(/[￥¥]\s*[\d,]+/);
                                if (priceMatch) return priceMatch[0];
                            }
                        }

                        // 搜索页面中的价格模式
                        const pageText = document.body.textContent;
                        const priceMatch = pageText.match(/[￥¥]\s*[\d,]+/);
                        return priceMatch ? priceMatch[0] : '';
                    })(),

                    "颜色": (() => {
                        const colors = new Set();

                        // 方法1：从颜色选择器提取
                        const colorSelectors = [
                            '.color-options .color-option',
                            '.variation-options .variation-option',
                            '[data-color]'
                        ];

                        for (const selector of colorSelectors) {
                            document.querySelectorAll(selector).forEach(element => {
                                const colorName = element.textContent.trim();
                                if (colorName && colorName.length > 0) {
                                    colors.add(colorName);
                                }
                            });
                        }

                        // 方法2：从图片alt属性提取颜色
                        const images = document.querySelectorAll('img');
                        images.forEach(img => {
                            const alt = img.alt;
                            if (alt) {
                                const colorMatch = alt.match(/(ネイビー|ブラック|ホワイト|グレー|ブルー|ベージュ|レッド|グリーン|イエロー|ブラウン|パープル|ピンク|オレンジ|ベージュ|グレー×|ブラック×|ネイビー×)/);
                                if (colorMatch) {
                                    colors.add(colorMatch[1]);
                                }
                            }
                        });

                        return Array.from(colors);
                    })(),

                    "尺码": (() => {
                        const sizes = new Set();

                        // 综合尺码提取策略
                        const sizeSelectors = [
                            '.size-options .size-option',
                            '.variation-options .variation-option[data-size]',
                            '.size-item',
                            '[data-size]'
                        ];

                        for (const selector of sizeSelectors) {
                            document.querySelectorAll(selector).forEach(element => {
                                const sizeText = element.textContent.trim();
                                if (sizeText && /^[SMLXL0-9\s]+$/.test(sizeText)) {
                                    sizes.add(sizeText);
                                }
                            });
                        }

                        // 从尺码表提取标准尺码
                        const sizeChartArea = document.querySelector('table');
                        if (sizeChartArea) {
                            const chartText = sizeChartArea.textContent;
                            const sizeMatches = chartText.match(/\b(S|M|L|LL|3L|4L|5L|XS|XL|XXL)\b/g);
                            if (sizeMatches) {
                                sizeMatches.forEach(size => sizes.add(size));
                            }
                        }

                        // 按标准顺序排序
                        const standardOrder = ['XS', 'S', 'M', 'L', 'LL', '3L', '4L', '5L', 'XL', 'XXL'];
                        const sortedSizes = Array.from(sizes).sort((a, b) => {
                            const indexA = standardOrder.indexOf(a);
                            const indexB = standardOrder.indexOf(b);
                            if (indexA !== -1 && indexB !== -1) return indexA - indexB;
                            if (indexA !== -1) return -1;
                            if (indexB !== -1) return 1;
                            return a.localeCompare(b);
                        });

                        return sortedSizes;
                    })(),

                    "图片链接": (() => {
                        const imageUrls = new Set();

                        // 遍历所有img标签
                        const images = document.querySelectorAll('img');
                        images.forEach(img => {
                            let imageUrl = img.src || img.getAttribute('data-src');
                            if (imageUrl) {
                                // 转换为完整URL
                                if (imageUrl.startsWith('//')) {
                                    imageUrl = 'https:' + imageUrl;
                                } else if (imageUrl.startsWith('/')) {
                                    imageUrl = window.location.origin + imageUrl;
                                }

                                // 过滤：只保留产品图片
                                const excludePatterns = [
                                    'logo', 'icon', 'banner', 'thumb', 'small',
                                    'sprite', 'pixel', 'tracking', 'analytics'
                                ];

                                const shouldExclude = excludePatterns.some(pattern =>
                                    imageUrl.toLowerCase().includes(pattern)
                                );

                                if (!shouldExclude && imageUrl.includes('http')) {
                                    imageUrls.add(imageUrl);
                                }
                            }
                        });

                        // 优先选择包含商品ID的高质量图片
                        const productId = window.location.href.match(/\/([A-Z]{2,}\d{4,})\//)?.[1];
                        if (productId) {
                            const productImages = Array.from(imageUrls).filter(url =>
                                url.includes(productId) || url.includes('/commodity/images/')
                            );
                            if (productImages.length > 0) {
                                return productImages.slice(0, 10); // 最多10张
                            }
                        }

                        return Array.from(imageUrls).slice(0, 10);
                    })(),

                    "详情页文字": (() => {
                        // 查找产品描述区域
                        const descriptionSelectors = [
                            '.product-description',
                            '.item-description',
                            '.product-detail',
                            '[data-product-description]'
                        ];

                        for (const selector of descriptionSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                return element.textContent.trim().substring(0, 2000);
                            }
                        }

                        // 备用方法：查找包含主要关键词的段落
                        const keywords = ['素材', '仕様', '特徴', '機能', 'サイズ'];
                        const paragraphs = document.querySelectorAll('p, div');
                        for (const paragraph of paragraphs) {
                            const text = paragraph.textContent.trim();
                            if (text.length > 50 && keywords.some(keyword => text.includes(keyword))) {
                                return text.substring(0, 2000);
                            }
                        }

                        return '';
                    })(),

                    "尺码表": (() => {
                        // 查找尺码表
                        const tableSelectors = [
                            'table',
                            '.size-table',
                            '[class*="chart"]',
                            '.spec-table'
                        ];

                        for (const selector of tableSelectors) {
                            const table = document.querySelector(selector);
                            if (table) {
                                // 检查是否包含尺码信息
                                const tableText = table.textContent;
                                if (tableText.includes('cm') || tableText.includes('サイズ') || tableText.includes('cm')) {
                                    return {
                                        html: table.outerHTML,
                                        text: table.textContent.trim()
                                    };
                                }
                            }
                        }

                        return {
                            html: '',
                            text: ''
                        };
                    })(),

                    "性别": (() => {
                        const pageText = document.body.textContent.toLowerCase();

                        if (pageText.includes('メンズ') || pageText.includes('男性')) {
                            return '男';
                        } else if (pageText.includes('レディース') || pageText.includes('女性')) {
                            return '女';
                        } else if (pageText.includes('ユニセックス')) {
                            return '男女通用';
                        }

                        return '';
                    })(),

                    // 向后兼容字段
                    "productId": (() => {
                        const urlMatch = window.location.href.match(/\/([A-Z]{2,}\d{4,})\//);
                        return urlMatch ? urlMatch[1] : '';
                    })(),

                    "productName": (() => {
                        const selectors = [
                            'h1',
                            '.product-name',
                            '.item-name'
                        ];

                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                return element.textContent.trim();
                            }
                        }
                        return document.title.trim();
                    })(),

                    "priceText": (() => {
                        const priceSelectors = [
                            '.price',
                            '.product-price',
                            '[data-price]'
                        ];

                        for (const selector of priceSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const priceText = element.textContent.trim();
                                const priceMatch = priceText.match(/[￥¥]\s*[\d,]+/);
                                if (priceMatch) return priceMatch[0];
                            }
                        }
                        return '';
                    })(),

                    "detailUrl": window.location.href
                };
            });

            console.log('✅ 抓取完成');
            console.log('   商品ID:', this.results['商品ID']);
            console.log('   商品标题:', this.results['商品标题']);
            console.log('   品牌:', this.results['品牌名']);
            console.log('   价格:', this.results['价格']);
            console.log('   颜色数:', this.results['颜色']?.length || 0);
            console.log('   尺码数:', this.results['尺码']?.length || 0);
            console.log('   图片数:', this.results['图片链接']?.length || 0);

            await browser.close();
            return this.results;

        } catch (error) {
            console.error('❌ 抓取失败:', error.message);
            await browser.close();
            throw error;
        }
    }

    /**
     * 智能增强：尝试点击尺码表按钮
     * 容错设计：失败不影响主要功能
     */
    async tryEnhanceSizeChart(page) {
        console.log('🔍 检测尺码表增强机会...');

        try {
            // 等待页面稳定
            await page.waitForTimeout(2000);

            // 方法1：查找常见的尺码表按钮文字
            const buttonSelectors = [
                'text=サイズ詳細',
                'text=サイズ表',
                'text=详细尺寸',
                'text=尺码指南',
                'text=サイズガイド',
                'a[href*="size"]',
                'button[class*="size"]',
                '.size-table-button',
                '[data-action="show-size-chart"]'
            ];

            let buttonFound = false;
            for (const selector of buttonSelectors) {
                try {
                    const button = await page.locator(selector).first();
                    if (await button.isVisible({ timeout: 3000 })) {
                        await button.click();
                        console.log(`✅ 点击了尺码表按钮: ${selector}`);
                        buttonFound = true;
                        await page.waitForTimeout(2000); // 等待内容加载
                        break;
                    }
                } catch (e) {
                    // 继续尝试下一个选择器
                }
            }

            // 方法2：查找包含特定关键词的链接
            if (!buttonFound) {
                const links = await page.$$('a');
                for (const link of links) {
                    const text = await link.textContent();
                    if (text && (
                        text.includes('サイズ') ||
                        text.includes('サイズ表') ||
                        text.includes('详细') ||
                        text.includes('寸法')
                    )) {
                        try {
                            await link.click();
                            console.log('✅ 点击了尺码表链接:', text.trim());
                            buttonFound = true;
                            await page.waitForTimeout(2000);
                            break;
                        } catch (e) {
                            // 继续尝试下一个链接
                        }
                    }
                }
            }

            if (!buttonFound) {
                console.log('ℹ️ 未发现尺码表按钮，使用基础抓取');
            }

        } catch (error) {
            console.log('⚠️ 尺码表增强失败，继续基础抓取:', error.message);
            // 不抛出错误，让主流程继续
        }
    }

    async saveResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19) + 'Z';
        const filename = `single_url_${timestamp}.json`;

        const result = {
            timestamp: new Date().toISOString(),
            url: this.url,
            processed_data: this.results
        };

        fs.writeFileSync(filename, JSON.stringify(result, null, 2), 'utf8');
        console.log(`💾 结果已保存: ${filename}`);
        return filename;
    }
}

// 主函数
async function main() {
    const url = process.argv[2];

    if (!url) {
        console.error('❌ 请提供产品URL');
        console.log('用法: node single_url_processor.js <产品URL>');
        process.exit(1);
    }

    const processor = new SingleURLProcessor();

    try {
        await processor.processSingleURL(url);
        const outputFile = await processor.saveResults();
        console.log('🎉 处理完成！');

    } catch (error) {
        console.error('❌ 处理失败:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = SingleURLProcessor;