#!/usr/bin/env python3
"""
真正的飞书API数据同步
"""

import sys
import os
sys.path.append('/Users/sanshui/Desktop/CallawayJP')

import json
import requests
from datetime import datetime

def sync_to_feishu():
    """真正同步到飞书"""
    print("🔄 Step 3: 真正的飞书API数据同步...")

    # 设置环境变量
    os.environ['FEISHU_TABLE_ID'] = 'tblhBepAOlCyhfoN'

    try:
        # 读取准备好的飞书数据
        with open('/Users/sanshui/Desktop/CallawayJP/feishu_ready.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        records = data.get('records', [])
        if not records:
            print("❌ 未找到飞书同步数据")
            return False

        record = records[0]
        fields = record.get('fields', {})

        print("📊 飞书同步数据验证:")
        print(f"  - 商品标题: {fields.get('商品标题', 'N/A')[:30]}...")
        print(f"  - 性别字段: {fields.get('性别', 'N/A')}")
        print(f"  - 品牌: {fields.get('品牌', 'N/A')}")

        # 获取飞书access_token
        print("🔄 获取飞书access_token...")

        # 飞书配置
        app_id = "cli_a123b3c45d789f0a"  # 需要替换为真实的APP_ID
        app_secret = "your_app_secret"  # 需要替换为真实的APP_SECRET

        # 尝试从环境变量获取
        app_id = os.getenv('FEISHU_APP_ID', app_id)
        app_secret = os.getenv('FEISHU_APP_SECRET', app_secret)

        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        token_response = requests.post(token_url, json={
            "app_id": app_id,
            "app_secret": app_secret
        })

        if token_response.status_code != 200:
            print(f"❌ 获取access_token失败: {token_response.status_code}")
            print(f"响应: {token_response.text}")
            return False

        token_data = token_response.json()
        if token_data.get('code') != 0:
            print(f"❌ access_token API错误: {token_data}")
            return False

        access_token = token_data.get('tenant_access_token')
        print("✅ access_token获取成功")

        # 构建飞书API调用
        table_id = os.getenv('FEISHU_TABLE_ID', 'tblhBepAOlCyhfoN')
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{table_id}/tables/tbldataXXXX/records/batch_create"

        # 准备请求数据 - 简化字段避免字段不存在错误
        simplified_fields = {
            "商品标题": fields.get('商品标题', ''),
            "品牌": fields.get('品牌', ''),
            "性别": fields.get('性别', ''),
            "价格": fields.get('价格', ''),
            "商品编号": fields.get('商品编号', ''),
            "详情页链接": fields.get('详情页链接', ''),
            "颜色选项": fields.get('颜色选项', ''),
            "尺寸选项": fields.get('尺寸选项', ''),
            "状态": fields.get('状态', '')
        }

        # 移除空值字段
        simplified_fields = {k: v for k, v in simplified_fields.items() if v}

        request_data = {
            "records": [
                {
                    "fields": simplified_fields
                }
            ]
        }

        print(f"🔄 调用飞书API...")
        print(f"URL: {url}")
        print(f"字段数量: {len(simplified_fields)}")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=request_data, headers=headers)

        print(f"📊 飞书API响应状态: {response.status_code}")
        print(f"📋 飞书API响应: {response.text}")

        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 飞书数据同步成功！")
                record_id = result.get('data', {}).get('records', [{}])[0].get('record_id')
                print(f"📝 记录ID: {record_id}")

                # 验证性别字段
                gender = simplified_fields.get('性别', '')
                if gender == '女':
                    print(f"✅ 性别字段验证成功: {gender}")
                    return True
                else:
                    print(f"❌ 性别字段错误: {gender}")
                    return False
            else:
                print(f"❌ 飞书API业务错误: {result}")
                return False
        else:
            print(f"❌ 飞书API HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 飞书同步异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始真正的飞书API同步")

    # 检查环境变量
    if not os.getenv('FEISHU_TABLE_ID'):
        print("⚠️ 未设置FEISHU_TABLE_ID环境变量，使用默认值")

    success = sync_to_feishu()

    if success:
        print("\\n🎉 飞书同步成功！")
        print("✅ 数据已写入飞书多维表格")
        print("✅ 性别字段正确显示")
    else:
        print("\\n❌ 飞书同步失败")
        print("💡 请检查飞书API配置和权限")