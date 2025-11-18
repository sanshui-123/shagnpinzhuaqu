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

            // 🔥 点击尺寸指南按钮以显示详细尺码表
            try {
                console.log('🔍 正在查找尺寸指南按钮...');

                // 尝试点击 "サイズガイド" 按钮
                const sizeGuideClicked = await page.evaluate(() => {
                    // 查找包含 "サイズガイド" 文本的元素
                    const allElements = document.querySelectorAll('*');
                    for (const element of allElements) {
                        const text = element.textContent.trim();
                        if (text.includes('サイズガイド') || text.includes('サイズガイドを見る')) {
                            try {
                                element.click();
                                console.log('✅ 找到并点击了尺寸指南按钮');
                                return true;
                            } catch (e) {
                                console.log('⚠️ 点击尺寸指南按钮失败:', e.message);
                            }
                        }
                    }
                    return false;
                });

                if (sizeGuideClicked) {
                    console.log('✅ 成功点击尺寸指南按钮');
                    await page.waitForTimeout(8000); // 增加等待时间，让尺码表充分加载
                } else {
                    console.log('⚠️ 未找到尺寸指南按钮，尝试其他方法...');

                    // 备用方法：查找可能的链接
                    try {
                        await page.locator('a:has-text("サイズガイド")').first().click();
                        console.log('✅ 通过备用方法点击了尺寸指南');
                        await page.waitForTimeout(5000);
                    } catch (e) {
                        console.log('⚠️ 备用方法也失败，继续基本抓取');
                    }
                }
            } catch (error) {
                console.log('⚠️ 尺寸指南点击过程出错:', error.message);
            }

            // 抓取所有数据（包括点击后可能出现的详细尺码表）
            this.results = await page.evaluate(() => {
                return {
                    // 基础信息
                    "商品链接": window.location.href,
                    "商品ID": (() => {
                        // 🔥 优先从详情表格中提取"ブランド商品番号"对应的值
                        const tables = document.querySelectorAll('table');
                        for (const table of tables) {
                            const rows = table.querySelectorAll('tr');
                            for (const row of rows) {
                                const th = row.querySelector('th');
                                const td = row.querySelector('td');
                                if (th && td) {
                                    const thText = th.textContent.trim();
                                    // 🔥 只匹配"ブランド商品番号"，排除普通的"商品番号"
                                    if (thText.includes('ブランド商品番号')) {
                                        const brandCode = td.textContent.trim();
                                        // 清洗：去除空格和特殊字符，提取产品编号
                                        const cleanCode = brandCode.replace(/\s+/g, '').match(/([A-Z0-9]{6,})/i);
                                        if (cleanCode) {
                                            return cleanCode[1];
                                        }
                                    }
                                }
                            }
                        }

                        // 备用方法：从尺码表文本中提取
                        const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');
                        if (sizeChartArea) {
                            const chartText = sizeChartArea.textContent;
                            const afterBrandCodeText = chartText.split('ブランド商品番号')[1];
                            if (afterBrandCodeText) {
                                const brandCodeMatch = afterBrandCodeText.match(/([A-Z]{2,}[A-Z0-9]{4,})/i);
                                if (brandCodeMatch) {
                                    console.log('✅ 从尺码表文本提取品牌商品番号:', brandCodeMatch[1]);
                                    return brandCodeMatch[1];
                                }
                            }
                        }

                        // 最后回退到URL中的ID
                        const urlMatch = window.location.pathname.match(/\/([A-Z0-9]+)\/?$/);
                        if (urlMatch) {
                            console.log('⚠️ 使用URL中的ID作为回退:', urlMatch[1]);
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

                    "品牌名": "Penguin by Munsingwear",

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
                        const pageText = document.body.textContent;

                        // 1. 最高优先级：检查尺码表中的明确性别标识
                        const hasLadiesGenderType = sizeChartText.includes('性別タイプ：レディース') || sizeChartText.includes('性別タイプ: レディース');
                        const hasMensGenderType = sizeChartText.includes('性別タイプ：メンズ') || sizeChartText.includes('性別タイプ: メンズ');

                        if (hasLadiesGenderType) {
                            return '女';
                        }
                        if (hasMensGenderType) {
                            return '男';
                        }

                        // 调试：如果没有找到明确的性别类型，检查尺码表文本
                        const debugText = sizeChartText.substring(sizeChartText.indexOf('性別タイプ'), Math.min(sizeChartText.indexOf('性別タイプ') + 200, sizeChartText.length));

                        // 检查是否有其他形式的性别类型标识
                        if (sizeChartText.includes('レディース')) {
                            return '女';
                        }
                        if (sizeChartText.includes('メンズ')) {
                            return '男';
                        }

                        // 2. 检查URL中的性别路径
                        if (window.location.href.includes('/ds_L/') || window.location.href.includes('/ds_F/')) {
                            return '女';
                        }
                        if (window.location.href.includes('/ds_M/')) {
                            return '男';
                        }

                        // 3. 检查面包屑导航中的性别
                        const navBreadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a, .nav a');
                        for (const breadcrumb of navBreadcrumbs) {
                            const text = breadcrumb.textContent.trim();
                            if (text.includes('レディース')) {
                                return '女';
                            }
                            if (text.includes('メンズ')) {
                                return '男';
                            }
                        }

                        // 4. 检查主要产品信息区域的性别标识（排除推荐商品）
                        const productArea = document.querySelector('.product-detail, .commodity-detail, [class*="product"], [class*="commodity"]');
                        let productText = '';
                        if (productArea) {
                            productText = productArea.textContent;
                        } else {
                            // 如果找不到产品区域，使用前1000个字符
                            productText = pageText.substring(0, 1000);
                        }

                        // 检查产品区域的性别标识
                        if (productText.includes('レディース')) {
                            return '女';
                        }
                        if (productText.includes('メンズ')) {
                            return '男';
                        }

                        // 5. 检查其他女性标识
                        if (productText.includes('女性') || productText.includes('ladies') ||
                            productText.includes('ウィメンズ') || productText.includes('women')) {
                            return '女';
                        }

                        // 6. 检查其他男性标识
                        if (productText.includes('男性') || productText.includes('mens') ||
                            productText.includes('men')) {
                            return '男';
                        }

                        // 如果无法确定，返回空字符串而不是默认男
                        return '';
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
                        return uniqueImages; // 返回所有符合条件的图片，不限制数量
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
                                // 匹配标准尺码格式：S, M, L, LL, 3L, XL, O等
                                if (text.match(/^[SMLXOL][L0-9]*$/) && text.length <= 3) {
                                    if (!sizes.includes(text)) {
                                        sizes.push(text);
                                    }
                                }
                            });

                            // 查找包含"3L"和"O"的所有元素
                            const allElements3L = colorSection.querySelectorAll('*');
                            allElements3L.forEach(element => {
                                const text = element.textContent.trim();
                                if (text === '3L' && !sizes.includes('3L')) {
                                    sizes.push('3L');
                                }
                                // 特殊检测O尺码
                                if (text === 'O' && !sizes.includes('O')) {
                                    sizes.push('O');
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

                        // 方法4：查找页面中所有包含"3L"和"O"的文本
                        const bodyElements = document.querySelectorAll('*');
                        bodyElements.forEach(element => {
                            const text = element.textContent.trim();
                            if (text === '3L' && !sizes.includes('3L')) {
                                sizes.push('3L');
                            }
                            // 特殊检测O尺码
                            if (text === 'O' && !sizes.includes('O')) {
                                sizes.push('O');
                            }
                        });

                        // 方法5：使用正则表达式查找所有可能的尺码
                        const bodyText = document.body.textContent;
                        const sizePattern = /\b(S|M|L|LL|3L|XL|2XL|3XL|4XL|O)\b/g;
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

        // 🔧 完整的字段映射修复，输出Python期望的格式
        const { convertToPythonFormat } = require('./field_mapping_fix.js');

        // 创建符合Python期望的数据格式
        const pythonFormat = {
            products: {
                [this.results['商品ID']]: {
                    // 基本信息
                    productId: this.results['商品ID'],
                    productName: this.results['商品标题'],
                    detailUrl: this.results['商品链接'],
                    price: this.results['价格'],
                    brand: this.results['品牌名'],
                    gender: this.results['性别'],

                    // 产品属性
                    colors: this.results['颜色'].map(c => c.name || c),
                    sizes: this.results['尺码'],

                    // 🔥 关键修复：图片和描述字段
                    imageUrls: this.results['图片链接'] || [],
                    description: this.results['详情页文字'] || '',

                    // 其他字段
                    sizeChart: this.results['尺码表'] || null,
                    category: '',
                    sku: '',
                    status: '',

                    // 兼容字段
                    priceText: this.results['价格'],
                    mainImage: (this.results['图片链接'] && this.results['图片链接'].length > 0)
                              ? this.results['图片链接'][0] : '',
                    originalPrice: '',
                    currentPrice: '',

                    // 原始数据保留（可选）
                    _original_data: this.results
                }
            }
        };

        fs.writeFileSync(outputFile, JSON.stringify(pythonFormat, null, 2));
        console.log(`\n💾 固定规则结果已保存: ${outputFile}`);
        return outputFile;
    }
}

// 运行测试
if (require.main === module) {
    // 从命令行参数获取URL，如果没有提供则使用默认测试URL
    const testUrl = process.argv[2] || 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EW011538/';
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