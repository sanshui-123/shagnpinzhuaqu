#!/usr/bin/env python3
"""
飞书衣服分类重新处理脚本

专门用于重新计算和更新飞书表格中的衣服分类字段：
- 只更新"衣服分类"字段
- 保持其他所有字段不变
- 批量处理所有产品记录
- 强制写入更新

使用方法：
    python scripts/update_clothing_category_only.py
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "feishu_update"))

# 导入模块
try:
    from feishu_update.clients.feishu_client import FeishuClient
    from feishu_update.services.classifiers import determine_clothing_type
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path[:3]}")
    sys.exit(1)


def load_feishu_records(feishu_client: FeishuClient) -> Dict[str, Dict]:
    """加载所有飞书记录"""
    print("📥 正在读取飞书记录...")

    try:
        records_dict = feishu_client.get_records()

        # 将字典转换为列表格式，方便处理
        all_records = []
        for product_id, record_info in records_dict.items():
            record = {
                'record_id': record_info['record_id'],
                'fields': record_info['fields']
            }
            all_records.append(record)

        print(f"✅ 总共读取到 {len(all_records)} 条记录")
        return records_dict, all_records

    except Exception as e:
        print(f"❌ 读取记录失败: {e}")
        return {}, []


def extract_product_data_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """从飞书记录中提取产品数据用于分类"""
    fields = record.get('fields', {})

    # 辅助函数：安全地获取字段值
    def get_field_value(field_name: str) -> str:
        value = fields.get(field_name, '')
        if isinstance(value, list) and value:
            return str(value[0])
        return str(value) if value else ''

    # 提取产品名称
    product_name = get_field_value('商品标题')

    # 提取产品ID相关信息
    product_id = get_field_value('商品ID')  # 注意是'商品ID'不是'产品ID'

    # 尝试从其他字段获取更多信息
    brand = get_field_value('品牌名')

    # 提取商品链接
    detail_url = get_field_value('商品链接')

    # 从商品链接推断性别，如果没有则从性别字段获取
    gender = get_field_value('性别').lower()
    category = ''
    if '/mens/' in detail_url.lower():
        category = 'mens'
    elif '/womens/' in detail_url.lower():
        category = 'womens'
    elif '男' in gender:
        category = 'mens'
    elif '女' in gender:
        category = 'womens'

    # 构造用于分类的数据结构
    product_data = {
        'productName': product_name,
        'productId': product_id,
        'brand': brand,
        'category': category,
        'detailUrl': detail_url
    }

    return product_data


def update_clothing_category_batch(feishu_client: FeishuClient, updates: List[Dict[str, Any]]) -> int:
    """批量更新衣服分类"""
    if not updates:
        return 0

    print(f"🔄 正在批量更新 {len(updates)} 条记录的衣服分类...")

    try:
        response = feishu_client.batch_update(updates, batch_size=len(updates))

        success_count = response.get('success_count', 0)
        failed_count = response.get('failed_count', 0)

        print(f"✅ 成功更新 {success_count} 条记录")
        if failed_count > 0:
            print(f"⚠️  失败 {failed_count} 条记录")

        return success_count

    except Exception as e:
        print(f"❌ 批量更新异常: {e}")
        return 0


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


def main():
    """主函数"""
    print("🚀 飞书衣服分类重新处理工具")
    print("=" * 50)

    # 加载环境变量
    load_env_file()

    # 从环境变量或直接配置创建飞书客户端
    try:
        # 检查环境变量
        app_id = os.getenv('FEISHU_APP_ID')
        app_secret = os.getenv('FEISHU_APP_SECRET')
        app_token = os.getenv('FEISHU_APP_TOKEN')
        table_id = os.getenv('FEISHU_TABLE_ID')

        if not all([app_id, app_secret, app_token, table_id]):
            print("❌ 请设置环境变量:")
            print("   FEISHU_APP_ID")
            print("   FEISHU_APP_SECRET")
            print("   FEISHU_APP_TOKEN")
            print("   FEISHU_TABLE_ID")
            return

        # 创建飞书客户端
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

    # 读取所有飞书记录
    try:
        records_dict, all_records = load_feishu_records(feishu_client)

        if not all_records:
            print("⚠️  没有找到任何飞书记录，退出")
            return

    except Exception as e:
        print(f"❌ 读取飞书记录失败: {e}")
        return

    # 统计现有数据
    print(f"\n📊 现有记录统计:")
    print(f"   总记录数: {len(all_records)}")

    # 统计性别分布
    gender_stats = {}
    clothing_stats = {}

    for record in all_records:
        fields = record.get('fields', {})

        # 安全地获取字段值
        def get_field_value(field_name: str) -> str:
            value = fields.get(field_name, '')
            if isinstance(value, list) and value:
                return str(value[0])
            return str(value) if value else ''

        gender = get_field_value('性别')
        clothing = get_field_value('衣服分类')

        gender_stats[gender] = gender_stats.get(gender, 0) + 1
        clothing_stats[clothing] = clothing_stats.get(clothing, 0) + 1

    print(f"   性别分布: {gender_stats}")
    print(f"   服装分类分布: {clothing_stats}")

    # 处理每条记录的衣服分类
    updates = []
    changes_count = 0

    print("\n🔄 开始分析衣服分类...")

    for i, record in enumerate(all_records):
        try:
            record_id = record.get('record_id')
            fields = record.get('fields', {})

            # 辅助函数：安全地获取字段值
            def get_field_value(field_name: str) -> str:
                value = fields.get(field_name, '')
                if isinstance(value, list) and value:
                    return str(value[0])
                return str(value) if value else ''

            # 获取当前衣服分类
            current_category = get_field_value('衣服分类')

            # 提取产品数据进行分类
            product_data = extract_product_data_from_record(record)

            # 使用新的分类算法
            new_category = determine_clothing_type(product_data)

            # 检查是否需要更新
            if current_category != new_category:
                print(f"📝 记录 {i+1}/{len(all_records)}: {current_category} → {new_category}")

                # 构造更新数据（只更新衣服分类字段）
                update_data = {
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

    # 确认更新 - 自动确认
    print(f"\n🔄 自动确认更新这 {changes_count} 条记录的衣服分类...")

    # 分批更新（每批100条）
    batch_size = 100
    total_updated = 0

    for i in range(0, len(updates), batch_size):
        batch_updates = updates[i:i + batch_size]

        print(f"\n🔄 处理批次 {i//batch_size + 1}/{(len(updates)-1)//batch_size + 1}...")

        try:
            updated_count = update_clothing_category_batch(feishu_client, batch_updates)
            total_updated += updated_count

            if updated_count == 0:
                print(f"⚠️  批次 {i//batch_size + 1} 更新失败，跳过")

        except Exception as e:
            print(f"❌ 批次 {i//batch_size + 1} 处理异常: {e}")

    print(f"\n🎉 处理完成！")
    print(f"   总计更新: {total_updated} 条记录")
    print(f"   成功率: {total_updated/changes_count*100:.1f}%" if changes_count > 0 else "N/A")


if __name__ == "__main__":
    main()