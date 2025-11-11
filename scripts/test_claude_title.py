#!/usr/bin/env python3
"""
使用 Claude API 生成标题的测试脚本
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_claude_title():
    """测试使用 Claude 生成标题"""

    # 检查 API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 请设置 ANTHROPIC_API_KEY 环境变量")
        print("\n设置方法：")
        print("export ANTHROPIC_API_KEY='sk-ant-api03-...'")
        return None

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # 构建提示词 - 基于压缩版的格式
        prompt = """你是一个专业的中文电商标题专家。请将商品名改写成淘宝标题。

要求：
1. 标题长度：25-30个中文字符
2. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
3. 结尾必须是：夹克
4. 格式：25秋冬卡拉威Callaway高尔夫男士+功能词+夹克

商品是男士夹克，全拉链设计，有弹力，适合运动。

原始名称：スターストレッチフルジップブルゾン (MENS)
请直接输出标题："""

        print("=== 使用 Claude 生成标题 ===")
        print(f"API Key: {api_key[:20]}...")
        print(f"Prompt长度: {len(prompt)} 字符")
        print(f"Model: claude-3-5-sonnet-20241022")

        print("\n调用 Claude API...")

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
            "包含男士": "男士" in title,
            "包含季节": "25秋冬" in title,
            "结尾正确": title.endswith("夹克")
        }

        print("\n=== 验证结果 ===")
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n✅ 所有检查通过！")

        return title

    except ImportError:
        print("❌ 需要安装 anthropic 库：")
        print("pip install anthropic")
    except Exception as e:
        print(f"❌ Claude API 调用失败: {e}")
        import traceback
        traceback.print_exc()

    return None

def test_two_products():
    """测试两个产品的标题生成"""

    print("="*60)
    print("测试产品 1: C25215107 (中綿ブルゾン)")
    print("="*60)

    # 产品1：中棉夹克
    prompt1 = """你是一个专业的中文电商标题专家。请将商品名改写成淘宝标题。

要求：
1. 标题长度：25-30个中文字符
2. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
3. 结尾必须是：夹克
4. 格式：25秋冬卡拉威Callaway高尔夫男士+功能词+夹克

重要：如果原始名称包含"中綿"或"中棉"，必须在标题中体现为"棉服"！

商品是男士夹克，中棉填充，保暖舒适，两用设计。

原始名称：スターストレッチ2WAY中綿ブルゾン (MENS)
请直接输出标题："""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n❌ 请设置 ANTHROPIC_API_KEY 环境变量")
        return

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # 生成标题1
        response1 = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt1}]
        )
        title1 = response1.content[0].text.strip()
        print(f"\n标题1: {title1}")
        print(f"长度: {len(title1)} 字符")
        print(f"包含棉服: {'是' if '棉服' in title1 else '否'}")

    except Exception as e:
        print(f"❌ 生成标题1失败: {e}")

    print("\n" + "="*60)
    print("测试产品 2: C25215100 (フルジップブルゾン)")
    print("="*60)

    # 产品2：全拉链夹克
    prompt2 = """你是一个专业的中文电商标题专家。请将商品名改写成淘宝标题。

要求：
1. 标题长度：25-30个中文字符
2. 必须包含：25秋冬、卡拉威Callaway、高尔夫、男士
3. 结尾必须是：夹克
4. 格式：25秋冬卡拉威Callaway高尔夫男士+功能词+夹克

商品是男士夹克，全拉链设计，有弹力，适合运动。

原始名称：スターストレッチフルジップブルゾン (MENS)
请直接输出标题："""

    try:
        # 生成标题2
        response2 = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt2}]
        )
        title2 = response2.content[0].text.strip()
        print(f"\n标题2: {title2}")
        print(f"长度: {len(title2)} 字符")

    except Exception as e:
        print(f"❌ 生成标题2失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 提示用户设置 API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("\n请先设置 Claude API 密钥：")
        print('export ANTHROPIC_API_KEY="sk-ant-api03-..."')
        print("\n然后重新运行：")
        print("python3 scripts/test_claude_title.py")
    else:
        # 测试两个产品
        test_two_products()