#!/usr/bin/env python3
"""
使用Claude API生成标题的测试脚本
"""

import os
import sys
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_claude_title():
    """
    测试使用Claude生成标题
    需要设置ANTHROPIC_API_KEY环境变量
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 请设置ANTHROPIC_API_KEY环境变量")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return None

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # 测试腰带产品
        prompt = """你是一个专业的中文电商标题专家。请将商品名改写成淘宝标题。

要求：
1. 标题长度：25-30个中文字符
2. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
3. 结尾必须是：腰带
4. 格式：25秋冬卡拉威Callaway高尔夫男士+功能词+腰带

商品是高尔夫腰带，有调节功能，舒适透气。

原始名称：セレーションベルト (MENS)
请直接输出标题："""

        print("=== 使用Claude生成标题 ===")
        print(f"Prompt长度: {len(prompt)} 字符")
        print("\n调用Claude API...")

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        title = response.content[0].text.strip()
        print(f"\n生成的标题: {title}")
        print(f"标题长度: {len(title)} 字符")

        # 验证标题
        checks = {
            "长度合规": 25 <= len(title) <= 30,
            "包含品牌": "卡拉威" in title and "Callaway" in title,
            "包含高尔夫": "高尔夫" in title,
            "包含腰带": "腰带" in title,
            "包含季节": "25秋冬" in title
        }

        print("\n=== 验证结果 ===")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

        return title

    except ImportError:
        print("❌ 需要安装anthropic库:")
        print("   pip install anthropic")
    except Exception as e:
        print(f"❌ Claude API调用失败: {e}")

    return None

if __name__ == "__main__":
    # 提示用户设置API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("\n请先设置Claude API密钥：")
        print('export ANTHROPIC_API_KEY="sk-ant-api03-..."')
        print("\n然后重新运行：")
        print("python3 scripts/claude_title_test.py")
    else:
        test_claude_title()