#!/usr/bin/env python3
"""
检查飞书数据中的空字段
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "feishu_update"))

try:
    from feishu_update.clients.feishu_client import FeishuClient
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

def check_empty_fields():
    """检查飞书数据中的空字段"""
    print("🔍 正在检查飞书数据中的空字段...")

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

    # 获取所有记录
    try:
        records_dict = feishu_client.get_records()
        print(f"✅ 总共读取到 {len(records_dict)} 条记录")
    except Exception as e:
        print(f"❌ 读取记录失败: {e}")
        return

    # 检查空字段
    empty_fields_stats = {}
    problem_records = []

    # 需要检查的字段
    fields_to_check = [
        '商品标题', '商品ID', '价格', '商品链接', '性别',
        '衣服分类', '品牌名', '颜色', '尺码', '图片URL',
        '图片数量', '尺码表', '详情页文字'
    ]

    for product_id, record_info in records_dict.items():
        record_id = record_info['record_id']
        fields = record_info['fields']

        empty_fields = []
        missing_fields = []

        for field_name in fields_to_check:
            if field_name not in fields:
                missing_fields.append(field_name)
            else:
                value = fields[field_name]
                if isinstance(value, list):
                    if not value or (len(value) == 1 and str(value[0]).strip() == ''):
                        empty_fields.append(field_name)
                elif str(value).strip() == '':
                    empty_fields.append(field_name)

        # 记录问题
        if empty_fields or missing_fields:
            problem_records.append({
                'product_id': product_id,
                'record_id': record_id,
                'empty_fields': empty_fields,
                'missing_fields': missing_fields,
                'fields': fields
            })

            # 统计空字段
            for field in empty_fields:
                empty_fields_stats[field] = empty_fields_stats.get(field, 0) + 1
            for field in missing_fields:
                empty_fields_stats[field] = empty_fields_stats.get(field, 0) + 1

    # 输出结果
    print(f"\n📊 空字段统计:")
    if empty_fields_stats:
        for field, count in sorted(empty_fields_stats.items()):
            print(f"   {field}: {count} 条记录")
    else:
        print("   ✅ 没有发现空字段")

    print(f"\n🚨 问题记录总数: {len(problem_records)}")

    if problem_records:
        print(f"\n📋 问题记录详情 (前10条):")
        for i, record in enumerate(problem_records[:10]):
            print(f"\n{i+1}. 商品ID: {record['product_id']}")
            if record['empty_fields']:
                print(f"   空字段: {', '.join(record['empty_fields'])}")
            if record['missing_fields']:
                print(f"   缺失字段: {', '.join(record['missing_fields'])}")

            # 显示一些关键字段的值
            fields = record['fields']
            title = fields.get('商品标题', [''])[0] if fields.get('商品标题') else ''
            category = fields.get('衣服分类', [''])[0] if fields.get('衣服分类') else ''
            image_count = fields.get('图片数量', [''])[0] if fields.get('图片数量') else ''

            if title:
                print(f"   标题: {title[:50]}{'...' if len(title) > 50 else ''}")
            if category:
                print(f"   分类: {category}")
            if image_count:
                print(f"   图片数量: {image_count}")

        if len(problem_records) > 10:
            print(f"\n... 还有 {len(problem_records) - 10} 条问题记录")

    return problem_records

if __name__ == "__main__":
    check_empty_fields()