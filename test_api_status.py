#!/usr/bin/env python3
"""
测试API可用性脚本
"""

import os
import requests
import json

def test_glm_api():
    """测试GLM API"""
    print("=== GLM API 测试 ===")

    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("❌ ZHIPU_API_KEY 未设置")
        return False

    print(f"✅ API Key: {api_key[:10]}...")

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 测试标题生成
    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": "生成标题：25秋冬Le Coq Sportif Golf男士弹力Polo衫"}],
        "temperature": 0.3,
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and data['choices']:
                content = data['choices'][0]['message']['content']
                print(f"✅ GLM API 正常工作")
                print(f"   生成结果: {content}")
                return True
        else:
            print(f"❌ GLM API 错误: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ GLM API 异常: {e}")
        return False

def test_feishu_api():
    """测试飞书API"""
    print("\n=== 飞书API 测试 ===")

    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    app_token = os.environ.get('FEISHU_APP_TOKEN')
    table_id = os.environ.get('FEISHU_TABLE_ID')

    if not all([app_id, app_secret, app_token, table_id]):
        print("❌ 飞书配置不完整")
        print(f"   FEISHU_APP_ID: {app_id}")
        print(f"   FEISHU_APP_SECRET: {app_secret[:10] if app_secret else 'None'}...")
        print(f"   FEISHU_APP_TOKEN: {app_token[:10] if app_token else 'None'}...")
        print(f"   FEISHU_TABLE_ID: {table_id}")
        return False

    print("✅ 飞书配置完整")

    # 1. 获取access_token
    auth_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    auth_payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    try:
        response = requests.post(auth_url, json=auth_payload, timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            if auth_data.get('code') == 0:
                access_token = auth_data.get('tenant_access_token')
                print(f"✅ 获取access_token成功: {access_token[:20]}...")

                # 2. 测试读取表格数据
                records_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=1"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }

                response = requests.get(records_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == 0:
                        total = data.get('data', {}).get('total', 0)
                        print(f"✅ 飞书API正常，表格总记录数: {total}")
                        return True
                    else:
                        print(f"❌ 飞书表格读取错误: {data}")
                        return False
                else:
                    print(f"❌ 飞书API请求错误: {response.status_code} - {response.text}")
                    return False
            else:
                print(f"❌ 获取access_token失败: {auth_data}")
                return False
        else:
            print(f"❌ 飞书认证请求错误: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 飞书API异常: {e}")
        return False

if __name__ == "__main__":
    # 加载环境变量
    from pathlib import Path

    env_file = Path("callaway.env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ 加载callaway.env配置")
    else:
        print("❌ 找不到callaway.env文件")

    glm_ok = test_glm_api()
    feishu_ok = test_feishu_api()

    print(f"\n=== 测试总结 ===")
    print(f"GLM API: {'✅ 正常' if glm_ok else '❌ 异常'}")
    print(f"飞书API: {'✅ 正常' if feishu_ok else '❌ 异常'}")

    if glm_ok and feishu_ok:
        print("🎉 所有API都正常工作！")
    else:
        print("⚠️ 部分API存在问题，请检查配置")