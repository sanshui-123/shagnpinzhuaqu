#!/usr/bin/env python3
"""
显示产品图片URL和数量
"""

import glob
import json

# 读取最新的C25292102文件
file_pattern = 'results/product_details_C25292102_*.json'
files = sorted(glob.glob(file_pattern))
if not files:
    print(f"未找到C25292102文件")
    exit(1)

detail_path = files[-1]
print(f"读取文件: {detail_path}")
print()

# 加载数据
with open(detail_path, encoding='utf-8') as f:
    detail = json.load(f)

# 获取产品信息
product_id = detail.get("product", {}).get("productId", "未知")
product_title = detail.get("product", {}).get("title", "未知")

print("="*60)
print(f"产品ID: {product_id}")
print(f"产品名称: {product_title}")
print("="*60)

# 统计图片信息
total_images = 0
image_urls = []

# 从colors中获取图片
if "product" in detail and "colors" in detail["product"]:
    print("\n按颜色分类的图片:")
    print("-"*60)

    for i, color in enumerate(detail["product"]["colors"], 1):
        color_name = color.get("name", "")
        color_code = color.get("code", "")
        images = color.get("images", [])

        print(f"\n{i}. {color_name} ({color_code}) - {len(images)}张图片")

        for j, img in enumerate(images[:3], 1):  # 只显示前3张
            img_url = img.get("url", "")
            if img_url:
                print(f"   {j}. {img_url}")
                image_urls.append(img_url)

        if len(images) > 3:
            print(f"   ... 还有{len(images)-3}张图片")

        total_images += len(images)

# 从mainImage获取主图
if "product" in detail and "mainImage" in detail["product"]:
    main_img = detail["product"]["mainImage"]
    if main_img and main_img not in image_urls:
        image_urls.insert(0, main_img)
        total_images += 1
        print("\n主图:")
        print(f"   {main_img}")

# 汇总信息
print("\n" + "="*60)
print("图片汇总:")
print(f"- 总图片数量: {total_images} 张")
print(f"- 颜色数量: {len(detail.get('product', {}).get('colors', []))} 种")
print(f"- 每种颜色: {total_images // len(detail.get('product', {}).get('colors', [1]))} 张")

# 输出所有图片URL（前10张）
print("\n前10张图片URL:")
print("-"*60)
for i, url in enumerate(image_urls[:10], 1):
    print(f"{i:2d}. {url}")

if len(image_urls) > 10:
    print(f"... 还有{len(image_urls)-10}张图片")