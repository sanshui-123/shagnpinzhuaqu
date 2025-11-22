"""
标题生成系统 - 核心逻辑
版本：v6.1 - 精简款（地区+季节款）
核心思想：提示词简短，明确格式，带“地区+季节款”
"""

import re
import requests
import os
from typing import Dict, Tuple
from itertools import combinations
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
    '帽子', '手套', '球包', '高尔夫球',
]

# 通用填充/修饰词（用于裁剪或补长时优先移除/插入）
FILLER_WORDS = ['时尚', '新款', '运动', '舒适', '经典', '优雅', '精品', '轻便', '透气', '款']
MODIFIERS = ['新款', '时尚', '轻便', '透气', '运动', '专业', '经典', '优雅', '高级', '精品']

# 禁用词
FORBIDDEN_WORDS = [
    '官网', '正品', '专柜', '代购', '海外', '进口',
    '授权', '旗舰', '限量', '促销', '特价', '淘宝',
    '天猫', '京东', '拼多多'
]

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
    # 🔥 确保所有字段都是字符串类型
    name = str(
        product.get('productName')
        or product.get('title')
        or product.get('name')
        or product.get('product_name')
        or ''
    )
    gender = str(product.get('gender', '') or '')

    # 提取品牌信息
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    # 品牌文案：中文+英文（去掉斜杠）
    brand_display = (BRAND_MAP.get(brand_key, brand_short)).replace('/', '')
    region = BRAND_REGION.get(brand_key, '日本')

    # 性别映射
    gender_text = ""
    if gender:
        if gender.lower() in ['女', '女性', 'womens', 'ladies']:
            gender_text = "女士"
        elif gender.lower() in ['男', '男性', 'mens', 'men']:
            gender_text = "男士"

    # 🎯 智能季节判断（从表格数据优先）
    current_season = extract_season_from_name(name, product) or get_season_by_date()
    # 季节可带“款”可不带

    # 品类提示（兜底给 GLM 明确方向，避免配件写成夹克）
    name_hint = name.lower()
    if any(k in name_hint for k in ['バッグ', 'bag', 'キャディ', 'caddy']):
        category_hint = '高尔夫球包（中性，可不写性别）'
    elif any(k in name_hint for k in ['ボール', 'ball']):
        category_hint = '高尔夫球'
    elif any(k in name_hint for k in ['cap', '帽', 'キャップ']):
        category_hint = '帽子'
    elif any(k in name_hint for k in ['glove', 'グローブ', '手套']):
        category_hint = '手套'
    else:
        category_hint = '服装或配件，按商品名匹配准确品类'

    prompt = (
        "请生成淘宝标题，长度 26-30 字，务必遵循下列规则：\n"
        f"1) 格式：[地区][季节款][品牌]高尔夫[性别][功能词可选][品类结尾]，高尔夫固定只出现 1 次，放在品牌之后。\n"
        f"2) 地区：{region}；季节：{current_season}（写成“{current_season}款”放品牌前）。\n"
        f"3) 品牌：{brand_display or '请写实际品牌'}，可含品牌英文，禁止写“未知品牌”。性别：{gender_text or '按商品判定男士/女士/中性'}。\n"
        "4) 功能词可选保暖/防泼水/弹力/抓绒/轻量/透气/速干，“中棉/中綿”统一写成棉服。\n"
        f"5) 结尾必须是白名单品类之一：{tail_whitelist}；当前建议品类：{category_hint}（优先写 {target_tail}），除非品类是“高尔夫球”，否则禁止以单字“球”结尾，不要用“运动/时尚”。\n"
        "6) 禁止出现正品/代购/旗舰/促销等词，只能使用简体中文和品牌英文，去掉日文假名、斜杠、特殊符号。\n"
        f"补充信息：商品名《{name}》，分类/性别：{category_text} / {gender_text_raw}，描述片段：{desc_text}\n"
        "直接输出符合格式的标题，不要解释。"
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


def optimize_title(title: str, product: Dict = None) -> str:
    """
    优化标题，解决之前遇到的问题
    """
    if not title:
        return title

    # 1. 去除连续重复的词
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

    # 2. 长度调整（26-30）
    if len(title) > 30:
        title = title[:30]
    elif len(title) < 26:
        # 如果太短，尝试在"高尔夫"后插入修饰词
        insert_pos = -1
        golf_idx = title.find('高尔夫')
        if golf_idx > 0 and golf_idx + 3 < len(title):
            insert_pos = golf_idx + 3

        if insert_pos > 0:
            need_len = 26 - len(title)
            found = False
            for n in range(1, 5):
                from itertools import product as iter_product
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

                # 最终检查：如果还是不够26字或超过30字，截断/补充
                if len(title) < 26:
                    title = title[:insert_pos] + add_mod + '优雅' + title[insert_pos:]
                if len(title) > 30:
                    title = title[:30]

class TitleGenerationError(Exception):
    """标题生成异常"""
    pass
