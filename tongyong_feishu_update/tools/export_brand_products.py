"""
导出指定品牌的商品列表
用于库存巡检脚本的输入
"""

import argparse
import json
import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tongyong_feishu_update.clients import create_feishu_client


def export_brand_products(brand_name: str, limit: int = 0, output_path: str = None):
    """
    导出指定品牌的商品列表

    Args:
        brand_name: 品牌名称（如 "Le Coq公鸡乐卡克"）
        limit: 限制导出数量（0=全部）
        output_path: 输出文件路径

    Returns:
        产品列表
    """
    print(f"🔍 正在获取飞书记录...")

    feishu_client = create_feishu_client()
    feishu_records = feishu_client.get_records()

    print(f"✅ 已获取 {len(feishu_records)} 条飞书记录")

    # 过滤指定品牌
    products = []
    for product_id, record_info in feishu_records.items():
        fields = record_info['fields']
        record_brand = fields.get('品牌名', '').strip()

        if record_brand == brand_name:
            # 提取商品链接
            url_field = fields.get('商品链接', '')
            if isinstance(url_field, list) and url_field:
                url = url_field[0].get('link', '') if isinstance(url_field[0], dict) else str(url_field[0])
            else:
                url = str(url_field) if url_field else ''

            if url:
                # 提取库存状态字段（用于跳过已标记都缺货的商品）
                stock_status_text = fields.get('库存状态', '').strip()

                products.append({
                    'productId': product_id,
                    'url': url,
                    'recordId': record_info.get('record_id', ''),
                    'stockStatusText': stock_status_text
                })

    print(f"📊 找到 {len(products)} 个 {brand_name} 商品")

    # 应用限制
    if limit > 0 and len(products) > limit:
        products = products[:limit]
        print(f"📋 限制为 {limit} 个")

    # 构建输出
    output = {
        'brand': brand_name,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'total': len(products),
        'products': products
    }

    # 保存或返回
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存到: {output_path}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description='导出指定品牌的商品列表（用于库存巡检）'
    )

    parser.add_argument(
        '--brand', '-b',
        required=True,
        help='品牌名称（如 "Le Coq公鸡乐卡克"）'
    )

    parser.add_argument(
        '--output', '-o',
        help='输出文件路径'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=0,
        help='限制导出数量（默认: 全部）'
    )

    parser.add_argument(
        '--stdout',
        action='store_true',
        help='输出到标准输出'
    )

    args = parser.parse_args()

    try:
        result = export_brand_products(
            brand_name=args.brand,
            limit=args.limit,
            output_path=args.output if not args.stdout else None
        )

        if args.stdout:
            print(json.dumps(result, ensure_ascii=False, indent=2))

        sys.exit(0)

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
