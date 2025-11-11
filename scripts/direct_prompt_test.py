#!/usr/bin/env python3
"""
使用直接提示词测试 GLM API
"""

import os
import json
import ssl
import urllib.request
import time

def test_direct_prompt():
    """使用更直接的提示词测试 GLM"""

    # 创建忽略 SSL 验证的上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    api_key = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    print("="*60)
    print("使用直接提示词测试（避免触发推理）")
    print("="*60)

    # 测试产品1 - 直接提示词
    print("\n产品1: C25215107 (中綿ブルゾン)")
    print("-" * 40)

    prompt1 = "25秋冬卡拉威Callaway高尔夫男士两用棉服夹克"

    data1 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt1}],
        "max_tokens": 50,
        "temperature": 0.1
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data1).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                title = content.strip() if content else reasoning.strip()

                if title:
                    print(f"标题1: {title}")
                    print(f"长度: {len(title)}")
                    print(f"含棉服: {'✅' if '棉服' in title else '❌'}")
                else:
                    print("❌ 未获取到标题")

    except Exception as e:
        print(f"❌ 请求失败: {e}")

    time.sleep(1)

    # 测试产品2 - 直接提示词
    print("\n产品2: C25215100 (フルジップブルゾン)")
    print("-" * 40)

    prompt2 = "25秋冬卡拉威Callaway高尔夫男士弹力全拉链夹克"

    data2 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt2}],
        "max_tokens": 50,
        "temperature": 0.1
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data2).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                title = content.strip() if content else reasoning.strip()

                if title:
                    print(f"标题2: {title}")
                    print(f"长度: {len(title)}")
                else:
                    print("❌ 未获取到标题")

    except Exception as e:
        print(f"❌ 请求失败: {e}")

    time.sleep(1)

    # 测试产品2 - 让 GLM 续写
    print("\n产品2续写测试:")
    print("-" * 40)

    prompt3 = "请补全标题（25-30字）：25秋冬卡拉威Callaway高尔夫男士"

    data3 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt3}],
        "max_tokens": 50,
        "temperature": 0.3
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data3).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )

        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                title = content.strip() if content else reasoning.strip()

                if title:
                    full_title = "25秋冬卡拉威Callaway高尔夫男士" + title
                    print(f"补全部分: {title}")
                    print(f"完整标题: {full_title}")
                    print(f"长度: {len(full_title)}")
                else:
                    print("❌ 未获取到内容")

    except Exception as e:
        print(f"❌ 请求失败: {e}")

    print("\n=== 测试完成 ===")
    print("\n结论：")
    print("1. GLM-4.6 对复杂的指令会触发推理模式")
    print("2. 简单直接的提示词可以避免推理")
    print("3. 让模型续写（补全）的方式更容易得到期望的结果")

if __name__ == "__main__":
    test_direct_prompt()