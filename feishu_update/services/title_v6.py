"""
标题生成系统 - 核心逻辑
版本：v6.0 - 方案C混合模式
核心思想：硬性规则代码控制，软性判断交给GLM
"""

import re
import random
import time
import threading
import requests
import os
from typing import Dict, List, Tuple, Optional
from ..config.title_config import *

# 全局变量
glm_call_lock = threading.Lock()
last_glm_call_ts = 0.0

# ============================================================================
# 一、基础信息推断（代码实现）
# ============================================================================

def determine_gender(product: Dict) -> str:
    """
    推断性别

    优先级：
    1. category字段
    2. URL路径
    3. 商品名
    4. 默认"男"

    Returns:
        "男" or "女"
    """
    category = product.get('category', '').lower()
    url = product.get('detailUrl', '').lower()
    name = product.get('productName', '').lower()

    # 女性关键词（优先检查，避免"women"与"men"冲突）
    female_keywords = ['womens', 'women', 'ladies', 'lady', 'レディース', '女士', '女款']
    male_keywords = ['mens', 'men', 'メンズ', '男士', '男款']

    # 检查category
    for keyword in female_keywords:
        if keyword in category:
            return "女"
    for keyword in male_keywords:
        if keyword in category:
            return "男"

    # 检查URL（精确匹配，避免冲突）
    if any(f'/{kw}/' in url for kw in ['womens', 'women', 'ladies']):
        return "女"
    if any(f'/{kw}/' in url for kw in ['mens', 'men']):
        return "男"

    # 检查商品名
    for keyword in female_keywords:
        if keyword in name:
            return "女"
    for keyword in male_keywords:
        if keyword in name:
            return "男"

    return "男"  # 默认


def determine_category(product: Dict) -> str:
    """
    推断大分类（只分6大类）

    Returns:
        '外套' | '上衣' | '下装' | '鞋类' | '配件' | '雨具'
    """
    name = product.get('productName', '').lower()
    category = product.get('category', '').lower()

    # 关键词映射（日文+英文）
    keywords_map = {
        CATEGORY_OUTERWEAR: [
            'ブルゾン', 'blouson', 'ジャケット', 'jacket', 'ベスト', 'vest',
            'コート', 'coat', 'アウター', 'outer', 'パーカー', 'parka',
            'ダウン', 'down', 'フリース', 'fleece', '外套', '夹克'
        ],
        CATEGORY_TOP: [
            'ポロ', 'polo', 'シャツ', 'shirt', 'トップ', 'top',
            'ニット', 'knit', 'セーター', 'sweater', 'スウェット', 'sweat',
            'カットソー', 'cutsew', 'Tシャツ', 'tシャツ', 't-shirt',
            '上衣', '衬衫', '卫衣'
        ],
        CATEGORY_BOTTOM: [
            'パンツ', 'pants', 'ショート', 'short', 'スカート', 'skirt',
            'ズボン', 'ロング', 'long', '裤', '短裤', '长裤', '裙'
        ],
        CATEGORY_SHOES: [
            'シューズ', 'shoes', 'スニーカー', 'sneaker', 'ゴルフシューズ',
            '鞋', '球鞋'
        ],
        CATEGORY_RAINWEAR: [
            'レイン', 'rain', '雨', '防水'
        ],
        CATEGORY_ACCESSORY: [
            'キャップ', 'cap', 'ハット', 'hat', 'ビーニー', 'beanie',
            'グローブ', 'glove', 'ベルト', 'belt', 'ソックス', 'socks',
            'ヘッドカバー', 'headcover', 'head cover', 'カバー', 'cover',
            '帽', '手套', '袜', '腰带', '护腕', '头带', '围脖',
            'marker', 'マーカー', 'クリップ', 'clip', 'ball marker',
            'フェアウェイカバー', 'driver cover'
        ]
    }

    # 匹配
    combined_text = f"{name} {category}"
    for cat, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in combined_text:
                return cat

    return CATEGORY_OUTERWEAR  # 默认


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


