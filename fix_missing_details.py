#!/usr/bin/env python3
"""
修复飞书中缺失的详细字段
重新抓取产品的详细信息并更新到飞书
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "feishu_update"))

try:
    from feishu_update.clients.feishu_client import FeishuClient
    from feishu_update.services.detail_scraper import DetailScraper
    from feishu_update.services.content_generator import ContentGenerator
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def load_env_file(env_file: str = "callaway.env"):
    """加载环境变量文件"""
    env_path = project_root / env_file
    if env_path.exists():
        print(f"📄 加载环境变量文件: {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"⚠️  环境变量文件不存在: {env_path}")

def get_feishu_records_needing_update(feishu_client: FeishuClient) -> List[Dict]:
    """获取需要更新的记录（缺失详细字段的记录）"""
    print("🔍 正在获取需要更新的记录...")

    try:
        records_dict = feishu_client.get_records()
        print(f"✅ 总共读取到 {len(records_dict)} 条记录")

        # 需要检查的字段
        required_fields = ['图片URL', '图片数量', '尺码表', '详情页文字']
        records_needing_update = []

        for product_id, record_info in records_dict.items():
            record_id = record_info['record_id']
            fields = record_info['fields']

            # 检查是否缺失关键字段
            missing_fields = []
            for field_name in required_fields:
                if field_name not in fields:
                    missing_fields.append(field_name)
                else:
                    value = fields[field_name]
                    if isinstance(value, list) and (not value or (len(value) == 1 and str(value[0]).strip() == '')):
                        missing_fields.append(field_name)
                    elif str(value).strip() == '':
                        missing_fields.append(field_name)

            if missing_fields:
                records_needing_update.append({
                    'product_id': product_id,
                    'record_id': record_id,
                    'fields': fields,
                    'missing_fields': missing_fields
                })

        print(f"📊 需要更新的记录: {len(records_needing_update)} 条")
        return records_needing_update

    except Exception as e:
        print(f"❌ 获取记录失败: {e}")
        return []

def extract_product_url_from_record(fields: Dict[str, Any]) -> str:
    """从飞书记录中提取产品链接"""
    detail_url = fields.get('商品链接', '')
    if isinstance(detail_url, list) and detail_url:
        return str(detail_url[0])
    return str(detail_url) if detail_url else ''

def fix_missing_details():
    """修复缺失的详细字段"""
    print("🚀 开始修复飞书中的缺失字段...")
    print("=" * 50)

    # 加载环境变量
    load_env_file()

    # 创建飞书客户端
    try:
        app_id = os.getenv('FEISHU_APP_ID')
        app_secret = os.getenv('FEISHU_APP_SECRET')
        app_token = os.getenv('FEISHU_APP_TOKEN')
        table_id = os.getenv('FEISHU_TABLE_ID')

        if not all([app_id, app_secret, app_token, table_id]):
            print("❌ 请设置环境变量")
            return

        feishu_client = FeishuClient(
            app_id=app_id,
            app_secret=app_secret,
            app_token=app_token,
            table_id=table_id
        )

        print("✅ 飞书客户端初始化成功")

    except Exception as e:
        print(f"❌ 配置或客户端初始化失败: {e}")
        return

    # 创建详情抓取器和内容生成器
    detail_scraper = DetailScraper()
    content_generator = ContentGenerator()

    # 获取需要更新的记录
    records_needing_update = get_feishu_records_needing_update(feishu_client)

    if not records_needing_update:
        print("✅ 所有记录的详细字段都已完整，无需更新")
        return

    # 批量处理记录
    batch_size = 10
    total_updated = 0
    total_failed = 0

    for i in range(0, len(records_needing_update), batch_size):
        batch = records_needing_update[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(records_needing_update) - 1) // batch_size + 1

        print(f"\n🔄 处理批次 {batch_num}/{total_batches} ({len(batch)} 条记录)...")

        updates = []

        for record in batch:
            try:
                product_id = record['product_id']
                record_id = record['record_id']
                fields = record['fields']
                missing_fields = record['missing_fields']

                print(f"📦 处理产品: {product_id}")

                # 获取产品链接
                detail_url = extract_product_url_from_record(fields)
                if not detail_url:
                    print(f"⚠️  产品 {product_id} 没有商品链接，跳过")
                    total_failed += 1
                    continue

                print(f"🔍 抓取详情: {detail_url}")

                # 抓取产品详情
                detail_data = detail_scraper.scrape_product_detail(detail_url, product_id)

                if not detail_data:
                    print(f"❌ 产品 {product_id} 详情抓取失败")
                    total_failed += 1
                    continue

                # 生成翻译内容
                if detail_data.get('description'):
                    try:
                        print(f"🔄 翻译描述...")
                        translated_content = content_generator.translate_description(
                            detail_data['description'],
                            product_id,
                            detail_url
                        )
                        detail_data['translated_description'] = translated_content
                    except Exception as e:
                        print(f"⚠️  产品 {product_id} 翻译失败: {e}")
                        detail_data['translated_description'] = detail_data['description']

                # 构造更新数据
                update_fields = {}

                # 添加缺失的详细字段
                if '图片URL' in missing_fields and detail_data.get('images'):
                    update_fields['图片URL'] = '\\n'.join(detail_data['images'])
                    update_fields['图片数量'] = len(detail_data['images'])

                if '尺码表' in missing_fields and detail_data.get('size_chart'):
                    update_fields['尺码表'] = detail_data['size_chart']

                if '详情页文字' in missing_fields and detail_data.get('translated_description'):
                    update_fields['详情页文字'] = detail_data['translated_description']

                if update_fields:
                    update_data = {
                        'record_id': record_id,
                        'fields': update_fields
                    }
                    updates.append(update_data)
                    print(f"✅ 产品 {product_id} 准备更新: {', '.join(update_fields.keys())}")
                else:
                    print(f"⚠️  产品 {product_id} 没有可更新的字段")

                # 添加延迟避免请求过于频繁
                time.sleep(1)

            except Exception as e:
                print(f"❌ 处理产品 {product_id} 失败: {e}")
                total_failed += 1
                continue

        # 批量更新到飞书
        if updates:
            try:
                print(f"📤 批量更新 {len(updates)} 条记录到飞书...")
                response = feishu_client.batch_update(updates, batch_size=len(updates))

                success_count = response.get('success_count', 0)
                failed_count = response.get('failed_count', 0)

                total_updated += success_count
                total_failed += failed_count

                print(f"✅ 批次 {batch_num} 完成: 成功 {success_count} 条, 失败 {failed_count} 条")

            except Exception as e:
                print(f"❌ 批次 {batch_num} 更新失败: {e}")
                total_failed += len(updates)

        # 添加批次间延迟
        if i + batch_size < len(records_needing_update):
            print("⏳ 等待 5 秒后继续下一批次...")
            time.sleep(5)

    print(f"\n🎉 修复完成！")
    print(f"   总记录数: {len(records_needing_update)}")
    print(f"   成功更新: {total_updated} 条")
    print(f"   更新失败: {total_failed} 条")
    print(f"   成功率: {total_updated/len(records_needing_update)*100:.1f}%" if records_needing_update else "N/A")

if __name__ == "__main__":
    fix_missing_details()