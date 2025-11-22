"""
标题生成系统 - 核心逻辑
版本：v6.1 - 精简款（地区+季节款）
核心思想：提示词简短，明确格式，带“地区+季节款”
"""

import re
import time
import threading
import requests
import os
from typing import Dict, Tuple
from itertools import combinations, product as iter_product
try:
    from ..config.title_config import *
except ImportError:
    # 如果无法导入配置，从新的prompt模块导入
    from ..config.prompts import (
        BRAND_KEYWORDS, BRAND_MAP, BRAND_SHORT_NAME,
        SEASON_PATTERNS, FUNCTION_WORD_MAPPING, ENDING_WORD_MAPPING
    )

# 地区映射（按品牌扩展，默认日本）
BRAND_REGION = {
    'callawaygolf': '日本',
    'lecoqgolf': '日本',
    'pearlygates': '日本',
    'munsingwear': '日本',
    'puma': '日本',
    'adidas': '日本',
    'nike': '日本',
    'titleist': '日本',
    'mizuno': '日本',
    'ping': '日本',
    'taylormade': '日本',
    'cleveland': '日本',
    'underarmour': '日本',
    'footjoy': '日本',
}

# 品类白名单（结尾必须命中其中之一）
ALLOWED_TAIL_CATEGORIES = [
    '夹克', '外套', '卫衣', '棉服', '马甲', '背心', '连帽衫',
    '短袖', '长袖', 'T恤', 'POLO衫',
    '短裤', '长裤', '短裙', '连衣裙',
    '帽子', '手套', '球包', '高尔夫球', '杆头套', '套装'
]

# 通用填充/修饰词（用于裁剪或补长时优先移除/插入）
APPAREL_CATEGORIES = {
    '夹克', '外套', '卫衣', '棉服', '马甲', '背心', '连帽衫',
    '短袖', '长袖', 'T恤', 'POLO衫',
    '短裤', '长裤', '短裙', '连衣裙'
}

# 禁用词
FORBIDDEN_WORDS = [
    '官网', '正品', '专柜', '代购', '海外', '进口',
    '授权', '旗舰', '限量', '促销', '特价', '淘宝',
    '天猫', '京东', '拼多多'
]

# 全局限流相关
glm_call_lock = threading.Lock()
last_glm_call_ts = 0.0


def _collect_title_features(product: Dict) -> Dict[str, str]:
    name = str(
        product.get('productName')
        or product.get('title')
        or product.get('name')
        or product.get('product', {}).get('name')
        or ''
    )
    description = str(product.get('description') or product.get('详情页文字') or '')

    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    brand_display = ''
    if brand_chinese:
        brand_display = brand_chinese
    if brand_short and brand_short not in brand_display:
        brand_display += brand_short
    brand_display = brand_display.replace('/', '') or '卡拉威Callaway'

    region = BRAND_REGION.get(brand_key, '日本')

    season_phrase = extract_season_from_name(name, product) or get_season_by_date()
    if not season_phrase.endswith('款'):
        season_phrase = season_phrase + '款'

    target_category = _infer_tail_category(product)

    return {
        'brand_display': brand_display,
        'region': region,
        'season_phrase': season_phrase,
        'target_category': target_category,
        'product_name': name or '未知商品'
    }


def build_template_title(features: Dict[str, str]) -> str:
    parts = [
        features['region'],
        features['season_phrase'],
        features['brand_display'],
    ]
    base_cat = features['target_category']
    if '高尔夫' not in base_cat:
        parts.append('高尔夫')
    if features['target_category'] in APPAREL_CATEGORIES:
        parts.append('服装')
    parts.append(features['target_category'])
    title = ''.join(parts)

    if len(title) > 30:
        title = title[:30]
    return title


