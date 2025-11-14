#!/usr/bin/env node

/**
 * 通用智能标题生成器
 * 基于卡拉威的提示词系统，为所有品牌生成标准化的淘宝标题
 * 输入：日文商品名 + 品牌信息
 * 输出：26-30汉字的淘宝标准标题
 */

const fs = require('fs');
const path = require('path');

class UniversalTitleGenerator {
    constructor() {
        // 品牌关键词映射
        this.brandKeywords = {
            'callawaygolf': ['callaway', 'callaway golf', '卡拉威', '卡拉威高尔夫'],
            'titleist': ['titleist', '泰特利斯', 'titleist golf'],
            'puma': ['puma', 'puma golf', '彪马'],
            'adidas': ['adidas', 'adidas golf', '阿迪达斯'],
            'nike': ['nike', 'nike golf', '耐克'],
            'underarmour': ['under armour', 'ua', '安德玛'],
            'footjoy': ['footjoy', 'fj', 'joy'],
            'cleveland': ['cleveland', 'cleveland golf'],
            'mizuno': ['mizuno', '美津濃', '美津浓'],
            'ping': ['ping', 'ping golf'],
            'taylormade': ['taylor made', 'taylormade', 'tm', '泰勒梅'],
            'lecoqgolf': ['le coq sportif', 'lecoq', '乐卡', 'le coq sportif golf', '公鸡']
        };

        // 品牌中文名映射
        this.brandMap = {
            'callawaygolf': '卡拉威Callaway',
            'titleist': '泰特利斯Titleist',
            'puma': '彪马Puma',
            'adidas': '阿迪达斯Adidas',
            'nike': '耐克Nike',
            'underarmour': '安德玛UA',
            'footjoy': 'FootJoy',
            'cleveland': 'Cleveland',
            'mizuno': '美津浓Mizuno',
            'ping': 'Ping',
            'taylormade': '泰勒梅TaylorMade',
            'lecoqgolf': '公鸡Le Coq Sportif'
        };

        // 品牌简称
        this.brandShortName = {
            'callawaygolf': '卡拉威',
            'titleist': '泰特利斯',
            'puma': '彪马',
            'adidas': '阿迪达斯',
            'nike': '耐克',
            'underarmour': '安德玛',
            'footjoy': 'FootJoy',
            'cleveland': 'Cleveland',
            'mizuno': '美津浓',
            'ping': 'Ping',
            'taylormade': '泰勒梅',
            'lecoqgolf': '公鸡'
        };

        // 完整的提示词模板
        this.promptTemplate = `你是淘宝标题生成专家。根据日文商品名生成中文标题。

标题格式：
[季节][品牌]高尔夫[性别][功能词][结尾词]

判断规则（你需要自己判断）：

1. 季节判断
从商品名提取年份+季节代码：
- "25FW"、"25AW" → "25秋冬"
- "26SS"、"26SP" → "26春夏"
如果没有，默认用"25秋冬"

2. 品牌
根据商品名判断品牌，使用简短版品牌名（不要英文）：
- Callaway → "卡拉威"
- Titleist → "泰特利斯"
- Puma → "彪马"
- Adidas → "阿迪达斯"
- Nike → "耐克"
- Under Armour → "安德玛"
- FootJoy → "FootJoy"
- Cleveland → "Cleveland"
- Mizuno → "美津浓"
- Ping → "Ping"
- TaylorMade → "泰勒梅"
- Le Coq Sportif → "公鸡"
本商品的品牌是：{{BRAND_SHORT}}

3. 性别判断
商品名包含"メンズ/mens/men" → "男士"
商品名包含"レディース/womens/women/ladies" → "女士"
没有明确标识 → 默认"男士"

4. 功能词判断（根据商品特点选择）
包含"中綿/中棉/棉服" → "保暖棉服"
包含"フルジップ/全拉链" → "弹力全拉链"
包含"防寒/保暖" → "保暖"
包含"フリース/fleece" → "抓绒"
包含"撥水/防水" → "防泼水"
包含"速乾/quickdry" → "速干"
包含"軽量/轻量" → "轻量"
包含"ストレッチ/stretch" → "弹力"
其他普通服装 → "舒适"
配件类 → 不需要功能词（留空或用"轻便"、"时尚"）

5. 结尾词判断（根据商品类型）

配件类结尾词：
- "ベルト/belt/皮带" → "腰带"
- "キャップ/cap/帽子" → "帽子"
- "ハット/hat" → "帽子"
- "ビーニー/beanie" → "帽子"
- "グローブ/glove/手套" → "手套"
- "ヘッドカバー/head cover/カバー" → "球杆头套"
- "マーカー/marker/クリップ" → "标记夹"
- "ソックス/socks/袜子" → "袜子"
- "シューズ/shoes/球鞋" → "球鞋"
- "傘/umbrella/雨伞" → "雨伞"
- "バッグ/bag/包" → "高尔夫包"
其他配件 → "配件"

服装类结尾词：
- "ジャケット/jacket/ブルゾン/blouson/アウター/outer" → "夹克"
- "ベスト/vest" → "背心"
- "コート/coat" → "外套"
- "パーカー/parka" → "连帽衫"
- "ダウン/down" → "羽绒服"
- "ポロ/polo/シャツ/shirt/トップ/top" → "上衣"
- "ニット/knit/セーター/sweater" → "针织衫"
- "スウェット/sweat/卫衣" → "卫衣"
- "パンツ/pants/ズボン/长裤" → "长裤"
- "ショート/short/短裤" → "短裤"
- "スカート/skirt/裙" → "半身裙"
- "シューズ/shoes/スニーカー/sneaker" → "球鞋"
- "レイン/rain/雨" → "雨衣"

严格要求（必须遵守）：

1. 长度要求
总长度：26-30个汉字
如果长度不够，可以在功能词前加修饰：
- "新款"、"时尚"、"轻便"、"透气"、"运动"、"专业"、"经典"等

2. 格式要求
- 只用简体中文，不要日文假名、英文字母、繁体字
- 不要任何符号：空格、斜杠/、破折号-、加号+、乘号×等
- "高尔夫"必须且只能出现1次
- 必须以完整的结尾词结束（不要"夹克外"、"上"等残缺词）

请生成标题，只返回标题本身，不要其他解释。`;
    }

