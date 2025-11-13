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
        this.brandName = 'le coq sportif golf'; // 品牌写死
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

            // 按照新要求提取数据
            this.results = {
                商品链接: url,
                商品ID: await this.extractProductCodeFromName(page),
                商品标题: await this.extractAndTranslateTitle(page),
                品牌名: this.brandName, // 写死品牌
                价格: await this.extractPrice(page),
                性别: await this.extractGenderFromPosition(page),
                颜色: await this.extractColors(page),
                图片总数: await this.extractImages(page),
                图片链接: await this.extractAllImageUrls(page),
                尺码: await this.extractSizes(page),
                衣服分类: await this.extractClothingCategory(page),
                详情页文字: await this.extractAndTranslateDetailDescription(page),
                尺码表: await this.extractAndTranslateSizeChart(page)
            };

            return this.results;

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

            images.total = largeImages.length;
            images.urls = largeImages.map(img => img.src);
            images.firstColorImages = largeImages.slice(0, 6).map(img => img.src);
            images.otherColorsImages = largeImages.slice(0, 6).map(img => img.src);

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

            return allImageUrls;
        });
    }

    async extractSizes(page) {
        return await page.evaluate(() => {
            const sizes = [];
            const sizeElements = document.querySelectorAll('[class*="size"]');

            sizeElements.forEach(element => {
                const text = element.textContent.trim();
                const sizeMatch = text.match(/[SML][L0-9]*/);
                if (sizeMatch) {
                    const size = sizeMatch[0];
                    if (!sizes.find(s => s.size === size)) {
                        sizes.push({
                            size: size
                        });
                    }
                }
            });

            return sizes;
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
            // 提取详情页描述文字
            const descriptionElements = document.querySelectorAll('.description, .product-description, [class*="description"]');
            let fullText = '';

            descriptionElements.forEach(el => {
                const text = el.textContent.trim();
                if (text) {
                    fullText += text + '\n';
                }
            });

            // 简单翻译映射（后续可接入GLM）
            const translations = {
                '袖が取り外し可能な2WAY仕様': '可拆卸袖子的两用设计',
                '中わたブルゾン': '中棉夹克',
                'ブルゾンとして、ベストとして': '作为夹克，作为马甲',
                'アームホール内側': '袖窿内侧',
                'ストレッチ素材のアクションプリーツ': '伸缩材质的活动褶',
                '肩甲骨周りの可動域を広げ': '扩大肩胛骨周围的活动范围',
                'スイング時のストレスを軽減': '减轻挥杆时的压力',
                '独自開発の保温機能': '独自开发的保温功能',
                '光吸収性能を高めた蓄熱保温素材': '提高了光吸收性能的蓄热保温材料',
                '従来の未加工素材と比べて+5℃の効果': '与传统未加工材料相比+5℃的效果',
                'ほぼ全ての光を熱に変換': '将几乎所有光转化为热量',
                'たとえ運動しなくても暖かさを実感': '即使不运动也能感受到温暖',
                'トライアングル柄のキルトステッチ': '三角形图案的绗缝',
                'デザイン性と保温性を両立': '兼顾设计性和保温性',
                'ロゴ刺繍': '标志刺绣',
                'ワッペン': '布章',
                '配色テープ': '配色带',
                'ファスナー付きポケット': '带拉链的口袋',
                'シルエット：レギュラー': '版型：常规',
                '表地：ストレッチ性と防風性を兼ね備えたポリエステルタフタ': '表料：兼具伸缩性和防风性的聚酯纤维塔夫绸',
                '裏地：ヒートナビ機能付きのストレッチ裏地': '里料：带热航功能的伸缩里料',
                '中わた：ストレッチ性のある機能中わた': '中棉：有伸缩性的功能中棉',
                '機能性とファッション性あふれる': '充满功能性和时尚性',
                'お洒落なゴルフスタイルを創造します': '创造时尚的高尔夫风格'
            };

            let translatedText = fullText;
            Object.entries(translations).forEach(([jp, cn]) => {
                translatedText = translatedText.replace(new RegExp(jp, 'g'), cn);
            });

            return {
                original: fullText,
                translated: translatedText
            };
        });
    }

    async extractAndTranslateSizeChart(page) {
        try {
            // 使用Playwright的方法查找按钮
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

                // 提取尺码表内容
                const sizeChartData = await page.evaluate(() => {
                    const sizeChartArea = document.querySelector('table, [class*="size-table"], [class*="chart"]');

                    if (sizeChartArea) {
                        let tableHtml = sizeChartArea.innerHTML;
                        let tableText = sizeChartArea.textContent || '';

                        // 简单的日文到中文翻译映射
                        const translations = {
                            '重さ': '重量',
                            '着丈': '衣长',
                            '肩幅': '肩宽',
                            '胸囲': '胸围',
                            '袖丈': '袖长',
                            '袖幅': '袖宽',
                            '（片足）': '（单只）',
                            '商品サイズ': '商品尺寸',
                            '商品サイズ(実寸)': '商品尺寸（实寸）',
                            'ヌード寸': '裸体尺寸'
                        };

                        let translatedHtml = tableHtml;
                        let translatedText = tableText;

                        Object.entries(translations).forEach(([jp, cn]) => {
                            translatedHtml = translatedHtml.replace(new RegExp(jp, 'g'), cn);
                            translatedText = translatedText.replace(new RegExp(jp, 'g'), cn);
                        });

                        return {
                            html: tableHtml,
                            translatedHtml: translatedHtml,
                            text: tableText,
                            translatedText: translatedText
                        };
                    }
                    return null;
                });

                return sizeChartData || {
                    html: '',
                    translatedHtml: '',
                    text: '',
                    translatedText: ''
                };
            }
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
            scraper.printResults();

            // 保存结果到文件
            const fs = require('fs');
            const outputPath = './golf_content/lecoqgolf/';

            if (!fs.existsSync(outputPath)) {
                fs.mkdirSync(outputPath, { recursive: true });
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const outputFile = `${outputPath}enhanced_detail_${timestamp}.json`;

            fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
            console.log(`\n💾 增强版结果已保存: ${outputFile}`);
        })
        .catch(error => {
            console.error('❌ 测试失败:', error);
        });
}

module.exports = EnhancedDetailScraper;