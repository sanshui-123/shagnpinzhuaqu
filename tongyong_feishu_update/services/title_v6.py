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
    '短袖', '长袖', 'T恤', 'POLO',
    '短裤', '长裤', '短裙', '连衣裙',
    '帽子', '手套', '球包', '高尔夫球',
    '紧身衣裤', '训练服', '场训服', '腰带', '袜子', '其他'
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
    # 🔥 确保所有字段都是字符串类型
    brand_from_json = str(product.get('brand', '') or '')
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

    # 🔥 确保 name 和 url 都是字符串
    name = str(product.get('productName', '') or '').lower()
    url = str(product.get('detailUrl', '') or '').lower()

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

    # 未匹配到品牌时，不强制回落卡拉威，返回未知品牌
    return (
        'unknown',
        '未知品牌',
        ''
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
    # 🔥 使用 get 方法安全获取 _original_data
    original_data = product.get('_original_data', None)
    if original_data:

        # 检查尺码表中的季节信息
        size_chart = original_data.get('尺码表', {}) if isinstance(original_data, dict) else {}
        if isinstance(size_chart, dict) and 'tables' in size_chart:
            tables = size_chart.get('tables', [])
            for table in tables:
                # 🔥 确保 text 字段是字符串类型
                table_text = str(table.get('text', '') or '') if isinstance(table, dict) else ''
                if table_text and 'シーズン' in table_text:
                    # 提取 "2025年 秋冬" 格式的季节信息
                    # 使用正则表达式匹配 "年份 季节" 格式
                    season_match = re.search(r'(\d{4})年\s*(春夏|秋冬)', table_text)
                    if season_match:
                        year = season_match.group(1)[2:]  # 取后两位，如2025->25
                        season_text = season_match.group(2)  # 春夏或秋冬
                        return f"{year}{season_text}"

        # 也可以从html中搜索
        # 🔥 确保 html 字段是字符串类型
        html = str(size_chart.get('html', '') or '') if isinstance(size_chart, dict) else ''
        if html:
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

    # 拼接辅助信息，弥补分类文件字段缺失
    category_text = str(product.get('category', '') or '')
    desc_text = str(product.get('description', '') or '')[:80]
    gender_text_raw = gender_text or '未提供'
    target_tail = _resolve_target_category(product)
    tail_whitelist = '、'.join(ALLOWED_TAIL_CATEGORIES)

    prompt = (
        "请生成淘宝标题，长度 26-30 字，务必遵循下列规则：\n"
        f"1) 格式：[地区][季节款][品牌]高尔夫[性别][功能词可选][品类结尾]，高尔夫固定只出现 1 次，放在品牌之后。\n"
        f"2) 地区：{region}；季节：{current_season}（写成“{current_season}款”放品牌前）。\n"
        f"3) 品牌：{brand_display or '请写实际品牌'}，可含品牌英文，禁止写“未知品牌”。性别：{gender_text or '按商品判定男士/女士/中性'}。\n"
        "4) 功能词可选保暖/防泼水/弹力/抓绒/轻量/棉服等，“中棉/中綿”统一写成棉服。\n"
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


def _get_forced_category(product: Dict) -> str:
    """基于商品名称/分类判断强制品类（用于标题兜底，不影响服装分类字段）"""
    name_hint = (product.get('productName') or product.get('title') or '').lower()
    cat_hint = str(product.get('category', '') or '').lower()
    text = name_hint + ' ' + cat_hint
    # 若明显是服装关键词，避免误判为配件
    apparel_tokens = ['jacket', 'ブルゾン', 'coat', 'パーカー', 'hoodie', 'pants', 'パンツ', 'shirt', 'シャツ', 'sweat', '卫衣', '夹克']
    if any(t in text for t in apparel_tokens):
        pass  # 不提前返回，让后续服装判定继续
    # 包/球包
    if any(k in text for k in ['バッグ', 'bag', 'キャディ', 'caddy', 'tote', 'トート', 'pouch', 'ポーチ']):
        return '球包' if 'caddy' in text or 'キャディ' in text else '包'
    # 球
    if any(k in text for k in ['ボール', 'ball', '球']):
        return '球'
    # 手套
    if any(k in text for k in ['glove', 'グローブ', '手套']):
        return '手套'
    # 帽子
    if any(k in text for k in ['cap', '帽', 'キャップ']):
        return '帽子'
    # 背心
    if any(k in text for k in ['vest', 'gilet', 'ベスト', 'ジレ']):
        return '背心'
    # 连帽衫
    if any(k in text for k in ['parka', 'hoodie', 'パーカー']):
        return '连帽衫'
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


def _match_allowed_tail(title: str) -> str:
    """匹配标题结尾的品类（按白名单和常见错误尾巴）"""
    for cat in sorted(ALLOWED_TAIL_CATEGORIES, key=len, reverse=True):
        if title.endswith(cat):
            return cat
    if title.endswith('球'):
        return '球'
    return ''


def optimize_title(title: str, product: Dict = None) -> str:
    """
    优化标题，解决之前遇到的问题
    """
    if not title:
        return title

    forced_cat = _get_forced_category(product or {})
    target_cat = _resolve_target_category(product or {})

    # 1. 去除日文、斜杠和特殊符号，保留品牌英文与空格；移除通用英文占位如 UNISEX
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uFF66-\uFF9F]')
    title = japanese_pattern.sub('', title)
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]+', '', title)
    title = re.sub(r'(?i)unisex', '', title)
    # 允许英文和空格，但压缩多余空格
    title = re.sub(r'\s+', ' ', title).strip()
    # 中棉/中綿 统一为 棉服
    title = title.replace('中棉', '棉服').replace('中綿', '棉服')

    # 2. 确保含“高尔夫”，若缺少则补在“款”后或开头
    if '高尔夫' not in title:
        if '款' in title:
            title = title.replace('款', '款高尔夫', 1)
        else:
            title = '高尔夫' + title

    # 确保"高尔夫"只出现一次
    if title.count('高尔夫') > 1:
        title = _ensure_single_golf(title)

    # 3. 如长度因补“高尔夫”超长，优先移除修饰词/低优先占位再截断
    title = _truncate_with_fillers(title, max_len=30)

    # 4. 根据强制品类兜底修正结尾
    if forced_cat:
        # 去掉错误的服装结尾
        wrong_tail = ['夹克', '外套', '卫衣', '毛衣', '长裤', '短裤', '裤', '背心']
        for w in wrong_tail:
            if title.endswith(w):
                title = title[: -len(w)]
        if forced_cat == '球包':
            if '球包' not in title:
                title += '球包'
        elif forced_cat == '包':
            if '包' not in title:
                title += '包'
        elif forced_cat == '球':
            if '球' not in title:
                title += '高尔夫球'
        elif forced_cat == '手套':
            if '手套' not in title:
                title += '手套'
        elif forced_cat == '帽子':
            if '帽子' not in title:
                title += '帽子'
        elif forced_cat == '背心':
            if not title.endswith('背心'):
                title = title.rstrip('夹克外套卫衣毛衣长裤短裤裤') + '背心'
        elif forced_cat == '连帽衫':
            if not title.endswith('连帽衫'):
                title = title.rstrip('夹克外套毛衣长裤短裤裤') + '连帽衫'
        # 再次长度校验，若因补品类超长，尝试移除修饰词后截断到30
        if len(title) > 30:
            title = _truncate_with_fillers(title, max_len=30)
            if len(title) > 30:
                # 尽量保留结尾品类
                if len(forced_cat) < 30:
                    title = title[:30 - len(forced_cat)] + forced_cat
                else:
                    title = forced_cat[:30]

    # 4.5 结尾品类白名单与尾部“球”纠偏
    tail = _match_allowed_tail(title)
    if tail == '球' and target_cat != '高尔夫球':
        title = title[:-1] + target_cat
    elif tail and tail not in ALLOWED_TAIL_CATEGORIES:
        title = title[: -len(tail)] + target_cat
    elif not tail:
        title = title.rstrip(' ，。,.、') + target_cat

    # 品牌缺失时补品牌短名（放在最前）
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product or {})
    brand_main = (brand_short or brand_chinese or '').replace('/', '')
    if brand_key != 'unknown' and brand_main:
        normalized = title.replace(' ', '').lower()
        if brand_main.replace(' ', '').lower() not in normalized:
            title = brand_main + title

    # 性别缺失时补
    gender_word = ''
    gender_val = str((product or {}).get('gender', '') or '')
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
        # 检查2字重复
        if i >= 3 and words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        # 检查3字重复
        elif i >= 5 and words[i-4] == words[i-3] == words[i-2] == words[i-1] == words[i]:
            words.pop(i)
        else:
            i += 1
    title = ''.join(words)

    # 6. 长度调整（26-30）
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

    # 3. 必须包含对应品牌（若无法识别品牌则跳过此校验）
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    brand_short_clean = (brand_short or '').replace('/', '')
    brand_full_clean = BRAND_MAP.get(brand_key, brand_short) or ''
    brand_full_clean = brand_full_clean.replace('/', '')
    title_nospace = title.replace(' ', '').lower()

    if brand_key != 'unknown':
        candidates = set()
        if brand_short_clean:
            candidates.add(brand_short_clean.replace(' ', '').lower())
        if brand_full_clean:
            candidates.add(brand_full_clean.replace(' ', '').lower())
        # 加入品牌关键词（去空格/斜杠）作为候选
        for kw in BRAND_KEYWORDS.get(brand_key, []):
            candidates.add(kw.replace(' ', '').replace('/', '').lower())
        # 匹配任一即可
        if not any(c and c in title_nospace for c in candidates):
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

    # 6. 不能包含日文字符
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', title):
        return False

    # 7. 不能包含连续重复
    if re.search(r'(.)\1{2,}', title):  # 3个及以上相同字符连续
        return False
    if re.search(r'(..)\1{2,}', title):  # 2字词语重复3次
        return False

    # 8. 结尾品类必须在白名单，且非高尔夫球时不得以“球”结尾
    tail = _match_allowed_tail(title)
    if tail == '' or tail == '球':
        return False
    if tail not in ALLOWED_TAIL_CATEGORIES:
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
            title = optimize_title(title, product)

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
