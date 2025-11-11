#!/usr/bin/env python3
"""
基于规则的标题生成测试（不使用 GLM）
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_title_by_rules(product):
    """完全基于规则生成标题"""

    name = product.get('productName', '')
    category = determine_category(product)
    is_accessory = is_small_accessory(category, name)
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    season = extract_season_from_name(name)

    # 默认值
    gender = '男士'  # 简化处理
    if not season:
        season = '25秋冬'

    print(f"\n=== 规则生成 ===")
    print(f"产品名: {name}")
    print(f"分类: {category}")
    print(f"配件: {is_accessory}")
    print(f"品牌: {brand_chinese}")
    print(f"季节: {season}")

    # 规则生成
    if is_accessory:
        # 配件类
        if '皮带' in name or 'ベルト' in name or '腰带' in name:
            ending = '腰带'
        elif '帽子' in name or 'キャップ' in name:
            ending = '帽子'
        elif '手套' in name or 'グローブ' in name:
            ending = '手套'
        elif '袜子' in name or 'ソックス' in name:
            ending = '袜子'
        else:
            ending = '腰带'

        title = f"{season}{brand_chinese}高尔夫{gender}轻便{ending}"

    else:
        # 服装类
        # 功能词推断
        if '中綿' in name or '中棉' in name:
            feature = '两用棉服'
        elif 'フルジップ' in name or '全開' in name or '全拉链' in name:
            feature = '弹力全拉链'
        elif 'ストレッチ' in name or '弹力' in name:
            feature = '弹力'
        elif '防寒' in name or '保暖' in name or '裏起毛' in name:
            feature = '保暖'
        elif '軽量' in name or '轻量' in name or 'ライト' in name:
            feature = '轻薄'
        elif '防風' in name or 'wind' in name.lower():
            feature = '防风'
        elif '透湿' in name or '透气' in name or 'メッシュ' in name:
            feature = '透气'
        else:
            feature = '舒适'

        # 结尾词
        if category == '外套':
            ending = '夹克'
        elif category == '上衣':
            if 'ポロ' in name or 'POLO' in name:
                ending = 'POLO衫'
            elif 'Tシャツ' in name or 'T恤' in name:
                ending = 'T恤'
            else:
                ending = '上衣'
        elif category == '下装':
            if 'ショーツ' in name or '短裤' in name:
                ending = '短裤'
            else:
                ending = '长裤'
        elif category == '雨具':
            ending = '雨衣'
        else:
            ending = '夹克'

        # 组合标题
        title = f"{season}{brand_chinese}高尔夫{gender}{feature}{ending}"

    # 长度调整
    if len(title) < 25:
        # 添加更多描述词
        extra_words = ['新款', '正品', '运动', '专业', '休闲']
        for word in extra_words:
            if len(title) + len(word) <= 30:
                title = title.replace(feature, feature + word)
                break

    if len(title) > 30:
        # 截断
        title = title[:30]

    return title

# 需要导入的函数
def determine_category(product):
    """简化版分类判断"""
    name = product.get('productName', '').lower()
    category = product.get('category', '')

    # 外套关键词
    outer_keywords = ['ブルゾン', 'ジャケット', 'コート', 'アウター', '夹克', '外套', '风衣']
    # 上衣关键词
    top_keywords = ['シャツ', 'トップス', 'tシャツ', 'ポロ', '上衣', 't恤']
    # 下装关键词
    bottom_keywords = ['パンツ', 'トラウザーズ', '裤', '长裤', '短裤']
    # 配件关键词
    accessory_keywords = ['帽子', 'キャップ', '手袋', 'グローブ', 'ベルト', '腰带', '袜子']

    for kw in accessory_keywords:
        if kw in name:
            return '配件'

    for kw in outer_keywords:
        if kw in name:
            return '外套'

    for kw in top_keywords:
        if kw in name:
            return '上衣'

    for kw in bottom_keywords:
        if kw in name:
            return '下装'

    return category if category else '其他'

def is_small_accessory(category, product_name):
    """判断是否为小配件"""
    if category == '配件':
        return True
    accessory_keywords = ['帽子', '手套', '腰带', '皮带', '袜子', '毛巾']
    for kw in accessory_keywords:
        if kw in product_name:
            return True
    return False

def extract_brand_from_product(product):
    """提取品牌"""
    brand = product.get('brand', '').lower()
    if 'callaway' in brand:
        return 'callawaygolf', '卡拉威Callaway', '卡拉威'
    return 'unknown', '未知品牌', '未知'

def extract_season_from_name(name):
    """提取季节"""
    if '25' in name:
        return '25秋冬'
    if '24' in name:
        return '24秋冬'
    if '春夏' in name or 'spring' in name.lower():
        return '25春夏'
    return '25秋冬'  # 默认

# 测试
if __name__ == "__main__":
    # 测试两个产品
    products = [
        {
            'productName': 'スターストレッチ2WAY中綿ブルゾン (MENS)',
            'productId': 'C25215107',
            'brand': 'Callaway Golf',
            'category': '外套'
        },
        {
            'productName': 'スターストレッチフルジップブルゾン (MENS)',
            'productId': 'C25215100',
            'brand': 'Callaway Golf',
            'category': '外套'
        }
    ]

    print("="*60)
    print("基于规则的标题生成测试")
    print("="*60)

    for i, product in enumerate(products, 1):
        print(f"\n产品 {i}: {product['productId']}")
        print("-" * 40)

        title = generate_title_by_rules(product)

        print(f"\n生成标题: {title}")
        print(f"标题长度: {len(title)} 字符")

        # 验证
        checks = {
            "长度25-30": 25 <= len(title) <= 30,
            "含卡拉威": "卡拉威" in title,
            "含Callaway": "Callaway" in title,
            "含高尔夫": "高尔夫" in title,
            "含男士": "男士" in title,
            "含25秋冬": "25秋冬" in title,
        }

        print("\n检查结果:")
        all_pass = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
            if not passed:
                all_pass = False

        if all_pass:
            print("\n✅ 所有基础检查通过！")

    print("\n=== 测试完成 ===")