def _infer_tail_category(product: Dict) -> str:
    """
    根据名称/分类/URL 直接推断标题尾部品类，找不到时默认长袖
    """
    name = (product.get('productName') or product.get('title') or '').lower()
    category = str(product.get('category', '') or '').lower()
    url = str(product.get('detailUrl') or product.get('url') or '').lower()
    text = f"{name} {category} {url}"

    keyword_map = [
        (['套装', 'set', 'セットアップ'], '套装'),
        (['headcover', 'ヘッドカバー', '头套', '杆头套'], '杆头套'),
        (['bag', 'バッグ', 'キャディ', 'caddy', 'tote', 'トート', 'pouch', 'ポーチ'], '球包'),
        (['glove', 'グローブ', '手套'], '手套'),
        (['cap', 'hat', 'ハット', 'キャップ', 'バイザー', '帽'], '帽子'),
        (['ball', 'ボール', '高尔夫球'], '高尔夫球'),
        (['dress', 'ドレス', '连衣裙'], '连衣裙'),
        (['skirt', 'skort', 'スカート', '裙'], '短裙'),
        (['shorts', 'ショーツ', '短裤', 'ハーフパンツ'], '短裤'),
        (['pant', 'trouser', 'パンツ', '長ズボン', '长裤'], '长裤'),
        (['down', 'padded', 'quilted', '棉服', '羽绒', '中綿', '中棉'], '棉服'),
        (['vest', 'gilet', 'ベスト', 'ジレ', '马甲', '背心'], '马甲'),
        (['polo', 'ポロ'], 'POLO衫'),
        (['t-shirt', 'tshirt', 'tee', 't恤', '短袖', '半袖'], '短袖'),
        (['long sleeve', '長袖', '长袖', 'knit', 'ニット', 'sweater', 'シャツ', '衬衫'], '长袖'),
        (['hoodie', 'パーカー', 'フーディ', '连帽衫', '卫衣', 'sweat'], '卫衣'),
        (['jacket', 'ジャケット', 'ブルゾン', 'coat', '外套', '夹克'], '外套')
    ]

    for keywords, category_name in keyword_map:
        if any(kw in text for kw in keywords):
            return category_name

    return '长袖'

# ============================================================================
# 品牌提取功能（复用配置模块逻辑）
# ============================================================================

from ..config.brands import extract_brand_from_product

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

def _extract_season_from_text(text: str) -> str:
    """从任意文本中提取季节信息，支持“2025年 春夏/秋冬”或 FW/SS 代码"""
    if not text:
        return None

    # 直接查找 2025年 春夏/秋冬
    match = re.search(r'(\d{4})年\s*(春夏|秋冬)', text)
    if match:
        year = match.group(1)[2:]
        season_text = match.group(2)
        return f"{year}{season_text}"

    # 查找代码型 FW/SS
    season_patterns = [
        (r'26FW|26AW', '26秋冬'),
        (r'26SS|26SP', '26春夏'),
        (r'25FW|25AW', '25秋冬'),
        (r'25SS|25SP', '25春夏'),
    ]
    for pattern, season in season_patterns:
        if re.search(pattern, text):
            return season

    return None


def extract_season_from_name(name: str, product: Dict = None) -> str:
    """
    仅依赖描述/详情文本提取季节；若缺失则根据当前日期兜底
    """
    if product:
        desc_text = str(product.get('description', '') or '')
        detail_text = str(product.get('详情页文字', '') or product.get('detail_text', '') or '')
        combined_text = desc_text + '\n' + detail_text
        text_season = _extract_season_from_text(combined_text)
        if text_season:
            return text_season

    return get_season_by_date()

# ============================================================================
# 第一步：构建超完整提示词（包含所有规则）
# ============================================================================

