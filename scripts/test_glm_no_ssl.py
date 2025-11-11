#!/usr/bin/env python3
"""
忽略 SSL 验证的 GLM API 测试脚本
"""

import os
import json
import ssl
import urllib.request
import urllib.error

def test_glm_no_ssl():
    """忽略 SSL 验证测试 GLM API"""

    # 创建忽略 SSL 验证的上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    api_key = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    print("="*60)
    print("测试产品 1: C25215107 (中綿ブルゾン)")
    print("="*60)

    prompt1 = """请将商品名改写成25-30字的淘宝标题。

要求：
1. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
2. 结尾必须是：夹克
3. 如果有"中綿"要改成"棉服"

商品：スターストレッチ2WAY中綿ブルゾン (MENS)
直接输出标题："""

    data1 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt1}],
        "max_tokens": 100,
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

        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            print(f"\n原始响应: {json.dumps(result, indent=2, ensure_ascii=False)}\n")

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                title = content if content else reasoning
                if title:
                    title = title.strip()
                    print(f"标题1: {title}")
                    print(f"长度: {len(title)} 字符")
                    print(f"包含棉服: {'✅' if '棉服' in title else '❌'}")
                else:
                    print("❌ 未获取到标题")
            else:
                print("❌ 响应中没有 choices")
                print(f"错误信息: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("测试产品 2: C25215100 (フルジップブルゾン)")
    print("="*60)

    # 测试产品2
    prompt2 = """请将商品名改写成25-30字的淘宝标题。

要求：
1. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
2. 结尾必须是：夹克

商品：スターストレッチフルジップブルゾン (MENS)
直接输出标题："""

    data2 = {
        "model": "glm-4.6",
        "messages": [{"role": "user", "content": prompt2}],
        "max_tokens": 100,
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

        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))

            print(f"\n原始响应: {json.dumps(result, indent=2, ensure_ascii=False)}\n")

            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                message = choice.get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')

                title = content if content else reasoning
                if title:
                    title = title.strip()
                    print(f"标题2: {title}")
                    print(f"长度: {len(title)} 字符")
                else:
                    print("❌ 未获取到标题")
            else:
                print("❌ 响应中没有 choices")
                print(f"错误信息: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_glm_no_ssl()