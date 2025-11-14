#!/usr/bin/env python3
"""
测试真实的Le Coq产品页面数据
"""

import sys
import os
from pathlib import Path

# 加载环境变量
env_file = Path("callaway.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("✅ 已加载callaway.env环境变量")
else:
    print("⚠️ 未找到callaway.env文件")

# 添加当前路径
sys.path.insert(0, '.')

from callaway_13field_processor import Callaway13FieldProcessor

def create_real_lecoq_data():
    """基于真实产品页面创建测试数据"""

    # 从产品页面标题提取的信息
    # 标题: ルコックスポルティフ ゴルフ le coq sportif golf 【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）

    real_lecoq_data = {
        # 基础信息（第一步抓取结果）
        'productId': 'LE1872EM012989',  # 真实产品ID
        'productName': '【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）',
        'detailUrl': 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
        'priceText': '￥19,800',
        'brand': 'Le Coq Sportif Golf',

        # 产品详情（模拟第一步抓取结果）
        'colors': [
            {'name': 'NAVY', 'code': 'NV'},  # 海军蓝
            {'name': 'BLACK', 'code': 'BK'},  # 黑色
            {'name': 'GREY', 'code': 'GY'},   # 灰色
        ],
        'sizes': ['S', 'M', 'L', 'LL', '3L'],
        'description': '''保温性に優れた中綿入りブルゾン。袖は取り外し可能で、シーズンを通して活躍する2WAY仕様。ヒートナビ仕様で、体の冷えやすい部分を効果的に保温。アクティブなゴルフシーンをサポートする高機能アイテム。''',
        'mainImage': 'https://store.descente.co.jp/images/lecoq/main.jpg',

        # 图片组（模拟第一步抓取结果）
        'imageGroups': [
            {
                'colorCode': 'NV',
                'colorName': 'NAVY',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/navy_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_4.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_5.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_6.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_7.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_8.jpg'
                ]
            },
            {
                'colorCode': 'BK',
                'colorName': 'BLACK',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/black_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_4.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_5.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_6.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_7.jpg'
                ]
            },
            {
                'colorCode': 'GY',
                'colorName': 'GREY',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/grey_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/grey_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/grey_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/grey_4.jpg',
                    'https://store.descente.co.jp/images/lecoq/grey_5.jpg'
                ]
            }
        ]
    }

    return real_lecoq_data