def extract_season_from_name(name: str) -> str:
    """
    提取季节

    优先级：
    1. 年份+季节代码（25FW, 26SS等）
    2. 中文季节（秋冬、春夏）
    3. 默认"25秋冬"

    Returns:
        "25秋冬" | "26春夏" 等
    """
    name_upper = name.upper()

    # 匹配年份+季节代码
    season_match = re.search(r'(\d{2})(FW|SS|AW|SP)', name_upper)
    if season_match:
        year = season_match.group(1)
        season_code = season_match.group(2)

        if season_code in ['FW', 'AW']:
            return f"{year}秋冬"
        elif season_code in ['SS', 'SP']:
            return f"{year}春夏"

    # 匹配中文季节
    if '秋冬' in name:
        year_match = re.search(r'(\d{2})秋冬', name)
        if year_match:
            return f"{year_match.group(1)}秋冬"
        return "25秋冬"
    elif '春夏' in name:
        year_match = re.search(r'(\d{2})春夏', name)
        if year_match:
            return f"{year_match.group(1)}春夏"
        return "26春夏"

    return "25秋冬"  # 默认


def is_small_accessory(category: str, product_name: str) -> bool:
    """
    判断是否是小配件

    小配件特征：
    1. category是"配件"
    2. 商品名包含小配件关键词

    Returns:
        True: 小配件（袜子、帽子等）
        False: 标准服装
    """
    if category != CATEGORY_ACCESSORY:
        return False

    name_lower = product_name.lower()
    accessory_keywords = [
        'ソックス', 'socks', '袜',
        'キャップ', 'cap', 'ハット', 'hat', 'ビーニー', 'beanie', '帽',
        'グローブ', 'glove', '手套',
        'ベルト', 'belt', '腰带', '皮带',
        'ヘッドカバー', 'headcover', 'head cover', 'カバー', 'cover',
        '護腕', '腕帯', '头帯', '围脖',
        'marker', 'マーカー', 'クリップ', 'clip', 'ball marker',
        'フェアウェイカバー', 'driver cover'
    ]

    return any(kw in name_lower for kw in accessory_keywords)


# ============================================================================
# 二、GLM API调用
# ============================================================================

