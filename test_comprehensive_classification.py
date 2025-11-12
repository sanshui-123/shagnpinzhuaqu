#!/usr/bin/env python3
"""
全面的衣服分类测试
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'feishu_update'))

from services.classifiers import determine_clothing_type, determine_gender

# 更广泛的测试数据
comprehensive_test_products = [
    # 夹克类
    {
        "productName": "スターストレッチ2WAY中綿ブルゾン (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/test1.html",
        "expected": "夹克"
    },

    # 卫衣/连帽衫类
    {
        "productName": "Callaway＋CLUBHAUS Crewneck Sweat 2025 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/test2.html",
        "expected": "卫衣/连帽衫"
    },
    {
        "productName": "フーディーパーカー (WOMENS)",
        "detailUrl": "https://www.callawaygolf.jp/womens/tops/test3.html",
        "expected": "卫衣/连帽衫"
    },

    # 马甲/背心类
    {
        "productName": "スターストレッチフルジップ中綿ベスト (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/test4.html",
        "expected": "马甲/背心"
    },

    # Polo衫类
    {
        "productName": "プルオーバーポロシャツ (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/polo/test5.html",
        "expected": "Polo衫"
    },

    # T恤类
    {
        "productName": "Tシャツ カジュアル (WOMENS)",
        "detailUrl": "https://www.callawaygolf.jp/womens/tshirt/test6.html",
        "expected": "T恤"
    },

    # 衬衫类
    {
        "productName": "ボタンシャツ長袖 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/shirt/test7.html",
        "expected": "衬衫"
    },

    # 羽绒服类
    {
        "productName": "ダウンジャケット 防寒 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/outer/test8.html",
        "expected": "羽绒服/棉服"
    },

    # 针织衫类
    {
        "productName": "ニットセーター 秋冬 (WOMENS)",
        "detailUrl": "https://www.callawaygolf.jp/womens/knit/test9.html",
        "expected": "针织衫/毛衣"
    },

    # 长裤类
    {
        "productName": "ゴルフパンツ ストレッチ (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/pants/test10.html",
        "expected": "长裤"
    },

    # 短裤类
    {
        "productName": "ショートパンツ 夏用 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/shorts/test11.html",
        "expected": "短裤"
    },

    # 高尔夫球鞋类
    {
        "productName": "ゴルフシューズ 軽量 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/shoes/test12.html",
        "expected": "高尔夫球鞋"
    },

    # 配件类
    {
        "productName": "ゴルフグローブ 皮革 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/accessory/test13.html",
        "expected": "高尔夫手套"
    },

    # 外套类（通用）
    {
        "productName": "アウター 防風 (MENS)",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/test14.html",
        "expected": "外套"
    }
]

print("=" * 100)
print("全面分类测试结果")
print("=" * 100)

correct_count = 0
total_count = len(comprehensive_test_products)

for i, product in enumerate(comprehensive_test_products, 1):
    print(f"\n【测试 {i:2d}】 {product['productName']}")
    print(f"期望分类: {product['expected']}")

    # 测试衣服分类
    clothing_type = determine_clothing_type(product)
    gender = determine_gender(product)

    print(f"实际分类: {clothing_type}")
    print(f"性别分类: {gender}")

    # 检查是否正确
    is_correct = clothing_type == product['expected']
    status = "✅ 正确" if is_correct else "❌ 错误"
    print(f"结果: {status}")

    if is_correct:
        correct_count += 1

    print("-" * 60)

print("\n" + "=" * 100)
print(f"测试完成! 正确率: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
print("=" * 100)