    /**
     * 从商品数据中提取品牌信息
     */
    extractBrand(productData) {
        const name = productData.title?.original || productData.productName || '';
        const url = productData.url || productData.detailUrl || '';
        const brand = productData.brand || '';

        // 从商品名匹配
        for (const [brandKey, keywords] of Object.entries(this.brandKeywords)) {
            for (const keyword of keywords) {
                if (name.toLowerCase().includes(keyword.toLowerCase()) ||
                    url.toLowerCase().includes(keyword.toLowerCase()) ||
                    brand.toLowerCase().includes(keyword.toLowerCase())) {
                    return {
                        key: brandKey,
                        fullName: this.brandMap[brandKey],
                        shortName: this.brandShortName[brandKey]
                    };
                }
            }
        }

        return {
            key: 'unknown',
            fullName: '未知品牌',
            shortName: '品牌'
        };
    }

    /**
     * 判断性别
     */
    detectGender(productName) {
        const name = (productName || '').toLowerCase();
        if (name.includes('メンズ') || name.includes('mens') || name.includes('men')) {
            return '男士';
        }
        if (name.includes('レディース') || name.includes('womens') || name.includes('women') || name.includes('ladies')) {
            return '女士';
        }
        return '男士'; // 默认男士
    }

    /**
     * 生成智能标题
     */
    async generateTitle(productData) {
        const productName = productData.title?.original || productData.productName || '';
        const brand = this.extractBrand(productData);
        const gender = this.detectGender(productName);

        // 替换提示词中的品牌占位符
        const prompt = this.promptTemplate.replace('{{BRAND_SHORT}}', brand.shortName);

        console.log(`🎯 标题生成分析:`);
        console.log(`   商品名: ${productName}`);
        console.log(`   品牌: ${brand.shortName}`);
        console.log(`   性别: ${gender}`);

        // 构建模拟的AI响应（实际应用中这里会调用真实的AI API）
        const title = this.generateTitleByRules(productName, brand.shortName, gender);

        console.log(`   生成标题: ${title}`);
        console.log(`   长度: ${title.length}字`);

        return {
            original: productName,
            generated: title,
            brand: brand,
            gender: gender
        };
    }

