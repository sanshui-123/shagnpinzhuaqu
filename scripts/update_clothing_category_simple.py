#!/usr/bin/env python3
"""
飞书衣服分类重新处理脚本 (简化版)

专门用于重新计算和更新飞书表格中的衣服分类字段：
- 只更新"衣服分类"字段
- 保持其他所有字段不变
- 批量处理所有产品记录
- 强制写入更新

使用方法：
    python3 scripts/update_clothing_category_simple.py
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入模块
from feishu_update.services.classifiers import determine_clothing_type
from feishu_update.clients.feishu_client import FeishuClient
from feishu_update.config.settings import resolve_feishu_config_path




def load_feishu_client():
    """加载并创建飞书客户端"""
    config_path = resolve_feishu_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    feishu_config = config['feishu']

    # 创建现有的FeishuClient
    return FeishuClient(
        app_id=feishu_config['app_id'],
        app_secret=feishu_config['app_secret'],
        app_token=feishu_config['app_token'],
        table_id=feishu_config['table_id']
    )


def extract_product_data_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """从飞书记录中提取产品数据用于分类"""
    fields = record.get('fields', {})

    # 提取产品名称
    product_name = ""
    if '商品标题' in fields and fields['商品标题']:
        title_value = fields['商品标题']
        if isinstance(title_value, list) and len(title_value) > 0:
            title_item = title_value[0]
            if isinstance(title_item, dict) and 'text' in title_item:
                product_name = str(title_item['text'])
            else:
                product_name = str(title_item)
        elif isinstance(title_value, dict) and 'text' in title_value:
            product_name = str(title_value['text'])
        else:
            product_name = str(title_value)

    # 提取产品ID
    product_id = ""
    if '产品ID' in fields and fields['产品ID']:
        product_id = str(fields['产品ID'][0]) if isinstance(fields['产品ID'], list) else str(fields['产品ID'])

    # 提取性别信息
    gender = ""
    if '性别' in fields and fields['性别']:
        gender = str(fields['性别'][0]) if isinstance(fields['性别'], list) else str(fields['性别'])

    # 构造用于分类的数据结构
    product_data = {
        'productName': product_name,
        'productId': product_id,
        'category': 'mens_all' if '男' in gender else 'womens_all'
    }

    # 不构造URL，因为构造的URL没有实际分类价值
    # 保持detailUrl为空，让分类器完全基于产品名称进行分类

    return product_data


def main():
    """主函数"""
    print("🚀 飞书衣服分类重新处理工具")
    print("=" * 50)

    # 获取飞书客户端
    try:
        client = load_feishu_client()
        print("✅ 飞书客户端初始化成功")

    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return

    # 读取所有飞书记录
    try:
        print("📥 正在读取飞书记录...")
        records_response = client.get_records()
        all_records = list(records_response.values())
        print(f"✅ 总共读取到 {len(all_records)} 条记录")

        if not all_records:
            print("⚠️  没有找到任何飞书记录，退出")
            return

    except Exception as e:
        print(f"❌ 读取飞书记录失败: {e}")
        return

    # 处理每条记录的衣服分类
    updates = []
    changes_count = 0

    print("\n🔄 开始分析衣服分类...")

    for i, (product_id, record) in enumerate(records_response.items()):
        try:
            record_id = record.get('record_id')
            fields = record.get('fields', {})

            # 获取当前衣服分类
            current_category = ""
            if '衣服分类' in fields and fields['衣服分类']:
                category_value = fields['衣服分类']
                if isinstance(category_value, list) and len(category_value) > 0:
                    # 处理复杂格式：{'text': '外套', 'type': 'text'}
                    category_item = category_value[0]
                    if isinstance(category_item, dict) and 'text' in category_item:
                        current_category = str(category_item['text'])
                    else:
                        current_category = str(category_item)
                elif isinstance(category_value, dict) and 'text' in category_value:
                    current_category = str(category_value['text'])
                else:
                    current_category = str(category_value)

            # 提取产品数据进行分类
            product_data = extract_product_data_from_record(record)

            # 使用新的分类算法
            new_category = determine_clothing_type(product_data)

            # 检查是否需要更新
            if current_category != new_category:
                print(f"📝 记录 {i+1}/{len(all_records)}: '{current_category}' → '{new_category}'")

                # 显示产品信息帮助调试
                product_name = product_data.get('productName', '')[:50]
                if len(product_name) > 50:
                    product_name += "..."
                print(f"    产品: {product_name}")
                print(f"    URL: {product_data.get('detailUrl', 'N/A')}")

                # 构造更新数据（只更新衣服分类字段）
                update_data = {
                    'product_id': product_id,  # 使用product_id作为标识
                    'record_id': record_id,
                    'fields': {
                        '衣服分类': new_category
                    }
                }

                updates.append(update_data)
                changes_count += 1
            else:
                if (i + 1) % 50 == 0 or i == len(all_records) - 1:
                    print(f"⏳ 已处理 {i+1}/{len(all_records)} 条记录，{changes_count} 条需要更新")

        except Exception as e:
            print(f"❌ 处理记录 {i+1} 失败: {e}")
            continue

    print(f"\n📊 分析完成:")
    print(f"   总记录数: {len(all_records)}")
    print(f"   需要更新: {changes_count} 条")
    print(f"   更新比例: {changes_count/len(all_records)*100:.1f}%")

    if not updates:
        print("✅ 所有记录的衣服分类都是最新的，无需更新")
        return

    # 自动确认更新
    print(f"\n🔄 自动确认更新这 {changes_count} 条记录的衣服分类...")

    # 分批更新（每批100条）
    batch_size = 100
    total_updated = 0

    for i in range(0, len(updates), batch_size):
        batch_updates = updates[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(updates) - 1) // batch_size + 1

        print(f"\n🔄 处理批次 {batch_num}/{total_batches}...")

        try:
            # 使用现有的FeishuClient的batch_update方法
            result = client.batch_update(batch_updates, batch_size=batch_size)

            updated_count = result.get('success_count', 0)
            total_updated += updated_count

            if updated_count > 0:
                print(f"✅ 批次 {batch_num} 成功更新 {updated_count} 条记录")
            else:
                print(f"⚠️  批次 {batch_num} 更新失败或无变化")

            # 显示失败详情
            failed_batches = result.get('failed_batches', [])
            if failed_batches:
                print(f"❌ 批次 {batch_num} 失败批次: {len(failed_batches)}")
                for failed_batch in failed_batches[:3]:  # 只显示前3个错误
                    print(f"   错误: {failed_batch.get('error', '未知错误')}")

        except Exception as e:
            print(f"❌ 批次 {batch_num} 处理异常: {e}")

    print(f"\n🎉 处理完成！")
    print(f"   总计更新: {total_updated} 条记录")
    print(f"   成功率: {total_updated/changes_count*100:.1f}%" if changes_count > 0 else "N/A")


if __name__ == "__main__":
    main()