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

from .classifiers import determine_gender

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
    '帽子', '手套', '球包', '高尔夫球',
]

# 通用填充/修饰词（用于裁剪或补长时优先移除/插入）
FILLER_WORDS = ['时尚', '新款', '运动', '舒适', '经典', '优雅', '精品', '轻便', '透气', '款']
MODIFIERS = ['新款', '时尚', '轻便', '透气', '运动', '专业', '经典', '优雅', '高级', '精品']
FEATURE_KEYWORDS = ['保暖', '防水', '透气', '轻量', '弹力', '抓绒', '速干', '防风', '舒适', '抗皱', '耐磨']
FALLBACK_FILLERS = ['时尚', '舒适', '畅销', '精选']

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
    brand_display = (brand_short or brand_chinese or '').replace('/', '')
    if brand_chinese and brand_short and brand_short not in brand_display:
        brand_display = f"{brand_chinese}{brand_short}"
    if not brand_display:
        brand_display = '卡拉威Callaway'

    region = BRAND_REGION.get(brand_key, '日本')

    gender_raw = determine_gender(product)
    gender_text = {
        '女': '女士',
        '男': '男士'
    }.get(gender_raw, '中性')

    season_phrase = extract_season_from_name(name, product) or get_season_by_date()
    if not season_phrase.endswith('款'):
        season_phrase = season_phrase + '款'

    forced_category = _get_forced_category(product)
    target_category = _resolve_target_category(product)
    if target_category == '场训服' and forced_category and forced_category != '场训服':
        target_category = '其他' if forced_category not in ALLOWED_TAIL_CATEGORIES else forced_category
    if target_category not in ALLOWED_TAIL_CATEGORIES:
        target_category = '其他'

    text_pool = f"{name} {description}"
    feature_tokens = []
    for kw in FEATURE_KEYWORDS:
        if kw in text_pool and kw not in feature_tokens:
            feature_tokens.append(kw)
        if len(feature_tokens) >= 2:
            break
    feature_phrase = ''.join(feature_tokens[:2])

    return {
        'brand_display': brand_display,
        'region': region,
        'gender_text': gender_text,
        'season_phrase': season_phrase,
        'target_category': target_category,
        'feature_phrase': feature_phrase,
        'product_name': name or '未知商品'
    }


def build_template_title(features: Dict[str, str]) -> str:
    parts = [
        features['region'],
        features['season_phrase'],
        features['brand_display'],
        '高尔夫',
        features['gender_text'],
    ]
    if features['feature_phrase']:
        parts.append(features['feature_phrase'])
    parts.append(features['target_category'])
    title = ''.join(parts)

    if len(title) < 26:
        for filler in FALLBACK_FILLERS:
            if filler not in title:
                insert_index = title.rfind(features['target_category'])
                if insert_index != -1:
                    title = title[:insert_index] + filler + features['target_category']
                else:
                    title += filler
                if len(title) >= 26:
                    break
    if len(title) < 26:
        title += '精选'
    if len(title) > 30:
        title = title[:30]
    return title

# ============================================================================
# 品牌提取功能（复用配置模块逻辑）
# ============================================================================

from ..config.brands import extract_brand_from_product as brand_extractor

# 为兼容旧调用，保留同名函数：直接委托给配置模块
def extract_brand_from_product(product: Dict) -> Tuple[str, str, str]:
    return brand_extractor(product)

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
        "你是一名资深电商标题优化师，请根据以下商品信息输出 1 条淘宝标题。\n"
        "必须遵守：\n"
        "1. 长度 26-30 个汉字，结构为“地区+季节款+品牌+高尔夫+性别+功能词+品类”。\n"
        "2. 品牌写成“卡拉威Callaway”这类中文+英文组合，高尔夫只出现一次且紧跟品牌。\n"
        "3. 性别写“男士/女士/中性”，若无法判断写“中性”。\n"
        f"4. 功能词从保暖/防水/透气/轻量/弹力/抓绒/速干/防风/舒适中挑 1-2 个贴合特点，可省略。\n"
        f"5. 结尾必须是以下品类之一：{tail_whitelist}，当前推荐：{features['target_category']}。\n"
        "6. 禁止出现“正品/代购/旗舰/促销/淘宝/拼多多”等词，去掉日文假名、数字编号及符号，不要解释或加引号。\n"
        f"示例：{example_title}\n\n"
        "商品信息：\n"
        f"- 品牌：{features['brand_display']}\n"
        f"- 地区：{features['region']}  季节：{features['season_phrase']}\n"
        f"- 性别：{features['gender_text']}\n"
        f"- 推荐功能词：{features['feature_phrase'] or '保暖/轻量/透气'}\n"
        f"- 品类：{features['target_category']}\n"
        f"- 商品名称：{features['product_name']}\n"
        f"- 描述片段：{desc_text}\n"
        "只输出最终标题。"
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
    for f in FILLER_WORDS:
        if len(title) <= max_len:
            break
        if f in title:
            title = title.replace(f, '', 1)
    if len(title) > max_len:
        title = title[:max_len]
    return title


