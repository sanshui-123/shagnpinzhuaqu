#!/usr/bin/env python3
"""
测试第二部分处理器处理第一部分数据
"""

import json
import sys
import os
from callaway_13field_processor import Callaway13FieldProcessor

def test_step2_processing():
    """测试第二部分处理"""

    # 读取第一部分生成的数据
    input_file = "/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/test_product_4_pants_complete_data.json"

    print("🔄 读取第一部分数据...")
    with open(input_file, 'r', encoding='utf-8') as f:
        step1_data = json.load(f)

    print(f"📋 第一部分数据概览:")
    print(f"   - 商品标题: {step1_data.get('商品标题', 'N/A')}")
    print(f"   - 品牌名: {step1_data.get('品牌名', 'N/A')}")
    print(f"   - 价格: {step1_data.get('价格', 'N/A')}")
    print(f"   - 性别: {step1_data.get('性别', 'N/A')}")
    print(f"   - 颜色数量: {len(step1_data.get('颜色', []))}")
    print(f"   - 图片数量: {len(step1_data.get('图片链接', []))}")
    print(f"   - 尺码数量: {len(step1_data.get('尺码', []))}")
    print(f"   - 详情文字长度: {len(step1_data.get('详情页文字', ''))}")

    # 初始化第二部分处理器
    print("\n🔄 初始化第二部分13字段处理器...")
    processor = Callaway13FieldProcessor()

    # 将第一部分数据转换为第二部分需要的格式
    converted_data = {
        "url": step1_data.get("商品链接", ""),
        "product_id": step1_data.get("商品ID", ""),
        "title": step1_data.get("商品标题", ""),
        "brand": step1_data.get("品牌名", ""),
        "price": step1_data.get("价格", ""),
        "gender": step1_data.get("性别", ""),
        "colors": step1_data.get("颜色", []),
        "images": step1_data.get("图片链接", []),
        "sizes": step1_data.get("尺码", []),
        "description": step1_data.get("详情页文字", ""),
        "size_chart": step1_data.get("尺码表", {})
    }

    print("\n🔄 执行第二部分处理...")
    try:
        # 处理产品数据
        processed_data = processor.process_product(converted_data)

        print("✅ 第二部分处理成功!")

        # 保存处理结果
        output_file = "/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/step2_processed_product_4.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)

        print(f"📁 处理结果已保存到: {output_file}")

        # 显示处理结果概览
        print(f"\n📊 第二部分处理结果概览:")
        print(f"   - 处理状态: {'✅ 成功' if processed_data.get('success') else '❌ 失败'}")
        print(f"   - 记录ID: {processed_data.get('record_id', 'N/A')}")
        print(f"   - AI生成标题: {processed_data.get('ai_title', 'N/A')[:50]}...")
        print(f"   - 商品类别: {processed_data.get('product_category', 'N/A')}")
        print(f"   - 上身建议: {processed_data.get('outfit_suggestion', 'N/A')[:50]}...")
        print(f"   - 适用场景: {processed_data.get('suitable_scene', 'N/A')}")
        print(f"   - 库存单位: {processed_data.get('inventory_unit', 'N/A')}")
        print(f"   - 处理时间: {processed_data.get('processing_time', 'N/A')}")
        print(f"   - 错误信息: {processed_data.get('error_message', 'N/A')}")

        # 显示颜色转换结果
        colors = processed_data.get('颜色', [])
        if colors:
            print(f"\n🎨 颜色转换结果:")
            for color in colors:
                original = color.get('original', 'N/A')
                chinese = color.get('chinese', 'N/A')
                print(f"   - {original} → {chinese}")

        # 显示图片处理结果
        images = processed_data.get('images', [])
        print(f"\n📷 图片处理结果:")
        print(f"   - 总图片数: {len(images)}")
        if images:
            print(f"   - 前3张图片: {[img.get('url', 'N/A')[:50] + '...' for img in images[:3]]}")

        # 显示尺码处理结果
        sizes = processed_data.get('尺码', [])
        print(f"\n📏 尺码处理结果:")
        print(f"   - 尺码列表: {sizes}")

        print(f"\n🔗 飞书表格链接: {processed_data.get('feishu_url', 'N/A')}")

    except Exception as e:
        print(f"❌ 第二部分处理失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_step2_processing()