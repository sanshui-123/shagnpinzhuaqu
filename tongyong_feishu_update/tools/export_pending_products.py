"""
导出待处理产品ID工具
读取飞书表，找出指定字段为空或记录缺失的 product_id
"""

import argparse
import json
import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tongyong_feishu_update.clients import create_feishu_client
from tongyong_feishu_update.loaders.factory import LoaderFactory


def get_pending_products(
    feishu_records: dict,
    source_products: list = None,
    check_field: str = "商品标题",
    brand_filter: str = None
) -> list:
    """
    获取待处理的产品ID列表

    Args:
        feishu_records: 飞书现有记录 {product_id: {record_id, fields}}
        source_products: 源文件中的产品列表（可选）
        check_field: 要检查的字段名称
        brand_filter: 品牌过滤（仅返回该品牌的产品）

    Returns:
        待处理的 product_id 列表
    """
    pending_ids = []

    # 如果提供了源文件，只检查源文件中的产品
    if source_products:
        source_ids = {p.product_id for p in source_products if p.product_id}
    else:
        source_ids = None

    # 检查每个产品
    if source_ids:
        for product_id in source_ids:
            # 记录不存在 或 指定字段为空
            if product_id not in feishu_records:
                pending_ids.append(product_id)
            else:
                record_fields = feishu_records[product_id]['fields']

                # 品牌过滤
                if brand_filter:
                    record_brand = record_fields.get('品牌名', '').strip()
                    if record_brand != brand_filter:
                        continue

                # 检查指定字段是否为空
                field_value = record_fields.get(check_field, '').strip()
                if not field_value:
                    pending_ids.append(product_id)
    else:
        # 没有源文件，检查所有飞书记录
        for product_id, record_info in feishu_records.items():
            record_fields = record_info['fields']

            # 品牌过滤
            if brand_filter:
                record_brand = record_fields.get('品牌名', '').strip()
                if record_brand != brand_filter:
                    continue

            # 检查指定字段是否为空
            field_value = record_fields.get(check_field, '').strip()
            if not field_value:
                pending_ids.append(product_id)

    return pending_ids


def main():
    parser = argparse.ArgumentParser(
        description='导出待处理产品ID（飞书标题为空或记录缺失）'
    )

    parser.add_argument(
        '--field',
        default='商品标题',
        help='要检查的字段名称（默认：商品标题）'
    )

    parser.add_argument(
        '--source',
        help='源数据文件路径（JSON格式）'
    )

    parser.add_argument(
        '--output',
        help='输出文件路径'
    )

    parser.add_argument(
        '--stdout',
        action='store_true',
        help='输出到标准输出（JSON格式）'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )

    parser.add_argument(
        '--brand',
        default=None,
        help='品牌过滤（仅返回该品牌的产品）'
    )

    args = parser.parse_args()

    try:
        # 1. 获取飞书现有记录
        if args.verbose:
            print("🔍 正在获取飞书记录...", file=sys.stderr)

        feishu_client = create_feishu_client()
        feishu_records = feishu_client.get_records()

        if args.verbose:
            print(f"✅ 已获取 {len(feishu_records)} 条飞书记录", file=sys.stderr)

        # 2. 读取源文件（如果提供）
        source_products = None
        if args.source:
            if args.verbose:
                print(f"📄 正在读取源文件: {args.source}", file=sys.stderr)

            with open(args.source, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查是否是 scrape_category.js 格式
            if 'results' in data and isinstance(data['results'], list):
                # 直接从 results 中提取产品
                from tongyong_feishu_update.models.product import Product
                source_products = []
                for result in data['results']:
                    if 'products' in result and isinstance(result['products'], list):
                        for item in result['products']:
                            product = Product(
                                product_id=item.get('productId', ''),
                                detail_url=item.get('url', ''),
                                product_name=item.get('title', ''),
                                brand=item.get('brand', '')
                            )
                            if product.product_id:  # 只添加有 productId 的商品
                                source_products.append(product)
            else:
                # 使用 LoaderFactory
                loader = LoaderFactory.create(data)
                source_products = loader.parse(data)

            if args.verbose:
                print(f"✅ 已加载 {len(source_products)} 个源产品", file=sys.stderr)

        # 3. 获取待处理产品ID
        pending_ids = get_pending_products(
            feishu_records=feishu_records,
            source_products=source_products,
            check_field=args.field,
            brand_filter=args.brand
        )

        if args.verbose:
            print(f"📊 待处理产品数: {len(pending_ids)}", file=sys.stderr)
            if pending_ids and len(pending_ids) <= 10:
                print(f"   产品ID: {', '.join(pending_ids)}", file=sys.stderr)

        # 4. 输出结果
        result = pending_ids

        if args.stdout:
            # 输出到标准输出（供其他程序读取）
            print(json.dumps(result, ensure_ascii=False))
        elif args.output:
            # 输出到文件
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if args.verbose:
                print(f"✅ 已保存到: {args.output}", file=sys.stderr)
        else:
            # 默认输出到标准输出
            print(json.dumps(result, ensure_ascii=False, indent=2))

        sys.exit(0)

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
