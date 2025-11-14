#!/usr/bin/env python3
"""
调试标题生成问题
"""

import os
import requests
import json
from pathlib import Path

def load_env():
    """加载环境变量"""
    env_file = Path("callaway.env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def call_glm_api_debug(prompt):
    """调用GLM API并返回完整响应"""
    api_key = os.environ.get('ZHIPU_API_KEY')

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("完整API响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                content = choice.get('message', {}).get('content', '')
                return content.strip()
        else:
            print(f"错误响应: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def build_test_prompt():
    """构建测试提示词"""

    # 简化版的提示词，专注于长度控制
    prompt = """你是淘宝标题生成专家。根据日文商品名生成中文标题。

商品名：【袖取り外し可能】ヒートナビ中わた2WAYブルゾン

标题格式：
[季节][品牌]高尔夫[性别][功能词][结尾词]

具体要求：
1. 季节：25FW → 25秋冬（没有则用25秋冬）
2. 品牌：Le Coq Sportif Golf → Le Coq公鸡乐卡克
3. 性别：默认男士
4. 功能词：包含"中わた" → 保暖棉服，包含"2WAY" → 可拆卸
5. 结尾词：ブルゾン → 夹克

长度控制（最严格）：
- 总长度必须是26-30个汉字
- 基础结构：25秋冬Le Coq公鸡乐卡克高尔夫男士保暖棉服可拆卸夹克
- 基础长度：25字（需要增加1-5个字）

扩展方法：
如果需要增加字数，可以在功能词前添加修饰词：
- "新款保暖棉服可拆卸"
- "时尚保暖棉服可拆卸"
- "专业保暖棉服可拆卸"
- "轻便保暖棉服可拆卸"
- "高品质保暖棉服可拆卸"

示例：
- 25秋冬卡拉威高尔夫男士保暖舒适夹克（27字）
- 26春夏阿迪达斯高尔夫女士弹力全拉链上衣（28字）

输出要求：
1. 直接输出标题，不要任何解释
2. 必须是26-30个汉字
3. 自己先数一遍字数确保正确

现在生成标题："""

    return prompt

if __name__ == "__main__":
    load_env()

    print("=== 调试标题生成 ===")
    print()

    prompt = build_test_prompt()

    print("生成的提示词:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    print()

    print("调用GLM API...")
    result = call_glm_api_debug(prompt)

    if result:
        print()
        print("生成结果:")
        print(f"标题: {result}")
        print(f"长度: {len(result)}字")
        print(f"长度合规(26-30): {'✅' if 26 <= len(result) <= 30 else '❌'}")

        # 检查其他要求
        has_golf = '高尔夫' in result
        has_season = '25秋冬' in result
        has_gender = '男士' in result
        has_ending = result.endswith('夹克')

        print(f"包含'高尔夫': {'✅' if has_golf else '❌'}")
        print(f"包含'25秋冬': {'✅' if has_season else '❌'}")
        print(f"包含'男士': {'✅' if has_gender else '❌'}")
        print(f"以'夹克'结尾: {'✅' if has_ending else '❌'}")

        # 如果长度不对，给出建议
        if len(result) < 26:
            needed = 26 - len(result)
            print(f"❌ 长度不足：需要增加{needed}字")
        elif len(result) > 30:
            extra = len(result) - 30
            print(f"❌ 长度超长：需要删除{extra}字")
        else:
            print("✅ 长度完美!")

    else:
        print("❌ API调用失败")