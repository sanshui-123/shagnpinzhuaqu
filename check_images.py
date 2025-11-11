#!/usr/bin/env python3
"""
详细检查产品图片信息
"""

import json

# 读取文件
with open('results/product_details_C25292102_2025-11-11T06-32-06-433Z.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('='*60)
print(f"产品ID: {data['product']['productId']}")
print(f"产品名称: {data['product']['title']}")
print('='*60)

# 1. 检查主图
if 'mainImage' in data['product']:
    print(f"\n主图 (1张):")
    print(f"  {data['product']['mainImage']}")

# 2. 检查顶级images字段
if 'images' in data:
    images = data['images']
    print(f"\n顶级images字段:")
    if isinstance(images, list):
        print(f"  数量: {len(images)}张")
        for i, img in enumerate(images[:10], 1):
            if isinstance(img, str):
                print(f"  {i}. {img[:100]}...")
            elif isinstance(img, dict):
                url = img.get('url', img.get('src', ''))
                print(f"  {i}. {url[:100]}...")
    else:
        print(f"  类型: {type(images)}")
        print(f"  内容: {str(images)[:200]}...")

# 3. 检查顶级colors字段
if 'colors' in data:
    colors = data['colors']
    print(f"\n颜色信息:")
    print(f"  颜色数量: {len(colors)}")

    total_images = 0
    for i, color in enumerate(colors, 1):
        color_name = color.get('name', '未知')
        color_code = color.get('code', '')
        print(f"\n  {i}. {color_name} ({color_code})")

        # 检查该颜色的图片
        if 'images' in color:
            color_images = color['images']
            print(f"     图片数量: {len(color_images)}")
            total_images += len(color_images)

            # 显示前3张
            for j, img in enumerate(color_images[:3], 1):
                if isinstance(img, str):
                    print(f"     {j}. {img[:120]}...")
                elif isinstance(img, dict):
                    url = img.get('url', img.get('src', ''))
                    print(f"     {j}. {url[:120]}...")

    print(f"\n颜色图片总计: {total_images}张")

# 4. 检查variants中的图片
if 'variants' in data:
    variants = data['variants']
    print(f"\n变体信息:")
    print(f"  变体数量: {len(variants)}")

    variant_images = 0
    for i, variant in enumerate(variants[:5], 1):
        print(f"\n  变体{i}:")
        print(f"    ID: {variant.get('id', 'N/A')}")
        print(f"    颜色: {variant.get('color', {}).get('name', 'N/A')}")
        print(f"    尺码: {variant.get('size', {}).get('name', 'N/A')}")

        if 'images' in variant:
            img_count = len(variant['images'])
            variant_images += img_count
            print(f"    图片: {img_count}张")

            # 显示第一张
            if variant['images']:
                first_img = variant['images'][0]
                if isinstance(first_img, dict):
                    url = first_img.get('url', '')
                    if url:
                        print(f"    首图: {url[:120]}...")

    print(f"\n变体图片总计: {variant_images}张")

# 5. 汇总
print("\n" + "="*60)
print("图片汇总:")
# 从scrape日志中我们知道总共抓取了20张图片（4颜色 x 5张）
print(f"  根据抓取日志: 20张图片 (4种颜色 × 5张)")
print(f"  数据来源: dom_enhanced")