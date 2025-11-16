#!/usr/bin/env python3
"""
将step2结果转换为tongyong_feishu_update格式
"""

import json
import sys

def convert_step2_to_feishu_format(input_file, output_file):
    """转换step2格式为tongyong格式"""

    with open(input_file, 'r', encoding='utf-8') as f:
        step2_data = json.load(f)

    # 转换为products格式
    product_id = step2_data.get('商品ID', f'product_{int(time.time())}')

    products = {}
    products[product_id] = {
        'productId': step2_data.get('商品ID', ''),
        'productName': step2_data.get('商品名称', ''),
        'detailUrl': step2_data.get('商品链接', ''),
        'price': step2_data.get('价格', ''),
        'brand': step2_data.get('品牌', ''),
        'category': step2_data.get('分类', ''),
        'gender': step2_data.get('性别', ''),
        'description': step2_data.get('描述翻译', ''),
        'colors': step2_data.get('颜色', '').split('\n') if step2_data.get('颜色') else [],
        'sizes': step2_data.get('尺寸', '').split(', ') if step2_data.get('尺寸') else [],
        'imageUrls': step2_data.get('图片链接', '').split(', ') if step2_data.get('图片链接') else [],
        'sizeChart': {},
        'scrapeInfo': {
            'totalColors': len(step2_data.get('颜色', '').split('\n')) if step2_data.get('颜色') else 0,
            'totalSizes': len(step2_data.get('尺寸', '').split(', ')) if step2_data.get('尺寸') else 0,
            'totalImages': len(step2_data.get('图片链接', '').split(', ')) if step2_data.get('图片链接') else 0
        }
    }

    # 创建tongyong格式输出
    output_data = {
        'products': products,
        'total': 1,
        'processed': 1,
        'failed': 0,
        'errors': [],
        'timestamp': '',
        'brand': 'lecoqgolf',
        'batchMode': False
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成：{input_file} → {output_file}")
    print(f"📦 产品ID: {product_id}")
    print(f"🏷️ 标题: {step2_data.get('生成标题', '')}")

if __name__ == "__main__":
    import time

    input_file = sys.argv[1] if len(sys.argv) > 1 else 'step2_test_result.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'step2_feishu_format.json'

    convert_step2_to_feishu_format(input_file, output_file)