def build_smart_prompt(product: Dict) -> str:
    """
    构建简短提示词：地区+季节款+品牌+高尔夫+性别+功能词可选+品类结尾
    """
    features = _collect_title_features(product)
    example_title = build_template_title(features)
    tail_whitelist = '、'.join(ALLOWED_TAIL_CATEGORIES)
    desc_text = (str(product.get('description') or product.get('详情页文字') or '')
                 [:80]).replace('\n', ' ')
    prompt = (
        "生成一条 24-30 个汉字的淘宝标题，格式固定为：“地区+季节款+品牌（中文+英文）+高尔夫+品类”。\n"
        f"品牌用 {features['brand_display']}，地区固定写 {features['region']}，季节写 {features['season_phrase']}。\n"
        f"“高尔夫”只出现一次，紧跟品牌；尾部品类只能是以下之一：{tail_whitelist}，当前推荐 {features['target_category']}。\n"
        "禁止包含“正品/代购/旗舰/淘宝/拼多多”等词，不要写性别或“中性”，不要加解释。\n"
        f"示例：{example_title}\n\n"
        "商品信息：\n"
        f"- 品类：{features['target_category']}\n"
        f"- 商品名称：{features['product_name']}\n"
        f"- 描述片段：{desc_text}\n"
        "只输出标题。"
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


def _ensure_single_golf(title: str) -> str:
    """确保“高尔夫”恰好出现一次；多余的全部去掉，仅保留第一次"""
    if '高尔夫' not in title:
        return title
    first_idx = title.find('高尔夫')
    # 保留第一次，移除后续所有
    prefix = title[: first_idx + len('高尔夫')]
    suffix = title[first_idx + len('高尔夫'):]
    suffix = suffix.replace('高尔夫', '')
    return prefix + suffix


def _truncate_with_fillers(title: str, max_len: int = 30) -> str:
    """超长时优先移除填充词，再截断"""
    if len(title) <= max_len:
        return title
    return title[:max_len]


def optimize_title(title: str, product: Dict = None) -> str:
    if not title:
        return title

    product = product or {}
    target_cat = _infer_tail_category(product)

    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uFF66-\uFF9F]')
    title = japanese_pattern.sub('', title)
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]+', '', title)
    title = re.sub(r'(?i)unisex', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace('中棉', '棉服').replace('中綿', '棉服')

    if '高尔夫' not in title and '高尔夫' not in target_cat:
        if '款' in title:
            title = title.replace('款', '款高尔夫', 1)
        else:
            title = '高尔夫' + title
    if title.count('高尔夫') > 1:
        title = _ensure_single_golf(title)

    title = _truncate_with_fillers(title, max_len=30)

    title = title.rstrip(' ，。,.、')
    for cat in ALLOWED_TAIL_CATEGORIES:
        if title.endswith(cat) and cat != target_cat:
            title = title[:-len(cat)]
            break
    if target_cat in APPAREL_CATEGORIES and '服装' not in title:
        insert_pos = title.rfind('高尔夫')
        if insert_pos != -1:
            title = title[:insert_pos + len('高尔夫')] + '服装' + title[insert_pos + len('高尔夫'):]
    if not title.endswith(target_cat):
        title = title + target_cat

    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    brand_main = (brand_short or brand_chinese or '').replace('/', '')
    if brand_key != 'unknown' and brand_main:
        normalized = title.replace(' ', '').lower()
        if brand_main.replace(' ', '').lower() not in normalized:
            title = brand_main + title

    words = list(title)
    i = 1
    while i < len(words):
        if i >= 3 and words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        elif i >= 5 and words[i-4] == words[i-3] == words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        else:
            i += 1
    title = ''.join(words)

    if len(title) > 30:
        title = title[:30]
    elif len(title) < 24:
        pass  # 短标题直接保留，不再强行补词

    return title


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
            title = clean_title(raw_title.strip())
            if not title:
                print(f"尝试 {attempt + 1}: 清理后标题为空，重新生成")
                continue

            title = optimize_title(title, product)

            print(f"✅ 标题生成成功: {title}")
            return title
        else:
            print(f"尝试 {attempt + 1}: GLM返回空，重新生成")

    print("❌ GLM生成失败，2次尝试未通过验证")
    fallback_features = _collect_title_features(product)
    fallback_title = build_template_title(fallback_features)
    print(f"⚠️ 使用模板标题: {fallback_title}")
    return fallback_title


class TitleGenerationError(Exception):
    """标题生成异常"""
    pass
