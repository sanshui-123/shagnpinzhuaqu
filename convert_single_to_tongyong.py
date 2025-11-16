#!/usr/bin/env python3
"""
将单个抓取结果转换为tongyong_feishu_update期望的格式
"""

import json
import sys
import os

def convert_single_to_tongyong_format(input_file, output_file):
    """转换单个产品数据为tongyong格式"""

    with open(input_file, 'r', encoding='utf-8') as f:
        single_data = json.load(f)

    # 转换为products格式
    product_id = single_data.get('商品ID', single_data.get('productId', f'product_{int(os.path.getmtime(input_file))}'))

    products = {}
    products[product_id] = {
        'productId': single_data.get('商品ID', single_data.get('productId', '')),
        'productName': single_data.get('商品标题', single_data.get('productName', '')),
        'detailUrl': single_data.get('商品链接', single_data.get('detailUrl', '')),
        'price': single_data.get('价格', single_data.get('priceText', '')),
        'brand': single_data.get('品牌名', ''),
        'category': '',
        'gender': single_data.get('性别', ''),
        'description': single_data.get('详情页文字', ''),

        # 处理颜色 - 从对象数组转为名称数组
        'colors': [color.get('name', '') for color in single_data.get('颜色', []) if color.get('name')],

        # 处理尺码
        'sizes': single_data.get('尺码', []),

        # 处理图片
        'imageUrls': single_data.get('图片链接', []),

        # 处理尺码表
        'sizeChart': single_data.get('尺码表', {}),

        'scrapeInfo': {
            'totalColors': len(single_data.get('颜色', [])),
            'totalSizes': len(single_data.get('尺码', [])),
            'totalImages': len(single_data.get('图片链接', []))
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
    print(f"🏷️ 商品标题: {single_data.get('商品标题', '')}")
    print(f"👕 性别: {single_data.get('性别', '')}")
    print(f"🎨 颜色数量: {len(products[product_id]['colors'])}")
    print(f"📏 尺码数量: {len(products[product_id]['sizes'])}")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'single_url_fixed_latest.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'tongyong_format.json'

    convert_single_to_tongyong_format(input_file, output_file)