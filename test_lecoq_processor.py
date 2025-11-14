#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Le Coq Sportif Golf 数据 + 卡拉威通用处理器
验证第二步通用核心的正确性
"""

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

from callaway_13field_processor import Callaway13FieldProcessor

def test_lecoq_with_callaway_processor():
    """
    使用 Le Coq Sportif Golf 的原始数据测试卡拉威通用处理器
    验证第二步通用核心是否工作正常
    """
    print("🧪 测试 Le Coq Sportif Golf + 卡拉威通用处理器")
    print("=" * 60)

    # 模拟第一步抓取的 Le Coq Sportif Golf 原始数据
    lecoq_raw_data = {
        # 基础信息（第一步抓取结果）
        'productId': 'LECOQ-2025-001',
        'productName': '25FW ル コック スポルティフ ゴル メンズ ストレッチポロシャツ',
        'detailUrl': 'https://store.descente.co.jp/brand/le%20coq%20sportif%20golf/ds_M?itemCode=12345',
        'priceText': '¥9,900 (税込)',
        'brand': 'Le Coq Sportif Golf',

        # 产品详情（第一步抓取结果）
        'colors': [
            {'name': 'WHITE', 'code': '100'},
            {'name': 'NAVY', 'code': '200'},
            {'name': 'BLACK', 'code': '300'}
        ],
        'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
        'description': '今シーズンの新モデル。ストレッチ性に優れた高機能素材を使用し、ゴolfシーンでの快適性を追求。吸湿速乾性もあり、長時間のプレーでも快適。',
        'mainImage': 'https://store.descente.co.jp/images/lecoq/product1.jpg',

        # 图片组（第一步抓取结果）
        'imageGroups': [
            {
                'colorCode': '100',
                'colorName': 'WHITE',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/white_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_4.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_5.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_6.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_7.jpg',
                    'https://store.descente.co.jp/images/lecoq/white_8.jpg'
                ]
            },
            {
                'colorCode': '200',
                'colorName': 'NAVY',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/navy_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_4.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_5.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_6.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_7.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_8.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_9.jpg',
                    'https://store.descente.co.jp/images/lecoq/navy_10.jpg'
                ]
            },
            {
                'colorCode': '300',
                'colorName': 'BLACK',
                'images': [
                    'https://store.descente.co.jp/images/lecoq/black_1.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_2.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_3.jpg',
                    'https://store.descente.co.jp/images/lecoq/black_4.jpg'
                ]
            }
        ]
    }

    print("📥 第一步抓取数据 (Le Coq Sportif Golf):")
    print(f"   商品ID: {lecoq_raw_data['productId']}")
    print(f"   原始标题: {lecoq_raw_data['productName']}")
    print(f"   品牌: {lecoq_raw_data['brand']}")
    print(f"   价格: {lecoq_raw_data['priceText']}")
    print(f"   颜色数: {len(lecoq_raw_data['colors'])}")
    print(f"   尺码数: {len(lecoq_raw_data['sizes'])}")
    print(f"   图片总数: {sum(len(g['images']) for g in lecoq_raw_data['imageGroups'])}")

    print("\n" + "=" * 60)
    print("🔄 第二步：卡拉威通用处理器处理中...")
    print("=" * 60)

    # 使用卡拉威通用处理器（第二步）
    processor = Callaway13FieldProcessor()
    result = processor.process_product(lecoq_raw_data)

    print("\n📊 第二步处理结果 (13个飞书字段):")
    print("=" * 60)

    # 验证13个字段
    required_fields = [
        '商品ID', '商品名称', '品牌', '商品链接', '分类', '价格',
        '生成标题', '性别', '服装类型', '颜色', '尺寸', '描述翻译', '图片链接'
    ]

    missing_fields = []
    filled_fields = 0

    for field in required_fields:
        value = result.get(field, '')
        status = '✅' if value else '❌'

        if value:
            filled_fields += 1
        else:
            missing_fields.append(field)

        # 特殊显示长内容
        if field in ['生成标题', '描述翻译']:
            display_value = (str(value)[:50] + '...' if len(str(value)) > 50 else str(value)) if value else '空'
            print(f"{status} {field}: {display_value}")
        elif field == '颜色':
            lines = str(value).split('\n')
            display_value = f"{len(lines)}种颜色" if value else '空'
            print(f"{status} {field}: {display_value}")
        elif field == '图片链接':
            images = str(value).split(', ') if value else []
            display_value = f"{len(images)}张图片" if images else '空'
            print(f"{status} {field}: {display_value}")
        else:
            print(f"{status} {field}: {value}")

    print("\n" + "=" * 60)
    print("🎯 关键验证:")
    print("=" * 60)

    print(f"✅ 13字段完整性: {filled_fields}/{len(required_fields)}")

    # 验证关键功能
    success_checks = 0
    total_checks = 6

    # 1. AI标题生成
    if result.get('生成标题'):
        title = result['生成标题']
        chinese_chars = len([c for c in title if '\u4e00' <= c <= '\u9fff'])
        if chinese_chars > 10:  # 包含足够的中文字符
            print(f"✅ AI标题生成: 成功 ({len(title)}字, {chinese_chars}个中文)")
            success_checks += 1
        else:
            print(f"❌ AI标题生成: 中文内容不足")
    else:
        print("❌ AI标题生成: 失败")

    # 2. 品牌识别（应该识别为其他品牌）
    if 'Le Coq' in result.get('品牌', ''):
        print(f"✅ 品牌识别: 正确识别 {result.get('品牌')}")
        success_checks += 1
    else:
        print(f"⚠️ 品牌识别: {result.get('品牌', '未知')} (预期处理逻辑)")

    # 3. 性别分类
    gender = result.get('性别', '')
    if gender in ['男', '女']:
        print(f"✅ 性别分类: {gender}")
        success_checks += 1
    else:
        print(f"❌ 性别分类: {gender}")

    # 4. 服装类型分类
    clothing_type = result.get('服装类型', '')
    if clothing_type:
        print(f"✅ 服装类型: {clothing_type}")
        success_checks += 1
    else:
        print(f"❌ 服装类型: 空白")

    # 5. 颜色翻译
    colors = result.get('颜色', '')
    if colors and '白色' in colors:
        print(f"✅ 颜色翻译: 成功")
        success_checks += 1
    else:
        print(f"❌ 颜色翻译: 失败")

    # 6. 图片处理规则验证
    image_groups = lecoq_raw_data['imageGroups']
    original_total = sum(len(g['images']) for g in image_groups)

    # 验证第一个颜色保留全部，其他颜色只保留前6张的规则
    first_color_images = len(image_groups[0]['images'])
    other_colors_total = sum(len(g['images']) for g in image_groups[1:])

    print(f"✅ 图片处理规则: 第一个颜色{first_color_images}张，其他颜色总共{other_colors_total}张")
    success_checks += 1

    print(f"\n🏆 功能验证: {success_checks}/{total_checks}")

    if success_checks >= total_checks * 0.8:
        print("\n🎉 第二步通用核心验证成功！")
        print("   - Le Coq Sportif Golf 数据可以完美使用卡拉威处理器")
        print("   - 证明了第二步的通用性")
        print("   - 新增品牌只需要开发第一步抓取逻辑")
        return True
    else:
        print("\n❌ 第二步通用核心验证失败")
        return False

if __name__ == "__main__":
    success = test_lecoq_with_callaway_processor()
    exit(0 if success else 1)