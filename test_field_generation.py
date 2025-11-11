#!/usr/bin/env python3
"""测试字段生成的完整脚本"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_field_generation():
    """测试字段生成"""
    # 读取测试数据
    with open('single_test.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    from feishu_update.loaders.factory import LoaderFactory
    from feishu_update.services.field_assembler import FieldAssembler
    from feishu_update.services.title_generator import TitleGenerator
    from feishu_update.services.translator import Translator
    from feishu_update.services.size_table_formatter import SizeTableFormatter

    # 解析产品
    loader = LoaderFactory.create(data)
    products = loader.parse(data)
    product = products[0]

    print("=" * 60)
    print("产品数据结构检查")
    print("=" * 60)
    print(f"产品ID: {product.product_id}")
    print(f"产品名称: {product.product_name}")
    print(f"品牌: {product.brand}")
    print(f"颜色: {product.colors}")
    print(f"尺码: {product.sizes}")
    print(f"extra keys: {list(product.extra.keys()) if product.extra else 'None'}")

    # 检查_detail_data
    detail_data = None
    if product.extra:
        detail_data = product.extra.get('_detail_data')

    if detail_data:
        print("\n✅ _detail_data 存在")
        colors = detail_data.get('colors', [])
        sizes = detail_data.get('sizes', [])
        images = detail_data.get('images', {})
        size_chart = detail_data.get('product', {}).get('sizeSectionText', '')

        print(f"   - 颜色数量: {len(colors)}")
        print(f"   - 尺码数量: {len(sizes)}")
        print(f"   - 图片数量: {len(images.get('product', []))}")
        print(f"   - 尺码表文字: {'有' if size_chart else '无'}")
    else:
        print("\n❌ _detail_data 不存在")

    # 创建FieldAssembler并生成字段
    print("\n" + "=" * 60)
    print("字段生成测试")
    print("=" * 60)

    assembler = FieldAssembler()

    # 转换Product对象为字典格式
    product_dict = {
        'productId': product.product_id,
        'productName': product.product_name,
        'brand': product.brand,
        'detailUrl': product.detail_url,
        'colors': product.colors,
        'sizes': product.sizes,
        # 透传extra中的所有数据
        **(product.extra or {})
    }

    # 生成字段
    fields = assembler.build_update_fields(
        product=product_dict,
        pre_generated_title=None,
        title_only=False,
        product_detail=detail_data
    )

    # 显示生成的字段
    print("\n生成的字段:")
    for key, value in fields.items():
        # 截断长值以便显示
        display_value = value
        if isinstance(value, str) and len(value) > 80:
            lines = value.split('\n')
            if len(lines) > 1:
                display_value = f"{lines[0]} ... (共{len(lines)}行)"
            else:
                display_value = value[:80] + "..."
        print(f"  {key}: {display_value}")

    # 检查关键字段
    print("\n" + "=" * 60)
    print("关键字段检查")
    print("=" * 60)

    checks = [
        ('商品标题', fields.get('商品标题', '')),
        ('颜色', fields.get('颜色', '')),
        ('尺码', fields.get('尺码', '')),
        ('尺码表', fields.get('尺码表', '')),
        ('图片URL', fields.get('图片URL', '')),
        ('图片数量', fields.get('图片数量', '')),
        ('详情页文字', fields.get('详情页文字', '')),
        ('库存状态', fields.get('库存状态', None)),
        ('性别', fields.get('性别', '')),
        ('衣服分类', fields.get('衣服分类', '')),
    ]

    for field_name, value in checks:
        if field_name == '库存状态':
            if value is None:
                print(f"✅ {field_name}: 已移除")
            else:
                print(f"❌ {field_name}: 仍然存在 ('{value}')")
        elif value:
            if field_name in ['颜色', '尺码', '图片URL', '尺码表', '详情页文字']:
                # 多行字段显示行数
                lines = str(value).split('\n')
                print(f"✅ {field_name}: 有内容 ({len(lines)}行)")
            else:
                print(f"✅ {field_name}: {value}")
        else:
            print(f"❌ {field_name}: 空值")

    # 分类检查
    print("\n" + "=" * 60)
    print("分类检查")
    print("=" * 60)

    from feishu_update.services.classifiers import determine_clothing_type, determine_gender

    gender = determine_gender(product_dict)
    clothing_type = determine_clothing_type(product_dict)

    print(f"性别: {gender}")
    print(f"衣服分类: {clothing_type}")

    if '配件' in clothing_type or '腰带' in clothing_type:
        print("✅ 分类正确识别为配件")
    else:
        print("❌ 分类未正确识别")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_field_generation()