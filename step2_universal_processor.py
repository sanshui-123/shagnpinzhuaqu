#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二步：通用字段改写处理器
=====================================

这是所有品牌的统一第二步处理器：
- 100%复制卡拉威改写逻辑
- 适用于任何品牌的第一步数据
- 永远不变的通用核心

使用方法：
  python3 step2_universal_processor.py --input input.json --output output.json

Author: Claude Code
Date: 2025-11-13
Version: 1.0 - 永久固定版
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any

# 导入我们的通用处理器（卡拉威完整逻辑）
from callaway_13field_processor import Callaway13FieldProcessor

def load_scraped_data(input_path: str) -> List[Dict]:
    """
    加载第一步抓取的原始数据

    Args:
        input_path: 输入文件路径

    Returns:
        原始产品数据列表
    """
    print(f"📥 加载第一步数据: {input_path}")

    if not Path(input_path).exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 处理不同的数据格式
    if isinstance(data, dict):
        if 'records' in data:  # Le Coq 格式
            products = data['records']
        elif 'products' in data:
            products = data['products']
        elif 'data' in data:
            products = data['data']
        else:
            # 单个产品
            products = [data]
    elif isinstance(data, list):
        products = data
    else:
        raise ValueError("不支持的数据格式")

    print(f"✅ 加载完成: {len(products)} 个产品")
    return products

def save_processed_data(processed_data: List[Dict], output_path: str):
    """
    保存第二步处理后的数据

    Args:
        processed_data: 处理后的产品数据
        output_path: 输出文件路径
    """
    print(f"💾 保存第二步结果: {output_path}")

    # 确保输出目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 构建输出数据结构
    output_data = {
        'processor': 'Callaway13FieldProcessor',
        'version': '1.0',
        'timestamp': Path(output_path).stem,
        'total_products': len(processed_data),
        'products': processed_data,

        # 添加处理统计
        'processing_stats': {
            'successful_titles': sum(1 for p in processed_data if p.get('生成标题')),
            'successful_translations': sum(1 for p in processed_data if p.get('描述翻译')),
            'brand_distribution': {},
            'gender_distribution': {},
            'clothing_type_distribution': {}
        }
    }

    # 统计分布
    for product in processed_data:
        brand = product.get('品牌', '未知')
        gender = product.get('性别', '未知')
        clothing_type = product.get('服装类型', '未知')

        output_data['processing_stats']['brand_distribution'][brand] = \
            output_data['processing_stats']['brand_distribution'].get(brand, 0) + 1
        output_data['processing_stats']['gender_distribution'][gender] = \
            output_data['processing_stats']['gender_distribution'].get(gender, 0) + 1
        output_data['processing_stats']['clothing_type_distribution'][clothing_type] = \
            output_data['processing_stats']['clothing_type_distribution'].get(clothing_type, 0) + 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 保存完成: {len(processed_data)} 个产品")

def process_brand_data(input_path: str, output_path: str = None) -> bool:
    """
    执行第二步：通用字段改写

    Args:
        input_path: 第一步抓取数据路径
        output_path: 输出路径（可选）

    Returns:
        是否成功
    """
    try:
        print("🚀 开始第二步：通用字段改写处理")
        print("=" * 60)

        # 1. 加载第一步数据
        scraped_data = load_scraped_data(input_path)

        # 2. 初始化通用处理器（卡拉威逻辑）
        processor = Callaway13FieldProcessor()
        print("✅ 通用处理器初始化完成 (卡拉威完整逻辑)")

        # 3. 批量处理
        print(f"🔄 开始处理 {len(scraped_data)} 个产品...")
        processed_data = processor.process_products_batch(scraped_data)

        # 4. 生成输出路径
        if not output_path:
            input_file = Path(input_path)
            timestamp = input_file.stem.replace('_processed', '')
            output_path = f"step2_processed_{timestamp}.json"

        # 5. 保存结果
        save_processed_data(processed_data, output_path)

        # 6. 生成处理报告
        summary = processor.get_processing_summary(processed_data)

        print("\n" + "=" * 60)
        print("📊 第二步处理完成报告")
        print("=" * 60)
        print(f"总产品数: {summary['总产品数']}")
        print(f"成功标题生成: {summary['成功标题生成']}")
        print(f"成功描述翻译: {summary['成功描述翻译']}")
        print(f"输出文件: {output_path}")

        if summary['品牌分布']:
            print("\n品牌分布:")
            for brand, count in summary['品牌分布'].items():
                print(f"  {brand}: {count}")

        if summary['性别分布']:
            print("\n性别分布:")
            for gender, count in summary['性别分布'].items():
                print(f"  {gender}: {count}")

        if summary['服装类型分布']:
            print("\n服装类型分布:")
            for clothing_type, count in summary['服装类型分布'].items():
                print(f"  {clothing_type}: {count}")

        print("\n🎉 第二步处理完成！可进行第三步飞书同步")
        return True

    except Exception as e:
        print(f"❌ 第二步处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='第二步：通用字段改写处理器 (所有品牌统一)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理Le Coq Sportif数据
  python3 step2_universal_processor.py --input golf_content/lecoqgolf/lecoqgolf_products.json

  # 处理其他品牌数据
  python3 step2_universal_processor.py --input brand_data.json --output processed_brand.json

  # 处理并指定输出目录
  python3 step2_universal_processor.py --input raw_data.json --output results/processed_data.json

注意：这是第二步处理器，需要第一步的数据作为输入。
    """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='第一步抓取的原始数据文件路径 (必需)'
    )

    parser.add_argument(
        '--output', '-o',
        help='第二步处理后的输出文件路径 (可选)'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='第二步通用处理器 v1.0 (永久固定版)'
    )

    args = parser.parse_args()

    # 验证输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        sys.exit(1)

    # 执行第二步处理
    success = process_brand_data(str(input_path), args.output)

    if success:
        print("\n🎯 第二步统一指令执行成功！")
        sys.exit(0)
    else:
        print("\n❌ 第二步处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()