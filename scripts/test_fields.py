#!/usr/bin/env python3
"""测试字段提取"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_update.services.field_assembler import FieldAssembler

def test_fields():
    # 读取测试数据
    with open('single_test.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for product in data.get('products', []):
        print(f"\n{'='*60}")
        print(f"测试产品: {product['productId']}")
        print(f"产品名称: {product.get('productName', '')}")
        print(f"{'='*60}")

        # 调用字段组装器
        assembler = FieldAssembler()
        fields = assembler.build_update_fields(product)

        # 打印所有字段
        field_names = {
            'title': '商品标题',
            'productId': '商品ID',
            'priceText': '价格',
            'detailUrl': '商品链接',
            'gender': '性别',
            'category': '衣服分类',
            'brandName': '品牌名',
            'colors': '颜色',
            'sizes': '尺码',
            'imageUrls': '图片URL',
            'imageCount': '图片数量',
            'sizeChart': '尺码表',
            'detailsText': '详情页文字'
        }

        for field, name in field_names.items():
            value = fields.get(field, '')
            if isinstance(value, list):
                print(f"{name}: {len(value)}行 (总长度:{sum(len(str(v)) for v in value)}字符)")
                if field == 'sizes':
                    print(f"  内容: {', '.join(str(v) for v in value[:5])}")
            elif isinstance(value, dict):
                print(f"{name}: {value}")
            else:
                text = str(value) if value else '(空)'
                print(f"{name}: {text[:100]}{'...' if len(text) > 100 else ''}")

if __name__ == "__main__":
    test_fields()