def call_glm_api(
    prompt: str,
    model: str = TITLE_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 500
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
        "Authorization": f"{api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # 限流
    with glm_call_lock:
        current_ts = time.time()
        elapsed = current_ts - last_glm_call_ts
        if elapsed < GLM_MIN_INTERVAL:
            time.sleep(GLM_MIN_INTERVAL - elapsed)
        last_glm_call_ts = time.time()

    # 重试机制
    max_retries = 3
    for retry in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    content = data['choices'][0]['message']['content']
                    print(f"[GLM Debug] content: {content[:200]}...")
                    return content.strip()
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
# 三、智能Prompt构建（方案C核心）
# ============================================================================

def build_smart_prompt(
    product: Dict,
    gender: str,
    category: str,
    brand_chinese: str,
    season: str,
    is_accessory: bool
) -> str:
    """
    构建简洁Prompt - 优化版本，控制在350字以内
    """
    name = product.get('productName', '')
    gender_word = '男士' if gender == '男' else '女士'
    name_lower = name.lower()

    # 根据类别使用不同的模板
    if is_accessory:
        # 配件类专用极短模板，带类型标注
        # 检测配件类型
        accessory_type = "配件"
        if 'marker' in name_lower or 'マーカー' in name_lower:
            accessory_type = "记分标记夹"
        elif 'head' in name_lower and ('cover' in name_lower or 'カバー' in name):
            accessory_type = "球杆头套"
        elif 'belt' in name_lower or 'ベルト' in name_lower or '腰带' in name_lower:
            accessory_type = "腰带"

        return f"""将日文商品名改写成中文标题。

这是高尔夫{accessory_type}，禁止输出外套/上衣词汇。
要求：25-30字，格式：{season}{brand_chinese}高尔夫{gender_word}+功能词+结尾词。
结尾必须是：帽子,手套,袜子,球包,球杆头套,毛巾,腰带,皮带,伞,防晒用品,清洁用品之一。
禁止：服饰,精品,限定,训练,球场,外套,上衣,夹克。

名称：{name}
标题："""
    else:
        # 服装类简洁模板
        return f"""将日文商品名改写成中文标题。

要求：26-30字，格式：{season}{brand_chinese}高尔夫{gender_word}+功能词+结尾词。
结尾必须是：外套,夹克,上衣,POLO衫,T恤,裤,短裤,雨衣之一。
若有"中綿"或"中棉"必须写成"棉服"。
禁止：服饰,精品,限定,训练,球场。

例如：
✓ 25秋冬卡拉威高尔夫男士保暖舒适外套
✗ 25秋冬卡拉威高尔夫男士精品服饰

名称：{name}
标题："""


# ============================================================================
# 四、硬性规则检查与修正（方案C核心）
# ============================================================================

def enforce_hard_rules(title: str, category: str, is_accessory: bool) -> str:
    """
    强制执行硬性规则（代码控制）

    处理步骤：
    1. 清理格式（日文、繁体、符号）
    2. 移除禁止词
    3. 确保"高尔夫"只有1次
    4. 长度控制
    5. 结尾词完整性
    6. 重复词清理

    Returns:
        修正后的标题
    """
    if not title:
        return ""

    # ========================================================================
    # 步骤1：清理格式
    # ========================================================================
    # 移除日文
    title = JAPANESE_CHAR_PATTERN.sub('', title)
    # 全角转半角
    title = title.translate(FULLWIDTH_TO_HALFWIDTH)
    # 繁体转简体
    title = title.translate(TRADITIONAL_TO_SIMPLIFIED)
    # 清理空格和特殊符号
    title = re.sub(r'\s+', '', title)
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]', '', title)

    # 代码级兜底：强制替换中棉
    title = title.replace('中綿', '棉服').replace('中棉', '棉服')

    # ========================================================================
    # 步骤2：移除禁止词
    # ========================================================================
    for forbidden in FORBIDDEN_WORDS:
        title = title.replace(forbidden, '')

    # ========================================================================
    # 步骤3：确保"高尔夫"只有1次
    # ========================================================================
    parts = title.split('高尔夫')
    if len(parts) > 2:
        # 保留第一个"高尔夫"，去掉其他
        title = parts[0] + '高尔夫' + ''.join(parts[1:])

    # ========================================================================
    # 步骤4：长度控制
    # ========================================================================
    min_len = ACCESSORY_MIN_LEN if is_accessory else APPAREL_MIN_LEN
    max_len = ACCESSORY_MAX_LEN if is_accessory else APPAREL_MAX_LEN

    # 太长 → 智能截断（保留结尾词）
    if len(title) > max_len:
        # 检查是否包含允许的结尾词
        allowed_endings = ALLOWED_ENDINGS_ACCESSORIES if is_accessory else ALLOWED_ENDINGS_APPAREL
        found_ending = None
        for ending in sorted(allowed_endings, key=len, reverse=True):
            if ending in title:
                found_ending = ending
                idx = title.rfind(ending)
                # 如果结尾词+前面内容长度合适，保留到结尾词
                if idx + len(ending) <= max_len:
                    title = title[:idx + len(ending)]
                    break
        # 如果没有找到合适的结尾词，才简单截断
        if not found_ending or len(title) > max_len:
            title = title[:max_len]

    # ========================================================================
    # 步骤5：结尾词完整性检查与修正
    # ========================================================================
    allowed_endings = ALLOWED_ENDINGS_ACCESSORIES if is_accessory else ALLOWED_ENDINGS_APPAREL

    # 检查是否以允许的结尾词结束
    has_valid_ending = any(title.endswith(ending) for ending in allowed_endings)

    if not has_valid_ending:
        # 检查是否被截断（结尾是截断字符）
        if title and title[-1] in TRUNCATION_CHARS:
            # 尝试从标题中找到最近的完整结尾词
            for ending in sorted(allowed_endings, key=len, reverse=True):
                if ending in title:
                    idx = title.rfind(ending)
                    title = title[:idx + len(ending)]
                    has_valid_ending = True
                    break

        # 如果还是没有有效结尾，根据大分类补充
        if not has_valid_ending:
            # 根据大分类选择默认结尾
            default_endings = {
                CATEGORY_OUTERWEAR: '外套',
                CATEGORY_TOP: '上衣',
                CATEGORY_BOTTOM: '长裤',
                CATEGORY_SHOES: '球鞋',
                CATEGORY_ACCESSORY: '帽子',
                CATEGORY_RAINWEAR: '雨衣'
            }

            default_ending = default_endings.get(category, '外套')

            # 如果标题太长，先截断再补结尾
            if len(title) + len(default_ending) > max_len:
                title = title[:max_len - len(default_ending)]

            title = title + default_ending

    # 代码级兜底：配件特定关键词结尾修正
    if is_accessory:
        lower_title = title.lower()
        if 'head' in lower_title and ('cover' in lower_title or 'カバー' in title):
            # 球杆头套
            if not title.endswith('球杆头套'):
                # 移除旧结尾，添加正确结尾
                for old_ending in ['帽子', '套子', '套']:
                    if title.endswith(old_ending):
                        title = title[:-len(old_ending)]
                if len(title) + 4 <= 30:  # 确保长度不超限
                    title += '球杆头套'
        elif 'marker' in lower_title or 'マーカー' in title:
            # 标记夹
            if not title.endswith('标记夹'):
                for old_ending in ['帽子', '夹子', '夹']:
                    if title.endswith(old_ending):
                        title = title[:-len(old_ending)]
                if len(title) + 3 <= 30:
                    title += '标记夹'

    # ========================================================================
    # 步骤6：清理重复词（连续重复）
    # ========================================================================
    title = re.sub(r'([\u4e00-\u9fff]{2,})\1+', r'\1', title)

    # ========================================================================
    # 步骤7：最终长度验证（严格不超标）
    # ========================================================================
    if len(title) > max_len:
        title = title[:max_len]

    return title.strip()


