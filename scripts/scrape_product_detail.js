#!/usr/bin/env node

/**
 * CallawayJP 产品详情抓取脚本 - 精简版
 * 纯数据抓取，不含任何AI改写功能
 * 输出格式对齐 feishu_update/baseline/inputs/sample_product_details.json
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// 颜色翻译对照表
const COLOR_NAME_TRANSLATION = {
    // 基础颜色
    'White': '白色',
    'Black': '黑色',
    'Red': '红色',
    'Blue': '蓝色',
    'Green': '绿色',
    'Yellow': '黄色',
    'Pink': '粉色',
    'Purple': '紫色',
    'Orange': '橙色',
    'Brown': '棕色',
    'Gray': '灰色',
    'Grey': '灰色',

    // CallawayJP 特有颜色
    'Navy': '藏青色',
    'Royal': '宝蓝色',
    'Sky Blue': '天蓝色',
    'Light Blue': '浅蓝色',
    'Dark Blue': '深蓝色',
    'Turquoise': '绿松石色',
    'Teal': '青色',

    // 红色系
    'Burgundy': '酒红色',
    'Maroon': '栗色',
    'Coral': '珊瑚色',
    'Rose': '玫瑰色',
    'Fuchsia': '紫红色',
    'Magenta': '洋红色',

    // 绿色系
    'Olive': '橄榄色',
    'Khaki': '卡其色',
    'Lime': '青柠色',
    'Mint': '薄荷色',
    'Forest': '森林绿',
    'Emerald': '翡翠绿',

    // 灰色系
    'Charcoal': '炭灰色',
    'Silver': '银色',
    'Slate': '石板灰',
    'Heather': '麻灰色',

    // 棕色系
    'Tan': '棕褐色',
    'Beige': '米色',
    'Cream': '奶油色',
    'Ivory': '象牙色',
    'Ecrus': '米白色',
    'Camel': '驼色',

    // 紫色系
    'Lavender': '薰衣草紫',
    'Violet': '紫罗兰',
    'Plum': '梅子色',

    // 黄色系
    'Gold': '金色',
    'Mustard': '芥末黄',
    'Lemon': '柠檬黄',

    // 粉色系
    'Peach': '桃色',
    'Salmon': '鲑鱼粉',

    // 橙色系
    'Burnt Orange': '焦橙色',

    // 日文颜色（如果需要保留日文）
    'ホワイト': '白色',
    'ブラック': '黑色',
    'レッド': '红色',
    'ブルー': '蓝色',
    'ネイビー': '藏青色',
    'グレー': '灰色',
    'グリーン': '绿色',
    'イエロー': '黄色',
    'ピンク': '粉色',
    'パープル': '紫色',
    'オレンジ': '橙色',
    'ブラウン': '棕色',
    'ベージュ': '米色',
    'アイボリー': '象牙色',
    'カーキ': '卡其色',
    'オリーブ': '橄榄色',
    'ターコイズ': '绿松石色',
    'コーラル': '珊瑚色',
    'ローズ': '玫瑰色',
    'ラベンダー': '薰衣草紫',
    'ワイン': '酒红色',
    'モカ': '摩卡色',
    'チャコール': '炭灰色',
    'シルバー': '银色',
    'ゴールド': '金色'
};

// 颜色翻译函数
function translateColorName(englishColor) {
    if (!englishColor) return '';

    // 去除前后空格
    const colorName = englishColor.trim();

    // 直接查找翻译表
    if (COLOR_NAME_TRANSLATION[colorName]) {
        return COLOR_NAME_TRANSLATION[colorName];
    }

    // 尝试部分匹配（处理复合颜色名称）
    const lowerColorName = colorName.toLowerCase();
    for (const [english, chinese] of Object.entries(COLOR_NAME_TRANSLATION)) {
        if (lowerColorName.includes(english.toLowerCase())) {
            return chinese;
        }
    }

    // 如果没找到翻译，返回原名称
    return colorName;
}

// 生成多行中文颜色文本
function generateColorsCnText(colors) {
    if (!colors || colors.length === 0) {
        return '';
    }

    const colorLines = [];

    colors.forEach(color => {
        const englishName = color.name || '';
        const chineseName = translateColorName(englishName);

        // 只输出中文颜色名称
        if (chineseName) {
            colorLines.push(chineseName);
        } else if (englishName) {
            colorLines.push(englishName); // 如果翻译失败，保留原名称
        }
    });

    return colorLines.join('\n');
}

// 参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        url: null,
        productId: null,
        outputDir: 'CallawayJP/results'
    };

    for (let i = 0; i < args.length; i++) {
        switch(args[i]) {
            case '--url':
                options.url = args[++i];
                break;
            case '--product-id':
                options.productId = args[++i];
                break;
            case '--output-dir':
                options.outputDir = args[++i];
                break;
            case '--help':
                console.log(`
使用方法:
  node scrape_product_detail.js --url <产品URL> [选项]

参数:
  --url <url>              产品详情页URL (必需)
  --product-id <id>        产品ID (可选，从URL自动提取)
  --output-dir <path>      输出目录 (默认: CallawayJP/results)

示例:
  node scrape_product_detail.js --url "https://www.callawaygolf.jp/mens/tops/polo/C25128100_.html?pid=C25128100_0010_S"
                `);
                process.exit(0);
                break;
        }
    }

    if (!options.url) {
        console.error('错误: 需要提供 --url 参数');
        process.exit(1);
    }

    // 从URL自动提取productId
    if (!options.productId) {
        const match = options.url.match(/\/([A-Z]\d+)_\.html/);
        if (match) {
            options.productId = match[1];
        }
    }

    return options;
}

// 提取产品数据的主函数
async function extractProductData(page) {
    console.log('🔍 开始提取产品数据...');
    
    return await page.evaluate(() => {
        const result = {
            productDetail: null,
            imageGroups: [],
            variationAttributes: null,
            variants: [],
            sizeChart: null,
            dataSources: []
        };

        // 全局调试：检查页面上所有可能包含描述的元素
        console.log('🔍 全局搜索：检查页面上的描述元素...');
        const allElements = document.querySelectorAll('*');
        let foundElements = [];

        for (let element of allElements) {
            const text = element.textContent || '';
            if (text.includes('今シーズンの') || text.includes('スターストレッチ') || text.includes('千鳥')) {
                foundElements.push({
                    tag: element.tagName.toLowerCase(),
                    className: element.className || '',
                    id: element.id || '',
                    textLength: text.length,
                    preview: text.substring(0, 200)
                });
            }
        }

        if (foundElements.length > 0) {
            result.debugElementsInfo = foundElements;
            console.log(`🎉 找到 ${foundElements.length} 个包含描述内容的元素`);
            foundElements.forEach((elem, index) => {
                console.log(`  元素 ${index + 1}: ${elem.tag}.${elem.className || 'no-class'} [${elem.id || 'no-id'}]`);
                console.log(`    文本长度: ${elem.textLength} 字符`);
                console.log(`    预览: ${elem.preview}...`);
            });
        } else {
            console.log('⚠️ 未找到包含描述内容的元素');
        }

        try {
            // 1. 优先尝试 __NEXT_DATA__
            if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.pageProps) {
                console.log('✓ 找到 __NEXT_DATA__');
                const pageProps = window.__NEXT_DATA__.props.pageProps;
                if (pageProps.productDetail) {
                    result.productDetail = pageProps.productDetail;
                    result.dataSources.push('next_data');

                    // 检查描述内容和来源
                    const desc = pageProps.productDetail.description || pageProps.productDetail.longDescription || '';
                    if (desc) {
                        console.log('🎉 在 __NEXT_DATA__ 中找到描述内容!');
                        console.log(`  数据来源: __NEXT_DATA__.props.pageProps.productDetail`);
                        console.log(`  描述长度: ${desc.length} 字符`);
                        console.log(`  描述预览: ${desc.substring(0, 200)}...`);

                        // 添加到result中，以便在Node.js环境中查看
                        result.debugDescriptionInfo = {
                            strategy: '__NEXT_DATA__',
                            length: desc.length,
                            preview: desc.substring(0, 300),
                            source: '__NEXT_DATA__.props.pageProps.productDetail',
                            description: desc.substring(0, 500) // 保存更多内容用于分析
                        };
                    } else {
                        console.log('⚠️ __NEXT_DATA__ 中没有找到描述内容');
                        result.debugDescriptionInfo = {
                            strategy: '__NEXT_DATA__',
                            found: false,
                            message: '__NEXT_DATA__ 中没有找到描述内容'
                        };
                    }
                }
            }

            // 2. 搜索 __next_f 数据
            if (window.self && window.self.__next_f && Array.isArray(window.self.__next_f)) {
                console.log('🔍 正在搜索 __next_f 数据...');
                for (let i = 0; i < window.self.__next_f.length; i++) {
                    try {
                        const item = window.self.__next_f[i];
                        if (Array.isArray(item) && item.length > 1 && typeof item[1] === 'string') {
                            const jsonStr = item[1];
                            if (jsonStr.includes('productDetail') || jsonStr.includes('imageGroups')) {
                                const parsed = JSON.parse(jsonStr);
                                
                                // 递归查找productDetail
                                function findProductDetail(obj, path = '') {
                                    if (!obj || typeof obj !== 'object') return null;
                                    
                                    if (obj.productDetail) {
                                        console.log(`✓ 在 ${path} 找到 productDetail`);
                                        return obj.productDetail;
                                    }
                                    
                                    for (const [key, value] of Object.entries(obj)) {
                                        if (typeof value === 'object') {
                                            const found = findProductDetail(value, `${path}.${key}`);
                                            if (found) return found;
                                        }
                                    }
                                    return null;
                                }
                                
                                const foundDetail = findProductDetail(parsed, `__next_f[${i}]`);
                                if (foundDetail && !result.productDetail) {
                                    result.productDetail = foundDetail;
                                    result.dataSources.push('__next_f.productDetail');
                                }
                            }
                        }
                    } catch (e) {
                        // 忽略解析错误，继续下一个
                    }
                }
            }

            // 3. DOM数据提取策略 - 获取真实的颜色、图片、尺码
            console.log('🔍 开始DOM数据提取...');
            
            // 提取颜色选择器数据
            const colorElements = document.querySelectorAll('[data-color], [data-colorcode], .color-selector button, .variant-color');
            const extractedColors = [];
            const extractedImageGroups = [];
            
            // 尝试多种颜色选择器模式
            const colorSelectors = [
                '[data-color]',
                '[data-colorcode]', 
                '.color-selector button',
                '.variant-color',
                'button[class*="color"]',
                '[class*="swatch"]'
            ];
            
            console.log('🎨 搜索颜色选择器...');
            
            for (const selector of colorSelectors) {
                const elements = document.querySelectorAll(selector);
                console.log(`发现 ${elements.length} 个 ${selector} 元素`);
                
                elements.forEach((element, index) => {
                    const colorCode = element.getAttribute('data-color') || 
                                    element.getAttribute('data-colorcode') ||
                                    element.getAttribute('data-value') ||
                                    element.getAttribute('value') || 
                                    element.textContent?.trim();
                                    
                    const colorName = element.getAttribute('title') ||
                                    element.getAttribute('aria-label') ||
                                    element.textContent?.trim() ||
                                    colorCode;
                    
                    if (colorCode && colorName && !extractedColors.some(c => c.code === colorCode)) {
                        extractedColors.push({
                            code: colorCode,
                            name: colorName,
                            selector: selector
                        });
                        console.log(`✓ 找到颜色: ${colorName} (${colorCode})`);
                    }
                });
                
                if (extractedColors.length > 0) break; // 找到颜色就停止
            }
            
            // 提取尺码选择器数据
            const extractedSizes = [];
            const sizeSelectors = [
                '[data-size]',
                '.size-selector button',
                '.variant-size',
                'button[class*="size"]',
                'select[name*="size"] option',
                '[class*="size-option"]'
            ];
            
            console.log('📏 搜索尺码选择器...');
            
            for (const selector of sizeSelectors) {
                const elements = document.querySelectorAll(selector);
                console.log(`发现 ${elements.length} 个 ${selector} 元素`);
                
                elements.forEach(element => {
                    const sizeValue = element.getAttribute('data-size') ||
                                    element.getAttribute('data-value') ||
                                    element.getAttribute('value') ||
                                    element.textContent?.trim();
                    
                    if (sizeValue && !extractedSizes.includes(sizeValue)) {
                        extractedSizes.push(sizeValue);
                        console.log(`✓ 找到尺码: ${sizeValue}`);
                    }
                });
                
                if (extractedSizes.length > 0) break; // 找到尺码就停止
            }
            
            // 提取所有图片
            const allImages = [];
            const imageSelectors = [
                'img[src*="callawaygolf"]',
                'img[src*="webdamdb"]',
                '.product-images img',
                '.gallery img',
                '[class*="image"] img'
            ];
            
            console.log('🖼️ 搜索产品图片...');
            
            // 图片URL过滤函数 - 只保留1280尺寸商品图
            function isValidProductImage(imgSrc) {
                if (!imgSrc) return false;
                
                // 必须以指定格式开头
                const validPrefix = 'https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_';
                if (!imgSrc.startsWith(validPrefix)) {
                    return false;
                }
                
                // 排除追踪链接和缩略图
                const blockedPatterns = [
                    't.co/',
                    'analytics.twitter.com',
                    'bat.bing.com',
                    '100th_sm_',
                    '220th_sm_',
                    'logo',
                    'icon',
                    'favicon'
                ];
                
                for (const pattern of blockedPatterns) {
                    if (imgSrc.includes(pattern)) {
                        return false;
                    }
                }
                
                return true;
            }
            
            for (const selector of imageSelectors) {
                const images = document.querySelectorAll(selector);
                console.log(`发现 ${images.length} 个 ${selector} 图片`);
                
                images.forEach(img => {
                    if (isValidProductImage(img.src) && !allImages.includes(img.src)) {
                        allImages.push(img.src);
                    }
                });
            }
            
            console.log(`✓ 总共提取到 ${allImages.length} 张过滤后的商品图`);
            
            // 构建imageGroups
            if (extractedColors.length > 0) {
                extractedColors.forEach(color => {
                    result.imageGroups.push({
                        colorCode: color.code,
                        colorName: color.name,
                        images: allImages // 为每个颜色分配所有图片
                    });
                });
            } else {
                // 没有颜色时创建默认组
                result.imageGroups.push({
                    colorCode: 'DEFAULT',
                    colorName: 'DEFAULT',
                    images: allImages
                });
            }
            
            // 构建variationAttributes
            if (extractedSizes.length > 0) {
                result.variationAttributes = {
                    size: extractedSizes.map(size => ({ value: size, name: size }))
                };
            }
            
            // 如果还没有productDetail，创建基础信息
            if (!result.productDetail) {
                const title = document.querySelector('h1')?.textContent?.trim() || 
                             document.querySelector('[class*="title"]')?.textContent?.trim() || 
                             document.querySelector('[class*="name"]')?.textContent?.trim() || '';
                
                // 增强的描述抓取 - 使用多种策略寻找产品描述
                let description = '';

                // 策略1: 查找常见的描述选择器
                const descriptionSelectors = [
                    '[class*="description"]',
                    '[class*="detail"]',
                    '[class*="product"]',
                    '[class*="info"]',
                    '[class*="spec"]',
                    '[id*="description"]',
                    '[id*="detail"]',
                    'meta[name="description"]',
                    'meta[property="og:description"]'
                ];

                for (const selector of descriptionSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const text = element.getAttribute('content') || element.textContent;
                        if (text && text.length > 50) { // 确保内容足够丰富
                            description = text.trim();
                            console.log(`✓ 策略1成功 - 找到描述内容`);
                            console.log(`  选择器: ${selector}`);
                            console.log(`  元素标签: ${element.tagName.toLowerCase()}`);
                            console.log(`  元素类名: ${element.className || '无'}`);
                            console.log(`  元素ID: ${element.id || '无'}`);
                            console.log(`  文本长度: ${text.length} 字符`);
                            console.log(`  内容预览: ${description.substring(0, 200)}...`);
                            break;
                        } else {
                            console.log(`✗ 策略1 - 元素内容太短 (${selector}): ${text?.substring(0, 50) || '无内容'}`);
                        }
                    } else {
                        console.log(`✗ 策略1 - 未找到元素: ${selector}`);
                    }
                }

                // 策略2: 如果没找到，查找包含特定关键词的段落
                if (!description) {
                    console.log('🔍 策略2开始 - 搜索包含关键词的元素...');
                    const textElements = Array.from(document.querySelectorAll('p, div, span, section, article'));
                    console.log(`  找到 ${textElements.length} 个文本元素`);

                    for (let i = 0; i < textElements.length; i++) {
                        const element = textElements[i];
                        const text = element.textContent.trim();
                        if (text && text.length > 100 && (
                            text.includes('素材') ||
                            text.includes('MADE IN') ||
                            text.includes('バスト') ||
                            text.includes('着丈') ||
                            text.includes('ポリエステル') ||
                            text.includes('ストレッチ') ||
                            text.includes('デタッチャブル')
                        )) {
                            description = text;
                            console.log(`✓ 策略2成功 - 通过关键词找到描述内容`);
                            console.log(`  元素索引: ${i}`);
                            console.log(`  元素标签: ${element.tagName.toLowerCase()}`);
                            console.log(`  元素类名: ${element.className || '无'}`);
                            console.log(`  文本长度: ${text.length} 字符`);
                            console.log(`  包含关键词: ${[...text.matchAll(/(素材|MADE IN|バスト|着丈|ポリエステル|ストレッチ|デタッチャブル)/g)].map(m => m[0]).join(', ')}`);
                            console.log(`  内容预览: ${description.substring(0, 200)}...`);
                            break;
                        }
                    }

                    if (!description) {
                        console.log('✗ 策略2失败 - 未找到包含关键词的合适元素');
                    }
                }

                // 策略3: 查找页面标题之外的较长文本
                if (!description) {
                    console.log('🔍 策略3开始 - 提取页面长文本...');
                    const allText = document.body.textContent || '';
                    const title = document.querySelector('h1')?.textContent?.trim() || '';
                    const cleanText = allText.replace(title, '').replace(/\s+/g, ' ').trim();
                    console.log(`  页面总文本长度: ${allText.length} 字符`);
                    console.log(`  清理后文本长度: ${cleanText.length} 字符`);

                    if (cleanText.length > 200) {
                        description = cleanText.substring(0, 1000); // 取前1000字符
                        console.log(`✓ 策略3成功 - 使用页面文本作为描述`);
                        console.log(`  文本长度: ${description.length} 字符`);
                        console.log(`  内容预览: ${description.substring(0, 200)}...`);
                    } else {
                        console.log('✗ 策略3失败 - 页面文本太短');
                    }
                }

                // 最终状态输出
                if (description) {
                    console.log(`🎉 描述抓取最终成功!`);
                    console.log(`  最终描述长度: ${description.length} 字符`);
                    console.log(`  最终描述内容: ${description.substring(0, 300)}...`);

                    // 添加到result中，以便在Node.js环境中查看
                    result.debugDescriptionInfo = {
                        strategy: 'dom_fallback',
                        length: description.length,
                        preview: description.substring(0, 300),
                        source: 'DOM抓取策略'
                    };
                } else {
                    console.log(`❌ 所有策略均失败 - 未找到描述内容`);
                }
                
                const mainImage = allImages.length > 0 ? allImages[0] : '';

                result.productDetail = {
                    name: title,
                    title: title,
                    longDescription: description,
                    description: description,
                    brand: 'Callaway Golf',
                    mainImage: mainImage
                };
            }
            
            result.dataSources.push('dom_enhanced');
            
            console.log(`✅ DOM提取完成: ${extractedColors.length}颜色, ${extractedSizes.length}尺码, ${allImages.length}图片`);

            // 4. 提取图片信息
            if (result.productDetail && result.productDetail.imageGroups) {
                result.imageGroups = result.productDetail.imageGroups;
            } else {
                // DOM回退 - 查找所有产品图片
                const images = Array.from(document.querySelectorAll('img[src*="callawaygolf"]'))
                    .map(img => img.src)
                    .filter(src => src && !src.includes('logo'));
                
                if (images.length > 0) {
                    result.imageGroups = [{
                        colorCode: 'DEFAULT',
                        images: images
                    }];
                }
            }

            // 5. 提取变体属性
            if (result.productDetail && result.productDetail.variationAttributes) {
                result.variationAttributes = result.productDetail.variationAttributes;
            }

            // 6. 提取尺码表
            if (result.productDetail && result.productDetail.sizeChart) {
                result.sizeChart = result.productDetail.sizeChart;
            }

            const sizeSection = document.querySelector('#size .product-html');
            if (sizeSection) {
                const sizeSectionHtml = sizeSection.innerHTML.trim();
                const sizeSectionText = sizeSection.innerText
                    .replace(/\u00a0/g, ' ')
                    .replace(/\r\n/g, '\n')
                    .replace(/\r/g, '\n')
                    .replace(/\t/g, ' ')
                    .replace(/\s+\n/g, '\n')
                    .replace(/\n{2,}/g, '\n')
                    .trim();

                if (sizeSectionText.length > 0) {
                    result.sizeSectionHtml = sizeSectionHtml;
                    result.sizeSectionText = sizeSectionText;
                    console.log(`✓ DOM找到尺码表文本，长度: ${sizeSectionText.length}`);
                }
            }

            // 7. 提取价格信息（在多颜色抓取之后，DOM已经被点击过）
            try {
                console.log('🔍 开始提取价格信息...');

                // 扩展的价格选择器列表
                const priceSelectors = [
                    '[data-testid="price"]',
                    '.price_wrapper span',           // 页面默认价格
                    '.monica-translate-translate',   // 翻译层里的价格
                    '.price .text-\\[\\#000000\\]',    // 特定样式
                    '.product-price',
                    '.price-value',
                    '.current-price',
                    '.sale-price',
                    '[class*="price"]'
                ];

                let priceText = '';

                // 方法1：使用扩展选择器逐个查找
                for (const selector of priceSelectors) {
                    console.log(`🔍 尝试选择器: ${selector}`);
                    const priceElement = document.querySelector(selector);
                    if (priceElement) {
                        const text = priceElement.textContent.trim();
                        if (text && text.length > 0) {
                            priceText = text;
                            console.log(`✓ 找到价格文本: ${text}`);
                            break;
                        }
                    }
                }

                // 方法2：如果没有找到，搜索包含円(税込)的文本
                if (!priceText) {
                    console.log('🔍 搜索円(税込)格式...');
                    const allElements = document.querySelectorAll('span, div, p');
                    for (const element of allElements) {
                        const text = element.textContent.trim();
                        if (text && text.match(/円\(税込\)/)) {
                            priceText = text;
                            console.log(`✓ 找到价格文本（税込格式）: ${text}`);
                            break;
                        }
                    }
                }

                // 方法3：搜索包含¥或円的文本
                if (!priceText) {
                    console.log('🔍 搜索包含¥或円的文本...');
                    const allElements = document.querySelectorAll('span, div, p');
                    for (const element of allElements) {
                        const text = element.textContent.trim();
                        if (text && (text.includes('¥') || text.includes('円'))) {
                            // 确保文本看起来像价格（包含数字）
                            if (text.match(/\d/)) {
                                priceText = text;
                                console.log(`✓ 找到价格文本: ${text}`);
                                break;
                            }
                        }
                    }
                }

                // 方法4：从 __NEXT_DATA__ 回退
                if (!priceText) {
                    console.log('🔍 尝试从 __NEXT_DATA__ 获取...');
                    const nextDataScript = document.querySelector('#__NEXT_DATA__');
                    if (nextDataScript) {
                        try {
                            const nextData = JSON.parse(nextDataScript.textContent);
                            const productDetail = nextData?.props?.pageProps?.productDetail;
                            if (productDetail) {
                                priceText = productDetail.price || productDetail.priceText || '';
                                if (priceText) {
                                    console.log(`✓ 从 __NEXT_DATA__ 获取价格: ${priceText}`);
                                }
                            }
                        } catch (e) {
                            console.log('⚠️ 解析 __NEXT_DATA__ 失败:', e.message);
                        }
                    }
                }

                // 设置到结果中
                if (priceText) {
                    result.productDetail.priceText = priceText;
                    result.productDetail.price = priceText;
                    result.currentPrice = priceText; // 也设置到顶层
                    result.priceText = priceText;     // 也设置到顶层
                    console.log(`✅ 价格提取成功: ${priceText}`);
                } else {
                    console.log('⚠️ 未能提取到价格信息');
                }

            } catch (priceError) {
                console.log('❌ 价格提取失败:', priceError.message);
            }

        } catch (error) {
            console.log('❌ 数据提取过程中发生错误:', error.message);
            result.dataSources.push('error_fallback');
        }

        return result;
    });
}

// 构建最终产品数据
function buildFinalProductData(extractedData, productId, url, priceInfo = {}) {
    console.log('🔄 构建最终产品数据...');
    
    const startTime = Date.now();
    const productDetail = extractedData.productDetail || {};
    
    // 提取颜色信息
    const colors = [];
    const variants = [];
    const images = { product: [], variants: {} };
    
    // 优先使用多颜色抓取的数据
    if (extractedData.multiColorInfo && extractedData.multiColorInfo.colors.length > 0) {
        console.log(`✓ 使用多颜色抓取的${extractedData.multiColorInfo.colors.length}种颜色`);
        
        // 使用多颜色抓取的结果
        colors.push(...extractedData.multiColorInfo.colors);
        
        // 处理imageGroups数据
        if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups)) {
            extractedData.imageGroups.forEach(group => {
                const colorCode = group.colorCode || group.code;
                
                if (group.images && Array.isArray(group.images)) {
                    images.variants[colorCode] = group.images;
                    images.product.push(...group.images);
                }
                
                console.log(`✓ 颜色 ${group.colorName} (${colorCode}): ${group.images?.length || 0}张图片`);
            });
        }
        
        // 去重product图片
        images.product = [...new Set(images.product)];
        
    } else if (extractedData.imageGroups && Array.isArray(extractedData.imageGroups) && extractedData.imageGroups.length > 0) {
        console.log(`✓ 使用DOM提取的${extractedData.imageGroups.length}个颜色组`);
        
        extractedData.imageGroups.forEach(group => {
            const colorCode = group.colorCode || group.code || 'DEFAULT';
            const colorName = group.colorName || group.name || 'DEFAULT';
            
            // 只添加非DEFAULT的真实颜色
            if (colorCode !== 'DEFAULT' || colors.length === 0) {
                colors.push({
                    code: colorCode,
                    name: colorName
                });
                
                if (group.images && Array.isArray(group.images)) {
                    images.variants[colorCode] = group.images;
                    images.product.push(...group.images);
                }
                
                console.log(`✓ 添加颜色: ${colorName} (${colorCode}), ${group.images?.length || 0}张图片`);
            }
        });
    }
    
    // 如果DOM提取失败，尝试从URL和页面内容推断
    if (colors.length === 0 || colors.every(c => c.code === 'DEFAULT')) {
        console.log('🔍 DOM提取颜色失败，尝试从URL和页面内容推断...');
        
        const pageContent = (productDetail.longDescription || productDetail.description || '').toLowerCase();
        const urlContent = url.toLowerCase();
        
        // CallawayJP常见颜色关键词
        const commonColors = [
            { keywords: ['navy', 'ネイビー', '1031'], name: 'ネイビー', code: '1031' },
            { keywords: ['black', 'ブラック', '1040'], name: 'ブラック', code: '1040' },
            { keywords: ['white', 'ホワイト', '1000'], name: 'ホワイト', code: '1000' },
            { keywords: ['red', 'レッド', '1600'], name: 'レッド', code: '1600' },
            { keywords: ['blue', 'ブルー', '1030'], name: 'ブルー', code: '1030' },
            { keywords: ['gray', 'grey', 'グレー', '1900'], name: 'グレー', code: '1900' }
        ];
        
        const inferredColors = [];
        commonColors.forEach(color => {
            const found = color.keywords.some(keyword => 
                pageContent.includes(keyword) || urlContent.includes(keyword)
            );
            if (found) {
                inferredColors.push({
                    code: color.code,
                    name: color.name
                });
            }
        });
        
        if (inferredColors.length > 0) {
            console.log('✓ 推断出颜色:', inferredColors.map(c => c.name));
            colors.length = 0; // 清空原有的DEFAULT颜色
            colors.push(...inferredColors);
            
            // 更新images.variants以使用推断出的颜色
            if (images.product.length > 0) {
                images.variants = {};
                inferredColors.forEach(color => {
                    images.variants[color.code] = images.product;
                });
            }
        } else {
            console.log('❌ 推断颜色也失败，使用DEFAULT');
            // 确保至少有一个DEFAULT颜色
            if (colors.length === 0) {
                colors.push({ code: 'DEFAULT', name: 'DEFAULT' });
            }
        }
    } else {
        console.log(`✅ 成功提取到 ${colors.length} 种真实颜色: ${colors.map(c => c.name).join(', ')}`);
    }
    
    // 提取尺码信息
    const sizes = [];
    if (extractedData.variationAttributes && extractedData.variationAttributes.size) {
        extractedData.variationAttributes.size.forEach(size => {
            sizes.push(size.value || size.name || size);
        });
    } else {
        // 默认尺码
        sizes.push('S', 'M', 'L', 'LL');
    }
    
    // 生成变体（颜色×尺码笛卡尔积）
    if (colors.length > 0 && sizes.length > 0) {
        // 尝试从 extractedData 获取价格信息
        const extractedPrice = extractedData.currentPrice || extractedData.priceText || '';
        // 清理价格文本，只保留数字和円符号
        const cleanPrice = extractedPrice.replace(/[^\d円]/g, '');

        colors.forEach(color => {
            sizes.forEach(size => {
                variants.push({
                    variantId: `${productId}_${color.code}_${size}`,
                    colorName: color.name,
                    colorCode: color.code,
                    sizeName: size,
                    sizeCode: size,
                    availability: 'unknown',
                    sku: `${productId}_${color.code}_${size}`,
                    priceJPY: cleanPrice || null
                });
            });
        });
    }
    
    // 处理尺码表
    let sizeChart = { headers: [], rows: [] };
    if (extractedData.sizeChart) {
        sizeChart = extractedData.sizeChart;
    }

    const sizeSectionHtml = extractedData.sizeSectionHtml || '';
    const sizeSectionText = extractedData.sizeSectionText || '';
    
    // 生成颜色翻译文本
    const colorsCnText = generateColorsCnText(colors);
    console.log(`✅ 生成颜色翻译文本: ${colors.length}种颜色`);

    // 检查是否有调试信息
    console.log('🔍 检查extractedData中的调试信息...');
    if (extractedData.debugElementsInfo) {
        console.log(`✅ 找到debugElementsInfo: ${extractedData.debugElementsInfo.length} 个元素`);
    }
    if (extractedData.debugDescriptionInfo) {
        console.log(`✅ 找到debugDescriptionInfo: 策略=${extractedData.debugDescriptionInfo.strategy}`);
    }
    if (extractedData.productDetail && extractedData.productDetail.description) {
        console.log(`✅ 找到产品描述: 长度=${extractedData.productDetail.description.length} 字符`);
        console.log(`  描述预览: ${extractedData.productDetail.description.substring(0, 200)}...`);
    }

    // 构建最终数据结构
    const finalData = {
        scrapeInfo: {
            timestamp: new Date().toISOString(),
            version: "1.0.0",
            url: url,
            productId: productId,
            totalVariants: variants.length,
            totalColors: colors.length,
            totalSizes: sizes.length,
            totalImages: images.product.length,
            processingTimeMs: Date.now() - startTime,
            dataSources: extractedData.dataSources || []
        },

        // 保留调试信息（用于分析描述元素位置）
        debugElementsInfo: extractedData.debugElementsInfo || null,
        debugDescriptionInfo: extractedData.debugDescriptionInfo || null,

        product: {
            productId: productId,
            title: productDetail.name || productDetail.title || '',
            productUrl: url,
            description: productDetail.longDescription || productDetail.description || '',
            brand: productDetail.brand || 'Callaway Golf',
            category: '',
            tags: [],
            mainImage: productDetail.mainImage || (images.product.length > 0 ? images.product[0] : ''),
            detailUrl: url,
            sizeChart: sizeChart,
            sizeSectionHtml: sizeSectionHtml,
            sizeSectionText: sizeSectionText,
            // 添加价格信息
            currentPrice: priceInfo.currentPrice || null,
            originalPrice: priceInfo.originalPrice || null,
            priceText: priceInfo.priceText || ''
        },
        variants: variants,
        colors: colors,
        sizes: sizes,
        sizeChart: sizeChart,
        sizeSection: {
            text: sizeSectionText,
            html: sizeSectionHtml
        },
        images: images,
        colors_cn_text: colorsCnText, // 新增：多行中英文颜色对照文本
        ossLinks: {
            productImages: [],
            variantImages: {}
        }
    };
    
    return finalData;
}

// 主函数
async function main() {
    const options = parseArgs();
    const startTime = Date.now();
    
    console.log('🚀 开始抓取产品详情...');
    console.log(`📍 URL: ${options.url}`);
    console.log(`🏷️  产品ID: ${options.productId}`);
    
    let browser = null;
    
    try {
        // 启动浏览器
        console.log('🌐 启动浏览器...');
        browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-extensions',
                '--disable-plugins',
                '--no-first-run',
                '--no-default-browser-check'
            ]
        });
        
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale: 'ja-JP',
            timezone: 'Asia/Tokyo'
        });
        
        const page = await context.newPage();
        
        // 加载页面（带重试机制）
        console.log('📄 加载页面...');
        let pageLoaded = false;
        let attempts = 0;
        const maxAttempts = 3;

        while (!pageLoaded && attempts < maxAttempts) {
            attempts++;
            try {
                console.log(`🔄 尝试加载页面 (第${attempts}/${maxAttempts}次)...`);
                await page.goto(options.url, {
                    waitUntil: 'domcontentloaded',  // 改为domcontentloaded策略
                    timeout: 120000  // 调整超时时间到120秒
                });

                // 测试：检查页面是否正确加载并包含我们期望的内容
                const hasExpectedContent = await page.evaluate(() => {
                    const bodyText = document.body.textContent || '';
                    return bodyText.includes('今シーズンの') || bodyText.includes('Callaway') || bodyText.includes('Golf');
                });

                console.log(`📄 页面内容检查: ${hasExpectedContent ? '✅ 找到期望内容' : '⚠️ 未找到期望内容'}`);
                pageLoaded = true;
                
                // 等待页面完全加载
                await page.waitForTimeout(5000);
                pageLoaded = true;
                console.log('✅ 页面加载成功');
                
            } catch (error) {
                console.log(`❌ 第${attempts}次加载失败: ${error.message}`);
                if (attempts < maxAttempts) {
                    console.log(`⏱️  等待5秒后重试...`);
                    await page.waitForTimeout(5000);
                } else {
                    throw new Error(`页面加载失败，已重试${maxAttempts}次: ${error.message}`);
                }
            }
        }
        
        // 首先进行多颜色抓取
        const multiColorData = await extractMultiColorData(page);
        
        // 提取产品数据（包含价格信息）
        const extractedData = await extractProductData(page);

        // 将多颜色数据合并到extractedData中
        if (multiColorData.colors.length > 0) {
            console.log(`🎨 使用多颜色抓取结果: ${multiColorData.colors.length}种颜色`);
            extractedData.imageGroups = multiColorData.imageGroups;
            extractedData.multiColorInfo = {
                colors: multiColorData.colors,
                totalImages: multiColorData.allImages.size
            };
        }

        // 提取价格信息（使用extractedData中已提取的价格）
        const priceInfo = {
            currentPrice: extractedData.currentPrice || null,
            originalPrice: extractedData.originalPrice || null,
            priceText: extractedData.priceText || ''
        };

        console.log(`💰 价格信息: ${priceInfo.priceText || '未找到'}`);

        // 构建最终数据
        const finalData = buildFinalProductData(extractedData, options.productId, options.url, priceInfo);
        
        // 确保输出目录存在
        if (!fs.existsSync(options.outputDir)) {
            fs.mkdirSync(options.outputDir, { recursive: true });
        }
        
        // 生成输出文件名
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputFile = path.join(options.outputDir, `product_details_${options.productId}_${timestamp}.json`);
        
        // 写入文件
        fs.writeFileSync(outputFile, JSON.stringify(finalData, null, 2), 'utf8');
        
        console.log('✅ 抓取完成!');
        console.log(`📁 输出文件: ${outputFile}`);
        console.log(`⏱️  处理时间: ${Date.now() - startTime}ms`);
        console.log(`📊 统计信息:`);
        console.log(`   - 变体数量: ${finalData.scrapeInfo.totalVariants}`);
        console.log(`   - 颜色数量: ${finalData.scrapeInfo.totalColors}`);
        console.log(`   - 尺码数量: ${finalData.scrapeInfo.totalSizes}`);
        console.log(`   - 图片数量: ${finalData.scrapeInfo.totalImages}`);
        console.log(`   - 数据来源: ${finalData.scrapeInfo.dataSources.join(', ')}`);
        
    } catch (error) {
        console.error('❌ 抓取失败:', error.message);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// 运行脚本
if (require.main === module) {
    main().catch(console.error);
}

// 多颜色抓取函数
async function extractMultiColorData(page) {
    console.log('🎨 开始多颜色抓取...');
    
    const multiColorData = {
        colors: [],
        imageGroups: [],
        allImages: new Set() // 用于去重
    };
    
    try {
        // 定位颜色按钮容器
        console.log('🔍 定位颜色按钮容器...');
        
        // 使用优化的颜色按钮检测逻辑
        console.log('🔍 使用优化的颜色按钮检测逻辑...');

        // 扩展的CSS选择器列表
        const colorButtonSelectors = [
            // 原有选择器
            '.d_flex.items_center.gap_2\\.5.flex_row.flex-wrap_wrap button',
            '[class*="d_flex"][class*="items_center"][class*="gap_2.5"] button',
            '[class*="color"] button',
            'button[aria-label*="色"]',
            'button[title*="色"]',
            '.variant-selector button',
            '.color-selector button',

            // 新增选择器模式
            '[class*="swatch"] button',
            '[class*="variant"] button',
            '[class*="option"] button',
            '[class*="shade"] button',
            '[class*="tone"] button',
            '[class*="hue"] button',
            '[class*="palette"] button',
            '[class*="picker"] button',
            '[class*="selection"] button',
            '[class*="choice"] button',

            // 日文相关
            '[class*="カラー"] button',
            '[class*="カラ-"] button',
            '[class*="色"] button',
            'button[aria-label*="カラー"]',
            'button[aria-label*="カラ-"]',
            'button[title*="カラー"]',
            'button[title*="カラ-"]',

            // 英文相关
            '[class*="Color"] button',
            '[class*="colour"] button',
            'button[aria-label*="Color"]',
            'button[aria-label*="colour"]',
            'button[title*="Color"]',
            'button[title*="colour"]',

            // 通用模式
            '.product-options button',
            '.product-variants button',
            '.product-colors button',
            '.swatches button',
            '.color-options button',
            '.variant-options button',
            '[data-variant] button',
            '[data-color] button',
            '[data-option*="color"] button',
            '[data-option*="Color"] button',

            // 结构模式
            '.flex button[role="option"]',
            '.grid button[role="option"]',
            '[class*="flex"] button[aria-selected]',
            '[class*="grid"] button[aria-selected]',
            'button[data-value]',
            'button[value]',
            'input[type="radio"][class*="color"]',
            'input[type="radio"][class*="Color"]',

            // 图片模式
            'button img[alt*="色"]',
            'button img[alt*="カラー"]',
            'button img[alt*="Color"]',
            'button[style*="background"]',
            'button[style*="border-color"]',
            'button[class*="bg-"]'
        ];

        let colorButtons = [];
        let detectionMethod = '';

        // 1. CSS选择器检测
        console.log('🔍 开始CSS选择器检测...');
        for (const selector of colorButtonSelectors) {
            try {
                const buttons = await page.$$(selector);
                if (buttons.length > 0) {
                    console.log(`✓ 选择器 "${selector}" 找到 ${buttons.length} 个元素`);
                    colorButtons = buttons;
                    detectionMethod = `CSS选择器: ${selector}`;
                    break;
                }
            } catch (error) {
                console.log(`⚠️ 选择器 "${selector}" 执行失败:`, error.message);
            }
        }

        // 2. 文本内容检测
        if (colorButtons.length === 0) {
            console.log('🔍 开始文本内容检测...');

            // 扩展的颜色关键词
            const colorKeywords = [
                // 中文
                '色', '颜色', '色彩', '色调', '配色', '上色',
                // 日文
                'カラー', 'カラ-', '色', '色彩', '配色',
                // 英文
                'color', 'colour', 'shade', 'tone', 'hue', 'tint',
                'variant', 'option', 'selection', 'choice', 'swatch',
                'palette', 'picker', 'finish', 'style'
            ];

            const allButtons = await page.$$('button, [role="button"], input[type="button"], input[type="submit"]');

            for (const btn of allButtons) {
                try {
                    const text = (await btn.textContent() || '').toLowerCase();
                    const ariaLabel = (await btn.getAttribute('aria-label') || '').toLowerCase();
                    const title = (await btn.getAttribute('title') || '').toLowerCase();
                    const className = (btn.getAttribute('class') || '').toLowerCase();

                    const allText = [text, ariaLabel, title, className].join(' ');

                    if (colorKeywords.some(keyword =>
                        allText.includes(keyword.toLowerCase()) ||
                        allText.includes(keyword)
                    )) {
                        colorButtons.push(btn);
                        console.log(`✓ 通过文本检测找到按钮:`, text || ariaLabel || title);
                    }
                } catch (e) {
                    // 跳过无法读取的按钮
                    console.log(`⚠️ 按钮检测失败:`, e.message);
                }
            }

            if (colorButtons.length > 0) {
                detectionMethod = '文本内容检测';
            }
        }

        // 3. 智能结构检测
        if (colorButtons.length === 0) {
            console.log('🔍 开始智能结构检测...');

            // 扩展的颜色关键词
            const colorKeywords = [
                // 中文
                '色', '颜色', '色彩', '色调', '配色', '上色',
                // 日文
                'カラー', 'カラ-', '色', '色彩', '配色',
                // 英文
                'color', 'colour', 'shade', 'tone', 'hue', 'tint',
                'variant', 'option', 'selection', 'choice', 'swatch',
                'palette', 'picker', 'finish', 'style'
            ];

            // 查找包含多个按钮的容器
            const containers = await page.$$('div, section, article, nav');

            for (const container of containers) {
                const buttons = await container.$$('button, [role="button"]');

                if (buttons.length >= 2 && buttons.length <= 20) {
                    // 检查容器是否包含颜色相关属性
                    const containerClass = (await container.getAttribute('class') || '').toLowerCase();
                    const containerId = (await container.getAttribute('id') || '').toLowerCase();
                    const containerAria = (await container.getAttribute('aria-label') || '').toLowerCase();

                    const containerText = [containerClass, containerId, containerAria].join(' ');

                    if (colorKeywords.some(keyword =>
                        containerText.includes(keyword.toLowerCase())
                    )) {
                        colorButtons = buttons;
                        detectionMethod = `智能结构检测: 容器 ${container.tagName}.${containerClass}`;
                        console.log(`✓ 通过结构检测找到容器:`, containerClass);
                        break;
                    }

                    // 检查按钮是否具有相似的特征（如都是颜色选择器）
                    const buttonFeatures = await Promise.all(buttons.map(async btn => {
                        const style = await btn.getAttribute('style') || '';
                        const hasStyle = style !== '';
                        const hasBg = style.includes('background') || style.includes('backgroundColor');
                        const hasImg = await btn.$('img');
                        const hasValue = btn.hasAttribute('value') || btn.hasAttribute('data-value');
                        return { hasStyle, hasBg, hasImg, hasValue };
                    }));

                    // 如果大部分按钮都有样式或图片特征，可能是颜色选择器
                    const withFeatures = buttonFeatures.filter(f =>
                        f.hasStyle || f.hasBg || f.hasImg || f.hasValue
                    ).length;

                    if (withFeatures >= buttons.length * 0.6) {
                        colorButtons = buttons;
                        detectionMethod = `智能结构检测: 特征匹配`;
                        console.log(`✓ 通过特征匹配找到 ${buttons.length} 个按钮`);
                        break;
                    }
                }
            }
        }

        // 4. 最后尝试：查找所有可能的按钮并过滤
        if (colorButtons.length === 0) {
            console.log('🔍 尝试查找所有可能的按钮...');
            const allPossibleButtons = await page.$$('button, [role="button"], input[type="radio"], input[type="checkbox"]');

            // 过滤出可能是颜色选择的按钮
            for (const btn of allPossibleButtons) {
                try {
                    const style = await btn.getAttribute('style') || '';
                    const hasColorStyle = style.includes('background') || style.includes('backgroundColor') ||
                                           style.includes('borderColor') || style.includes('borderTopColor');
                    const className = (await btn.getAttribute('class') || '').toLowerCase();
                    const hasColorClass = /color|swatch|variant|option|shade|tone|hue|palette|picker/i.test(className);
                    const hasColorData = btn.hasAttribute('data-color') || btn.hasAttribute('data-variant') ||
                                        btn.hasAttribute('data-option') || btn.hasAttribute('data-value');
                    const hasColorImg = await btn.$('img[alt*="色"], img[alt*="カラー"], img[alt*="Color"]');

                    if (hasColorStyle || hasColorClass || hasColorData || hasColorImg) {
                        colorButtons.push(btn);
                    }
                } catch (e) {
                    console.log(`⚠️ 按钮过滤失败:`, e.message);
                }
            }

            if (colorButtons.length > 0) {
                detectionMethod = '全局按钮过滤';
            }
        }

        // 输出调试信息
        console.log(`🎯 检测方法: ${detectionMethod}`);
        console.log(`🎯 找到 ${colorButtons.length} 个颜色按钮`);

        // 如果仍然没有找到颜色按钮，使用默认颜色继续执行（不回退到单颜色模式）
        if (colorButtons.length === 0) {
            console.log('⚠️ 未找到颜色按钮，使用默认颜色继续执行...');
            // 添加默认颜色
            multiColorData.colors.push({
                code: 'DEFAULT',
                name: 'DEFAULT'
            });
            return multiColorData;
        }
        
        // 逐个点击颜色按钮并抓取数据
        for (let i = 0; i < colorButtons.length; i++) {
            const button = colorButtons[i];
            
            try {
                // 获取按钮信息
                const buttonText = await button.textContent();
                const ariaLabel = await button.getAttribute('aria-label');
                const title = await button.getAttribute('title');
                const dataValue = await button.getAttribute('data-value');
                const dataColor = await button.getAttribute('data-color');
                
                console.log(`🔘 点击颜色按钮 ${i + 1}/${colorButtons.length}: ${buttonText || ariaLabel || title || '未知'}`);
                
                // 点击按钮
                await button.click();
                
                // 等待页面更新 - 图片切换完成
                console.log('⏳ 等待页面更新...');
                await page.waitForTimeout(2000); // 等待2秒让图片加载
                
                // 尝试等待图片容器更新
                try {
                    await page.waitForFunction(() => {
                        const images = document.querySelectorAll('img[src*="callawaygolf"], img[src*="webdamdb"]');
                        return images.length > 0;
                    }, { timeout: 5000 });
                } catch (e) {
                    console.log('图片加载等待超时，继续执行...');
                }
                
                // 提取当前颜色信息
                const currentColorData = await page.evaluate((buttonInfo) => {
                    // 从按钮信息中提取颜色名称和代码
                    let colorName = buttonInfo.text || buttonInfo.ariaLabel || buttonInfo.title || 'Unknown';
                    let colorCode = buttonInfo.dataValue || buttonInfo.dataColor;
                    
                    // 如果没有明确的颜色代码，尝试生成一个
                    if (!colorCode) {
                        const colorMap = {
                            'ネイビー': '1031', 'navy': '1031',
                            'ブラック': '1040', 'black': '1040',
                            'ホワイト': '1000', 'white': '1000',
                            'ブルー': '1030', 'blue': '1030',
                            'レッド': '1600', 'red': '1600',
                            'グレー': '1900', 'gray': '1900', 'grey': '1900'
                        };
                        
                        const lowerName = colorName.toLowerCase();
                        for (const [key, value] of Object.entries(colorMap)) {
                            if (lowerName.includes(key.toLowerCase())) {
                                colorCode = value;
                                break;
                            }
                        }
                        
                        if (!colorCode) {
                            colorCode = `AUTO_${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
                        }
                    }
                    
                    // 抓取当前显示的图片
                    const currentImages = [];
                    const imageSelectors = [
                        'img[src*="callawaygolf"]',
                        'img[src*="webdamdb"]',
                        '.product-images img',
                        '.gallery img',
                        '[class*="image"] img'
                    ];
                    
                    // 图片URL过滤函数 - 只保留1280尺寸商品图
                    function isValidProductImage(imgSrc) {
                        if (!imgSrc) return false;
                        
                        // 必须以指定格式开头
                        const validPrefix = 'https://www.callawaygolf.jp/_next/image?url=https%3A%2F%2Fcdn2.webdamdb.com%2F1280_';
                        if (!imgSrc.startsWith(validPrefix)) {
                            return false;
                        }
                        
                        // 排除追踪链接和缩略图
                        const blockedPatterns = [
                            't.co/',
                            'analytics.twitter.com',
                            'bat.bing.com',
                            '100th_sm_',
                            '220th_sm_',
                            'logo',
                            'icon',
                            'favicon'
                        ];
                        
                        for (const pattern of blockedPatterns) {
                            if (imgSrc.includes(pattern)) {
                                return false;
                            }
                        }
                        
                        return true;
                    }
                    
                    for (const selector of imageSelectors) {
                        const images = document.querySelectorAll(selector);
                        images.forEach(img => {
                            if (isValidProductImage(img.src) && !currentImages.includes(img.src)) {
                                currentImages.push(img.src);
                            }
                        });
                    }
                    
                    console.log(`过滤后图片数量: ${currentImages.length}`);
                    
                    return {
                        colorName,
                        colorCode,
                        images: currentImages
                    };
                }, {
                    text: buttonText,
                    ariaLabel,
                    title,
                    dataValue,
                    dataColor
                });
                
                console.log(`✓ 提取颜色: ${currentColorData.colorName} (${currentColorData.colorCode}), ${currentColorData.images.length}张图片`);
                
                // 修复：保留所有图片，不再限制数量
                let finalImages = currentColorData.images;
                console.log(`   📌 保留全部 ${finalImages.length} 张图片`);
                
                // 添加到结果中
                multiColorData.colors.push({
                    code: currentColorData.colorCode,
                    name: currentColorData.colorName
                });
                
                multiColorData.imageGroups.push({
                    colorCode: currentColorData.colorCode,
                    colorName: currentColorData.colorName,
                    images: finalImages
                });
                
                // 将图片添加到总集合中
                finalImages.forEach(img => multiColorData.allImages.add(img));
                
            } catch (error) {
                console.log(`❌ 处理颜色按钮 ${i + 1} 时出错: ${error.message}`);
            }
        }
        
        console.log(`✅ 多颜色抓取完成: ${multiColorData.colors.length}种颜色, 总计${multiColorData.allImages.size}张图片`);
        
    } catch (error) {
        console.log(`❌ 多颜色抓取失败: ${error.message}`);
    }
    
    return multiColorData;
}

module.exports = {
    extractProductData,
    buildFinalProductData,
    extractMultiColorData,
    main
};
