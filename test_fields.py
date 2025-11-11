#!/usr/bin/env python3
"""
简单测试脚本来查看所有13个字段的输出
"""

import json
import os
import sys
from pprint import pprint

# 添加模块路径
sys.path.insert(0, '/Users/sanshui/Desktop/CallawayJP')

# 设置环境变量
os.environ['ZHIPU_API_KEY'] = 'f23663c41f894584a8a7584b25ae2006.SpD7H24yvHYWRqK8'

from feishu_update.services.field_assembler import FieldAssembler
from feishu_update.services.detail_fetcher import DetailFetcher

def test_fields():
    # 读取测试数据
    with open('/Users/sanshui/Desktop/CallawayJP/single_test.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # 获取第一个产品
    product = test_data['products'][0]
    print("=== 原始产品数据 ===")
    print(f"产品ID: {product.get('productId')}")
    print(f"产品名称: {product.get('productName')}")
    print(f"价格: {product.get('priceText')}")
    print()
    
    # 详情抓取
    print("=== 开始抓取详情 ===")
    detail_fetcher = DetailFetcher()
    
    if detail_fetcher.needs_detail_fetch(product):
        print("需要抓取详情数据...")
        detail_url = product.get('detailUrl') or product.get('detail_url')
        product_id = product.get('productId') or product.get('product_id')
        
        if detail_url:
            detail_data = detail_fetcher.fetch_product_detail(detail_url, product_id)
            if detail_data:
                enhanced_product = detail_fetcher.merge_detail_into_product(product, detail_data)
                print("详情抓取成功！")
            else:
                enhanced_product = product
                print("详情抓取失败，使用原数据")
        else:
            enhanced_product = product
            print("缺少详情URL")
    else:
        enhanced_product = product
        print("无需抓取详情")
    
    print()
    
    # 组装字段
    print("=== 开始组装字段 ===")
    field_assembler = FieldAssembler()
    
    # 获取详情数据用于字段组装
    detail_data = enhanced_product.get('_detail_data')
    
    print("=== 详情数据调试 ===")
    if detail_data:
        print(f"抓取的颜色数据: {detail_data.get('colors', 'None')}")
        print(f"抓取的尺码数据: {detail_data.get('sizes', 'None')}")
        if detail_data.get('images'):
            print(f"抓取的图片数量: {len(detail_data['images'].get('product', []))}")
    else:
        print("没有详情数据")
    print()
    
    # 生成所有字段（使用预生成标题绕过GLM客户端问题）
    pre_generated_title = "25秋冬卡拉威Callaway高尔夫男士保暖舒适棉服"
    fields = field_assembler.build_update_fields(
        enhanced_product, 
        pre_generated_title=pre_generated_title,
        product_detail=detail_data
    )
    
    print("\n=== 最终的13个字段 ===")
    for i, (field_name, field_value) in enumerate(fields.items(), 1):
        print(f"{i:2d}. {field_name}: {repr(field_value)}")
        if isinstance(field_value, str) and '\n' in field_value:
            lines = field_value.split('\n')
            print(f"     ({len(lines)} 行内容)")
            for j, line in enumerate(lines[:3], 1):  # 只显示前3行
                print(f"     {j}: {line}")
            if len(lines) > 3:
                print(f"     ... 还有 {len(lines)-3} 行")
        print()

if __name__ == '__main__':
    test_fields()
