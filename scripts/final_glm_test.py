#!/usr/bin/env python3
"""
最终 GLM API 测试脚本（使用正确的参数）
"""

import os
import json
import ssl
import urllib.request
import urllib.error
import time

def test_glm_final():
    """使用正确的参数测试 GLM API"""

    # 创建忽略 SSL 验证的上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    api_key = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # 测试产品1
    print("="*60)
    print("测试产品 1: C25215107 (中綿ブルゾン)")
    print("="*60)

    prompt1 = """请将商品名改写成25-30字的淘宝标题。

要求：
1. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
2. 结尾必须是：夹克
3. 如果有"中綿"要改成"棉服"

商品：スターストレッチ2WAY中綿ブルゾン (MENS)
标题："""

    data1 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt1}],
        "max_tokens": 200,  # 增加到200
        "temperature": 0.3
    }

    try:
        # 发送请求1
        req = urllib.request.Request(
            url,
            data=json.dumps(data1).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )

        print("发送请求...")
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                # 优先使用 content，如果为空则使用 reasoning_content
                title = content.strip() if content else reasoning.strip()

                if title:
                    print(f"\n标题1: {title}")
                    print(f"长度: {len(title)} 字符")
                    print(f"包含棉服: {'✅' if '棉服' in title else '❌'}")

                    # 检查各项要求
                    checks = {
                        "长度25-30": 25 <= len(title) <= 30,
                        "含卡拉威": "卡拉威" in title,
                        "含Callaway": "Callaway" in title,
                        "含高尔夫": "高尔夫" in title,
                        "含男士": "男士" in title,
                        "含25秋冬": "25秋冬" in title,
                        "结尾夹克": title.endswith("夹克")
                    }
                    print("\n检查结果:")
                    for check, passed in checks.items():
                        print(f"  {'✅' if passed else '❌'} {check}")
                else:
                    print("❌ 未获取到标题")
                    print(f"finish_reason: {choice.get('finish_reason', 'N/A')}")
            else:
                print("❌ 响应中没有 choices")

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    # 等待1秒避免限流
    time.sleep(1)

    print("\n" + "="*60)
    print("测试产品 2: C25215100 (フルジップブルゾン)")
    print("="*60)

    # 测试产品2
    prompt2 = """请将商品名改写成25-30字的淘宝标题。

要求：
1. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
2. 结尾必须是：夹克

商品：スターストレッチフルジップブルゾン (MENS)
标题："""

    data2 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt2}],
        "max_tokens": 200,  # 增加到200
        "temperature": 0.3
    }

    try:
        # 发送请求2
        req = urllib.request.Request(
            url,
            data=json.dumps(data2).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )

        print("发送请求...")
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                # 优先使用 content，如果为空则使用 reasoning_content
                title = content.strip() if content else reasoning.strip()

                if title:
                    print(f"\n标题2: {title}")
                    print(f"长度: {len(title)} 字符")

                    # 检查各项要求
                    checks = {
                        "长度25-30": 25 <= len(title) <= 30,
                        "含卡拉威": "卡拉威" in title,
                        "含Callaway": "Callaway" in title,
                        "含高尔夫": "高尔夫" in title,
                        "含男士": "男士" in title,
                        "含25秋冬": "25秋冬" in title,
                        "结尾夹克": title.endswith("夹克")
                    }
                    print("\n检查结果:")
                    for check, passed in checks.items():
                        print(f"  {'✅' if passed else '❌'} {check}")
                else:
                    print("❌ 未获取到标题")
                    print(f"finish_reason: {choice.get('finish_reason', 'N/A')}")
            else:
                print("❌ 响应中没有 choices")

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_glm_final()