def _get_forced_category(product: Dict) -> str:
    """根据名称/分类快速识别强制品类"""
    name_hint = (product.get('productName') or product.get('title') or '').lower()
    cat_hint = str(product.get('category', '') or '').lower()
    text = f"{name_hint} {cat_hint}"

    apparel_tokens = ['jacket', 'ブルゾン', 'coat', 'パーカー', 'hoodie',
                      'pants', 'パンツ', 'shirt', 'シャツ', 'sweat', '卫衣', '夹克']
    if any(t in text for t in apparel_tokens):
        pass
    if any(k in text for k in ['バッグ', 'bag', 'キャディ', 'caddy', 'tote', 'トート', 'pouch', 'ポーチ']):
        return '球包' if ('caddy' in text or 'キャディ' in text) else '包'
    if any(k in text for k in ['ボール', 'ball', '球']):
        return '球'
    if any(k in text for k in ['glove', 'グローブ', '手套']):
        return '手套'
    if any(k in text for k in ['cap', '帽', 'キャップ']):
        return '帽子'
    if any(k in text for k in ['vest', 'gilet', 'ベスト', 'ジレ']):
        return '背心'
    if any(k in text for k in ['parka', 'hoodie', 'パーカー']):
        return '连帽衫'
    return ''


def _match_allowed_tail(title: str) -> str:
    """匹配标题结尾的品类"""
    for cat in sorted(ALLOWED_TAIL_CATEGORIES, key=len, reverse=True):
        if title.endswith(cat):
            return cat
    if title.endswith('球'):
        return '球'
    return ''


def _resolve_target_category(product: Dict) -> str:
    """综合分类/名称/强制品类，确定标题尾部使用的品类"""
    # 优先使用强制品类
    forced = _get_forced_category(product)
    if forced == '球':
        forced = '高尔夫球'
    if forced:
        return forced

    # 其次使用分类文本命中白名单
    category_text = str(product.get('category', '') or '').lower()
    for cat in ALLOWED_TAIL_CATEGORIES:
        if cat.lower() in category_text:
            return cat

    # 兜底：若产品名中含常见品类关键词
    name_hint = (product.get('productName') or product.get('title') or '').lower()
    for cat in ALLOWED_TAIL_CATEGORIES:
        if cat.lower() in name_hint:
            return cat

    return '其他'


