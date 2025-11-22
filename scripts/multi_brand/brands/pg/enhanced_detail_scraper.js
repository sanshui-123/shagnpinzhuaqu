#!/usr/bin/env node

/**
 * Le Coq Sportif Golf 增强版详情页抓取器
 * 根据用户截图要求优化数据提取
 */

const { chromium } = require('playwright');

class EnhancedDetailScraper {
    constructor() {
        this.url = '';
        this.results = {};
        this.brandName = 'Le Coq公鸡乐卡克'; // 根据用户要求写死品牌名
    }

    async scrapeDetailPage(url) {
        this.url = url;
        console.log('🔍 开始增强版抓取详情页:', url);

        const browser = await chromium.launch({
            headless: true, // 改为true，纯后台运行
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        });
        const page = await browser.newPage();

        try {
            // 访问页面
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 60000 // 增加到60秒
            });

            // 等待内容加载
            await page.waitForTimeout(5000);

            // 点击尺码表按钮以显示详细尺寸数据
            try {
                // 方法1：查找并点击"サイズ詳細"链接
                const sizeDetailButton = await page.locator('text=サイズ詳細').first();
                if (await sizeDetailButton.isVisible()) {
                    await sizeDetailButton.click();
                    console.log('✅ 点击了サイズ詳細按钮');
                } else {
                    // 方法2：查找包含"サイズ"的链接或按钮
                    const sizeLinks = await page.locator('a:has-text("サイズ"), button:has-text("サイズ")').all();
                    for (const link of sizeLinks) {
                        if (await link.isVisible()) {
                            await link.click();
                            console.log('✅ 点击了包含"サイズ"的按钮');
                            break;
                        }
                    }
                }
            } catch (error) {
                console.log('⚠️ 尝试点击尺码表按钮失败:', error.message);
                // 方法3：尝试使用JavaScript直接点击
                await page.evaluate(() => {
                    const allElements = document.querySelectorAll('*');
                    for (const element of allElements) {
                        const text = element.textContent.trim();
                        if (text.includes('サイズ詳細') || (text.includes('サイズ') && element.tagName === 'A')) {
                            try {
                                element.click();
                                return 'clicked';
                            } catch (e) {
                                // 继续尝试下一个
                            }
                        }
                    }
                    return 'not_found';
                });
            }

            await page.waitForTimeout(3000); // 等待尺码表内容加载

            // 使用single_url_fixed_processor.js的成功逻辑提取数据
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

