#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将你的JSON格式转换为feishu_update能识别的格式
"""

import json
import sys
import os
import glob
from pathlib import Path
from datetime import datetime

def convert_single_json(input_file):
    """转换单个JSON文件为feishu_update格式"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 转换为feishu_update能识别的格式
        feishu_data = {
            "products": {
                data.get('商品ID', ''): {
                    "productId": data.get('商品ID', ''),
                    "productName": data.get('商品标题', ''),
                    "detailUrl": data.get('商品链接', ''),
                    "price": data.get('价格', ''),
                    "brand": data.get('品牌名', ''),
                    "category": "服装",  # 默认分类
                    "gender": data.get('性别', ''),
                    "description": data.get('详情页文字', ''),

                    # 颜色处理
                    "colors": data.get('颜色', []) if isinstance(data.get('颜色', []), list) else [],

                    # 尺码处理
                    "sizes": data.get('尺码', []) if isinstance(data.get('尺码', []), list) else [],

                    # 图片处理
                    "imageUrls": data.get('图片链接', []).split(', ') if isinstance(data.get('图片链接'), str) else data.get('图片链接', []) if data.get('图片链接') else [],

                    # 尺码表
                    "sizeChart": data.get('尺码表', {}),

                    # 其他信息
                    "scrapeInfo": {
                        "source": "single_url_fixed",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
        }

        # 保存转换后的文件
        output_file = input_file.replace('.json', '_feishu_format.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(feishu_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 转换完成: {input_file} → {output_file}")
        print(f"   商品ID: {data.get('商品ID', 'N/A')}")
        print(f"   商品名称: {data.get('商品标题', 'N/A')}")
        print(f"   价格: {data.get('价格', 'N/A')}")

        return output_file

    except Exception as e:
        print(f"❌ 转换失败 {input_file}: {e}")
        return None

def convert_batch_json(input_dir):
    """批量转换JSON文件"""
    pattern = os.path.join(input_dir, "single_url_fixed_*.json")
    json_files = glob.glob(pattern)

    if not json_files:
        print(f"❌ 在 {input_dir} 中未找到single_url_fixed_*.json文件")
        return

    print(f"✅ 找到 {len(json_files)} 个文件，开始批量转换...")

    converted_files = []
    failed_files = []

    for json_file in json_files:
        try:
            result = convert_single_json(json_file)
            if result:
                converted_files.append(result)
            else:
                failed_files.append(json_file)
        except Exception as e:
            print(f"❌ 转换失败: {json_file} - {e}")
            failed_files.append(json_file)

    # 创建批量合并文件
    if converted_files:
        print(f"\n🔄 创建批量合并文件...")

        all_products = {}
        for converted_file in converted_files:
            try:
                with open(converted_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 合并所有products
                all_products.update(data.get('products', {}))

            except Exception as e:
                print(f"❌ 读取转换文件失败: {converted_file} - {e}")

        # 保存批量文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_file = f"batch_feishu_format_{timestamp}.json"

        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump({"products": all_products}, f, ensure_ascii=False, indent=2)

        print(f"✅ 批量文件已创建: {batch_file}")
        print(f"   包含产品数: {len(all_products)}")

    print(f"\n📊 转换汇总:")
    print(f"   总文件数: {len(json_files)}")
    print(f"   转换成功: {len(converted_files)}")
    print(f"   转换失败: {len(failed_files)}")
    print(f"   成功率: {len(converted_files)/len(json_files)*100:.1f}%")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='将JSON文件转换为feishu_update格式')
    parser.add_argument('--input', '-i', type=str, help='单个JSON文件路径')
    parser.add_argument('--batch', '-b', action='store_true', help='批量转换目录中的所有文件')
    parser.add_argument('--dir', '-d', type=str, default='./scripts/multi_brand/brands/lecoqgolf/', help='批量转换的目录路径')

    args = parser.parse_args()

    if args.input:
        # 转换单个文件
        print(f"🔄 转换单个文件: {args.input}")
        result = convert_single_json(args.input)
        if result:
            print(f"\n✅ 转换完成！现在可以使用feishu_update:")
            print(f"python3 -m feishu_update.run_pipeline {result}")
        else:
            print("❌ 转换失败")
            sys.exit(1)

    elif args.batch:
        # 批量转换
        print(f"🔄 批量转换目录: {args.dir}")
        convert_batch_json(args.dir)

    else:
        print("使用方法:")
        print("  # 转换单个文件")
        print("  python3 convert_to_feishu_format.py --input single_url_fixed_xxx.json")
        print("")
        print("  # 批量转换")
        print("  python3 convert_to_feishu_format.py --batch --dir ./scripts/multi_brand/brands/lecoqgolf/")
        print("")
        print("  # 转换后使用feishu_update")
        print("  python3 -m feishu_update.run_pipeline batch_feishu_format_xxx.json")

if __name__ == "__main__":
    main()