def optimize_title(title: str, product: Dict = None) -> str:
    """
    优化标题，解决之前遇到的问题
    """
    if not title:
        return title

    product = product or {}
    forced_cat = _get_forced_category(product)
    target_cat = _resolve_target_category(product)

    # 1. 去除日文、斜杠和特殊符号，保留品牌英文与空格；移除通用英文占位如 UNISEX
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uFF66-\uFF9F]')
    title = japanese_pattern.sub('', title)
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]+', '', title)
    title = re.sub(r'(?i)unisex', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace('中棉', '棉服').replace('中綿', '棉服')

    # 2. 确保含“高尔夫”，若缺少则补在“款”后或最前
    if '高尔夫' not in title:
        if '款' in title:
            title = title.replace('款', '款高尔夫', 1)
        else:
            title = '高尔夫' + title
    if title.count('高尔夫') > 1:
        title = _ensure_single_golf(title)

    # 3. 如果长度超标，优先移除填充词再截断
    title = _truncate_with_fillers(title, max_len=30)

    # 4. 根据强制品类兜底修正结尾
    if forced_cat:
        wrong_tail = ['夹克', '外套', '卫衣', '毛衣', '长裤', '短裤', '裤', '背心']
        for w in wrong_tail:
            if title.endswith(w):
                title = title[:-len(w)]
        mapping = {
            '球包': '球包',
            '包': '包',
            '球': '高尔夫球',
            '手套': '手套',
            '帽子': '帽子',
            '背心': '背心',
            '连帽衫': '连帽衫'
        }
        replacement = mapping.get(forced_cat, forced_cat)
        if not title.endswith(replacement):
            title = title.rstrip('夹克外套卫衣毛衣长裤短裤裤') + replacement
        if len(title) > 30:
            title = _truncate_with_fillers(title, max_len=30)
            if len(title) > 30 and len(replacement) < 30:
                title = title[:30 - len(replacement)] + replacement

    tail = _match_allowed_tail(title)
    if tail == '球' and target_cat != '高尔夫球':
        title = title[:-1] + target_cat
    elif tail and tail not in ALLOWED_TAIL_CATEGORIES:
        title = title[:-len(tail)] + target_cat
    elif not tail:
        title = title.rstrip(' ，。,.、') + target_cat

    # 品牌缺失时补品牌短名
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    brand_main = (brand_short or brand_chinese or '').replace('/', '')
    if brand_key != 'unknown' and brand_main:
        normalized = title.replace(' ', '').lower()
        if brand_main.replace(' ', '').lower() not in normalized:
            title = brand_main + title

    # 性别缺失时补
    gender_word = ''
    gender_val = str(product.get('gender', '') or '')
    if gender_val:
        if gender_val.lower() in ['女', '女性', 'womens', 'ladies']:
            gender_word = '女士'
        elif gender_val.lower() in ['男', '男性', 'mens', 'men']:
            gender_word = '男士'
    if gender_word and gender_word not in title:
        title = title + gender_word

    # 5. 去除连续重复的词
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

    # 6. 长度调整（26-30）
    if len(title) > 30:
        title = title[:30]
    elif len(title) < 26:
        insert_pos = -1
        golf_idx = title.find('高尔夫')
        if golf_idx > 0 and golf_idx + 3 < len(title):
            insert_pos = golf_idx + 3

        if insert_pos > 0:
            need_len = 26 - len(title)
            found = False
            for n in range(1, 5):
                for combo in combinations(MODIFIERS, n):
                    for perm in iter_product(combo, repeat=n):
                        if len(set(perm)) != n:
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

            if not found and len(title) < 26:
                need_len = 26 - len(title)
                if need_len <= 2:
                    add_mod = '新款'
                elif need_len <= 4:
                    add_mod = '舒适时尚'
                elif need_len <= 6:
                    add_mod = '新款时尚轻便'
                else:
                    add_mod = ''
                    for mod in ['新款', '时尚', '轻便', '透气', '运动']:
                        if len(add_mod) + len(mod) <= need_len:
                            add_mod += mod
                        if len(add_mod) >= need_len:
                            break

                title = title[:insert_pos] + add_mod + title[insert_pos:]
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

    if not (26 <= len(title) <= 30):
        return False

    if '高尔夫' not in title or title.count('高尔夫') != 1:
        return False

    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    brand_short_clean = (brand_short or '').replace('/', '')
    brand_full_clean = (BRAND_MAP.get(brand_key, brand_short) or '').replace('/', '')
    title_nospace = title.replace(' ', '').lower()
    if brand_key != 'unknown':
        candidates = set()
        if brand_short_clean:
            candidates.add(brand_short_clean.replace(' ', '').lower())
        if brand_full_clean:
            candidates.add(brand_full_clean.replace(' ', '').lower())
        for kw in BRAND_KEYWORDS.get(brand_key, []):
            candidates.add(kw.replace(' ', '').replace('/', '').lower())
        if not any(c and c in title_nospace for c in candidates):
            return False

    for word in FORBIDDEN_WORDS:
        if word in title:
            return False

    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', title):
        return False

    if re.search(r'(.)\1{2,}', title):
        return False
    if re.search(r'(..)\1{2,}', title):
        return False

    tail = _match_allowed_tail(title)
    if tail == '' or tail == '球':
        return False
    if tail not in ALLOWED_TAIL_CATEGORIES:
        return False

    return True


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

            if validate_title(title, product):
                print(f"✅ 标题生成成功: {title}")
                return title
            else:
                print(f"尝试 {attempt + 1}: 验证失败，重新生成")
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
