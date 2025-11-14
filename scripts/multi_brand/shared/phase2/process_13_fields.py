#!/usr/bin/env python3

"""
13字段处理主入口
从stdin读取JSON数据，调用原版卡拉威服务处理，输出13字段结果
"""

import sys
import json
import os
import importlib.util

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """主函数：读取stdin，处理数据，输出结果"""
    try:
        # 从stdin读取输入数据
        input_data = json.loads(sys.stdin.read())

        print(f"🔄 Python服务开始处理...", file=sys.stderr)
        print(f"   品牌: {input_data.get('brand', 'unknown')}", file=sys.stderr)
        print(f"   URL: {input_data.get('url', 'unknown')}", file=sys.stderr)

        # 构建产品数据字典（原版格式）
        product_data = {
            'url': input_data.get('url', ''),
            'brand': input_data.get('brand', ''),
            'rawData': input_data.get('rawData', {}),
            'title': input_data.get('rawData', {}).get('title', ''),
            'images': input_data.get('rawData', {}).get('images', {}),
            'colors': input_data.get('rawData', {}).get('colors', []),
            'sizes': input_data.get('rawData', {}).get('sizes', []),
            'sizeChart': input_data.get('rawData', {}).get('sizeChart', {}),
            'description': input_data.get('rawData', {}).get('description', ''),
            'price': input_data.get('rawData', {}).get('price', ''),
            'productCode': input_data.get('rawData', {}).get('productCode', '')
        }

        # 处理13个字段
        result = process_13_fields(product_data)

        # 输出JSON结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}", file=sys.stderr)
        sys.exit(1)

def process_13_fields(product_data):
    """处理13个字段的完整逻辑"""

    # 1. 基本信息
    result = {}

    # 商品链接
    result['商品链接'] = product_data.get('url', '')

    # 商品ID
    result['商品ID'] = extract_product_id(product_data)

    # 品牌名
    result['品牌名'] = extract_brand_name(product_data)

    # 价格
    result['价格'] = extract_price(product_data)

    # 2. AI标题生成 - 调用原版title_v6
    try:
        from services.title_v6 import generate_cn_title
        title_result = generate_cn_title(product_data)
        result['商品标题'] = title_result
        print(f"   ✅ AI标题生成完成: {title_result[:30]}...", file=sys.stderr)
    except Exception as e:
        print(f"   ⚠️ AI标题生成失败: {str(e)}", file=sys.stderr)
        result['商品标题'] = extract_simple_title(product_data)

    # 3. 性别分类
    try:
        from services.classifiers import determine_gender
        result['性别'] = determine_gender(product_data)
    except Exception as e:
        print(f"   ⚠️ 性别分类失败: {str(e)}", file=sys.stderr)
        result['性别'] = '男'  # 默认

    # 4. 服装分类
    try:
        from services.classifiers import determine_clothing_type
        result['衣服分类'] = determine_clothing_type(product_data)
    except Exception as e:
        print(f"   ⚠️ 服装分类失败: {str(e)}", file=sys.stderr)
        result['衣服分类'] = '服装'  # 默认

    # 5. 图片处理
    try:
        result['图片总数'], result['图片链接'] = process_images(product_data)
    except Exception as e:
        print(f"   ⚠️ 图片处理失败: {str(e)}", file=sys.stderr)
        result['图片总数'] = '0'
        result['图片链接'] = ''

    # 6. 颜色处理
    result['颜色'] = process_colors(product_data.get('colors', []))

    # 7. 尺码处理
    result['尺码'] = process_sizes(product_data.get('sizes', []))

    # 8. 详情页文字翻译
    try:
        from services.translator_v2 import Translator
        translator = Translator()
        description = product_data.get('description', '')
        if description:
            result['详情页文字'] = translator.translate_ja_to_cn(description)
        else:
            result['详情页文字'] = ''
    except Exception as e:
        print(f"   ⚠️ 翻译失败: {str(e)}", file=sys.stderr)
        result['详情页文字'] = product_data.get('description', '')

    # 9. 尺码表处理
    try:
        from services.size_table_formatter import SizeTableFormatter
        formatter = SizeTableFormatter()
        size_chart = product_data.get('sizeChart', {})
        result['尺码表'] = formatter.format(size_chart)
    except Exception as e:
        print(f"   ⚠️ 尺码表处理失败: {str(e)}", file=sys.stderr)
        result['尺码表'] = format_size_chart_fallback(size_chart)

    return result