                    "品牌名": "Le Coq公鸡乐卡克", // 写死品牌名

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
                        return uniqueImages; // 不限制图片数量
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
                            // 查找包含详细尺寸数据的表格（优先寻找包含着丈、肩宽、胸围的表格）
                            const sizeTables = document.querySelectorAll('table');
                            for (const table of sizeTables) {
                                const text = table.textContent;
                                // 优先查找包含具体测量项目的表格（包含数值的详细表格）
                                if ((text.includes('着丈') || text.includes('肩幅') || text.includes('胸囲') || text.includes('身丈')) &&
                                    /\\d+/.test(text)) {
                                    return table.outerHTML;
                                }
                            }
                            // 如果没找到详细数据，再查找基本的尺码表格
                            for (const table of sizeTables) {
                                const text = table.textContent;
                                if (text.includes('商品サイズ') || text.includes('実寸')) {
                                    return table.outerHTML;
                                }
                            }
                            return '';
                        })(),
                        "text": (() => {
                            // 查找包含详细尺寸数据的表格
                            const sizeTables = document.querySelectorAll('table');
                            for (const table of sizeTables) {
                                const text = table.textContent.trim();
                                // 优先查找包含具体测量项目的表格（包含数值的详细表格）
                                if ((text.includes('着丈') || text.includes('肩幅') || text.includes('胸囲') || text.includes('身丈')) &&
                                    /\\d+/.test(text)) {
                                    return text;
                                }
                            }
                            // 如果没找到详细数据，再查找基本的尺码表格
                            for (const table of sizeTables) {
                                const text = table.textContent.trim();
                                if (text.includes('商品サイズ') || text.includes('実寸')) {
                                    return text;
                                }
                            }
                            return '';
                        })()
                    }
                };
            });

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

            return enhancedResults;

        } catch (error) {
            console.error('❌ 抓取失败:', error.message);
            throw error;
        } finally {
            await browser.close();
        }
    }

    async extractProductCodeFromName(page) {
        return await page.evaluate(() => {
            // 首先尝试从尺码表中提取 LG5FWB50M 格式的编号
            const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');
            if (sizeChartArea) {
                const chartText = sizeChartArea.textContent;

                // 优先匹配"ブランド商品番号※店舗お問い合わせ用"后面的编号
                const afterBrandCodeText = chartText.split('ブランド商品番号※店舗お問い合わせ用')[1];
                if (afterBrandCodeText) {
                    const brandCodeMatch = afterBrandCodeText.match(/\b([A-Z]{2,}\d{4,})\b/);
                    if (brandCodeMatch) {
                        return brandCodeMatch[1];
                    }
                }

                // 通用匹配：寻找LG开头的编号
                const lgCodeMatch = chartText.match(/\b(LG[A-Z0-9]{6,})\b/);
                if (lgCodeMatch) {
                    return lgCodeMatch[1];
                }

                // 匹配其他品牌的字母数字组合
                const brandCodeMatch = chartText.match(/\b([A-Z]{2,}\d{4,})\b/);
                if (brandCodeMatch && brandCodeMatch[1].length >= 6) {
                    return brandCodeMatch[1];
                }
            }

            // 备选方案：从有name属性的元素中提取
            const elementsWithNames = document.querySelectorAll('[name]');

            for (const element of elementsWithNames) {
                const nameValue = element.getAttribute('name');
                if (nameValue && nameValue.match(/^[A-Z]{2,}\d{4,}$/)) {
                    return nameValue;
                }
            }

            // 最后尝试从URL中提取
            const urlMatch = window.location.pathname.match(/\/([A-Z0-9]+)\/?$/);
            if (urlMatch) {
                return urlMatch[1];
            }

            return '';
        });
    }

    async extractAndTranslateTitle(page) {
        return await page.evaluate(() => {
            // 提取日文标题
            const titleSelectors = [
                '.productName',
                '.commodityName',
                '.product-title',
                'h1'
            ];

            let japaneseTitle = '';
            for (const selector of titleSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const text = element.textContent.trim();
                    if (text && text.length > 5) {
                        japaneseTitle = text;
                        break;
                    }
                }
            }

            if (!japaneseTitle) {
                japaneseTitle = document.title || '';
            }

            // 简单的翻译映射（后续可接入GLM）
            const translations = {
                'ブルゾン': '夹克',
                'ジャケット': '夹克',
                'アウター': '外套',
                'ウィンドブレーカー': '防风衣',
                '中わた': '中棉',
                'ヒートナビ': '热航',
                'デタッチャブル': '可拆卸',
                '2WAY': '两用',
                'リバーシブル': '双面',
                'ゴルフ': '高尔夫',
                '袖取り外し': '可拆卸袖子'
            };

            let chineseTitle = japaneseTitle;
            Object.entries(translations).forEach(([jp, cn]) => {
                chineseTitle = chineseTitle.replace(new RegExp(jp, 'g'), cn);
            });

            return {
                original: japaneseTitle,
                translated: chineseTitle
            };
        });
    }

    async extractGenderFromPosition(page) {
        return await page.evaluate(() => {
            // 1. 从页面标题和元数据中判断
            const title = document.title.toLowerCase();
            const metaKeywords = document.querySelector('meta[name="keywords"]')?.content.toLowerCase() || '';

            // 检查明确的性别标识
            if (title.includes('men') || title.includes('男性') || metaKeywords.includes('men') || metaKeywords.includes('男性')) {
                return '男';
            }
            if (title.includes('women') || title.includes('女性') || title.includes('ladies') || metaKeywords.includes('women') || metaKeywords.includes('女性')) {
                return '女';
            }

            // 2. 从URL路径中判断
            const url = window.location.href;
            if (url.includes('/ds_M/') || url.includes('/mens/') || url.includes('men-')) {
                return '男';
            }
            if (url.includes('/ds_F/') || url.includes('/ds_L/') || url.includes('/womens/') || url.includes('women-')) {
                return '女';
            }

            // 3. 从面包屑导航判断（排除导航按钮）
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

            // 4. 从分类信息判断
            const categories = [
                'メンズゴルフウェア',
                'ladies golf',
                'women golf',
                'mens golf'
            ];

            const bodyText = document.body.textContent.toLowerCase();
            for (const category of categories) {
                if (bodyText.includes(category)) {
                    if (category.includes('men') || category.includes('メンズ')) {
                        return '男';
                    }
                    if (category.includes('women') || category.includes('ladies') || category.includes('ウィメンズ')) {
                        return '女';
                    }
                }
            }

            // 5. 从尺码范围判断
            const sizeElements = document.querySelectorAll('[class*="size"]');
            let hasMensSizes = false;
            let hasWomensSizes = false;

            sizeElements.forEach(element => {
                const text = element.textContent;
                if (text.includes('M') || text.includes('L')) hasMensSizes = true;
                if (text.includes('S') && text.includes('XL')) hasWomensSizes = true;
            });

            // 6. 如果还无法确定，检查URL中的特定路径
            if (url.includes('le%20coq%20sportif%20golf/ds_M')) {
                return '男';
            }
            if (url.includes('le%20coq%20sportif%20golf/ds_F') || url.includes('le%20coq%20sportif%20golf/ds_L')) {
                return '女';
            }

            // 7. 从尺码表中查找"性別タイプ"字段
            const sizeChartText = document.body.textContent;
            const genderTypeMatch = sizeChartText.match(/性別タイプ[：:\s]*([^メンズウィメンズラブズ]*(メンズ|ウィメンズ|ラブズ))/);
            if (genderTypeMatch) {
                const genderValue = genderTypeMatch[1];
                if (genderValue === 'メンズ') return '男';
                if (genderValue === 'ウィメンズ' || genderValue === 'ラブズ') return '女';
            }

            // 8. 从产品描述中的关键词判断
            const descriptionText = document.body.textContent;
            if (descriptionText.includes('men\'s golf') || descriptionText.includes('男性用')) {
                return '男';
            }
            if (descriptionText.includes('women\'s golf') || descriptionText.includes('女性用')) {
                return '女';
            }

            // 9. 默认规则：如果URL路径在ds_M下，则为男性
            if (url.includes('ds_M')) {
                return '男';
            }

            return 'Unisex';
        });
    }

    async extractPrice(page) {
        return await page.evaluate(() => {
            const selectors = [
                '.price',
                '.price-current',
                '[class*="price"]'
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    const price = element.textContent.trim();
                    const priceMatch = price.match(/[￥¥$]\s*[\d,]+/);
                    if (priceMatch) {
                        return priceMatch[0];
                    }
                }
            }

            return '';
        });
    }

    async extractColors(page) {
        return await page.evaluate(() => {
            const colors = [];
            const colorElements = document.querySelectorAll('#color-selector .colorName, .colorName');

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
        });
    }

    async extractImages(page) {
        return await page.evaluate(() => {
            const images = {
                total: 0,
                urls: [],
                firstColorImages: [],
                otherColorsImages: []
            };

            const imgElements = document.querySelectorAll('img[src*="LE/LE"], img[src*="commodity_image"]');

            const allImages = [];
            imgElements.forEach(el => {
                if (el.src && !allImages.find(img => img.src === el.src)) {
                    allImages.push({
                        src: el.src,
                        alt: el.alt || ''
                    });
                }
            });

            // 筛选大图
            const largeImages = allImages.filter(img =>
                img.src.includes('_l.') ||
                img.src.includes('_large') ||
                img.src.includes('1100')
            );

            // 按图片URL排序确保一致性
            largeImages.sort((a, b) => {
                const aNum = parseInt(a.src.match(/_(\d+)_l\.jpg/)?.[1] || '0');
                const bNum = parseInt(b.src.match(/_(\d+)_l\.jpg/)?.[1] || '0');
                return aNum - bNum;
            });

            // 规则：每个颜色6张图片，6个颜色 = 36张图片
            const imagesPerColor = 6;
            const totalColors = 6;
            const maxImages = imagesPerColor * totalColors;

            // 取前36张图片，如果不够就取全部
            const selectedImages = largeImages.slice(0, maxImages);

            // 分配给第一个颜色（6张）和其他颜色（30张）
            const firstColorImages = selectedImages.slice(0, imagesPerColor);
            const otherColorsImages = selectedImages.slice(imagesPerColor);

            images.total = selectedImages.length;
            images.urls = selectedImages.map(img => img.src);
            images.firstColorImages = firstColorImages.map(img => img.src);
            images.otherColorsImages = otherColorsImages.map(img => img.src);

            return images;
        });
    }

    async extractAllImageUrls(page) {
        return await page.evaluate(() => {
            // 查找所有产品图片
            const imgElements = document.querySelectorAll('img[src*="LE/LE"], img[src*="commodity_image"]');

            const allImageUrls = [];
            const uniqueUrls = new Set();

            imgElements.forEach(el => {
                if (el.src) {
                    // 去重并添加所有图片URL
                    if (!uniqueUrls.has(el.src)) {
                        uniqueUrls.add(el.src);
                        allImageUrls.push(el.src);
                    }
                }
            });

            // 如果没有找到产品图片，尝试查找其他可能的图片元素
            if (allImageUrls.length === 0) {
                const productImages = document.querySelectorAll('img[src*="jpg"], img[src*="jpeg"], img[src*="png"]');
                productImages.forEach(el => {
                    if (el.src && !el.src.includes('logo') && !el.src.includes('icon') && !uniqueUrls.has(el.src)) {
                        uniqueUrls.add(el.src);
                        allImageUrls.push(el.src);
                    }
                });
            }

            // 筛选大图并按颜色分组
            const largeImages = allImageUrls.filter(url =>
                url.includes('_l.') || url.includes('_large') || url.includes('1100')
            );

            if (largeImages.length === 0) return allImageUrls;

            // 应用您的完美图片规则：第一个颜色保留所有图片，其他颜色只保留前6张
            const filteredUrls = [];

            // 应用图片规则：第一个颜色保留所有图片，其他颜色只保留前6张
            let firstColorImages = [];
            let otherColorsImages = [];

            // 简单处理：前半部分作为第一个颜色，后半部分作为其他颜色
            // 这样可以避免假设，直接按比例分配
            const firstColorCount = Math.ceil(largeImages.length / 2);

            for (let i = 0; i < largeImages.length; i++) {
                if (i < firstColorCount) {
                    // 第一个颜色：保留所有图片
                    firstColorImages.push(largeImages[i]);
                } else {
                    // 其他颜色：只保留前6张
                    if (otherColorsImages.length < 6) {
                        otherColorsImages.push(largeImages[i]);
                    }
                }
            }

            console.log(`   📌 第一个颜色保留全部 ${firstColorImages.length} 张图片`);
            console.log(`   📌 其他颜色保留前6张图片（共${otherColorsImages.length}张）`);

            // 合并结果
            filteredUrls.push(...firstColorImages, ...otherColorsImages);

            return filteredUrls.length > 0 ? filteredUrls : allImageUrls;
        });
    }

    async extractSizes(page) {
        return await page.evaluate(() => {
            const sizes = [];

            // 方法1：查找所有可能的尺码元素
            const sizeSelectors = [
                '[class*="size"] option',
                '[class*="size"] li',
                '[class*="size"] span',
                '[name*="size"]',
                '.size-select option',
                '.size-list li'
            ];

            sizeSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    const text = element.textContent.trim();
                    // 匹配 S, M, L, LL, 3L 等尺码
                    const sizeMatch = text.match(/^[A-Z0-9]+$/);
                    if (sizeMatch && !sizes.includes(text)) {
                        sizes.push(text);
                    }
                });
            });

            // 方法2：从下拉菜单中查找
            const selectElements = document.querySelectorAll('select');
            selectElements.forEach(select => {
                const options = select.querySelectorAll('option');
                options.forEach(option => {
                    const text = option.textContent.trim();
                    const sizeMatch = text.match(/^[SML][L0-9]*$/);
                    if (sizeMatch && !sizes.includes(text)) {
                        sizes.push(text);
                    }
                });
            });

            // 方法3：查找页面中所有可能的尺码文本
            const bodyText = document.body.textContent;
            const sizePattern = /\b[SML][L0-9]*\b/g;
            const foundSizes = bodyText.match(sizePattern);
            if (foundSizes) {
                foundSizes.forEach(size => {
                    if (size !== 'M' || !sizes.includes('M')) { // 避免重复M
                        if (!sizes.includes(size)) {
                            sizes.push(size);
                        }
                    }
                });
            }

            // 排序并去重
            return [...new Set(sizes)].sort();
        });
    }

    async extractClothingCategory(page) {
        return await page.evaluate(() => {
            // 尝试从多个位置提取衣服分类信息

            // 方法1：从面包屑导航提取
            const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a, .breadcrumb li');
            for (const breadcrumb of breadcrumbs) {
                const text = breadcrumb.textContent.trim();
                if (text.includes('ウェア') || text.includes('ウエア') || text.includes('アウター') ||
                    text.includes('トップス') || text.includes('ボトムス') || text.includes('パンツ') ||
                    text.includes('スカート') || text.includes('ドレス') || text.includes('ジャケット') ||
                    text.includes('ブルゾン') || text.includes('コート') || text.includes('ベスト') ||
                    text.includes('シャツ') || text.includes('ニット') || text.includes('セーター') ||
                    text.includes('ポロシャツ') || text.includes('Tシャツ')) {
                    return text;
                }
            }

            // 方法2：从页面标题提取
            const title = document.title;
            if (title.includes('ブルゾン')) return 'ブルゾン';
            if (title.includes('ジャケット')) return 'ジャケット';
            if (title.includes('コート')) return 'コート';
            if (title.includes('ベスト')) return 'ベスト';
            if (title.includes('シャツ')) return 'シャツ';
            if (title.includes('ニット')) return 'ニット';
            if (title.includes('セーター')) return 'セーター';
            if (title.includes('ポロシャツ')) return 'ポロシャツ';
            if (title.includes('パンツ')) return 'パンツ';
            if (title.includes('スカート')) return 'スカート';
            if (title.includes('ドレス')) return 'ドレス';

            // 方法3：从产品分类标签提取
            const categoryElements = document.querySelectorAll('[class*="category"], [class*="tag"], .product-category');
            for (const element of categoryElements) {
                const text = element.textContent.trim();
                if (text && (text.includes('ウェア') || text.includes('アウター') || text.includes('トップス'))) {
                    return text;
                }
            }

            // 方法4：从商品描述关键词提取
            const description = document.body.textContent;
            if (description.includes('アウター')) return 'アウター';
            if (description.includes('トップス')) return 'トップス';

            // 如果都没找到，返回高尔夫服装
            return 'ゴルフウェア';
        });
    }


    async extractCategories(page) {
        return await page.evaluate(() => {
            const categories = [];
            const breadcrumbs = document.querySelectorAll('.breadcrumb a, [class*="breadcrumb"] a');

            breadcrumbs.forEach(el => {
                const text = el.textContent.trim();
                if (text && !text.includes('前に戻る') && !categories.includes(text)) {
                    categories.push(text);
                }
            });

            return categories;
        });
    }

    async extractAndTranslateDetailDescription(page) {
        return await page.evaluate(() => {
            // 提取详情页描述文字 - 只抓取原文，不翻译
            const descriptionElements = document.querySelectorAll('.description, .product-description, [class*="description"], .product-detail, .item-detail');
            let fullText = '';

            descriptionElements.forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length > 10) { // 过滤掉太短的文本
                    fullText += text + '\n';
                }
            });

            // 如果没有找到描述元素，尝试从页面主体内容中提取
            if (!fullText || fullText.length < 50) {
                const mainContent = document.querySelector('main, .main, .content, .product-content');
                if (mainContent) {
                    fullText = mainContent.textContent.trim();
                }
            }

            // 清理文本 - 移除多余的空白和换行
            fullText = fullText
                .replace(/\n\s*\n/g, '\n')
                .replace(/^\s+|\s+$/g, '');

            return {
                original: fullText
            };
        });
    }

    async extractAndTranslateSizeChart(page) {
        try {
            // 优先点击「サイズ表記」tab，确保尺码表加载
            const sizeTab = page.locator('button.tabs-nav__item.heading.heading--small', { hasText: 'サイズ表記' }).first();
            if (await sizeTab.count() > 0) {
                try {
                    await sizeTab.scrollIntoViewIfNeeded();
                    await sizeTab.click();
                    console.log('✅ 点击了「サイズ表記」tab');
                    await page.waitForSelector('div.table-wrapper table, div.table-wrapper', { timeout: 5000 });
                } catch (e) {
                    console.log('⚠️ 点击サイズ表記失败，继续使用旧逻辑:', e.message);
                }
            }

            // 使用Playwright的方法查找按钮（旧逻辑保留作为兜底）
            const sizeButton = await page.locator('button, a', { hasText: '商品サイズ' }).first();
            const sizeDetailButton = await page.locator('button, a', { hasText: 'サイズ詳細' }).first();

            let buttonToClick = null;
            if (await sizeButton.count() > 0) {
                buttonToClick = sizeButton.first();
            } else if (await sizeDetailButton.count() > 0) {
                buttonToClick = sizeDetailButton.first();
            } else {
                // 尝试通过class查找
                const classButton = await page.locator('[class*="size"] button').first();
                if (await classButton.count() > 0) {
                    buttonToClick = classButton.first();
                }
            }

            if (buttonToClick) {
                console.log('🔘 找到尺码表按钮，准备点击...');
                await buttonToClick.click();
                await page.waitForTimeout(2000);
            }

            // 提取尺码表内容 - 只抓取原文，不翻译
            const sizeChartData = await page.evaluate(() => {
                const sizeChartArea = document.querySelector('div.table-wrapper table') ||
                    document.querySelector('div.table-wrapper') ||
                    document.querySelector('table, [class*="size-table"], [class*="chart"]');

                if (sizeChartArea) {
                    let tableHtml = sizeChartArea.outerHTML; // 获取完整HTML包括table标签
                    let tableText = sizeChartArea.textContent || '';

                    return {
                        html: tableHtml,
                        text: tableText.trim()
                    };
                }
                return null;
            });

            return sizeChartData || {
                html: '',
                text: ''
            };
        } catch (error) {
            console.log('⚠️ 尺码表提取失败:', error.message);
        }

        return {
            html: '',
            translatedHtml: '',
            text: '',
            translatedText: ''
        };
    }

    printResults() {
        console.log('\n=== 📊 增强版详情页抓取结果 ===\n');
        console.log('🔗 商品链接:', this.results.商品链接);
        console.log('🏷️ 商品ID:', this.results.商品ID);
        console.log('📝 商品标题:');
        console.log('  原文:', this.results.商品标题.original);
        console.log('  译文:', this.results.商品标题.translated);
        console.log('🏷️ 品牌名:', this.results.品牌名);
        console.log('👕 性别:', this.results.性别);
        console.log('💰 价格:', this.results.价格);

        console.log('\n🎨 颜色信息:');
        this.results.颜色.forEach((color, index) => {
            console.log(`  ${index + 1}. ${color.name}`);
        });

        console.log('\n🖼️ 图片统计:');
        console.log(`  总数: ${this.results.图片总数.total}张`);
        console.log(`  图片URL总数: ${this.results.图片链接 ? this.results.图片链接.length : 0}个`);
        if (this.results.图片链接 && this.results.图片链接.length > 0) {
            console.log(`  前3个图片URL:`);
            this.results.图片链接.slice(0, 3).forEach((url, index) => {
                console.log(`    ${index + 1}. ${url}`);
            });
        }

        console.log('\n📏 尺码信息:');
        this.results.尺码.forEach((size, index) => {
            console.log(`  ${index + 1}. ${size.size}`);
        });

        console.log('\n👕 衣服分类:', this.results.衣服分类);

        console.log('\n📄 详情描述（译文前200字符）:');
        console.log(`  ${this.results.详情页文字.translated.substring(0, 200)}...`);

        if (this.results.尺码表.text) {
            console.log('\n📏 尺码表信息（前200字符）:');
            console.log(`  ${this.results.尺码表.translatedText.substring(0, 200)}...`);
        }
    }
}

// 运行测试
if (require.main === module) {
    const testUrl = 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/';
    const scraper = new EnhancedDetailScraper();

    scraper.scrapeDetailPage(testUrl)
        .then(results => {
            scraper.results = results;

            // 显示完整的抓取数据
            console.log('\n=== 🎯 完整抓取数据输出 ===\n');
            console.log('📄 JSON格式完整输出：');
            console.log(JSON.stringify(results, null, 2));

            scraper.printResults();

            // 保存结果到文件
            const fs = require('fs');
            const outputPath = './golf_content/lecoqgolf/';

            if (!fs.existsSync(outputPath)) {
                fs.mkdirSync(outputPath, { recursive: true });
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const outputFile = `${outputPath}single_url_complete_data_${timestamp}.json`;

            fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
            console.log(`\n💾 完整数据已保存: ${outputFile}`);
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
        });
}

module.exports = EnhancedDetailScraper;
