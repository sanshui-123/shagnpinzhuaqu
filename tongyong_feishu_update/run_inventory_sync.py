"""
库存同步脚本 - 只更新飞书的 颜色/尺码/库存状态 三个字段

使用方式:
python -m tongyong_feishu_update.run_inventory_sync inventory.json --brand "Le Coq公鸡乐卡克"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# 确保可以导入本地模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from tongyong_feishu_update.clients import create_feishu_client
from tongyong_feishu_update.config import translation


def build_inventory_fields(product_data: dict) -> dict:
    """
    从库存数据构建飞书字段（只包含 颜色/尺码/库存状态）

    Args:
        product_data: 包含 variantInventory 的产品数据

    Returns:
        飞书字段字典
    """
    fields = {}

    variant_inventory = product_data.get('variantInventory', [])

    if not variant_inventory:
        return fields

    # 分析库存状态
    in_stock_colors = set()
    in_stock_sizes = set()
    color_oos_map: Dict[str, List[str]] = {}

    for variant in variant_inventory:
        color = variant.get('color', '')
        size = variant.get('size', '')
        in_stock = variant.get('inStock', True)

        # 清理颜色名称（去掉括号内容）
        color_display = ''
        if color:
            color_display = color.split('（')[0].split('(')[0].strip() or color.strip()

        if in_stock:
            if color:
                in_stock_colors.add(color)
            if size:
                in_stock_sizes.add(size)
        else:
            if color_display and size:
                if color_display not in color_oos_map:
                    color_oos_map[color_display] = []
                size_label = str(size).strip()
                if size_label and size_label not in color_oos_map[color_display]:
                    color_oos_map[color_display].append(size_label)

    # 判断库存状态
    stock_status = product_data.get('stockStatus', 'in_stock')
    if not in_stock_colors and not in_stock_sizes and variant_inventory:
        stock_status = 'out_of_stock'

    # 构建颜色字段（只保留有货的）
    colors = product_data.get('colors', [])
    if variant_inventory and in_stock_colors:
        filtered_colors = []
        for color in colors:
            color_clean = color.split('（')[0].split('(')[0].strip() if color else ''
            if color_clean in in_stock_colors or color in in_stock_colors:
                filtered_colors.append(color)
        colors = filtered_colors if filtered_colors else colors

    if stock_status == 'out_of_stock':
        colors = []

    # 翻译颜色
    color_lines = []
    for color in colors:
        chinese = translation.translate_color_name(str(color).strip())
        if chinese:
            color_lines.append(chinese)

    fields['颜色'] = '\n'.join(color_lines)

    # 构建尺码字段（只保留有货的）
    sizes = product_data.get('sizes', [])
    if variant_inventory and in_stock_sizes:
        filtered_sizes = [s for s in sizes if str(s) in in_stock_sizes]
        sizes = filtered_sizes if filtered_sizes else sizes

    if stock_status == 'out_of_stock':
        sizes = []

    fields['尺码'] = '\n'.join(str(s) for s in sizes)

    # 构建库存状态字段
    stock_notes: List[str] = []
    if variant_inventory:
        if stock_status == 'out_of_stock':
            stock_notes.append('都缺货')
        else:
            for color_name, size_list in color_oos_map.items():
                if not size_list:
                    continue
                # 翻译颜色名称
                color_chinese = translation.translate_color_name(color_name)
                stock_notes.append(f"{color_chinese}({'/'.join(size_list)}) 没货")

            # 如果没有缺货信息，显示"不缺货"
            if not stock_notes:
                stock_notes.append('不缺货')

    fields['库存状态'] = '\n'.join(stock_notes)

    return fields


def sync_inventory(input_file: str, brand_name: str = None, dry_run: bool = False):
    """
    同步库存数据到飞书

    Args:
        input_file: 库存数据文件路径
        brand_name: 品牌名称（用于日志）
        dry_run: 是否只预览不实际更新
    """
    print(f"📦 开始库存同步...")
    print(f"📄 输入文件: {input_file}")

    # 加载库存数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = data.get('products', [])
    if not products:
        print("⚠️ 没有找到产品数据")
        return

    print(f"📊 共 {len(products)} 个产品待同步")

    # 获取飞书客户端
    feishu_client = create_feishu_client()
    feishu_records = feishu_client.get_records()
    print(f"✅ 已获取 {len(feishu_records)} 条飞书记录")

    # 构建 product_id -> record_id 映射
    id_to_record = {}
    for pid, record_info in feishu_records.items():
        id_to_record[pid] = record_info.get('record_id', '')

    # 处理每个产品，收集更新记录
    update_records = []
    skip_count = 0

    for product_data in products:
        product_id = product_data.get('productId', '')

        if not product_id:
            skip_count += 1
            continue

        # 查找飞书记录
        record_id = id_to_record.get(product_id)
        if not record_id:
            print(f"⚠️ 未找到记录: {product_id}")
            skip_count += 1
            continue

        # 构建库存字段
        fields = build_inventory_fields(product_data)

        if not fields:
            print(f"⚠️ 无库存数据: {product_id}")
            skip_count += 1
            continue

        # 显示更新内容
        stock_status = fields.get('库存状态', '')
        print(f"\n📝 {product_id}:")
        print(f"   库存状态: {stock_status}")

        if dry_run:
            print(f"   [预览模式，不实际更新]")
        else:
            # 添加到更新列表
            update_records.append({
                'record_id': record_id,
                'fields': fields,
                'product_id': product_id
            })

    # 批量更新飞书
    success_count = 0
    error_count = 0

    if not dry_run and update_records:
        print(f"\n📤 开始批量更新 {len(update_records)} 条记录...")
        try:
            result = feishu_client.batch_update(update_records)
            success_count = result.get('success_count', 0)
            failed_batches = result.get('failed_batches', [])
            error_count = len(update_records) - success_count
        except Exception as e:
            print(f"❌ 批量更新失败: {e}")
            error_count = len(update_records)
    elif dry_run:
        success_count = len(products) - skip_count

    # 汇总
    print('\n' + '=' * 50)
    print('📊 同步完成汇总:')
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  失败: {error_count}")
    print('=' * 50)


def main():
    parser = argparse.ArgumentParser(
        description='库存同步 - 只更新飞书的 颜色/尺码/库存状态'
    )

    parser.add_argument(
        'input_file',
        help='库存数据文件路径'
    )

    parser.add_argument(
        '--brand', '-b',
        default=None,
        help='品牌名称（用于日志）'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际更新'
    )

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"❌ 文件不存在: {args.input_file}")
        sys.exit(1)

    try:
        sync_inventory(
            input_file=args.input_file,
            brand_name=args.brand,
            dry_run=args.dry_run
        )
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
