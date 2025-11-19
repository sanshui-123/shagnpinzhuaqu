#!/usr/bin/env python3
"""
飞书记录去重脚本

功能：
- 检测并删除飞书表中重复的记录
- 同时按「商品ID」和「商品链接」进行去重
- 优先保留有标题的记录

使用方法：
    python3 scripts/dedupe_feishu_records.py          # 预览模式
    python3 scripts/dedupe_feishu_records.py --apply  # 执行删除
"""

import sys
import time
import argparse
import requests
from collections import defaultdict
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tongyong_feishu_update.config.settings import get_feishu_config


def normalize_url(url: str) -> str:
    """规范化URL用于去重比较"""
    if not url:
        return ''
    cleaned = url.strip().replace('http://', 'https://').rstrip('/')
    return cleaned.lower()


def main():
    parser = argparse.ArgumentParser(description='飞书记录去重脚本')
    parser.add_argument('--apply', action='store_true', help='执行删除（默认为预览模式）')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    args = parser.parse_args()

    # 使用项目配置系统获取飞书凭证
    cfg = get_feishu_config()
    APP_ID = cfg.app_id
    APP_SECRET = cfg.app_secret
    APP_TOKEN = cfg.app_token
    TABLE_ID = cfg.table_id

    if not all([APP_ID, APP_SECRET, APP_TOKEN, TABLE_ID]):
        print("错误: 飞书配置不完整，请检查环境变量或配置文件")
        sys.exit(1)

    # 获取token
    auth_url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(auth_url, json={'app_id': APP_ID, 'app_secret': APP_SECRET}, timeout=15)
    token = resp.json()['tenant_access_token']

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 获取所有记录
    records_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records'
    all_records = []
    page_token = None

    print("正在获取所有飞书记录...")
    page_count = 0
    while True:
        params = {
            'page_size': 500,
            'field_names': '["商品ID","商品链接","商品标题"]'
        }
        if page_token:
            params['page_token'] = page_token

        resp = requests.get(records_url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if data.get('code') != 0:
            print(f"API错误: {data}")
            break

        items = data.get('data', {}).get('items', [])
        for item in items:
            fields = item.get('fields', {})
            record = {
                'record_id': item.get('record_id'),
                'product_id': fields.get('商品ID', '').strip(),
                'url': normalize_url(fields.get('商品链接', '')),
                'title': fields.get('商品标题', '').strip(),
                'has_title': bool(fields.get('商品标题', '').strip())
            }
            all_records.append(record)

        page_count += 1
        print(f"  已获取 {len(all_records)} 条记录 (第 {page_count} 页)")

        page_token = data.get('data', {}).get('page_token')
        if not page_token:
            break
        time.sleep(0.2)

    print(f"\n总共获取 {len(all_records)} 条记录")

    # 按商品ID和URL分组
    by_product_id = defaultdict(list)
    by_url = defaultdict(list)

    for record in all_records:
        if record['product_id']:
            by_product_id[record['product_id']].append(record)
        if record['url']:
            by_url[record['url']].append(record)

    # 找出需要删除的记录
    # 使用 set 防止重复删除
    to_delete = set()
    to_keep = set()

    # 按商品ID去重
    id_duplicates = {pid: recs for pid, recs in by_product_id.items() if len(recs) > 1}
    print(f"\n按商品ID发现 {len(id_duplicates)} 组重复")

    for product_id, records in id_duplicates.items():
        # 优先保留有标题的记录
        records_with_title = [r for r in records if r['has_title']]
        if records_with_title:
            keep = records_with_title[0]
        else:
            keep = records[0]

        to_keep.add(keep['record_id'])
        for r in records:
            if r['record_id'] != keep['record_id']:
                to_delete.add(r['record_id'])

        if args.verbose:
            print(f"  商品ID {product_id}: 保留 {keep['record_id']} (有标题: {keep['has_title']})")

    # 按URL去重
    url_duplicates = {url: recs for url, recs in by_url.items() if len(recs) > 1}
    print(f"按商品链接发现 {len(url_duplicates)} 组重复")

    for url, records in url_duplicates.items():
        # 过滤掉已经标记为删除的
        remaining = [r for r in records if r['record_id'] not in to_delete]
        if len(remaining) <= 1:
            continue

        # 优先保留有标题的记录
        records_with_title = [r for r in remaining if r['has_title']]
        if records_with_title:
            keep = records_with_title[0]
        else:
            keep = remaining[0]

        to_keep.add(keep['record_id'])
        for r in remaining:
            if r['record_id'] != keep['record_id']:
                to_delete.add(r['record_id'])

        if args.verbose:
            print(f"  URL ...{url[-50:]}: 保留 {keep['record_id']} (有标题: {keep['has_title']})")

    print(f"\n需要删除 {len(to_delete)} 条重复记录")

    if not to_delete:
        print("没有重复记录需要删除")
        sys.exit(0)

    # 显示部分删除示例
    delete_list = list(to_delete)
    print("\n将删除的记录ID示例:")
    for rid in delete_list[:10]:
        print(f"  {rid}")
    if len(delete_list) > 10:
        print(f"  ... 还有 {len(delete_list) - 10} 条")

    if not args.apply:
        print("\n这是预览模式，未执行删除。")
        print("如需执行删除，请运行: python3 scripts/dedupe_feishu_records.py --apply")
        sys.exit(0)

    # 执行批量删除
    print("\n开始删除重复记录...")
    delete_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_delete'
    batch_size = 500
    deleted_count = 0

    for i in range(0, len(delete_list), batch_size):
        batch = delete_list[i:i+batch_size]
        payload = {'records': batch}

        resp = requests.post(delete_url, headers=headers, json=payload, timeout=30)
        data = resp.json()

        if data.get('code') == 0:
            deleted_count += len(batch)
            print(f"  已删除 {deleted_count}/{len(delete_list)} 条记录")
        else:
            print(f"  删除失败: {data}")

        time.sleep(0.3)

    print(f"\n完成！共删除 {deleted_count} 条重复记录")


if __name__ == '__main__':
    main()
