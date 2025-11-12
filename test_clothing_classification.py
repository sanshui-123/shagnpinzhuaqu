#!/usr/bin/env python3
"""
测试衣服分类器
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'feishu_update'))

from services.classifiers import determine_clothing_type, determine_gender

# 测试数据
test_products = [
    {
        "productId": "C25117160",
        "productName": "《再入荷》Callaway＋CLUBHAUS Crewneck Sweat 2025 (MENS)",
        "category": "mens_all",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/C25117160_.html?pid=C25117160_1010_L"
    },
    {
        "productId": "C25215107",
        "productName": "スターストレッチ2WAY中綿ブルゾン (MENS)",
        "category": "mens_all",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/C25215107_.html?pid=C25215107_1030_L"
    },
    {
        "productId": "C25215106",
        "productName": "スターストレッチ中綿ブルゾン ※4Lサイズあり (MENS)",
        "category": "mens_all",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/C25215106_.html?pid=C25215106_1120_L"
    },
    {
        "productId": "C25215100",
        "productName": "スターストレッチフルジップブルゾン (MENS)",
        "category": "mens_all",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/C25215100_.html?pid=C25215100_1180_L"
    },
    {
        "productId": "C25216103",
        "productName": "スターストレッチフルジップ中綿ベスト (MENS)",
        "category": "mens_all",
        "detailUrl": "https://www.callawaygolf.jp/mens/tops/outer/C25216103_.html?pid=C25216103_1030_L"
    }
]

print("=" * 80)
print("衣服分类测试结果")
print("=" * 80)

for i, product in enumerate(test_products, 1):
    print(f"\n【产品 {i}】")
    print(f"Product ID: {product['productId']}")
    print(f"Product Name: {product['productName']}")
    print(f"Category: {product['category']}")
    print(f"URL: {product['detailUrl']}")

    # 测试性别分类
    gender = determine_gender(product)
    print(f"性别分类: {gender}")

    # 测试衣服分类
    clothing_type = determine_clothing_type(product)
    print(f"衣服分类: {clothing_type}")

    print("-" * 60)

print("\n分类测试完成!")