    /**
     * 基于规则生成标题（备用方案，不依赖AI）
     */
    generateTitleByRules(productName, brandShort, gender) {
        let title = '';

        // 1. 季节判断
        let season = '25秋冬';
        if (productName.includes('25FW') || productName.includes('25AW')) {
            season = '25秋冬';
        } else if (productName.includes('26SS') || productName.includes('26SP')) {
            season = '26春夏';
        }

        // 2. 功能词判断
        let functionWord = '舒适';
        if (productName.includes('中綿') || productName.includes('中棉') || productName.includes('棉服')) {
            functionWord = '保暖棉服';
        } else if (productName.includes('フリース') || productName.includes('fleece')) {
            functionWord = '抓绒';
        } else if (productName.includes('撥水') || productName.includes('防水')) {
            functionWord = '防泼水';
        } else if (productName.includes('ストレッチ') || productName.includes('stretch')) {
            functionWord = '弹力';
        } else if (productName.includes('軽量') || productName.includes('轻量')) {
            functionWord = '轻量';
        }

        // 3. 结尾词判断
        let endingWord = '上衣';
        if (productName.includes('ジャケット') || productName.includes('jacket') || productName.includes('ブルゾン')) {
            endingWord = '夹克';
        } else if (productName.includes('ベスト') || productName.includes('vest')) {
            endingWord = '背心';
        } else if (productName.includes('パーカー') || productName.includes('parka')) {
            endingWord = '连帽衫';
        } else if (productName.includes('パンツ') || productName.includes('pants')) {
            endingWord = '长裤';
        }

        // 4. 组装标题
        title = `${season}${brandShort}高尔夫${gender}${functionWord}${endingWord}`;

        // 5. 长度调整
        while (title.length < 26) {
            if (title.length + 2 <= 30) {
                title = `${season}新款${brandShort}高尔夫${gender}${functionWord}${endingWord}`;
                break;
            }
        }

        // 6. 长度检查
        if (title.length < 26) {
            // 添加修饰词
            const modifiers = ['时尚', '轻便', '透气', '运动', '专业', '经典'];
            for (const mod of modifiers) {
                const newTitle = title.replace(functionWord, `${mod}${functionWord}`);
                if (newTitle.length >= 26 && newTitle.length <= 30) {
                    title = newTitle;
                    break;
                }
            }
        }

        if (title.length > 30) {
            // 截断
            title = title.substring(0, 30);
        }

        return title;
    }

    /**
     * 批量处理产品数据
     */
    async batchGenerate(products) {
        console.log(`🚀 开始批量生成标题，共 ${products.length} 个产品...`);

        const results = [];
        for (let i = 0; i < products.length; i++) {
            const product = products[i];
            console.log(`\n[${i + 1}/${products.length}] 处理产品...`);

            try {
                const result = await this.generateTitle(product);
                results.push(result);
            } catch (error) {
                console.error(`❌ 产品 ${i + 1} 标题生成失败:`, error.message);
                results.push({
                    original: product.title?.original || product.productName || '',
                    generated: '标题生成失败',
                    error: error.message
                });
            }
        }

        console.log(`\n✅ 批量标题生成完成！`);
        return results;
    }
}

// 导出类
module.exports = UniversalTitleGenerator;

// 如果直接运行此文件
if (require.main === module) {
    const generator = new UniversalTitleGenerator();

    // 测试用例
    const testData = {
        title: {
            original: '【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）'
        },
        brand: 'le coq sportif golf',
        url: 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/'
    };

    console.log('🧪 通用标题生成器测试');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    generator.generateTitle(testData).then(result => {
        console.log('\n✅ 测试完成！');
        console.log(`原始标题: ${result.original}`);
        console.log(`生成标题: ${result.generated}`);
        console.log(`品牌信息: ${result.brand.shortName} (${result.brand.fullName})`);
        console.log(`性别判断: ${result.gender}`);
    }).catch(error => {
        console.error('❌ 测试失败:', error);
    });
}