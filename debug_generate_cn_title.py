#!/usr/bin/env python3
"""
直接调试generate_cn_title函数
"""

import os
import sys
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

sys.path.insert(0, '.')

def debug_generate_cn_title():
    """直接调试generate_cn_title函数"""
    print("=== 调试generate_cn_title函数 ===")
    print()

    # 导入相关函数
    from callaway_13field_processor import (
        generate_cn_title,
        build_smart_prompt,
        call_glm_api,
        clean_title,
        optimize_title,
        validate_title
    )

    # 测试产品数据
    product = {
        'productId': 'LE1872EM012989',
        'productName': '【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）',
        'brand': 'Le Coq Sportif Golf',
        'detailUrl': 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
        'priceText': '￥19,800'
    }

    print("测试产品:")
    print(f"  产品名称: {product['productName']}")
    print(f"  品牌: {product['brand']}")
    print()

    print("=== 直接调用generate_cn_title ===")

    # 手动模拟generate_cn_title的每一步
    for attempt in range(2):
        print(f"\n--- 尝试 {attempt + 1} ---")

        # 1. 构建提示词
        print("1. 构建提示词...")
        prompt = build_smart_prompt(product)
        print(f"   提示词长度: {len(prompt)}字符")

        # 2. 调用GLM
        print("2. 调用GLM API...")
        raw_title = call_glm_api(prompt)
        if not raw_title:
            print("   ❌ GLM返回空")
            continue

        print(f"   原始返回: '{raw_title}'")
        print(f"   原始长度: {len(raw_title)}字")

        # 3. 清理标题
        print("3. 清理标题...")
        cleaned_title = clean_title(raw_title.strip())
        print(f"   清理后: '{cleaned_title}'")
        print(f"   清理后长度: {len(cleaned_title)}字")

        # 4. 优化标题
        print("4. 优化标题...")
        optimized_title = optimize_title(cleaned_title)
        print(f"   优化后: '{optimized_title}'")
        print(f"   优化后长度: {len(optimized_title)}字")

        # 5. 验证标题
        print("5. 验证标题...")
        is_valid = validate_title(optimized_title, product)
        print(f"   验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

        if not is_valid:
            # 详细验证分析
            print("   失败原因分析:")
            length = len(optimized_title)
            if length < 26:
                print(f"     - 长度不足: {length}字")
            elif length > 30:
                print(f"     - 长度超长: {length}字")

            has_golf = '高尔夫' in optimized_title
            print(f"     - 包含'高尔夫': {'是' if has_golf else '否'}")

            from callaway_13field_processor import extract_brand_from_product
            brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
            has_brand = brand_short in optimized_title
            print(f"     - 包含品牌'{brand_short}': {'是' if has_brand else '否'}")

        if is_valid:
            print(f"\n🎉 成功生成标题: {optimized_title}")
            print(f"📏 长度: {len(optimized_title)}字")
            return optimized_title

    print("\n❌ 两次尝试都失败")
    return None

if __name__ == "__main__":
    result = debug_generate_cn_title()
    if result:
        print(f"\n✅ 最终成功标题: {result}")
    else:
        print(f"\n❌ 生成失败")