"""
导入基础产品信息到飞书工具
从 scrape_category 输出中提取基础信息，批量创建飞书记录

⚠️ 重要说明：去重逻辑
- Stage1 导入时使用「商品链接」（URL）作为去重依据
- 即使 productId 不同，只要 URL 相同就会跳过
- 导入时会将 URL 编号写入「商品ID」字段
- Stage2 会抓取详情页并将「商品ID」覆盖为品牌货号
"""

import argparse
import json
import sys
from pathlib import Path

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tongyong_feishu_update.clients import create_feishu_client


def normalize_url(url: str) -> str:
    """
    规范化URL，用于去重比较

    处理：
    - 去除首尾空格
    - 统一协议为 https
    - 去除末尾斜杠

    Args:
        url: 原始URL

    Returns:
        规范化后的URL
    """
    if not url:
        return ''
    cleaned = url.strip()
    cleaned = cleaned.replace('http://', 'https://')  # 统一协议
    return cleaned.rstrip('/')  # 去掉末尾斜杠


def import_basic_products(
    source_file: str,
    brand: str = "",
    batch_size: int = 30,
    verbose: bool = False
):
    """
    从 scrape_category 输出导入基础产品信息到飞书

    Args:
        source_file: scrape_category 输出文件路径
        brand: 品牌名称
        batch_size: 批量创建的批次大小
        verbose: 是否显示详细信息

    Returns:
        dict: 导入结果统计
    """
    # 1. 读取源文件
    if verbose:
        print(f"📄 正在读取源文件: {source_file}", file=sys.stderr)

    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 提取产品基础信息
    products_to_import = []

    if 'results' in data and isinstance(data['results'], list):
        # scrape_category.js 格式
        for result in data['results']:
            if 'products' in result and isinstance(result['products'], list):
                for item in result['products']:
                    product_id = item.get('productId', '')
                    if product_id:
                        products_to_import.append({
                            'product_id': product_id,
                            'url': item.get('url', ''),
                            'brand': brand or item.get('brand', '')
                        })

    if verbose:
        print(f"✅ 提取到 {len(products_to_import)} 个产品", file=sys.stderr)

    if not products_to_import:
        print("⚠️ 未找到任何产品", file=sys.stderr)
        return {'success_count': 0, 'skip_count': 0, 'error_count': 0}

    # 3. 获取飞书现有记录
    if verbose:
        print("🔍 正在获取飞书现有记录...", file=sys.stderr)

    feishu_client = create_feishu_client()
    existing_records = feishu_client.get_records()

    if verbose:
        print(f"✅ 已获取 {len(existing_records)} 条现有记录", file=sys.stderr)

    # 4. 构建已存在的 URL 集合（用于去重）
    # ⚠️ 去重逻辑已改为基于 URL 而非 productId
    # 🔥 使用 normalize_url 规范化，避免因协议/末尾斜杠不同导致重复
    existing_urls = set()
    for record_data in existing_records.values():
        fields = record_data.get('fields', {})
        url = fields.get('商品链接', '')
        if url:
            existing_urls.add(normalize_url(url))

    if verbose:
        print(f"📊 已提取 {len(existing_urls)} 个已存在的商品链接", file=sys.stderr)

    # 5. 过滤掉已存在的记录（基于 URL 去重）
    # 🔥 使用 normalize_url 规范化后进行比较
    new_products = []
    skip_count = 0

    for product in products_to_import:
        url = product.get('url', '')
        normalized = normalize_url(url)
        if normalized in existing_urls:
            skip_count += 1
            if verbose:
                print(f"⏭️ 跳过已存在的 URL: {url}", file=sys.stderr)
        else:
            new_products.append(product)

    if verbose:
        print(f"📊 新增: {len(new_products)} 个，跳过: {skip_count} 个", file=sys.stderr)

    if not new_products:
        print("✅ 所有产品 URL 已存在，无需创建新记录", file=sys.stderr)
        return {'success_count': 0, 'skip_count': skip_count, 'error_count': 0}

    # 6. 批量创建新记录
    create_records = []
    for product in new_products:
        create_records.append({
            'fields': {
                '商品ID': product['product_id'],
                '商品链接': product['url'],
                '品牌名': product['brand']
            },
            'product_id': product['product_id']
        })

    if verbose:
        print(f"🚀 开始批量创建 {len(create_records)} 条记录...", file=sys.stderr)

    result = feishu_client.batch_create(create_records, batch_size=batch_size)

    success_count = result.get('success_count', 0)
    error_count = len(result.get('failed_batches', []))

    if verbose:
        print(f"✅ 创建完成: 成功 {success_count} 条，失败 {error_count} 个批次", file=sys.stderr)

    return {
        'success_count': success_count,
        'skip_count': skip_count,
        'error_count': error_count
    }


def main():
    parser = argparse.ArgumentParser(
        description='导入基础产品信息到飞书'
    )

    parser.add_argument(
        '--source',
        required=True,
        help='scrape_category 输出文件路径'
    )

    parser.add_argument(
        '--brand',
        default='',
        help='品牌名称'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=30,
        help='批量创建的批次大小（默认：30）'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )

    args = parser.parse_args()

    try:
        result = import_basic_products(
            source_file=args.source,
            brand=args.brand,
            batch_size=args.batch_size,
            verbose=args.verbose
        )

        # 输出结果摘要
        print(f"\n📊 导入结果摘要:")
        print(f"  ✅ 新增记录: {result['success_count']}")
        print(f"  ⏭️ 跳过记录: {result['skip_count']}")
        if result['error_count'] > 0:
            print(f"  ❌ 失败批次: {result['error_count']}")

        sys.exit(0 if result['error_count'] == 0 else 1)

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
