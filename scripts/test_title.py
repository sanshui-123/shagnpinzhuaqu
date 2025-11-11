#!/usr/bin/env python3
"""
测试标题生成脚本
只测试标题生成功能，不运行其他流程
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量（如果需要）
if 'ZHIPU_API_KEY' not in os.environ:
    # 尝试从callaway.env读取
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'callaway.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ZHIPU_API_KEY'):
                    key = line.split('=', 1)[1].strip()
                    os.environ['ZHIPU_API_KEY'] = key
                    break

# 设置环境变量
import os
os.environ['ZHIPU_API_KEY'] = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
os.environ['ZHIPU_TITLE_MODEL'] = 'glm-4.6'
os.environ['GLM_MIN_INTERVAL'] = '0.8'
os.environ['GLM_MAX_TOKENS'] = '400'

from feishu_update.services.title_v6 import generate_cn_title

def load_test_product(json_file: str):
    """从JSON文件加载测试产品"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 获取实际的产品信息
    # 文件结构是 {"products": [...]}
    products = data.get('products', [])

    if not products:
        raise ValueError("single_test.json 中没有 products 数据")

    # 取第一个产品
    product_info = products[0]

    # 使用实际产品的名称（提示词会自动处理中棉→棉服的翻译）
    product_name = product_info.get('productName', '')
    print(f"原始产品名: {product_name}")

    product = {
        'productName': product_name,
        'productId': product_info.get('productId', ''),
        'detailUrl': product_info.get('detailUrl', ''),
        'category': product_info.get('category', '其他'),  # 使用实际分类
        'brand': product_info.get('brand', 'Callaway Golf'),
        'description': product_info.get('description', ''),
        '_detail_data': product_info  # 包含原始数据
    }

    return product

def main():
    # 加载测试数据
    json_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'single_test.json')

    if not os.path.exists(json_file):
        print(f"错误：找不到测试文件 {json_file}")
        print("请确保single_test.json文件存在")
        return

    print("=== 标题生成测试 ===\n")

    # 加载产品数据
    product = load_test_product(json_file)

    print("测试产品信息：")
    print(f"  商品名称: {product['productName']}")
    print(f"  商品ID: {product['productId']}")
    print(f"  商品链接: {product['detailUrl']}")
    print(f"  品牌: {product['brand']}")
    print(f"  分类: {product['category']}")
    print()

    # 导入函数进行调试
    from feishu_update.services.title_v6 import (
        generate_cn_title,
        determine_category,
        is_small_accessory,
        extract_season_from_name,
        extract_brand_from_product
    )

    # 调试信息
    print("=== 调试信息 ===")
    category = determine_category(product)
    is_accessory = is_small_accessory(category, product['productName'])
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    season = extract_season_from_name(product['productName'])

    print(f"  推断分类: {category}")
    print(f"  是否为配件: {is_accessory}")
    print(f"  品牌: {brand_chinese}")
    print(f"  季节: {season}")
    print()

    # 生成标题
    print("正在生成标题...")
    try:
        # 启用详细日志
        import logging
        logging.basicConfig(level=logging.DEBUG)
        title = generate_cn_title(product)

        print("\n=== 生成结果 ===")
        print(f"标题: {title}")
        print(f"长度: {len(title)} 字符")

        # 检查是否以"腰带"结尾
        if title.endswith('腰带'):
            print("✅ 结尾正确：以'腰带'结尾")
        else:
            print("❌ 结尾错误：不以'腰带'结尾")
            # 如果没有腰带结尾，检查是否是其他配件
            accessory_endings = ['帽子', '皮带', '手套', '袜子', '护腕', '腕带', '头带', '发带', '围脖', '脖套']
            for ending in accessory_endings:
                if title.endswith(ending):
                    print(f"  ℹ️ 实际结尾：'{ending}'")
                    break

        # 检查长度
        if 25 <= len(title) <= 30:
            print("✅ 长度正确：25-30字符")
        else:
            print(f"❌ 长度错误：{len(title)}字符，需要在25-30之间")

        # 检查品牌
        if '卡拉威' in title or 'Callaway' in title:
            print("✅ 品牌正确：包含卡拉威/Callaway")
        else:
            print("❌ 品牌错误：不包含卡拉威/Callaway")

        # 检查高尔夫
        if '高尔夫' in title and title.count('高尔夫') == 1:
            print("✅ 高尔夫正确：包含一次'高尔夫'")
        else:
            print("❌ 高尔夫错误：不包含或包含多次'高尔夫'")

    except Exception as e:
        print(f"\n❌ 生成失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()