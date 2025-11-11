#!/usr/bin/env python3
"""
简化的 GLM API 测试脚本
"""

import os
import json
import urllib.request
import urllib.error

def test_glm_simple():
    """使用 urllib 简单测试 GLM API"""

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

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message'].get('content', '')
                reasoning = result['choices'][0]['message'].get('reasoning_content', '')

                title = content if content else reasoning
                if title:
                    title = title.strip()
                    print(f"\n标题1: {title}")
                    print(f"长度: {len(title)} 字符")
                    print(f"包含棉服: {'✅' if '棉服' in title else '❌'}")
                else:
                    print("\n❌ 未获取到标题")
            else:
                print("\n❌ 响应格式错误")
                print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

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

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message'].get('content', '')
                reasoning = result['choices'][0]['message'].get('reasoning_content', '')

                title = content if content else reasoning
                if title:
                    title = title.strip()
                    print(f"\n标题2: {title}")
                    print(f"长度: {len(title)} 字符")
                else:
                    print("\n❌ 未获取到标题")
            else:
                print("\n❌ 响应格式错误")
                print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_glm_simple()