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
try:
    from ..config.title_config import *
except ImportError:
    # 如果无法导入配置，从新的prompt模块导入
    from ..config.prompts import (
        BRAND_KEYWORDS, BRAND_MAP, BRAND_SHORT_NAME,
        SEASON_PATTERNS, FUNCTION_WORD_MAPPING, ENDING_WORD_MAPPING
    )

# 全局变量
glm_call_lock = threading.Lock()
last_glm_call_ts = 0.0

# ============================================================================
# 品牌提取功能
# ============================================================================

def extract_brand_from_product(product: Dict) -> Tuple[str, str, str]:
    """
    提取品牌 - 优先使用JSON中的品牌信息

    Returns:
        (brand_key, brand_chinese, brand_short)
        例如：('callawaygolf', '卡拉威Callaway', '卡拉威')
    """
    # 优先使用JSON中的品牌信息进行匹配
    brand_from_json = product.get('brand', '')
    if brand_from_json:
        # 尝试通过品牌名进行匹配
        for brand_key, keywords in BRAND_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in brand_from_json.lower():
                    return (
                        brand_key,
                        BRAND_MAP[brand_key],
                        BRAND_SHORT_NAME[brand_key]
                    )

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
# 智能季节判断函数
# ============================================================================

def get_season_by_date() -> str:
    """
    根据当前日期智能判断季节
    Returns:
        str: 格式为 "25春夏" 或 "25秋冬" 的季节字符串
    """
    import datetime
    now = datetime.datetime.now()
    year = str(now.year)[2:]  # 取后两位，如 2025 -> "25"

    # 根据月份判断季节
    month = now.month
    if month in [3, 4, 5]:  # 春季：3-5月
        return f"{year}春夏"
    elif month in [6, 7, 8]:  # 夏季：6-8月
        return f"{year}春夏"
    elif month in [9, 10, 11, 12]:  # 秋冬：9-12月
        return f"{year}秋冬"
    else:  # 冬季：1-2月
        # 1-2月属于上一年的秋冬系列
        prev_year = str(now.year - 1)[2:]
        return f"{prev_year}秋冬"

def extract_season_from_tables(product: Dict) -> str:
    """
    从抓取的表格数据中提取季节信息（网页实际数据）
    """
    # 优先从原始数据的表格中查找シーズン信息
    if '_original_data' in product:
        original_data = product['_original_data']

        # 检查尺码表中的季节信息
        if '尺码表' in original_data and 'tables' in original_data['尺码表']:
            tables = original_data['尺码表']['tables']
            for table in tables:
                if 'text' in table and 'シーズン' in table['text']:
                    # 提取 "2025年 秋冬" 格式的季节信息
                    text = table['text']
                    # 使用正则表达式匹配 "年份 季节" 格式
                    season_match = re.search(r'(\d{4})年\s*(春夏|秋冬)', text)
                    if season_match:
                        year = season_match.group(1)[2:]  # 取后两位，如2025->25
                        season_text = season_match.group(2)  # 春夏或秋冬
                        return f"{year}{season_text}"

        # 也可以从html中搜索
        if '尺码表' in original_data and 'html' in original_data['尺码表']:
            html = original_data['尺码表']['html']
            # 搜索HTML中的シーズン信息
            season_match = re.search(r'<th[^>]*>シーズン[^<]*</th>\s*<td[^>]*>(\d{4})年\s*(春夏|秋冬)', html)
            if season_match:
                year = season_match.group(1)[2:]  # 取后两位，如2025->25
                season_text = season_match.group(2)  # 春夏或秋冬
                return f"{year}{season_text}"

    # 如果没有找到表格中的季节信息，回退到商品名匹配
    return None

def extract_season_from_name(name: str, product: Dict = None) -> str:
    """
    从商品名中提取季节信息，优先使用表格数据，如果没有则根据当前时间判断
    """
    # 🎯 优先级1：从表格数据中提取（网页实际数据）
    if product:
        table_season = extract_season_from_tables(product)
        if table_season:
            return table_season

    # 🎯 优先级2：从商品名中提取季节代码 - 使用配置化的模式
    try:
        from ..config.prompts import SEASON_PATTERNS
        season_patterns = SEASON_PATTERNS
    except ImportError:
        # 回退到内置模式
        season_patterns = [
            (r'25FW|25AW', '25秋冬'),
            (r'25SS|25SP', '25春夏'),
            (r'26FW|26AW', '26秋冬'),
            (r'26SS|26SP', '26春夏'),
            (r'24FW|24AW', '24秋冬'),
            (r'24SS|24SP', '24春夏'),
        ]

    for pattern, season in season_patterns:
        if re.search(pattern, name):
            return season

    # 🎯 优先级3：如果都没有，根据当前时间判断
    return get_season_by_date()

# ============================================================================
# 第一步：构建超完整提示词（包含所有规则）
# ============================================================================

def build_smart_prompt(product: Dict) -> str:
    """
    构建超完整提示词 - 使用模板化的提示词配置
    让GLM自己判断性别、类别、功能词、结尾词
    """
    from ..config.prompts import TITLE_GENERATION_PROMPT

    name = product.get('productName', '')
    gender = product.get('gender', '')

    # 提取品牌信息
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)

    # 性别映射
    gender_text = "男士"  # 默认
    if gender:
        if gender.lower() in ['女', '女性', 'womens', 'ladies']:
            gender_text = "女士"
        elif gender.lower() in ['男', '男性', 'mens', 'men']:
            gender_text = "男士"

    # 🎯 智能季节判断（从表格数据优先）
    current_season = extract_season_from_name(name, product)

    # 使用模板化的提示词
    prompt = TITLE_GENERATION_PROMPT.format(
        name=name,
        gender=gender,
        current_season=current_season,
        brand_short=brand_short,
        gender_text=gender_text
    )

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

    # 去除特殊符号（不包括空格）
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]+', '', title)

    # 去除英文字母，但保留品牌名中的英文
    # 定义需要保留的英文品牌名
    english_brands = ['PEARLY GATES', 'FootJoy', 'Cleveland', 'Ping']

    # 先用占位符替换品牌名（使用中文占位符避免被正则删除）
    placeholders = {}
    for i, brand in enumerate(english_brands):
        placeholder = f'【品牌占位{i}】'
        if brand in title:
            title = title.replace(brand, placeholder)
            placeholders[placeholder] = brand

    # 去除其他英文字母（保留数字，用于年份）
    title = re.sub(r'[a-zA-Z]+', '', title)

    # 恢复品牌名
    for placeholder, brand in placeholders.items():
        title = title.replace(placeholder, brand)

    # 去除空格
    title = re.sub(r'\s+', '', title)

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
    # 检查品牌简称（去除空格后比较，因为标题中空格已被删除）
    brand_short_nospace = brand_short.replace(' ', '')
    if brand_short_nospace not in title:
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