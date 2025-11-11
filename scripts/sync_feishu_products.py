#!/usr/bin/env python3
"""
飞书同步脚本 - 增量同步产品数据
读取 all_products_dedup.json 并仅同步缺失的记录

新增功能:
- 飞书ID缓存机制: 缓存现有商品ID，有效期30分钟，避免重复API调用
- 缓存文件: CallawayJP/results/feishu_id_cache.json
- 缓存字段: fetchedAt (ISO时间戳), ids (商品ID列表)

新增参数:
- --refresh-cache: 强制跳过缓存重新拉取飞书ID

示例命令:
python3 sync_feishu_products.py --input all_products_dedup_*.json
python3 sync_feishu_products.py --input all_products_dedup_*.json --refresh-cache  # 强制刷新缓存
"""

import json
import math
import requests
from pathlib import Path
import time
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feishu_update.config.settings import resolve_feishu_config_path

def load_config():
    """加载飞书配置"""
    config_path = resolve_feishu_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config['feishu']

def get_token(app_id, app_secret):
    """获取飞书访问令牌"""
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    resp = requests.post(url, json={'app_id': app_id, 'app_secret': app_secret}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(f"failed to get token: {data}")
    return data['tenant_access_token']

def load_feishu_id_cache(cache_file: Path, cache_validity_minutes: int = 30) -> Set[str]:
    """
    加载飞书ID缓存
    
    Args:
        cache_file: 缓存文件路径
        cache_validity_minutes: 缓存有效期（分钟）
    
    Returns:
        Set[str]: 缓存的商品ID集合，如果缓存失效或不存在则返回空集合
    """
    if not cache_file.exists():
        return set()
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查缓存是否在有效期内
        fetched_at_str = cache_data.get('fetchedAt', '')
        if fetched_at_str:
            fetched_at = datetime.fromisoformat(fetched_at_str.replace('Z', '+00:00'))
            now = datetime.now(fetched_at.tzinfo)
            age_minutes = (now - fetched_at).total_seconds() / 60
            
            if age_minutes <= cache_validity_minutes:
                ids = set(cache_data.get('ids', []))
                print(f"🔄 缓存命中: 加载 {len(ids)} 个商品ID (缓存时间: {age_minutes:.1f}分钟前)")
                return ids
            else:
                print(f"⏰ 缓存失效: 缓存时间 {age_minutes:.1f}分钟 > 有效期 {cache_validity_minutes}分钟")
        
    except Exception as e:
        print(f"⚠️  缓存读取失败: {e}")
    
    return set()

def save_feishu_id_cache(cache_file: Path, ids: Set[str]):
    """
    保存飞书ID缓存
    
    Args:
        cache_file: 缓存文件路径
        ids: 商品ID集合
    """
    try:
        cache_data = {
            'fetchedAt': datetime.now().isoformat() + 'Z',
            'ids': list(ids)
        }
        
        # 确保目录存在
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 缓存已更新: {len(ids)} 个商品ID")
        
    except Exception as e:
        print(f"⚠️  缓存保存失败: {e}")

def get_existing_records(app_token: str, table_id: str, token: str) -> Set[str]:
    """获取飞书表中现有的所有商品ID"""
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    existing_ids = set()
    page_token = None
    
    while True:
        params = {
            'page_size': 500,
            'field_names': '["商品ID"]'
        }
        if page_token:
            params['page_token'] = page_token
        
        # 使用重试机制
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                
                if data.get('code') != 0:
                    break
                
                # 提取商品ID
                items = data.get('data', {}).get('items', [])
                existing_ids.update(
                    item.get('fields', {}).get('商品ID')
                    for item in items
                    if item.get('fields', {}).get('商品ID')
                )
                
                page_token = data.get('data', {}).get('page_token')
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(2 ** attempt)  # 指数退避
        
        if not page_token:
            break
        
        time.sleep(0.2)
    
    return existing_ids

def get_existing_records_with_cache(app_token: str, table_id: str, token: str, 
                                   cache_file: Path, refresh_cache: bool = False) -> Set[str]:
    """
    获取飞书表中现有的所有商品ID（支持缓存）
    
    Args:
        app_token: 飞书应用token
        table_id: 飞书表ID
        token: 访问token
        cache_file: 缓存文件路径
        refresh_cache: 是否强制刷新缓存
    
    Returns:
        Set[str]: 现有商品ID集合
    """
    if not refresh_cache:
        # 尝试加载缓存
        cached_ids = load_feishu_id_cache(cache_file)
        if cached_ids:
            return cached_ids
    
    # 缓存失效或强制刷新，从飞书API获取
    print("🔄 从飞书API获取商品ID...")
    existing_ids = get_existing_records(app_token, table_id, token)
    
    # 保存到缓存
    save_feishu_id_cache(cache_file, existing_ids)
    
    return existing_ids

def batch_create_with_retry(app_token: str, table_id: str, token: str, records: List[Dict]) -> int:
    """带重试机制的批量创建"""
    url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {'records': records}
    
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('code') != 0:
                raise RuntimeError(f"API error: {data}")
            
            return len(records)
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(2 ** attempt)  # 指数退避
    
    return 0

def find_latest_dedup_file(results_dir: Path) -> Path:
    """查找最新的去重文件"""
    # 使用 Path.glob 获取所有去重文件
    dedup_files = list(results_dir.glob('all_products_dedup*.json'))
    
    if not dedup_files:
        # 如果没有找到带时间戳的文件，检查默认文件
        old_file = results_dir / 'all_products_dedup.json'
        if old_file.exists():
            return old_file
        raise FileNotFoundError("未找到去重数据文件")
    
    # 按文件修改时间排序，返回最新的
    return max(dedup_files, key=lambda f: f.stat().st_mtime)

def main():
    parser = argparse.ArgumentParser(description='增量同步 CallawayJP 产品到飞书')
    parser.add_argument('--input', type=str, help='指定输入文件路径')
    parser.add_argument('--refresh-cache', action='store_true', help='强制跳过缓存重新拉取飞书商品ID')
    args = parser.parse_args()
    
    # 加载去重后的产品数据
    results_dir = Path(__file__).parent.parent / 'results'
    
    try:
        if args.input:
            dedup_file = Path(args.input)
        else:
            dedup_file = find_latest_dedup_file(results_dir)
        
        with open(dedup_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        
        all_products = products_data['products']
    except Exception as e:
        print(f"✗ 数据加载失败: {e}")
        return
    
    # 获取飞书配置和令牌
    try:
        feishu = load_config()
        token = get_token(feishu['app_id'], feishu['app_secret'])
    except Exception as e:
        print(f"✗ 认证失败: {e}")
        return
    
    # 获取飞书现有记录（支持缓存）
    cache_file = results_dir / 'feishu_id_cache.json'
    try:
        existing_ids = get_existing_records_with_cache(
            feishu['app_token'], feishu['table_id'], token, 
            cache_file, args.refresh_cache
        )
    except Exception as e:
        print(f"✗ 获取现有记录失败: {e}")
        return
    
    # 筛选出新产品
    new_products = [p for p in all_products if p['productId'] not in existing_ids]
    
    if not new_products:
        print("✓ 无新产品，跳过同步")
        return
    
    # 批量同步新产品
    batch_size = 30
    success_count = 0
    failed_batches = []
    
    total_batches = math.ceil(len(new_products) / batch_size)
    
    for i in range(total_batches):
        chunk = new_products[i * batch_size:(i + 1) * batch_size]
        records = [
            {
                'fields': {
                    '商品ID': item['productId'],
                    '商品链接': item['detailUrl']
                }
            }
            for item in chunk
        ]
        
        try:
            batch_success = batch_create_with_retry(
                feishu['app_token'], feishu['table_id'], token, records
            )
            success_count += batch_success
        except Exception as e:
            failed_batches.append({'batch': i + 1, 'error': str(e)})
        
        time.sleep(0.5)
    
    # 更新缓存（如果有成功同步的记录）
    if success_count > 0:
        # 将新同步成功的商品ID添加到缓存中
        successfully_synced_ids = [p['productId'] for p in new_products[:success_count]]
        updated_ids = existing_ids.union(set(successfully_synced_ids))
        save_feishu_id_cache(cache_file, updated_ids)
    
    # 保存详细同步日志
    log_dir = Path(__file__).parent.parent / 'sync_logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%fZ')[:-3] + 'Z'
    log_file = log_dir / f'sync_result_{timestamp}.json'
    
    log_data = {
        'syncedAt': datetime.now().isoformat(),
        'inputFile': str(dedup_file),
        'totalLocal': len(all_products),
        'existingInFeishu': len(existing_ids),
        'newProductsFound': len(new_products),
        'successCount': success_count,
        'failedBatches': failed_batches,
        'totalBatches': total_batches,
        'batchSize': batch_size
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    # 最小化控制台输出
    print(f"✓ 同步完成: {success_count}/{len(new_products)} 条")
    print(f"✓ 日志文件: {log_file}")
    
    return log_file

if __name__ == '__main__':
    main()
