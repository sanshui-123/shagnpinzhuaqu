#!/usr/bin/env python3
"""
检查环境变量加载情况
"""

import os
import sys
from pathlib import Path

def check_env_loading():
    """检查环境变量是否正确加载"""
    print("=== 环境变量加载检查 ===")
    print()

    # 1. 检查callaway.env文件是否存在
    env_file = Path("callaway.env")
    print(f"1. callaway.env文件: {'✅ 存在' if env_file.exists() else '❌ 不存在'}")

    if env_file.exists():
        print(f"   文件路径: {env_file.absolute()}")
        print(f"   文件大小: {env_file.stat().st_size}字节")
    print()

    # 2. 手动加载环境变量
    print("2. 手动加载环境变量...")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    if 'API_KEY' in key or 'SECRET' in key:
                        print(f"   行{line_num}: {key} = {value[:10]}...")
                    else:
                        print(f"   行{line_num}: {key} = {value}")
    print()

    # 3. 检查关键环境变量
    print("3. 检查关键环境变量:")
    critical_vars = [
        'ZHIPU_API_KEY',
        'ZHIPU_MODEL',
        'ZHIPU_TITLE_MODEL',
        'FEISHU_APP_ID',
        'FEISHU_APP_SECRET',
        'FEISHU_APP_TOKEN',
        'FEISHU_TABLE_ID'
    ]

    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            if 'API_KEY' in var or 'SECRET' in var:
                print(f"   ✅ {var}: {value[:10]}...")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: 未设置")
    print()

    # 4. 测试GLM API连接
    print("4. 测试GLM API连接:")
    api_key = os.environ.get('ZHIPU_API_KEY')
    if api_key:
        print(f"   API Key: {api_key[:10]}...")

        import requests

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": "测试"}],
            "temperature": 0.3,
            "max_tokens": 10
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ GLM API连接成功 (状态码: {response.status_code})")
            else:
                print(f"   ❌ GLM API连接失败 (状态码: {response.status_code})")
                print(f"   错误: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ GLM API连接异常: {e}")
    else:
        print("   ❌ 缺少ZHIPU_API_KEY")
    print()

    # 5. 测试Callaway13FieldProcessor初始化
    print("5. 测试Callaway13FieldProcessor初始化:")
    try:
        sys.path.insert(0, '.')
        from callaway_13field_processor import Callaway13FieldProcessor

        processor = Callaway13FieldProcessor()
        print("   ✅ Callaway13FieldProcessor初始化成功")

        # 检查API密钥在处理器中的访问
        processor_key = os.environ.get('ZHIPU_API_KEY')
        if processor_key:
            print(f"   ✅ 处理器中API Key可访问: {processor_key[:10]}...")
        else:
            print("   ❌ 处理器中API Key不可访问")

    except Exception as e:
        print(f"   ❌ Callaway13FieldProcessor初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_env_loading()