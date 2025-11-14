#!/usr/bin/env python3
"""
调试验证失败的具体原因
"""

import sys
import os
sys.path.insert(0, '.')

from callaway_13field_processor import Callaway13FieldProcessor

def debug_title_validation():
    """调试标题验证失败的原因"""

    processor = Callaway13FieldProcessor()

    # Le Coq测试产品
    product = {
        'productId': 'LG5FWB50M',
        'productName': '【可拆卸袖子可能】热航中棉两用夹克（武井壮着用）',
        'brand': 'Le Coq Sportif Golf',
        'detailUrl': 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
        'priceText': '￥19,800'
    }

    print("=== 调试标题验证失败 ===")
    print()

    # 手动模拟标题生成过程
    for attempt in range(2):
        print(f"=== 尝试 {attempt + 1} ===")

        # 1. 构建提示词
        from callaway_13field_processor import build_smart_prompt, call_glm_api, clean_title, validate_title

        prompt = build_smart_prompt(product)
        print(f"1. 提示词构建完成，长度: {len(prompt)}字符")

        # 2. 调用GLM
        raw_title = call_glm_api(prompt)
        if not raw_title:
            print("❌ GLM返回空")
            continue

        print(f"2. GLM原始返回: '{raw_title}'")
        print(f"   原始长度: {len(raw_title)}字")

        # 3. 清理标题
        title = clean_title(raw_title.strip())
        print(f"3. 清理后标题: '{title}'")
        print(f"   清理后长度: {len(title)}字")

        # 4. 验证标题
        print("4. 验证详情:")
        validation_result = validate_title_debug(title, product)

        if validation_result['passed']:
            print("✅ 验证通过!")
            print(f"✅ 成功标题: {title}")
            return
        else:
            print("❌ 验证失败:")
            for reason in validation_result['reasons']:
                print(f"   - {reason}")

    print("❌ 两次尝试都失败")

def validate_title_debug(title: str, product: dict) -> dict:
    """详细的验证函数，返回失败原因"""
    result = {'passed': True, 'reasons': []}

    if not title:
        result['passed'] = False
        result['reasons'].append("标题为空")
        return result

    # 1. 长度检查
    length = len(title)
    if not (26 <= length <= 30):
        result['passed'] = False
        if length < 26:
            result['reasons'].append(f"长度不足: {length}字 (需要26-30字)")
        else:
            result['reasons'].append(f"长度超长: {length}字 (需要26-30字)")

    # 2. 必须包含"高尔夫"
    if '高尔夫' not in title:
        result['passed'] = False
        result['reasons'].append("缺少'高尔夫'")
    elif title.count('高尔夫') != 1:
        result['passed'] = False
        result['reasons'].append(f"'高尔夫'出现次数错误: {title.count('高尔夫')}次")

    # 3. 品牌检查
    from callaway_13field_processor import extract_brand_from_product
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    if brand_short not in title:
        result['passed'] = False
        result['reasons'].append(f"缺少品牌: {brand_short}")

    # 4. 禁止词汇检查
    forbidden_words = [
        '官网', '正品', '专柜', '代购', '海外', '进口',
        '授权', '旗舰', '限量', '促销', '特价', '淘宝',
        '天猫', '京东', '拼多多'
    ]
    for word in forbidden_words:
        if word in title:
            result['passed'] = False
            result['reasons'].append(f"包含禁止词汇: {word}")
            break

    # 5. 日文字符检查
    import re
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', title):
        result['passed'] = False
        result['reasons'].append("包含日文字符")

    # 6. 连续重复检查
    if re.search(r'(.)\1{2,}', title):  # 3个及以上相同字符连续
        result['passed'] = False
        result['reasons'].append("包含连续重复字符")
    if re.search(r'(..)\1{2,}', title):  # 2字词语重复3次
        result['passed'] = False
        result['reasons'].append("包含连续重复词语")

    return result

if __name__ == "__main__":
    debug_title_validation()