def validate_title_quality(
    title: str,
    brand_chinese: str,
    category: str,
    is_accessory: bool
) -> bool:
    """
    质量检查（严格验证）

    检查项：
    1. 标题不为空
    2. 长度在范围内
    3. 包含品牌
    4. "高尔夫"恰好1次
    5. 结尾词完整
    6. 无连续重复
    7. 无错误指示词（不是复述任务）

    Returns:
        True: 通过检查
        False: 未通过，需要回退
    """
    if not title:
        return False

    # 检查长度
    min_len = ACCESSORY_MIN_LEN if is_accessory else APPAREL_MIN_LEN
    max_len = ACCESSORY_MAX_LEN if is_accessory else APPAREL_MAX_LEN

    if not (min_len <= len(title) <= max_len):
        return False

    # 检查品牌（放宽匹配）
    # 尝试多种品牌匹配方式
    has_brand = False
    # 1. 完整品牌匹配
    if brand_chinese in title:
        has_brand = True
    # 2. 中文部分匹配（去除英文）
    else:
        brand_cn_part = brand_chinese.split('Callaway')[0] if 'Callaway' in brand_chinese else brand_chinese
        brand_cn_part = brand_cn_part.strip()
        if brand_cn_part in title:
            has_brand = True
        # 3. 尝试单独匹配"卡拉威"
        elif '卡拉威' in brand_chinese and '卡拉威' in title:
            has_brand = True

    if not has_brand:
        return False

    # 检查"高尔夫"次数
    if title.count('高尔夫') != 1:
        return False

    # 检查结尾词
    allowed_endings = ALLOWED_ENDINGS_ACCESSORIES if is_accessory else ALLOWED_ENDINGS_APPAREL
    if not any(title.endswith(ending) for ending in allowed_endings):
        return False

    # 检查连续重复
    if REPEAT_PATTERN.search(title):
        return False

    # 检查是否包含错误指示词（说明GLM在复述任务而不是输出标题）
    for indicator in ERROR_INDICATORS:
        if indicator in title:
            return False

    return True


# ============================================================================
# 五、回退方案（方案C兜底）
# ============================================================================

