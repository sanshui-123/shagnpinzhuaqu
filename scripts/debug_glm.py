#!/usr/bin/env python3
"""
调试 GLM API 的独立脚本
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ['ZHIPU_API_KEY'] = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
os.environ['ZHIPU_TITLE_MODEL'] = 'glm-4.6'
os.environ['GLM_MIN_INTERVAL'] = '0.8'
os.environ['GLM_MAX_TOKENS'] = '400'

import time
import requests
from typing import Dict, Any

def test_glm_api_simple():
    """测试 GLM API 的简单调用"""

    api_key = os.environ.get('ZHIPU_API_KEY')
    model = os.environ.get('ZHIPU_TITLE_MODEL', 'glm-4.6')

    # 最简单的测试提示词
    simple_prompt = "请生成标题：25秋冬卡拉威Callaway高尔夫男士夹克"

    print(f"=== GLM API 简单测试 ===")
    print(f"模型: {model}")
    print(f"提示词: {simple_prompt}")
    print(f"提示词长度: {len(simple_prompt)} 字符")

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": simple_prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0.3,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        print("\n发送请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        print(f"HTTP状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n原始响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                print(f"\n=== 解析结果 ===")
                print(f"Content: {repr(content)}")
                print(f"Reasoning: {repr(reasoning)}")

                if content:
                    print(f"\n✅ 生成成功: {content}")
                elif reasoning:
                    print(f"\n✅ 使用推理内容: {reasoning}")
                else:
                    print("\n❌ 未找到有效内容")
            else:
                print("\n❌ 响应中没有 choices")
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"\n❌ 异常错误: {e}")
        import traceback
        traceback.print_exc()

def test_glm_with_full_prompt():
    """使用完整提示词测试 GLM"""

    # 导入提示词构建函数
    from feishu_update.services.title_v6 import build_smart_prompt, determine_category, extract_brand_from_product

    # 模拟产品数据
    product = {
        'productName': 'スターストレッチフルジップブルゾン (MENS)',
        'category': '外套',
        'brand': 'Callaway Golf'
    }

    category = determine_category(product)
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)

    print("\n=== 完整提示词测试 ===")

    # 构建完整提示词
    full_prompt = build_smart_prompt(product, category, brand_key, brand_chinese)

    print(f"提示词长度: {len(full_prompt)} 字符")
    print(f"提示词预览:\n{full_prompt[:500]}...")

    # 调用 GLM API
    api_key = os.environ.get('ZHIPU_API_KEY')
    model = os.environ.get('ZHIPU_TITLE_MODEL', 'glm-4.6')

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        "max_tokens": 200,
        "temperature": 0.3,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        print("\n发送请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                print(f"\nContent: {repr(content)}")
                print(f"Reasoning: {repr(reasoning)}")

                if content:
                    print(f"\n✅ 生成成功: {content}")
                elif reasoning:
                    print(f"\n✅ 使用推理内容: {reasoning}")
                else:
                    print("\n❌ 未找到有效内容")
            else:
                print("\n❌ 响应中没有 choices")
                print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")

    except Exception as e:
        print(f"\n❌ 异常错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始 GLM API 调试...\n")

    # 测试1: 简单提示词
    test_glm_api_simple()

    print("\n" + "="*60 + "\n")

    # 等待一下避免限流
    time.sleep(2)

    # 测试2: 完整提示词
    test_glm_with_full_prompt()