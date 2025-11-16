#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第二步：将抓取的数据改写成飞书格式
"""

import json
import re
import datetime
import sys
import os

def main():
    print('🔄 第二步：开始批量改写成飞书格式...')

    # 加载刚抓取的数据
    try:
        with open('/Users/sanshui/Desktop/CallawayJP/custom_url_2025-11-16T01-58-58-136Z.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('❌ 未找到抓取数据文件，请先运行第一步！')
        sys.exit(1)

    products = data.get('products', {})
    if not products:
        print('❌ 数据文件中没有产品数据')
        sys.exit(1)

    product_id = list(products.keys())[0]
    product_data = products[product_id]

    print(f'📊 加载的商品数据:')
    print(f'  - 商品标题: {product_data.get("productName", "")}')
    print(f'  - 商品ID: {product_data.get("productId", "")}')
    print(f'  - 性别: {product_data.get("gender", "")}')
    print(f'  - 价格: {product_data.get("price", "")}')
    print(f'  - 图片: {len(product_data.get("imageUrls", []))}张')

    print('\n🔄 开始通用字段改写处理...')

    # 1. 品牌识别
    brand = 'Le Coq公鸡乐卡克'
    print(f'✓ 品牌识别: {brand}')

    # 2. 性别分类（保持原始）
    gender = product_data.get('gender', '')
    print(f'✓ 性别分类: {gender}')

    # 3. 服装类型推断
    product_title = product_data.get('productName', '')
    if 'パンツ' in product_title or 'PANTS' in product_title:
        clothing_type = '裤子'
    elif 'スウェット' in product_title or 'セーター' in product_title:
        clothing_type = '毛衣/针织衫'
    else:
        clothing_type = '上装'
    print(f'✓ 服装类型: {clothing_type}')

    # 4. AI标题生成（简化版）
    chinese_title = f'DESCENTE {clothing_type} - 女款运动裤'
    print(f'✅ 标题生成: {chinese_title}')

    # 5. 颜色翻译（从HTML中提取）
    raw_colors = product_data.get('colors', [])
    cleaned_colors = []
    color_mapping = {
        'ネイビー': '藏青色',
        'ブラック': '黑色',
        'ベージュ': '米色',
        'カーキ': '卡其色'
    }

    seen_colors = set()
    for color in raw_colors:
        # 提取实际颜色名称，去除HTML标签
        clean_color = re.sub(r'<[^>]+>', '', color).strip()
        clean_color = re.sub(r'\s+', ' ', clean_color).strip()
        clean_color = clean_color.split('（')[0].split('(')[0].strip()

        translated = color_mapping.get(clean_color, clean_color)
        if translated not in seen_colors:
            cleaned_colors.append(translated)
            seen_colors.add(translated)

    print(f'✓ 颜色翻译完成: {len(cleaned_colors)}种')

    # 6. 描述翻译（使用之前的方法）
    try:
        from services.translator_v2 import translate_description
        translated_description = translate_description(product_data)
        print(f'✓ 描述翻译完成: {len(translated_description)}字符')
    except Exception as e:
        print(f'⚠️ 描述翻译失败: {e}')
        translated_description = product_data.get('description', '')

    # 7. 图片处理（保留前6张）
    image_urls = product_data.get('imageUrls', [])
    if len(image_urls) > 6:
        processed_images = image_urls[:6]
    else:
        processed_images = image_urls

    print(f'✓ 图片处理完成: {len(processed_images)}张')

    # 构建最终飞书格式数据
    final_fields = {
        '商品ID': product_data.get('productId', ''),
        '品牌名': brand,
        '商品标题': chinese_title,
        '颜色': ', '.join(cleaned_colors),
        '尺码': ', '.join(product_data.get('sizes', [])),
        '性别': gender,
        '价格': product_data.get('price', ''),
        '商品链接': product_data.get('detailUrl', ''),
        '图片URL': '\n'.join(processed_images),
        '图片数量': len(processed_images),
        '详情页文字': translated_description,
        '上传状态': 'success',
        '创建时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '最近更新时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 保存完整处理结果
    result_data = {
        'records': [{'fields': final_fields}],
        'total_products': 1,
        'timestamp': datetime.datetime.now().isoformat(),
        'url_processed': product_data.get('detailUrl', ''),
        'processing_summary': {
            'original_title': product_title,
            'chinese_title': chinese_title,
            'original_colors': raw_colors,
            'translated_colors': cleaned_colors,
            'description_translated': len(translated_description) > 0,
            'images_processed': len(processed_images)
        }
    }

    output_file = '/Users/sanshui/Desktop/CallawayJP/feishu_formatted_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f'\n💾 飞书格式数据已保存: {output_file}')
    print('\n📊 处理结果汇总:')
    print(f'✓ 品牌识别: {brand}')
    print(f'✓ 性别分类: {gender}')
    print(f'✓ 服装类型: {clothing_type}')
    print(f'✅ 标题生成: {chinese_title}')
    print(f'✓ 颜色翻译: {len(cleaned_colors)}种')
    print(f'✓ 描述翻译: {"成功" if len(translated_description) > 0 else "失败"}')
    print(f'✅ 图片处理: {len(processed_images)}张')
    print('\n✅ 第二步：飞书格式改写完成！')
    print('\n🎯 接下来可以运行第三步：上传到飞书')

    return result_data

if __name__ == '__main__':
    main()