def generate_fallback_title(
    brand_chinese: str,
    season: str,
    gender: str,
    category: str,
    is_accessory: bool,
    product_name: str = ''
) -> str:
    """
    回退方案：使用模板生成标题

    当GLM失败时使用，确保总能生成合规标题
    """
    gender_word = '男士' if gender == '男' else '女士'

    # 根据大分类选择功能词
    function_words_map = {
        CATEGORY_OUTERWEAR: ['防风', '保暖', '舒适'],
        CATEGORY_TOP: ['速干', '透气', '舒适'],
        CATEGORY_BOTTOM: ['弹力', '舒适', '速干'],
        CATEGORY_SHOES: ['防滑', '舒适', '轻量'],
        CATEGORY_ACCESSORY: ['舒适', '弹力', '防滑'],
        CATEGORY_RAINWEAR: ['防水', '防风', '轻量']
    }

    function_words = function_words_map.get(category, ['舒适', '透气'])

    # 智能选择配件结尾词
    if is_accessory and product_name:
        name_lower = product_name.lower()
        # 使用原始名称进行日文字符匹配
        name_original = product_name
        if any(kw in name_lower for kw in ['ベルト', 'belt', '腰带', '皮带']):
            ending = '腰带'
        elif 'ヘッドカバー' in name_original or 'headcover' in name_lower or 'head cover' in name_lower:
            ending = '球杆头套'  # 明确使用球杆头套
        elif any(kw in name_lower for kw in ['marker', 'マーカー', 'クリップ', 'clip', 'ball marker']):
            ending = '标记夹'
        elif any(kw in name_lower for kw in ['キャップ', 'cap', 'ハット', 'hat', '帽']):
            ending = '帽子'
        elif any(kw in name_lower for kw in ['グローブ', 'glove', '手套']):
            ending = '手套'
        elif any(kw in name_lower for kw in ['ソックス', 'socks', '袜']):
            ending = '袜子'
        elif any(kw in name_lower for kw in ['靴', 'shoes', 'シューズ']):
            ending = '球鞋'
        else:
            ending = '帽子'  # 配件默认选择帽子（更常见的配件）
    elif is_accessory:
        ending = '帽子'  # 没有产品名时的默认值
    else:
        default_endings = {
            CATEGORY_OUTERWEAR: '外套',
            CATEGORY_TOP: '上衣',
            CATEGORY_BOTTOM: '长裤',
            CATEGORY_SHOES: '球鞋',
            CATEGORY_RAINWEAR: '雨衣'
        }
        ending = default_endings.get(category, '外套')

    # 构建标题
    title = f"{season}{brand_chinese}高尔夫{gender_word}{''.join(function_words[:2])}{ending}"

    # 确保长度合规
    max_len = ACCESSORY_MAX_LEN if is_accessory else APPAREL_MAX_LEN
    if len(title) > max_len:
        # 优先缩短功能词
        excess = len(title) - max_len
        if len(function_words[0]) >= excess:
            title = title.replace(function_words[0], '')
        else:
            # 截断
            title = title[:max_len]

    return title


# ============================================================================
# 六、主流程（方案C完整流程）
# ============================================================================

def generate_cn_title(product: Dict) -> str:
    """
    生成中文标题 - 方案C主流程

    流程：
    1. 推断基础信息（代码）
    2. 构建智能prompt（让GLM发挥）
    3. 调用GLM生成
    4. 强制执行硬性规则（代码修正）
    5. 质量检查（严格验证）
    6. 失败则使用回退方案

    Args:
        product: 产品数据字典

    Returns:
        str: 最终标题
    """
    # ========================================================================
    # 步骤1：推断基础信息
    # ========================================================================
    gender = determine_gender(product)
    category = determine_category(product)
    brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
    season = extract_season_from_name(product.get('productName', ''))
    is_accessory = is_small_accessory(category, product.get('productName', ''))

    # ========================================================================
    # 步骤2：构建智能prompt
    # ========================================================================
    prompt = build_smart_prompt(
        product,
        gender,
        category,
        brand_chinese,
        season,
        is_accessory
    )

    # ========================================================================
    # 步骤3：调用GLM生成
    # ========================================================================
    raw_title = call_glm_api(prompt)

    # ========================================================================
    # 步骤4：强制执行硬性规则
    # ========================================================================
    if raw_title:
        title = enforce_hard_rules(raw_title, category, is_accessory)

        # ====================================================================
        # 步骤5：质量检查
        # ====================================================================
        if validate_title_quality(title, brand_chinese, category, is_accessory):
            return title

    # ========================================================================
    # 步骤6：回退方案
    # ========================================================================
    print("GLM生成失败或质量检查未通过，使用回退方案")
    fallback_title = generate_fallback_title(
        brand_chinese,
        season,
        gender,
        category,
        is_accessory,
        product.get('productName', '')
    )
    return fallback_title


# ============================================================================
# 七、错误处理
# ============================================================================

class TitleGenerationError(Exception):
    """标题生成异常"""
    pass