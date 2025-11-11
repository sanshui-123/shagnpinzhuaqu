#!/usr/bin/env python3
"""
超级简化版提示词测试
"""

import os
import json
import ssl
import urllib.request
import time

def test_ultra_simple():
    """使用超级简化版提示词"""

    # 创建忽略 SSL 验证的上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    api_key = '19a8bc1b7cfe4a888c179badd7b96e1d.9S05UjRMgHnCkbCW'
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    print("="*60)
    print("超级简化版提示词测试")
    print("="*60)

    # 测试：最简单的提示词
    prompts = [
        {
            "name": "产品1（中棉）",
            "prompt": "25秋冬卡拉威Callaway高尔夫男士两用棉服夹克"
        },
        {
            "name": "产品2（全拉链）",
            "prompt": "25秋冬卡拉威Callaway高尔夫男士弹力全拉链夹克"
        },
        {
            "name": "产品2（补全模式）",
            "prompt": "补全标题：25秋冬卡拉威Callaway高尔夫男士_ _ _夹克（共30字）"
        },
        {
            "name": "产品2（填空模式）",
            "prompt": "填空造句，25秋冬卡拉威Callaway高尔夫男士[功能]夹克\n功能词选一个：弹力,保暖,轻薄,防风,透气"
        }
    ]

    for i, test in enumerate(prompts, 1):
        print(f"\n测试{i}: {test['name']}")
        print("-" * 40)
        print(f"提示词: {test['prompt']}")

        data = {
            "model": "glm-4.6",
            "messages": [{"role": "user", "content": test['prompt']}],
            "max_tokens": 30,
            "temperature": 0.1
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
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

                    # 优先使用 content
                    output = content.strip() if content else reasoning.strip()

                    if output:
                        print(f"\n输出: {output}")
                        print(f"长度: {len(output)}")

                        # 如果是补全模式，组合完整标题
                        if "补全" in test['name']:
                            base = "25秋冬卡拉威Callaway高尔夫男士"
                            full_title = base + output
                            print(f"完整标题: {full_title}")
                            print(f"总长度: {len(full_title)}")
                    else:
                        print("\n❌ 无输出")
                        print(f"finish_reason: {choice.get('finish_reason', 'N/A')}")

        except Exception as e:
            print(f"\n❌ 请求失败: {e}")

        # 等待避免限流
        time.sleep(1)

    # 最终测试：使用 glm-4-flash 模型
    print("\n" + "="*60)
    print("使用 glm-4-flash 模型测试")
    print("="*60)

    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": "25秋冬卡拉威Callaway高尔夫男士弹力全拉链夹克"}],
        "max_tokens": 30,
        "temperature": 0.1
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
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

                print(f"\nglm-4-flash 输出: {content.strip() if content else '无内容'}")

    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

    print("\n=== 测试完成 ===")
    print("\n建议：")
    print("1. GLM-4.6 容易进入推理模式，不适合直接的标题生成")
    print("2. 可以考虑使用 glm-4-flash 或其他模型")
    print("3. 或者完全去掉提示词，直接使用预设的标题模板")

if __name__ == "__main__":
    test_ultra_simple()