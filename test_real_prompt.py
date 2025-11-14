#!/usr/bin/env python3
"""
用真实的提示词测试GLM API
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

def extract_brand_from_product(product):
    """复制品牌提取逻辑"""
    # 这里简化处理，实际代码在callaway_13field_processor.py
    brand = product.get('brand', '')
    product_name = product.get('productName', '')

    # 对于Le Coq Sportif Golf
    if 'Le Coq' in brand or 'lecoq' in brand.lower():
        return ('lecoq', 'Le Coq Sportif', '公鸡')  # 假设的品牌简称
    # 其他品牌...

    # 默认
    return ('unknown', '未知品牌', '未知')

def build_real_prompt(product):
    """构建真实的提示词"""
    name = product.get('productName', '')
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)

    prompt = f"""你是淘宝标题生成专家。根据日文商品名生成中文标题。

商品名：{name}

标题格式：
[季节][品牌]高尔夫[性别][功能词][结尾词]

判断规则（你需要自己判断）：

1. 季节判断
从商品名提取年份+季节代码：
- "25FW"、"25AW" → "25秋冬"
- "26SS"、"26SP" → "26春夏"
如果没有，默认用"25秋冬"

2. 品牌
根据商品名判断品牌，使用简短版品牌名（不要英文）：
- Callaway → "卡拉威"
- Titleist → "泰特利斯"
- Puma → "彪马"
- Adidas → "阿迪达斯"
- Nike → "耐克"
- Under Armour → "安德玛"
- FootJoy → "FootJoy"
- Cleveland → "Cleveland"
- Mizuno → "美津浓"
- Ping → "Ping"
- TaylorMade → "泰勒梅"
本商品的品牌是：{brand_short}

3. 性别判断
商品名包含"メンズ/mens/men" → "男士"
商品名包含"レディース/womens/women/ladies" → "女士"
没有明确标识 → 默认"男士"

4. 功能词判断（根据商品特点选择）
包含"中綿/中棉/棉服" → "保暖棉服"
包含"フルジップ/全拉链" → "弹力全拉链"
包含"防寒/保暖" → "保暖"
包含"フリース/fleece" → "抓绒"
包含"撥水/防水" → "防泼水"
包含"速乾/quickdry" → "速干"
包含"軽量/轻量" → "轻量"
包含"ストレッチ/stretch" → "弹力"
其他普通服装 → "舒适"
配件类 → 不需要功能词（留空或用"轻便"、"时尚"）

5. 结尾词判断（根据商品类型）

配件类结尾词：
- "ベルト/belt/皮带" → "腰带"
- "キャップ/cap/帽子" → "帽子"
- "ハット/hat" → "帽子"
- "ビーニー/beanie" → "帽子"
- "グローブ/glove/手套" → "手套"
- "ヘッドカバー/head cover/カバー" → "球杆头套"
- "マーカー/marker/クリップ" → "标记夹"
- "ソックス/socks/袜子" → "袜子"
- "シューズ/shoes/球鞋" → "球鞋"
- "傘/umbrella/雨伞" → "雨伞"
- "バッグ/bag/包" → "高尔夫包"
其他配件 → "配件"

服装类结尾词：
- "ジャケット/jacket/ブルゾン/blouson/アウター/outer" → "夹克"
- "ベスト/vest" → "背心"
- "コート/coat" → "外套"
- "パーカー/parka" → "连帽衫"
- "ダウン/down" → "羽绒服"
- "ポロ/polo/シャツ/shirt/トップ/top" → "上衣"
- "ニット/knit/セーター/sweater" → "针织衫"
- "スウェット/sweat/卫衣" → "卫衣"
- "パンツ/pants/ズボン/长裤" → "长裤"
- "ショート/short/短裤" → "短裤"
- "スカート/skirt/裙" → "半身裙"
- "シューズ/shoes/スニーカー/sneaker" → "球鞋"
- "レイン/rain/雨" → "雨衣"

严格要求（必须遵守）：

1. 长度要求
总长度：26-30个汉字
如果长度不够，可以在功能词前加修饰：
- "新款"、"时尚"、"轻便"、"透气"、"运动"、"专业"、"经典"等

2. 格式要求
- 只用简体中文，不要日文假名、英文字母、繁体字
- 不要任何符号：空格、斜杠/、破折号-、加号+、乘号×等
- "高尔夫"必须且只能出现1次
- 必须以完整的结尾词结束（不要"夹克外"、"上"等残缺词）

3. 禁止词汇
不要出现：官网、正品、专柜、代购、海外、进口、授权、旗舰、限量、促销、特价

4. 禁止重复
不要连续重复相同的词，如"夹克夹克"、"保暖保暖"

5. 逻辑要求
- 标题要通顺自然，符合中文表达习惯
- 功能词要与商品特性匹配
- 结尾词要准确反映商品类型

示例参考：

配件类示例：
- 25秋冬卡拉威高尔夫男士轻便透气帽子（26字）
- 26春夏泰特利斯高尔夫女士时尚运动腰带（27字）
- 25秋冬彪马高尔夫男士球杆头套（24字）← 如果太短，加"轻便"或"新款"
- 25秋冬耐克高尔夫男士专业高尔夫手套（27字）

服装类示例：
- 25秋冬卡拉威高尔夫男士保暖舒适夹克（27字）
- 26春夏阿迪达斯高尔夫女士弹力全拉链上衣（28字）
- 25秋冬泰勒梅高尔夫男士保暖棉服夹克（27字）
- 26春夏Puma高尔夫女士轻便运动短裤（28字）

输出要求：
- 直接输出标题，不要任何解释、不要"好的"等应答词、不要markdown格式
- 确保标题26-30个汉字
- 确保格式正确

现在生成标题："""

    return prompt

def call_glm_api(prompt):
    """调用GLM API"""
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        raise RuntimeError("ZHIPU_API_KEY environment variable not set")

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

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if 'choices' in data and data['choices']:
            content = data['choices'][0]['message']['content']
            return content.strip()
    return None

if __name__ == "__main__":
    load_env()

    # Le Coq测试产品
    lecoq_product = {
        'productId': 'LG5FWB50M',
        'productName': '【可拆卸袖子可能】热航中棉两用夹克（武井壮着用）',
        'brand': 'Le Coq Sportif Golf',
        'priceText': '￥19,800',
        'colors': ['藏青色', 'ネイビー×グレー', '黑色', '蓝色', '灰色', '米色'],
        'sizes': ['S', 'M', 'L', 'LL']
    }

    print("=== 用真实提示词测试Le Coq产品 ===")
    print(f"产品名称: {lecoq_product['productName']}")
    print(f"品牌: {lecoq_product['brand']}")
    print()

    prompt = build_real_prompt(lecoq_product)
    print("生成的提示词:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    print()

    print("GLM API响应:")
    result = call_glm_api(prompt)
    if result:
        print(f"生成结果: {result}")
        print(f"长度: {len(result)}字")
        print(f"包含'高尔夫': {'是' if '高尔夫' in result else '否'}")
        print(f"长度合规(26-30): {'是' if 26 <= len(result) <= 30 else '否'}")
    else:
        print("❌ API调用失败")