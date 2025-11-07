#!/usr/bin/env python3
"""
合并与去重脚本
读取最新的 raw_links_<category>_*.json 文件并生成去重后的产品列表
去重结果会保留 productName、价格等字段，方便下游同步/标题生成

新增参数:
- --print-path: 仅输出去重结果文件的绝对路径，其他提示不打印（用于脚本自动化）

保留字段:
- productName: 产品名称
- currentPrice: 当前价格
- priceText: 价格文本
- promotionText: 促销信息
- tags: 产品标签
- mainImage: 主图片URL
- detailUrl: 详情页URL
- category: 产品分类

示例命令:
python3 merge_dedup.py --category womens_all
python3 merge_dedup.py --category womens_all --print-path  # 仅输出文件路径
"""

import json
import os
import glob
import re
import argparse
from datetime import datetime
from pathlib import Path

def load_latest_raw_links(target_categories=None):
    """加载最新的原始链接文件"""
    results_dir = Path(__file__).parent.parent / 'results'
    pattern = str(results_dir / 'raw_links_*.json')
    
    # 找到所有匹配的文件
    files = glob.glob(pattern)
    
    if not files:
        return []
    
    # 使用正则表达式解析文件名和时间戳
    regex = re.compile(r'raw_links_(.+?)_(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z)\.json')
    latest_regex = re.compile(r'raw_links_(.+?)_latest\.json')
    latest_files = {}
    
    for file in files:
        basename = os.path.basename(file)
        match = regex.match(basename)
        if match:
            category, timestamp = match.groups()
            
            # 如果指定了目标分类，只处理指定的分类
            if target_categories and category not in target_categories:
                continue
            
            # 比较时间戳，保留最新的文件
            if category not in latest_files or timestamp > latest_files[category][1]:
                latest_files[category] = (file, timestamp)
            continue

        latest_match = latest_regex.match(basename)
        if latest_match:
            category = latest_match.group(1)

            if target_categories and category not in target_categories:
                continue

            try:
                mtime = os.path.getmtime(file)
                timestamp = datetime.fromtimestamp(mtime).isoformat()
            except OSError:
                continue

            if category not in latest_files or timestamp > latest_files[category][1]:
                latest_files[category] = (file, timestamp)
    
    # 加载所有最新的文件
    return [json.load(open(file_path, 'r', encoding='utf-8')) 
            for file_path, _ in latest_files.values()]

def merge_and_dedup(data_list):
    """合并并去重所有产品，保留完整字段信息"""
    all_products = {}
    category_stats = {}
    
    def merge_product_fields(existing, new_link, category):
        """合并产品字段，优先保留非空值"""
        # 如果是新产品，创建基础结构
        if not existing:
            product_id = new_link.get('variantId', '').split('_')[0] if '_' in new_link.get('variantId', '') else new_link.get('productId', '')
            existing = {
                'productId': product_id,
                'variantId': '',
                'detailUrl': '',
                'category': category,
                'brandName': 'callawaygolf',
                'addedAt': datetime.now().isoformat(),
                # 新增字段，默认为空字符串
                'productName': '',
                'currentPrice': '',
                'priceText': '',
                'promotionText': '',
                'tags': '',
                'mainImage': ''
            }
        
        # 字段映射和合并逻辑
        field_mapping = {
            'variantId': 'variantId',
            'detailUrl': 'detailUrl',
            'productName': 'productName',
            'currentPrice': 'currentPrice',
            'priceText': 'priceText',
            'promotionText': 'promotionText',
            'tags': 'tags',
            'mainImage': 'mainImage'
        }
        
        # 合并字段：优先保留已有非空值，如果原值为空则用新值填充
        for source_key, target_key in field_mapping.items():
            new_value = new_link.get(source_key, '')
            if new_value and (not existing.get(target_key) or existing[target_key] == ''):
                existing[target_key] = new_value
        
        return existing
    
    for data in data_list:
        category = data.get('category', 'unknown')
        links = data.get('links', [])
        
        category_stats[category] = {
            'expected': data.get('expectedCount', 0),
            'actual': data.get('actualCount', 0),
            'unique_products': 0
        }
        
        # 按 productId 去重，保留完整字段信息
        for link in links:
            if not (link.get('variantId') or link.get('productId')):
                continue
                
            # 提取 productId
            product_id = (link.get('variantId', '').split('_')[0] if '_' in link.get('variantId', '') 
                         else link.get('productId', ''))
            
            if not product_id:
                continue
            
            # 合并或创建产品记录
            existing_product = all_products.get(product_id)
            merged_product = merge_product_fields(existing_product, link, category)
            all_products[product_id] = merged_product
        
        # 计算当前分类的唯一产品数
        category_products = [p for p in all_products.values() if p['category'] == category]
        category_stats[category]['unique_products'] = len(category_products)
    
    return all_products, category_stats

def save_results(products, stats):
    """保存去重结果"""
    results_dir = Path(__file__).parent.parent / 'results'
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%fZ')[:-3] + 'Z'
    output_file = results_dir / f'all_products_dedup_{timestamp}.json'
    
    # 准备输出数据
    output_data = {
        'mergedAt': datetime.now().isoformat(),
        'totalUniqueProducts': len(products),
        'categories': list(stats.keys()),
        'categoryStats': stats,
        'products': list(products.values())
    }
    
    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='合并与去重 CallawayJP 产品数据')
    parser.add_argument('--category', type=str, help='指定处理的分类（逗号分隔）')
    parser.add_argument('--print-path', action='store_true', help='仅输出去重结果文件路径（绝对路径），其他提示不打印')
    args = parser.parse_args()
    
    # 解析目标分类
    target_categories = None
    if args.category:
        target_categories = [cat.strip() for cat in args.category.split(',')]
    
    # 加载最新的原始数据
    data_list = load_latest_raw_links(target_categories)
    
    if not data_list:
        if not args.print_path:
            print("✗ 无数据")
        return
    
    # 合并和去重
    products, stats = merge_and_dedup(data_list)
    
    # 保存结果
    output_file = save_results(products, stats)
    
    if args.print_path:
        # 仅输出绝对路径
        print(output_file.resolve())
    else:
        # 原有的详细输出格式
        total_products = len(products)
        categories_processed = len(stats)
        
        print(f"✓ 合并完成: {total_products}个产品, {categories_processed}个分类")
        print(f"✓ 输出文件: {output_file}")
    
    return output_file

if __name__ == '__main__':
    main()
