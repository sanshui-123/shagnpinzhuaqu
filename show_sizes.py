#!/usr/bin/env python3
"""
显示产品尺码信息
"""

import glob
import json

# 获取最新的产品详情文件
detail_path = sorted(glob.glob('results/product_details_*.json'))[-1]
print(f"读取文件: {detail_path}")

# 加载数据
with open(detail_path, encoding='utf-8') as f:
    detail = json.load(f)

# 获取产品信息
product_id = detail.get("product", {}).get("productId", "未知")
product_title = detail.get("product", {}).get("title", "未知")

print("\n" + "="*60)
print(f"产品ID: {product_id}")
print(f"产品名称: {product_title}")
print("="*60)

# 获取尺码信息
sizes = []
if "product" in detail and "variants" in detail["product"]:
    # 收集所有尺码
    size_set = set()
    for variant in detail["product"]["variants"]:
        size = variant.get("size", {}).get("name")
        if size:
            size_set.add(size)

    sizes = sorted(list(size_set))

# 输出尺码
if sizes:
    print(f"\n尺码信息 (共{len(sizes)}个):")
    print("-" * 30)
    for i, size in enumerate(sizes, 1):
        print(f"{i}. {size}")
else:
    print("\n未找到尺码信息")

# 输出颜色信息
colors = []
if "product" in detail and "colors" in detail["product"]:
    colors = detail["product"]["colors"]

if colors:
    print(f"\n颜色信息 (共{len(colors)}种):")
    print("-" * 30)
    for i, color in enumerate(colors, 1):
        code = color.get("code", "")
        name = color.get("name", "")
        print(f"{i}. {name} ({code})")

print("\n" + "="*60)