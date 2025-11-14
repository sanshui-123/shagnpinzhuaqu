"""
标题生成系统 - 核心逻辑
版本：v6.0 - 精简版
核心思想：提示词包含所有规则，GLM一步生成
"""

import re
import time
import threading
import requests
import os
from typing import Dict, Tuple
from itertools import combinations, product
from .title_config import *

# 全局变量
glm_call_lock = threading.Lock()
last_glm_call_ts = 0.0

# ============================================================================
# 品牌提取功能
# ============================================================================

def extract_brand_from_product(product: Dict) -> Tuple[str, str, str]:
    """
    提取品牌

    Returns:
        (brand_key, brand_chinese, brand_short)
        例如：('callawaygolf', '卡拉威Callaway', '卡拉威')
    """
    name = product.get('productName', '').lower()
    url = product.get('detailUrl', '').lower()

    # 从商品名匹配
    for brand_key, keywords in BRAND_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in name:
                return (
                    brand_key,
                    BRAND_MAP[brand_key],
                    BRAND_SHORT_NAME[brand_key]
                )

    # 从URL匹配
    for brand_key in BRAND_KEYWORDS.keys():
        if brand_key in url:
            return (
                brand_key,
                BRAND_MAP[brand_key],
                BRAND_SHORT_NAME[brand_key]
            )

    # 默认
    return (
        'callawaygolf',
        BRAND_MAP['callawaygolf'],
        BRAND_SHORT_NAME['callawaygolf']
    )

# ============================================================================
# 第一步：构建超完整提示词（包含所有规则）
# ============================================================================

def build_smart_prompt(product: Dict) -> str:
    """
    构建超完整提示词 - 包含所有规则和判断逻辑
    让GLM自己判断性别、类别、功能词、结尾词
    """
    name = product.get('productName', '')

    # 提取品牌信息
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


# ============================================================================
# 第二步：GLM API调用
# ============================================================================

def call_glm_api(
    prompt: str,
    model: str = "glm-4-flash",
    temperature: float = 0.3,
    max_tokens: int = 800
) -> str:
    """
    调用GLM API（带限流和重试）

    Returns:
        生成的内容，失败返回空字符串
    """
    global last_glm_call_ts

    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        raise RuntimeError("ZHIPU_API_KEY environment variable not set")

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # 重试机制
    max_retries = 2
    for retry in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    choice = data['choices'][0]
                    message = choice.get('message', {})
                    content = message.get('content', '')

                    # 如果content为空，尝试读取reasoning_content
                    if not content:
                        reasoning = message.get('reasoning_content', '')
                        if reasoning:
                            if isinstance(reasoning, str):
                                content = reasoning.strip()
                                print(f"[GLM Debug] 使用reasoning_content: {content[:200]}...")
                            else:
                                content = str(reasoning).strip()
                                print(f"[GLM Debug] reasoning转换为字符串: {content[:200]}...")

                    if content:
                        # 清洗内容：去除"好的"等应答词
                        content = content.strip()

                        # 检查并移除常见的应答词
                        reply_prefixes = [
                            '好的，', '好的。', '好的',
                            '明白了，', '明白了。', '明白了',
                            'OK，', 'OK.', 'OK',
                            'ok，', 'ok.', 'ok',
                            '收到，', '收到。', '收到',
                            '了解，', '了解。', '了解',
                            '好的，请看', '好的，参考', '好的，以下是',
                            '好的，我建议', '好的，我推荐',
                            '明白了，请看', '明白了，参考',
                            'OK，请看', 'OK，参考'
                        ]

                        for prefix in reply_prefixes:
                            if content.startswith(prefix):
                                content = content[len(prefix):].strip()
                                print(f"[GLM Debug] 移除应答词前缀: '{prefix}'")
                                break

                        if not content:
                            print("[GLM Debug] 清洗后内容为空")
                            return ""

                        return content
                    else:
                        print(f"[GLM Debug] finish_reason: {choice.get('finish_reason')}")
                        print(f"[GLM Debug] 完整响应data: {data}")
                        return ""
                else:
                    print(f"GLM API错误: 响应格式异常 - {data}")
                    return ""
            else:
                print(f"GLM API错误 (尝试 {retry+1}/{max_retries}): {response.status_code} - {response.text}")
                if retry < max_retries - 1:
                    time.sleep(2 ** retry)
                else:
                    return ""
        except requests.exceptions.RequestException as e:
            print(f"GLM API请求异常 (尝试 {retry+1}/{max_retries}): {e}")
            if retry < max_retries - 1:
                time.sleep(2 ** retry)
            else:
                return ""

    return ""


# ============================================================================
# 第三步：质量检查和优化规则
# ============================================================================

def clean_title(title: str) -> str:
    """
    清理标题中的常见问题
    """
    if not title:
        return title

    # 去除应答词前缀
    reply_prefixes = [
        '好的，', '好的。', '好的',
        '明白了，', '明白了。', '明白了',
        'OK，', 'OK.', 'OK',
        'ok，', 'ok.', 'ok',
        '收到，', '收到。', '收到',
        '了解，', '了解。', '了解',
        '好的，请看', '好的，参考', '好的，以下是',
        '好的，我建议', '好的，我推荐',
        '明白了，请看', '明白了，参考',
        'OK，请看', 'OK，参考',
        '标题：', '标题:', '标题',
        '生成的标题是：', '生成的标题:',
        '建议标题：', '建议标题:',
    ]

    for prefix in reply_prefixes:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
            break

    # 去除常见的解释性后缀
    explanation_suffixes = [
        '（', '(', '【', '[', '"', '"',
        '以上是', '这是一个', '这是',
        '长度', '字数', '符合',
    ]

    for suffix in explanation_suffixes:
        idx = title.find(suffix)
        if idx > 10:  # 确保不是标题开头的字符
            title = title[:idx].strip()
            break

    return title


