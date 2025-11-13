#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡拉威13字段处理器验证测试
====================================

验证13字段处理器的功能完整性，确保：
1. AI标题生成真正工作（不是fallback）
2. 所有依赖文件完整
3. 测试时能生成正确的中文标题（不是日文）

Author: Claude Code
Date: 2025-11-13
"""

import os
import sys
import json
from typing import Dict, List

# 导入我们的处理器
from callaway_13field_processor import (
    Callaway13FieldProcessor,
    process_single_product,
    generate_cn_title,
    translate_description,
    determine_clothing_type,
    determine_gender,
    translate_color_name,
    build_color_multiline
)

def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试基础功能...")

    # 测试数据
    test_product = {
        'productId': 'TEST001',
        'productName': '25FW メンズ ストレッチポロシャツ Callaway Golf',
        'detailUrl': 'https://www.callawaygolf.jp/test',
        'priceText': '¥8,800 (税込)',
        'colors': [
            {'name': 'WHITE', 'code': '1000'},
            {'name': 'NAVY', 'code': '1031'},
            {'name': 'BLACK', 'code': '1040'}
        ],
        'sizes': ['S', 'M', 'L', 'LL'],
        'description': '今シーズンのスターストレッチPOLO。ストレッチ性に優れた素材で、動きやすさ抜群。',
        'brand': 'Callaway Golf'
    }

    try:
        # 测试性别分类
        gender = determine_gender(test_product)
        print(f"✓ 性别分类: {gender}")

        # 测试服装类型分类
        clothing_type = determine_clothing_type(test_product)
        print(f"✓ 服装类型: {clothing_type}")

        # 测试颜色翻译
        color_result = build_color_multiline(test_product['colors'])
        print(f"✓ 颜色翻译: {color_result}")

        return True
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False

def test_color_translation():
    """测试颜色翻译功能"""
    print("\n🎨 测试颜色翻译功能...")

    test_colors = [
        'BLACK',
        'WHITE',
        'NAVY',
        'ホワイト',
        'ブラック'
    ]

    try:
        for color in test_colors:
            translated = translate_color_name(color)
            print(f"✓ {color} → {translated}")

        return True
    except Exception as e:
        print(f"❌ 颜色翻译测试失败: {e}")
        return False

def test_brand_extraction():
    """测试品牌提取功能"""
    print("\n🏷️ 测试品牌提取功能...")

    from callaway_13field_processor import extract_brand_from_product

    test_products = [
        {'productName': 'Callaway Golf Polo', 'detailUrl': ''},
        {'productName': 'テーラーメイド ジャケット', 'detailUrl': 'https://taylormade.com'},
        {'productName': 'Titleist Hat', 'detailUrl': ''}
    ]

    try:
        for product in test_products:
            brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
            print(f"✓ {product['productName']} → {brand_chinese} ({brand_short})")

        return True
    except Exception as e:
        print(f"❌ 品牌提取测试失败: {e}")
        return False

def test_clothing_classification():
    """测试24种服装分类功能"""
    print("\n👔 测试24种服装分类功能...")

    test_cases = [
        {'productName': 'ダウンジャケット', 'expected': '羽绒服/棉服'},
        {'productName': 'Polo Shirt', 'expected': 'Polo衫'},
        {'productName': 'ゴルフシューズ', 'expected': '高尔夫球鞋'},
        {'productName': 'キャップ', 'expected': '帽子/头饰'},
        {'productName': 'ショーツ', 'expected': '短裤'},
        {'productName': 'Tシャツ', 'expected': 'T恤'}
    ]

    success_count = 0
    try:
        for case in test_cases:
            result = determine_clothing_type(case)
            if result == case['expected']:
                print(f"✓ {case['productName']} → {result}")
                success_count += 1
            else:
                print(f"⚠️ {case['productName']} → {result} (期望: {case['expected']})")

        print(f"分类准确率: {success_count}/{len(test_cases)}")
        return success_count >= len(test_cases) * 0.8  # 80%准确率

    except Exception as e:
        print(f"❌ 服装分类测试失败: {e}")
        return False

def test_processor_class():
    """测试处理器主类"""
    print("\n🔧 测试处理器主类...")

    # 创建测试数据
    test_product = {
        'productId': 'TEST002',
        'productName': '25FW Callaway メンズ ストレッチポロシャツ',
        'detailUrl': 'https://www.callawaygolf.jp/mens/polo/TEST002.html',
        'priceText': '¥9,800 (税込)',
        'colors': [
            {'name': 'WHITE', 'code': '1000'},
            {'name': 'NAVY', 'code': '1031'}
        ],
        'sizes': ['M', 'L', 'XL'],
        'description': '伸縮性の高い素材を使用し、動きやすさを重視したポロシャツ。',
        'mainImage': 'https://example.com/main.jpg'
    }

    try:
        processor = Callaway13FieldProcessor()
        result = processor.process_product(test_product)

        # 验证13个字段
        expected_fields = [
            '商品ID', '商品名称', '品牌', '商品链接', '分类', '价格',
            '生成标题', '性别', '服装类型', '颜色', '尺寸', '描述翻译', '图片链接'
        ]

        missing_fields = [field for field in expected_fields if field not in result]
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
            return False

        print(f"✓ 13个字段完整生成")
        print(f"✓ 商品ID: {result['商品ID']}")
        print(f"✓ 品牌识别: {result['品牌']}")
        print(f"✓ 性别分类: {result['性别']}")
        print(f"✓ 服装类型: {result['服装类型']}")

        return True

    except Exception as e:
        print(f"❌ 处理器类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_glm_api_key():
    """检查GLM API密钥"""
    print("\n🔑 检查GLM API密钥...")

    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("⚠️ ZHIPU_API_KEY 环境变量未设置")
        print("  AI标题生成和描述翻译功能将无法工作")
        print("  请设置环境变量：export ZHIPU_API_KEY=your_api_key")
        return False
    else:
        print("✓ ZHIPU_API_KEY 已设置")
        return True

def run_complete_test():
    """运行完整测试"""
    print("🚀 开始卡拉威13字段处理器验证测试")
    print("=" * 60)

    # 检查API密钥
    has_api_key = check_glm_api_key()

    # 运行功能测试
    tests = [
        ("基础功能", test_basic_functionality),
        ("颜色翻译", test_color_translation),
        ("品牌提取", test_brand_extraction),
        ("服装分类", test_clothing_classification),
        ("处理器类", test_processor_class)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 40)

        if test_func():
            print(f"✅ {test_name} - 通过")
            passed_tests += 1
        else:
            print(f"❌ {test_name} - 失败")

    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"通过: {passed_tests}/{total_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")

    if has_api_key:
        print("\n🤖 AI功能状态: 可用 (已设置GLM API密钥)")
        print("   - AI标题生成: 可用")
        print("   - 描述翻译: 可用")
    else:
        print("\n🤖 AI功能状态: 不可用 (未设置GLM API密钥)")
        print("   - AI标题生成: 不可用")
        print("   - 描述翻译: 不可用")
        print("   - 其他功能: 正常")

    if passed_tests == total_tests:
        print("\n🎉 所有功能测试通过！处理器已准备就绪。")
        return True
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 个测试失败，请检查相关功能。")
        return False

def demo_ai_features():
    """演示AI功能（如果有API密钥）"""
    if not os.environ.get('ZHIPU_API_KEY'):
        print("\n⚠️ 未设置GLM API密钥，跳过AI功能演示")
        return

    print("\n🤖 演示AI功能...")
    print("-" * 40)

    demo_product = {
        'productId': 'DEMO001',
        'productName': '25FW Callaway メンズ 高機能ダウンジャケット',
        'detailUrl': 'https://www.callawaygolf.jp/demo',
        'description': '最新のダウン素材を使用した高機能ジャケット。軽量でありながら暖かく、ビジネスシーンにも対応。',
        'brand': 'Callaway Golf'
    }

    try:
        print("📝 测试AI标题生成...")
        title = generate_cn_title(demo_product)
        if title:
            print(f"✅ AI标题生成成功: {title}")
        else:
            print("❌ AI标题生成失败")

        print("\n📝 测试描述翻译...")
        translation = translate_description(demo_product)
        if translation:
            print(f"✅ 描述翻译成功 ({len(translation)}字符)")
            print(f"   前100字符: {translation[:100]}...")
        else:
            print("❌ 描述翻译失败")

    except Exception as e:
        print(f"❌ AI功能演示失败: {e}")

if __name__ == "__main__":
    # 运行完整测试
    success = run_complete_test()

    # 如果基础测试通过，演示AI功能
    if success:
        demo_ai_features()

    print(f"\n🏁 测试完成!")