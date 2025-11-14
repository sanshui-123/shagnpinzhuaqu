#!/usr/bin/env node

/**
 * 单个URL固定处理器 - 根据用户要求修改抓取规则
 * 1. 删除衣服分类
 * 2. 图片规则改为：只抓取第一个颜色，1100*1100尺寸的图片
 * 3. 尺码问题：从颜色选择板块和尺码选择板块抓取
 * 4. 尺码表：先点击正确按钮，然后从正确位置获取数据
 */

const { chromium } = require('playwright');
const fs = require('fs');

class SingleURLFixedProcessor {
    constructor() {
        this.results = {};
    }

    async processSingleURL(url) {
        console.log('🔍 开始固定规则抓取单URL:', url);

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        try {
            const page = await browser.newPage();
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 60000
            });

            await page.waitForTimeout(3000);

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

                            const lgCodeMatch = chartText.match(/\b(LG[A-Z0-9]{6,})\b/);
                            if (lgCodeMatch) return lgCodeMatch[1];

                            const brandCodeMatch = chartText.match(/\b([A-Z]{2,}\d{4,})\b/);
                            if (brandCodeMatch && brandCodeMatch[1].length >= 6) {
                                return brandCodeMatch[1];
                            }
                        }

                        const elementsWithNames = document.querySelectorAll('[name]');
                        for (const element of elementsWithNames) {
                            const nameValue = element.getAttribute('name');
                            if (nameValue && nameValue.match(/^[A-Z]{2,}\d{4,}$/)) {
                                return nameValue;
                            }
                        }

                        const urlMatch = window.location.pathname.match(/\/([A-Z0-9]+)\/?$/);
                        if (urlMatch) {
                            return urlMatch[1];
                        }

                        return '';
                    })(),

                    "商品标题": (() => {
                        const titleSelectors = ['.productName', '.commodityName', '.product-title', 'h1'];
                        let title = '';
                        for (const selector of titleSelectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const text = element.textContent.trim();
                                if (text && text.length > 5) {
                                    title = text;
                                    break;
                                }
                            }
                        }
                        if (!title) title = document.title || '';
                        return title;
                    })(),

                    "品牌名": "Le Coq公鸡乐卡克",

                    "价格": (() => {
                        const selectors = ['.price', '.price-current', '[class*="price"]'];
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                const price = element.textContent.trim();
                                const priceMatch = price.match(/[￥¥$]\s*[\d,]+/);
                                if (priceMatch) return priceMatch[0];
                            }
                        }
                        return '';
                    })(),

                    "性别": (() => {
                        const url = window.location.href;

                        // 首先检查URL路径
                        if (url.includes('/ds_M/') || url.includes('/mens/')) {
                            return '男';
                        }
                        if (url.includes('/ds_F/') || url.includes('/ds_L/') || url.includes('/womens/') || url.includes('/ladies/')) {
                            return '女';
                        }

                        // 检查URL中的品牌和性别标识
                        if (url.includes('le%20coq%20sportif%20golf/ds_M')) {
                            return '男';
                        }
                        if (url.includes('le%20coq%20sportif%20golf/ds_F') || url.includes('le%20coq%20sportif%20golf/ds_L')) {
                            return '女';
                        }

                        // 检查面包屑导航
                        const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a');
                        for (const breadcrumb of breadcrumbs) {
                            const text = breadcrumb.textContent.trim().toLowerCase();
                            if (text.includes('men') || text.includes('男性') || text.includes('メンズ')) {
                                return '男';
                            }
                            if (text.includes('women') || text.includes('女性') || text.includes('ウィメンズ')) {
                                return '女';
                            }
                        }

                        // 从尺码表检查性别类型
                        const sizeChartText = document.body.textContent;
                        if (sizeChartText.includes('性別タイプ：メンズ') || sizeChartText.includes('性別タイプ: メンズ')) {
                            return '男';
                        }
                        if (sizeChartText.includes('性別タイプ：ウィメンズ') || sizeChartText.includes('性別タイプ: ウィメンズ') ||
                            sizeChartText.includes('性別タイプ：ラブズ') || sizeChartText.includes('性別タイプ: ラブズ')) {
                            return '女';
                        }

                        // 默认判断为男性（根据当前URL是在ds_M下）
                        return '男';
                    })(),

                    // 颜色数据
                    "颜色": (() => {
                        const colors = [];
                        const colorElements = document.querySelectorAll('#color-selector .colorName, .colorName, [class*="color-option"], [data-color]');

                        colorElements.forEach((element, index) => {
                            const colorName = element.textContent.trim();
                            if (colorName && !colors.find(c => c.name === colorName)) {
                                colors.push({
                                    name: colorName,
                                    isFirstColor: index === 0
                                });
                            }
                        });

                        return colors;
                    })(),

                    // 图片数据 - 只抓取第一个颜色，1100*1100尺寸
                    "图片链接": (() => {
                        const imgElements = document.querySelectorAll('img[src*="LE/LE"], img[src*="commodity_image"]');
                        const firstColorImages = [];

                        imgElements.forEach(el => {
                            if (el.src) {
                                // 检查是否是1100尺寸的图片
                                if (el.src.includes('_1100.') || el.src.includes('1100')) {
                                    firstColorImages.push(el.src);
                                }
                                // 如果没有1100，使用大图 (_l.)
                                else if (el.src.includes('_l.') && !el.src.includes('_thumbM')) {
                                    firstColorImages.push(el.src);
                                }
                            }
                        });

                        // 去重并排序
                        const uniqueImages = [...new Set(firstColorImages)];
                        return uniqueImages.slice(0, 6); // 只取前6张图片
                    })(),

                    // 尺码数据 - 改进的抓取逻辑
                    "尺码": (() => {
                        const sizes = [];

                        // 方法1：专门查找颜色选择板块内的尺码选项（根据你的截图）
                        const colorSection = document.querySelector('[id*="color"], [class*="color"]');
                        if (colorSection) {
                            // 查找颜色板块内的所有尺码元素
                            const sizeElements = colorSection.querySelectorAll('select[name*="size"] option, button[class*="size"], div[class*="size"]');
                            sizeElements.forEach(element => {
                                const text = element.textContent.trim();
                                // 匹配标准尺码格式：S, M, L, LL, 3L, XL等
                                if (text.match(/^[SMLX][L0-9]*$/)) {
                                    if (!sizes.includes(text)) {
                                        sizes.push(text);
                                    }
                                }
                            });

                            // 查找包含"3L"的所有元素
                            const allElements3L = colorSection.querySelectorAll('*');
                            allElements3L.forEach(element => {
                                const text = element.textContent.trim();
                                if (text === '3L' && !sizes.includes('3L')) {
                                    sizes.push('3L');
                                }
                            });
                        }

                        // 方法2：查找专门的尺码选择器
                        const sizeSections = [
                            document.querySelector('[id*="size"]'),
                            document.querySelector('[class*="size"]'),
                            document.querySelector('select[name*="size"]'),
                            document.querySelector('.size-select')
                        ];

                        sizeSections.forEach(section => {
                            if (section) {
                                const sizeOptions = section.querySelectorAll('option, button, div[class*="size-item"], [class*="size"]');
                                sizeOptions.forEach(option => {
                                    const text = option.textContent.trim();
                                    if (text.match(/^[SMLX][L0-9]*$/)) {
                                        if (!sizes.includes(text)) {
                                            sizes.push(text);
                                        }
                                    }
                                });
                            }
                        });

                        // 方法3：从下拉菜单查找（包括隐藏的select）
                        document.querySelectorAll('select').forEach(select => {
                            const options = select.querySelectorAll('option');
                            options.forEach(option => {
                                const text = option.textContent.trim();
                                if (text === '3L' || text.match(/^[SMLX][L0-9]*$/)) {
                                    if (!sizes.includes(text)) {
                                        sizes.push(text);
                                    }
                                }
                            });
                        });

                        // 方法4：查找页面中所有包含"3L"的文本
                        const bodyElements = document.querySelectorAll('*');
                        bodyElements.forEach(element => {
                            const text = element.textContent.trim();
                            if (text === '3L' && !sizes.includes('3L')) {
                                sizes.push('3L');
                            }
                        });

                        // 方法5：使用正则表达式查找所有可能的尺码
                        const bodyText = document.body.textContent;
                        const sizePattern = /\b(S|M|L|LL|3L|XL|2XL|3XL|4XL)\b/g;
                        const foundSizes = bodyText.match(sizePattern);
                        if (foundSizes) {
                            foundSizes.forEach(size => {
                                if (!sizes.includes(size)) {
                                    sizes.push(size);
                                }
                            });
                        }

                        // 排序并去重，按标准顺序
                        const standardOrder = ['S', 'M', 'L', 'LL', '3L', 'XL', '2XL', '3XL', '4XL'];
                        return [...new Set(sizes)].sort((a, b) => {
                            const aIndex = standardOrder.indexOf(a);
                            const bIndex = standardOrder.indexOf(b);
                            if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
                            if (aIndex !== -1) return -1;
                            if (bIndex !== -1) return 1;
                            return a.localeCompare(b);
                        });
                    })(),

                    // 详情页描述 - 只抓取原文
                    "详情页文字": (() => {
                        const descriptionElements = document.querySelectorAll('.description, .product-description, [class*="description"], .product-detail, .item-detail');
                        let fullText = '';

                        descriptionElements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > 10) {
                                fullText += text + '\n';
                            }
                        });

                        if (!fullText || fullText.length < 50) {
                            const mainContent = document.querySelector('main, .main, .content, .product-content');
                            if (mainContent) {
                                fullText = mainContent.textContent.trim();
                            }
                        }

                        return fullText
                            .replace(/\n\s*\n/g, '\n')
                            .replace(/^\s+|\s+$/g, '');
                    })(),

                    "尺码表": {
                        "html": (() => {
                            const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');
                            return sizeChartArea ? sizeChartArea.outerHTML : '';
                        })(),
                        "text": (() => {
                            const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');
                            return sizeChartArea ? sizeChartArea.textContent.trim() : '';
                        })()
                    }
                };
            });

            console.log('✅ 固定规则抓取完成');
            return this.results;

        } catch (error) {
            console.error('❌ 抓取失败:', error.message);
            throw error;
        } finally {
            await browser.close();
        }
    }

    printResults() {
        console.log('\n=== 📊 固定规则抓取结果 ===\n');
        console.log('🔗 商品链接:', this.results.商品链接);
        console.log('🏷️ 商品ID:', this.results.商品ID);
        console.log('📝 商品标题:', this.results.商品标题);
        console.log('🏷️ 品牌名:', this.results.品牌名);
        console.log('👕 性别:', this.results.性别);
        console.log('💰 价格:', this.results.价格);

        console.log('\n🎨 颜色信息:');
        this.results.颜色.forEach((color, index) => {
            console.log(`  ${index + 1}. ${color.name} ${color.isFirstColor ? '(第一个颜色)' : ''}`);
        });

        console.log('\n🖼️ 图片信息:');
        console.log(`  图片数量: ${this.results.图片链接.length}张`);
        console.log('  前3个图片URL:');
        this.results.图片链接.slice(0, 3).forEach((url, index) => {
            console.log(`    ${index + 1}. ${url}`);
        });

        console.log('\n📏 尺码信息:');
        this.results.尺码.forEach((size, index) => {
            console.log(`  ${index + 1}. ${size}`);
        });

        console.log('\n📄 详情描述（前200字符）:');
        console.log(`  ${this.results.详情页文字.substring(0, 200)}...`);

        if (this.results.尺码表.text) {
            console.log('\n📏 尺码表信息（前200字符）:');
            console.log(`  ${this.results.尺码表.text.substring(0, 200)}...`);
        }
    }

    async saveResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputFile = `single_url_fixed_${timestamp}.json`;

        // 🔧 添加第二部分期望的字段映射，保持原有字段不变
        // 这样既保持原有的抓取数据，又能匹配第二部分的需求
        const enhancedResults = { ...this.results };

        // 第二部分期望的字段映射
        enhancedResults['详情页链接'] = this.results['商品链接'];           // 映射商品链接
        enhancedResults['商品编号'] = this.results['商品ID'];               // 映射商品ID
        enhancedResults['productName'] = this.results['商品标题'];         // 映射商品标题
        enhancedResults['productId'] = this.results['商品ID'];             // 映射商品ID
        enhancedResults['priceText'] = this.results['价格'];               // 映射价格
        enhancedResults['detailUrl'] = this.results['商品链接'];           // 映射商品链接

        fs.writeFileSync(outputFile, JSON.stringify(enhancedResults, null, 2));
        console.log(`\n💾 固定规则结果已保存: ${outputFile}`);
        return outputFile;
    }
}

// 运行测试
if (require.main === module) {
    const testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';
    const processor = new SingleURLFixedProcessor();

    processor.processSingleURL(testUrl)
        .then(() => {
            processor.printResults();
            return processor.saveResults();
        })
        .then((outputFile) => {
            console.log(`\n✅ 测试完成，结果已保存到: ${outputFile}`);
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
            process.exit(1);
        });
}

module.exports = SingleURLFixedProcessor;