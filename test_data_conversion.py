#!/usr/bin/env python3
"""
测试数据转换是否正确
"""

import sys
import os
sys.path.append('/Users/sanshui/Desktop/CallawayJP')

import json
from tongyong_feishu_update.services.field_assembler import FieldAssembler
from tongyong_feishu_update.models.product import Product

def test_data_conversion():
    """测试数据转换"""
    print("🔍 测试数据转换...")

    # 读取Step 1的输出
    with open('/Users/sanshui/Desktop/CallawayJP/test_fixed_final.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 Step 1数据结构:")
    products = data.get('products', {})
    print(f"  - 产品数量: {len(products)}")

    if products:
        first_product_id = list(products.keys())[0]
        first_product = products[first_product_id]

        print(f"  - 产品ID: {first_product_id}")
        print(f"  - 字段列表: {list(first_product.keys())}")

        # 检查关键字段
        print(f"\n🔍 关键字段检查:")
        print(f"  - gender: {first_product.get('gender', 'MISSING')}")
        print(f"  - imageUrls: {first_product.get('imageUrls', 'MISSING')}")
        print(f"  - description: {first_product.get('description', 'MISSING')}")
        print(f"  - colors: {first_product.get('colors', 'MISSING')}")
        print(f"  - sizes: {first_product.get('sizes', 'MISSING')}")

        # 测试Product模型创建
        print(f"\n🔧 测试Product模型...")
        try:
            product = Product.from_dict(first_product)
            print(f"✅ Product模型创建成功")

            # 转换为字典并检查
            product_dict = product.to_dict()
            print(f"  - to_dict gender: {product_dict.get('gender', 'MISSING')}")
            print(f"  - to_dict description: {product_dict.get('description', 'MISSING')}")

        except Exception as e:
            print(f"❌ Product模型创建失败: {e}")
            return False

        # 测试FieldAssembler
        print(f"\n🔧 测试FieldAssembler...")
        try:
            assembler = FieldAssembler()
            assembled_data = assembler.build_update_fields(product)

            print(f"✅ FieldAssembler成功")
            print(f"  - 性别字段: {assembled_data.get('性别', 'MISSING')}")
            print(f"  - 描述字段长度: {len(assembled_data.get('详情页文字', ''))}")
            print(f"  - 图片数量: {len(assembled_data.get('所有图片链接', '').split()) if assembled_data.get('所有图片链接') else 0}")

            # 验证性别是否正确
            gender = assembled_data.get('性别', '')
            if gender == '女':
                print(f"✅ 性别字段正确: {gender}")
                return True
            else:
                print(f"❌ 性别字段错误: {gender} (期望: 女)")
                return False

        except Exception as e:
            print(f"❌ FieldAssembler失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    return False

if __name__ == "__main__":
    print("🧪 开始数据转换测试")
    success = test_data_conversion()

    if success:
        print("\n🎉 数据转换测试成功！")
        print("✅ 字段映射修复生效")
        print("✅ 性别字段显示正确")
    else:
        print("\n❌ 数据转换测试失败")