def test_real_lecoq_product():
    """测试真实Le Coq产品"""
    print("🧪 测试真实Le Coq产品数据")
    print("=" * 60)

    # 创建真实产品数据
    product_data = create_real_lecoq_data()

    print("📥 真实产品数据:")
    print(f"   商品ID: {product_data['productId']}")
    print(f"   产品名称: {product_data['productName']}")
    print(f"   品牌: {product_data['brand']}")
    print(f"   价格: {product_data['priceText']}")
    print(f"   颜色数: {len(product_data['colors'])}")
    print(f"   尺码数: {len(product_data['sizes'])}")
    print(f"   图片总数: {sum(len(g['images']) for g in product_data['imageGroups'])}")
    print(f"   产品链接: {product_data['detailUrl']}")
    print()

    # 分析产品特点
    print("🔍 产品特点分析:")
    name = product_data['productName']
    print(f"   包含日文特征: {name}")

    # 检查关键词
    keywords = {
        '可拆卸袖子': '袖取り外し可能' in name,
        '中棉': '中わた' in name,
        '两用': '2WAY' in name,
        '外套': 'ブルゾン' in name,
        '保温': 'ヒートナビ' in name
    }

    for feature, found in keywords.items():
        status = '✅' if found else '❌'
        print(f"   {status} {feature}: {found}")
    print()

    print("🔄 第二步：卡拉威通用处理器处理中...")
    print("=" * 60)

    # 初始化处理器
    processor = Callaway13FieldProcessor()

    # 处理产品
    try:
        result = processor.process_product(product_data)

        print("\n📊 处理结果:")
        print("=" * 60)

        # 验证13个字段
        required_fields = [
            '商品ID', '商品名称', '品牌', '商品链接', '分类', '价格',
            '生成标题', '性别', '服装类型', '颜色', '尺寸', '描述翻译', '图片链接'
        ]

        filled_fields = 0
        missing_fields = []

        for field in required_fields:
            value = result.get(field, '')
            status = '✅' if value else '❌'

            if value:
                filled_fields += 1
            else:
                missing_fields.append(field)

            # 特殊显示长内容
            if field in ['生成标题']:
                if value:
                    print(f"{status} {field}: {value} (长度: {len(value)}字)")
                else:
                    print(f"{status} {field}: 空白")
            elif field in ['描述翻译']:
                if value:
                    preview = value[:100] + '...' if len(value) > 100 else value
                    print(f"{status} {field}: {preview} (总长度: {len(value)}字符)")
                else:
                    print(f"{status} {field}: 空白")
            elif field == '颜色':
                if value:
                    lines = str(value).split('\n')
                    print(f"{status} {field}: {len(lines)}种颜色")
                else:
                    print(f"{status} {field}: 空白")
            elif field == '图片链接':
                if value:
                    images = str(value).split(', ') if value else []
                    print(f"{status} {field}: {len(images)}张图片")
                else:
                    print(f"{status} {field}: 空白")
            else:
                print(f"{status} {field}: {value}")

        print(f"\n📈 字段完整性: {filled_fields}/{len(required_fields)}")

        # 关键功能验证
        print("\n🎯 关键验证:")
        print("=" * 60)

        # 1. 品牌识别
        brand = result.get('品牌', '')
        if 'Le Coq公鸡乐卡克' in brand:
            print(f"✅ 品牌识别: 正确 ({brand})")
        else:
            print(f"❌ 品牌识别: {brand}")

        # 2. 性别分类
        gender = result.get('性别', '')
        if gender:
            print(f"✅ 性别分类: {gender}")
        else:
            print("❌ 性别分类: 失败")

        # 3. 服装类型
        clothing_type = result.get('服装类型', '')
        if clothing_type:
            print(f"✅ 服装类型: {clothing_type}")
        else:
            print("❌ 服装类型: 失败")

        # 4. AI标题生成
        title = result.get('生成标题', '')
        if title:
            chinese_chars = len([c for c in title if '\u4e00' <= c <= '\u9fff'])
            length_ok = 26 <= len(title) <= 30
            has_golf = '高尔夫' in title
            has_brand = 'Le Coq公鸡乐卡克' in title

            print(f"✅ AI标题生成: 成功")
            print(f"   标题: {title}")
            print(f"   长度: {len(title)}字 ({'合规' if length_ok else '不合规'})")
            print(f"   中文字符: {chinese_chars}个")
            print(f"   包含'高尔夫': {'是' if has_golf else '否'}")
            print(f"   包含品牌: {'是' if has_brand else '否'}")
        else:
            print("❌ AI标题生成: 失败")

        # 5. 描述翻译
        translation = result.get('描述翻译', '')
        if translation:
            has_structure = '【产品描述】' in translation and '【产品亮点】' in translation
            print(f"✅ 描述翻译: 成功")
            print(f"   长度: {len(translation)}字符")
            print(f"   格式正确: {'是' if has_structure else '否'}")
        else:
            print("❌ 描述翻译: 失败")

        # 6. 图片处理
        original_total = sum(len(g['images']) for g in product_data['imageGroups'])
        final_images = result.get('图片链接', '')
        if final_images:
            final_count = len(final_images.split(', '))
            reduction = original_total - final_count
            print(f"✅ 图片处理: 成功")
            print(f"   原始: {original_total}张 → 处理后: {final_count}张 (减少{reduction}张)")
        else:
            print("❌ 图片处理: 失败")

        print(f"\n🏆 测试结果: {'成功' if filled_fields >= 11 else '部分成功'}")

        return result

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_real_lecoq_product()

    if result:
        print("\n🎉 真实Le Coq产品测试完成！")
    else:
        print("\n❌ 测试失败")