#!/usr/bin/env python3
"""
测试详情数据集成到FieldAssembler
"""

import json
import sys
from pathlib import Path

# 添加项目路径到sys.path
sys.path.insert(0, str(Path(__file__).parent))

from feishu_update.services.field_assembler import FieldAssembler


def main():
    # 1. 加载原始测试数据
    print("加载原始测试数据...")
    with open('single_test.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    original_product = test_data['products'][0]
    
    # 2. 加载抓取的详情数据
    print("加载抓取的详情数据...")
    detail_files = list(Path('CallawayJP/results').glob('product_details_C25215107_*.json'))
    if not detail_files:
        print("❌ 没有找到详情数据文件")
        return
    
    latest_detail_file = sorted(detail_files)[-1]
    print(f"使用详情文件: {latest_detail_file}")
    
    with open(latest_detail_file, 'r', encoding='utf-8') as f:
        detail_data = json.load(f)
    
    # 3. 创建FieldAssembler实例
    assembler = FieldAssembler()
    
    # 预生成的标题，避免调用GLM
    pre_generated_title = "25秋冬卡拉威Callaway高尔夫男士保暖舒适棉服"
    
    # 4. 测试不使用详情数据的情况
    print("\n=== 测试不使用详情数据 ===")
    fields_without_detail = assembler.build_update_fields(
        product=original_product,
        pre_generated_title=pre_generated_title,
        title_only=False
    )
    
    # 5. 测试使用详情数据的情况
    print("\n=== 测试使用详情数据 ===")
    fields_with_detail = assembler.build_update_fields(
        product=original_product,
        pre_generated_title=pre_generated_title,
        title_only=False,
        product_detail=detail_data
    )
    
    # 6. 对比结果
    print("\n=== 对比结果 ===")
    print(f"不使用详情数据时的字段数: {len(fields_without_detail)}")
    print(f"使用详情数据时的字段数: {len(fields_with_detail)}")
    
    # 重点关注之前为空的字段
    empty_fields_before = ['颜色', '尺码', '图片URL']
    for field in empty_fields_before:
        before = fields_without_detail.get(field, '')
        after = fields_with_detail.get(field, '')
        print(f"\n{field}:")
        print(f"  之前: {before[:100]}{'...' if len(str(before)) > 100 else ''}")
        print(f"  之后: {after[:100]}{'...' if len(str(after)) > 100 else ''}")


if __name__ == '__main__':
    main()