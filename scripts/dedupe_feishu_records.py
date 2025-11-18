#!/usr/bin/env python3
"""
飞书记录去重脚本
清理飞书表中重复的 URL 记录，保留有标题的记录
"""

import sys
import time
import requests
from pathlib import Path
from collections import defaultdict

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tongyong_feishu_update.clients import create_feishu_client


def normalize_url(url: str) -> str:
    """规范化 URL"""
    if not url:
        return ''
    return url.strip().rstrip('/')


def get_all_records_with_details(client):
    """
    获取所有记录的详细信息，包括 record_id

    Returns:
        list: 记录列表，每个记录包含 record_id 和 fields
    """
    token = client._get_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    all_records = []
    page_token = None

    while True:
        params = {
            'page_size': 500,
            'field_names': '["商品ID","品牌名","商品标题","颜色","尺码","价格","衣服分类","性别","商品链接"]'
        }
        if page_token:
            params['page_token'] = page_token

        resp = requests.get(
            client.records_url,
            headers=headers,
            params=params,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get('code') != 0:
            print(f"飞书API返回错误: {data}")
            break

        items = data.get('data', {}).get('items', [])
        for item in items:
            all_records.append({
                'record_id': item.get('record_id'),
                'fields': item.get('fields', {})
            })

        page_token = data.get('data', {}).get('page_token')
        if not page_token:
            break

        time.sleep(0.2)

    return all_records


def batch_delete_records(client, record_ids: list, batch_size: int = 50):
    """
    批量删除记录

    Args:
        client: 飞书客户端
        record_ids: 要删除的 record_id 列表
        batch_size: 每批删除数量

    Returns:
        int: 成功删除的数量
    """
    token = client._get_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    delete_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{client.app_token}/tables/{client.table_id}/records/batch_delete'

    total_deleted = 0
    total_batches = (len(record_ids) + batch_size - 1) // batch_size

    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        payload = {'records': batch}

        batch_num = i // batch_size + 1

        for attempt in range(3):
            try:
                resp = requests.post(
                    delete_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get('code') != 0:
                    print(f"批次 {batch_num}/{total_batches}: 删除失败 - {data}")
                    break

                total_deleted += len(batch)
                print(f"批次 {batch_num}/{total_batches}: 成功删除 {len(batch)} 条")
                break

            except Exception as e:
                if attempt < 2:
                    print(f"批次 {batch_num} 重试 ({attempt + 1}/3): {e}")
                    time.sleep(2 ** attempt)
                else:
                    print(f"批次 {batch_num}/{total_batches}: 删除失败 - {e}")

        time.sleep(0.3)

    return total_deleted


def find_duplicates(records: list):
    """
    查找重复的 URL 记录

    Args:
        records: 记录列表

    Returns:
        tuple: (要保留的记录, 要删除的记录)
    """
    # 按 URL 分组
    url_groups = defaultdict(list)

    for record in records:
        fields = record.get('fields', {})
        url = fields.get('商品链接', '')
        normalized = normalize_url(url)

        if normalized:
            url_groups[normalized].append(record)

    to_delete = []
    duplicate_urls = []

    for url, group in url_groups.items():
        if len(group) <= 1:
            continue

        duplicate_urls.append(url)

        # 分离有标题和无标题的记录
        with_title = []
        without_title = []

        for record in group:
            title = record.get('fields', {}).get('商品标题', '')
            if title and title.strip():
                with_title.append(record)
            else:
                without_title.append(record)

        # 决定保留哪条
        if with_title:
            # 保留第一条有标题的，其余全部删除
            keep = with_title[0]
            to_delete.extend(with_title[1:])
            to_delete.extend(without_title)
        else:
            # 都没标题，保留第一条
            keep = without_title[0]
            to_delete.extend(without_title[1:])

        print(f"URL: {url}")
        print(f"  重复 {len(group)} 条，保留 record_id={keep['record_id']}")
        print(f"  删除 {len(group) - 1} 条")

    return duplicate_urls, to_delete


def main():
    import argparse
    parser = argparse.ArgumentParser(description='飞书记录去重脚本')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认直接删除')
    args = parser.parse_args()

    print("=" * 60)
    print("飞书记录去重脚本")
    print("=" * 60)

    # 1. 创建客户端
    print("\n1. 连接飞书...")
    client = create_feishu_client()

    # 2. 获取所有记录
    print("\n2. 获取所有记录...")
    records = get_all_records_with_details(client)
    print(f"   共获取 {len(records)} 条记录")

    # 3. 查找重复
    print("\n3. 查找重复记录...")
    duplicate_urls, to_delete = find_duplicates(records)

    if not to_delete:
        print("\n没有找到重复记录!")
        return

    print(f"\n发现 {len(duplicate_urls)} 个重复 URL")
    print(f"需要删除 {len(to_delete)} 条重复记录")

    # 4. 显示将要删除的记录
    print("\n4. 将要删除的记录:")
    print("-" * 60)
    for i, record in enumerate(to_delete[:20], 1):  # 只显示前20条
        url = record.get('fields', {}).get('商品链接', '')
        title = record.get('fields', {}).get('商品标题', '(无标题)')
        print(f"  {i}. {record['record_id']}: {title[:30]}... | {url[:50]}...")

    if len(to_delete) > 20:
        print(f"  ... 还有 {len(to_delete) - 20} 条")

    # 5. 确认删除
    print("\n" + "=" * 60)
    if args.yes:
        print(f"自动确认删除 {len(to_delete)} 条重复记录")
    else:
        confirm = input(f"确认删除 {len(to_delete)} 条重复记录? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消删除操作")
            return

    # 6. 执行删除
    print("\n5. 执行删除...")
    delete_ids = [record['record_id'] for record in to_delete]
    deleted_count = batch_delete_records(client, delete_ids)

    # 7. 输出结果
    print("\n" + "=" * 60)
    print("删除完成!")
    print(f"  成功删除: {deleted_count} 条")
    print(f"  重复 URL 数: {len(duplicate_urls)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
