#!/usr/bin/env python3
"""
完整测试标题生成流程
"""

import sys
import os
sys.path.insert(0, '.')

from callaway_13field_processor import (
    Callaway13FieldProcessor,
    build_smart_prompt,
    call_glm_api,
    clean_title,
    validate_title
)

def test_full_title_process():
    """测试完整的标题生成流程"""

    # 真实的Le Coq产品数据
    product = {
        'productId': 'LE1872EM012989',
        'productName': '【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）',
        'brand': 'Le Coq Sportif Golf',
        'detailUrl': 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
        'priceText': '￥19,800'
    }

    print("=== 完整标题生成流程测试 ===")
    print()

    # 初始化处理器
    processor = Callaway13FieldProcessor()

    print("1. 构建提示词...")
    prompt = build_smart_prompt(product)
    print(f"提示词长度: {len(prompt)}字符")
    print()

    print("2. 调用GLM API...")
    raw_title = call_glm_api(prompt)
    if not raw_title:
        print("❌ GLM API调用失败")
        return

    print(f"GLM原始返回: {raw_title}")
    print(f"原始长度: {len(raw_title)}字")
    print()

    print("3. 清理标题...")
    cleaned_title = clean_title(raw_title)
    print(f"清理后标题: {cleaned_title}")
    print(f"清理后长度: {len(cleaned_title)}字")
    print()

    print("4. 验证标题...")
    is_valid = validate_title(cleaned_title, product)
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

    if not is_valid:
        print("\n详细验证问题:")
        # 检查长度
        length = len(cleaned_title)
        if length < 26:
            print(f"❌ 长度不足: {length}字 (需要26-30字)")
        elif length > 30:
            print(f"❌ 长度超长: {length}字 (需要26-30字)")
        else:
            print(f"✅ 长度正确: {length}字")

        # 检查必需词
        if '高尔夫' not in cleaned_title:
            print("❌ 缺少'高尔夫'")
        else:
            print("✅ 包含'高尔夫'")

        # 检查品牌
        brand_key, brand_chinese, brand_short = processor.extract_brand_from_product(product)
        if brand_short not in cleaned_title:
            print(f"❌ 缺少品牌: {brand_short}")
        else:
            print(f"✅ 包含品牌: {brand_short}")

    print("\n5. 最终结果:")
    if is_valid:
        print(f"✅ 成功生成标题: {cleaned_title}")
        print(f"✅ 长度: {len(cleaned_title)}字")
    else:
        print("❌ 标题生成失败")

if __name__ == "__main__":
    test_full_title_process()