def optimize_title(title: str) -> str:
    """
    优化标题，解决之前遇到的问题
    """
    if not title:
        return title

    # 1. 去除日文、英文、符号
    # 日文假名
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uFF66-\uFF9F]')
    title = japanese_pattern.sub('', title)

    # 去除特殊符号
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·\s]+', '', title)

    # 2. 确保"高尔夫"只出现一次
    if title.count('高尔夫') > 1:
        parts = title.split('高尔夫')
        title = parts[0] + '高尔夫' + ''.join(parts[1:])

    # 3. 去除连续重复的词
    words = list(title)
    i = 1
    while i < len(words):
        # 检查2字重复
        if i >= 3 and words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        # 检查3字重复
        elif i >= 5 and words[i-4] == words[i-3] == words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        else:
            i += 1
    title = ''.join(words)

    # 4. 长度调整
    if len(title) > 30:
        title = title[:30]
    elif len(title) < 26:
        # 如果太短，尝试在适当位置加修饰词
        modifiers = ['新款', '时尚', '轻便', '透气', '运动', '专业', '经典', '优雅', '高级', '精品']

        # 寻找插入位置（在品牌后或功能词前）
        insert_pos = -1

        # 尝试在"高尔夫"后插入
        golf_idx = title.find('高尔夫')
        if golf_idx > 0 and golf_idx + 3 < len(title):
            insert_pos = golf_idx + 3

        # 如果找到合适位置，插入修饰词
        if insert_pos > 0:
            # 计算需要增加的长度
            need_len = 26 - len(title)

            # 灵活组合修饰词以达到目标长度
            # 生成所有可能的组合

            # 尝试1-4个修饰词的组合
            found = False
            for n in range(1, 5):  # 尝试1到4个修饰词
                for combo in combinations(modifiers, n):
                    # 生成所有排列
                    for perm in product(combo, repeat=n):
                        if len(set(perm)) != n:  # 确保不重复
                            continue
                        test_title = title[:insert_pos] + ''.join(perm) + title[insert_pos:]
                        if 26 <= len(test_title) <= 30:
                            title = test_title
                            found = True
                            break
                    if found:
                        break
                if found:
                    break

            # 如果还是没有合适的，直接填充以达到最小长度
            if not found and len(title) < 26:
                need_len = 26 - len(title)  # 计算需要补充的字数

                # 根据需要的字数选择合适的修饰词
                if need_len <= 2:
                    add_mod = '新款'
                elif need_len <= 4:
                    add_mod = '舒适时尚'
                elif need_len <= 6:
                    add_mod = '新款时尚轻便'
                else:
                    # 需要更多字数，组合多个修饰词（不重复）
                    all_mods = ['新款', '时尚', '轻便', '透气', '运动']
                    add_mod = ''
                    for mod in all_mods:
                        if len(add_mod) + len(mod) <= need_len:
                            add_mod += mod
                        if len(add_mod) >= need_len:
                            break

                # 只插入一次
                title = title[:insert_pos] + add_mod + title[insert_pos:]

                # 最终检查：如果还是不够26字或超过30字，截断/补充
                if len(title) < 26:
                    title = title[:insert_pos] + add_mod + '优雅' + title[insert_pos:]
                if len(title) > 30:
                    title = title[:30]

    return title


def validate_title(title: str, product: Dict) -> bool:
    """
    验证标题质量
    """
    if not title:
        return False

    # 1. 长度检查
    if not (26 <= len(title) <= 30):
        return False

    # 2. 必须包含"高尔夫"
    if '高尔夫' not in title or title.count('高尔夫') != 1:
        return False

    # 3. 必须包含对应品牌
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    # 检查品牌简称
    if brand_short not in title:
        return False

    # 4. 不能包含禁止词汇
    forbidden_words = [
        '官网', '正品', '专柜', '代购', '海外', '进口',
        '授权', '旗舰', '限量', '促销', '特价', '淘宝',
        '天猫', '京东', '拼多多'
    ]
    for word in forbidden_words:
        if word in title:
            return False

    # 5. 不能包含日文字符
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', title):
        return False

    # 6. 不能包含连续重复
    if re.search(r'(.)\1{2,}', title):  # 3个及以上相同字符连续
        return False
    if re.search(r'(..)\1{2,}', title):  # 2字词语重复3次
        return False

    return True

# ============================================================================
# 主流程：带重试机制
# ============================================================================

def generate_cn_title(product: Dict) -> str:
    """
    生成中文标题 - 带重试机制

    流程：
    1. 构建超完整提示词（包含所有规则）
    2. 调用GLM API生成
    3. 清理和优化标题
    4. 如果失败，重新生成（最多2次）
    """
    for attempt in range(2):
        # 第一步：构建提示词
        prompt = build_smart_prompt(product)

        # 第二步：调用GLM生成
        raw_title = call_glm_api(prompt)

        if raw_title:
            # 第三步：清理标题
            title = clean_title(raw_title.strip())

            # 如果清理后为空，重新生成
            if not title:
                print(f"尝试 {attempt + 1}: 清理后标题为空，重新生成")
                continue

            # 第四步：优化标题
            title = optimize_title(title)

            # 第五步：验证标题
            if validate_title(title, product):
                return title
            else:
                print(f"尝试 {attempt + 1}: 验证失败，重新生成")
        else:
            print(f"尝试 {attempt + 1}: GLM返回空，重新生成")

    # 如果2次都失败，返回空字符串
    print("❌ GLM生成失败，2次尝试未通过验证")
    return ""


# ============================================================================
# 错误处理
# ============================================================================

class TitleGenerationError(Exception):
    """标题生成异常"""
    pass