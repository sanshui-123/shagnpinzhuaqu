#!/usr/bin/env python3
"""
测试飞书字段名称
"""

import os
import sys
from pathlib import Path

# 加载环境变量
env_file = Path("callaway.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, '.')

import requests

def test_feishu_fields():
    """测试哪些字段名是有效的"""
    print("=== 测试飞书字段名称 ===")
    print()

    # 获取配置
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    app_token = os.environ.get('FEISHU_APP_TOKEN')
    table_id = os.environ.get('FEISHU_TABLE_ID')

    # 获取access_token
    print("获取飞书access_token...")
    access_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    payload = {"app_id": app_id, "app_secret": app_secret}

    response = requests.post(access_url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            access_token = data.get('tenant_access_token')
            print("✅ access_token获取成功")
        else:
            print(f"❌ 获取token失败: {data}")
            return
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    # 获取表格字段信息
    print("\n获取表格字段信息...")
    fields_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(fields_url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            fields = data.get('data', {}).get('items', [])
            print(f"✅ 找到 {len(fields)} 个字段:")

            field_names = []
            for field in fields:
                field_name = field.get('field_name', '')
                field_names.append(field_name)
                print(f"   - {field_name}")

            return field_names
        else:
            print(f"❌ 获取字段失败: {data}")
            return []
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return []

if __name__ == "__main__":
    fields = test_feishu_fields()

    if fields:
        print(f"\n📊 可用字段总数: {len(fields)}")
        print("请确认这13个字段是否都存在:")

        required_fields = [
            "商品链接", "商品ID", "商品标题", "品牌名", "价格",
            "性别", "服装分类", "图片总数", "图片链接",
            "颜色", "尺码", "详情页文字", "尺码表"
        ]

        for field in required_fields:
            if field in fields:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - 不存在!")
                # 提供相似字段名建议
                suggestions = []
                for f in fields:
                    if field in f or f in field:
                        suggestions.append(f)
                if suggestions:
                    print(f"      建议使用: {suggestions[:3]}")

if __name__ == "__main__":
    test_feishu_fields()