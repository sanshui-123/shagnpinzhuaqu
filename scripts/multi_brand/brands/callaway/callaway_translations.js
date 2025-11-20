#!/usr/bin/env node

/**
 * Callaway 专用颜色翻译表
 * 从旧版 scrape_product_detail.js 迁移
 */

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

    // 日文颜色
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

/**
 * 颜色翻译函数
 */
function translateColorName(englishColor) {
    if (!englishColor) return '';

    const colorName = englishColor.trim();

    // 直接查找
    if (COLOR_NAME_TRANSLATION[colorName]) {
        return COLOR_NAME_TRANSLATION[colorName];
    }

    // 部分匹配（处理复合颜色名称）
    const lowerColorName = colorName.toLowerCase();
    for (const [english, chinese] of Object.entries(COLOR_NAME_TRANSLATION)) {
        if (lowerColorName.includes(english.toLowerCase())) {
            return chinese;
        }
    }

    // 没找到翻译，返回原名称
    return colorName;
}

/**
 * 生成多行中文颜色文本
 */
function generateColorsCnText(colors) {
    if (!colors || colors.length === 0) {
        return '';
    }

    const colorLines = [];

    colors.forEach(color => {
        const englishName = color.name || '';
        const chineseName = translateColorName(englishName);

        if (chineseName) {
            colorLines.push(chineseName);
        } else if (englishName) {
            colorLines.push(englishName);
        }
    });

    return colorLines.join('\n');
}

module.exports = {
    COLOR_NAME_TRANSLATION,
    translateColorName,
    generateColorsCnText
};