def extract_product_id(product_data):
    """提取商品ID"""
    # 优先从productCode
    product_code = product_data.get('productCode', '')
    if product_code:
        return product_code

    # 从尺码表提取
    size_chart = product_data.get('sizeChart', {})
    if isinstance(size_chart, dict):
        text = size_chart.get('text', '') or size_chart.get('html', '')
    else:
        text = str(size_chart)

    # 匹配字母数字组合
    import re
    matches = re.findall(r'\b[A-Z]{2,}\d{4,}\b', text)
    for match in matches:
        if len(match) >= 6:
            return match

    return ''

def extract_brand_name(product_data):
    """提取品牌名"""
    brand = product_data.get('brand', '').lower()

    # 品牌映射
    brand_mapping = {
        'le coq sportif golf': 'Le Coq Sportif Golf',
        'callaway': '卡拉威',
        'titleist': '泰特利斯',
        'footjoy': 'FootJoy',
        'descente': '迪桑特'
    }

    for key, value in brand_mapping.items():
        if key in brand:
            return value

    return '未知品牌'

def extract_price(product_data):
    """提取价格"""
    price = product_data.get('price', '')
    if isinstance(price, str):
        # 移除货币符号
        import re
        price = re.sub(r'[¥￥,]', '', price).strip()
    return price

def extract_simple_title(product_data):
    """简单标题提取（fallback）"""
    title = product_data.get('title', '')
    if isinstance(title, dict):
        title = title.get('original', title.get('translated', ''))
    return str(title)[:50] if title else ''

def process_images(product_data):
    """处理图片"""
    images = product_data.get('images', {})
    if not images:
        return '0', ''

    # 提取所有图片URL
    all_urls = []

    if isinstance(images, dict):
        # 从all字段获取
        if 'all' in images:
            for img in images['all']:
                if isinstance(img, dict):
                    url = img.get('src', '')
                else:
                    url = str(img)
                if url and url not in all_urls:
                    all_urls.append(url)

        # 从productImages字段获取
        if 'productImages' in images:
            for url in images['productImages']:
                if url and url not in all_urls:
                    all_urls.append(url)
    elif isinstance(images, list):
        all_urls = [str(img) for img in images if img]

    # 应用卡拉威图片规则：第一个颜色保留所有，其他颜色保留前6张
    if len(all_urls) > 0:
        # 简单实现：前半部分作为第一个颜色，后半部分限制6张
        first_color_count = len(all_urls) // 2
        final_urls = all_urls[:first_color_count] + all_urls[first_color_count:first_color_count+6]

        return str(len(final_urls)), '\n'.join(final_urls)

    return '0', ''

def process_colors(colors):
    """处理颜色"""
    if not colors:
        return ''

    result = []
    for color in colors:
        if isinstance(color, dict):
            name = color.get('name', '')
        else:
            name = str(color)

        if name and name not in result:
            result.append(name)

    return ', '.join(result)

def process_sizes(sizes):
    """处理尺码"""
    if not sizes:
        return ''

    result = []
    for size in sizes:
        if isinstance(size, dict):
            size_str = size.get('size', size.get('name', ''))
        else:
            size_str = str(size)

        if size_str and size_str not in result:
            result.append(size_str)

    return ', '.join(result)

def format_size_chart_fallback(size_chart):
    """尺码表格式化（fallback）"""
    if isinstance(size_chart, dict):
        return size_chart.get('html', '') or size_chart.get('text', '')
    return str(size_chart)

if __name__ == '__main__':
    main()