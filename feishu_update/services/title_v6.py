"""
标题生成系统 - 核心逻辑
版本：v6.0 - 方案C混合模式
核心思想：硬性规则代码控制，软性判断交给GLM
"""

import re
import random
import time
import threading
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入配置
from .title_config import *
from ..config import brands
from ..config.clothing import (
    JAPANESE_CHAR_PATTERN,
    FULLWIDTH_TO_HALFWIDTH,
    TRADITIONAL_TO_SIMPLIFIED,
)

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
    
    # 先检查配件类（优先级最高，避免ニットキャップ被误识别为上衣）
    accessory_keywords = [
        'キャップ', 'cap', 'ハット', 'hat', 'ビーニー', 'beanie', 'ニットキャップ', 'ニット帽',
        'グローブ', 'glove', 'ベルト', 'belt', 'ソックス', 'socks',
        '帽', '手套', '袜', '腰带', '护腕', '头带', '围脖'
    ]
    combined_text = f"{name} {category}"
    for keyword in accessory_keywords:
        if keyword in combined_text:
            return CATEGORY_ACCESSORY
    
    # 其他类别关键词映射
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
        ]
    }
    
    # 匹配其他类别
    for cat, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in combined_text:
                return cat
    
    return CATEGORY_OUTERWEAR  # 默认


def extract_brand_from_product(product: Dict) -> Tuple[str, str, str]:
    """
    从商品信息中提取品牌 - v5 增强版本，支持品牌别名
    返回: (brand_key, brand_chinese, brand_short)
    
    识别策略：
    1. 优先使用品牌别名映射（支持多语言和拼写变体）
    2. 回退到原有的关键词匹配
    3. 从 detailUrl 域名识别（兜底）
    4. 默认返回 callawaygolf
    """
    # 获取所有可能的标题字段
    title_fields = [
        product.get('productName', ''),
        product.get('title', ''),
        product.get('productTitle', ''),
        product.get('cnTitle', ''),
    ]
    
    # 合并所有标题字段进行规范化处理
    combined_text = ' '.join(filter(None, title_fields))
    normalized_text = combined_text.lower().replace(' ', '').replace('-', '')
    
    url = product.get('detailUrl', '').lower()
    
    # 方案1: 使用品牌别名映射（新增）
    for alias, brand_key in brands.BRAND_ALIASES.items():
        # 对别名也进行规范化处理（仅针对英文别名）
        normalized_alias = alias.lower().replace(' ', '').replace('-', '') if alias.isascii() else alias
        if normalized_alias in normalized_text:
            # 确保品牌信息存在
            if brand_key in brands.BRAND_MAP and brand_key in brands.BRAND_SHORT_NAME:
                return brand_key, brands.BRAND_MAP[brand_key], brands.BRAND_SHORT_NAME[brand_key]
            # 如果新品牌信息不存在，使用默认映射
            elif brand_key == 'callawaygolf':
                return brand_key, brands.BRAND_MAP[brand_key], brands.BRAND_SHORT_NAME[brand_key]
    
    # 方案2: 回退到原有的关键词匹配
    name = product.get('productName', '').lower()
    for brand_key, keywords in brands.BRAND_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in name:
                return brand_key, brands.BRAND_MAP[brand_key], brands.BRAND_SHORT_NAME[brand_key]
    
    # 方案3: 从 detailUrl 匹配域名
    for brand_key in brands.BRAND_KEYWORDS.keys():
        if brand_key in url:
            return brand_key, brands.BRAND_MAP[brand_key], brands.BRAND_SHORT_NAME[brand_key]
    
    # 默认返回卡拉威
    return 'callawaygolf', brands.BRAND_MAP['callawaygolf'], brands.BRAND_SHORT_NAME['callawaygolf']


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
        '護腕', '腕帯', '头帯', '围脖'
    ]
    
    return any(kw in name_lower for kw in accessory_keywords)


# ============================================================================
# 二、标题生成异常类
# ============================================================================

class TitleGenerationError(Exception):
    """标题生成失败异常"""
    pass


# ============================================================================
# 三、GLM API调用（带限流和重试）
# ============================================================================

# 常量定义（从配置文件中提取的必要常量）
TITLE_MODEL = 'glm-4.6'
TITLE_MAX_RETRIES = 3
TITLE_BACKOFF_FACTOR = 2
TITLE_MIN_INTERVAL = 0.4
TRUNCATION_CHARS = {'抓', '保', '透', '速', '轻', '防', '舒', '柔', '弹', '修', '运', '时'}
REPEAT_PATTERN = re.compile(r'(.{2,})\1+')
ERROR_INDICATORS = ['要求', '必须', '格式', '应该', '建议']

# 导入所需的常量从 title_config
try:
    from .title_config import (
        ALLOWED_ENDINGS_ACCESSORIES,
        ALLOWED_ENDINGS_APPAREL,
        FORBIDDEN_WORDS,
        ACCESSORY_MIN_LEN,
        ACCESSORY_MAX_LEN,
        APPAREL_MIN_LEN,
        APPAREL_MAX_LEN,
        CATEGORY_OUTERWEAR,
        CATEGORY_TOP,
        CATEGORY_BOTTOM,
        CATEGORY_SHOES,
        CATEGORY_ACCESSORY,
        CATEGORY_RAINWEAR
    )
except ImportError:
    # 如果导入失败，使用默认值
    print("警告：无法从 title_config 导入常量，使用默认值")
    ALLOWED_ENDINGS_ACCESSORIES = ['袜子', '帽子', '手套', '腰带']
    ALLOWED_ENDINGS_APPAREL = ['外套', '上衣', 'POLO衫', '长裤', '球鞋', '雨衣']
    FORBIDDEN_WORDS = ['服饰', '精品', '再入荷', '限定', '定番', '球场', '训练', '在线']
    ACCESSORY_MIN_LEN = 25
    ACCESSORY_MAX_LEN = 30
    APPAREL_MIN_LEN = 26
    APPAREL_MAX_LEN = 30
    CATEGORY_OUTERWEAR = '外套'
    CATEGORY_TOP = '上衣'
    CATEGORY_BOTTOM = '下装'
    CATEGORY_SHOES = '鞋类'
    CATEGORY_ACCESSORY = '配件'
    CATEGORY_RAINWEAR = '雨具'

def call_glm_api(
    prompt: str,
    model: str = TITLE_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 500
) -> str:
    """
    调用GLM API（带限流和重试）
    """
    import os
    import requests

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

    for attempt in range(TITLE_MAX_RETRIES + 1):
        try:
            with glm_call_lock:
                current_time = time.time()
                time_since_last_call = current_time - last_glm_call_ts
                sleep_time = max(0, TITLE_MIN_INTERVAL - time_since_last_call)
                if sleep_time > 0:
                    time.sleep(sleep_time)

                response = requests.post(url, headers=headers, json=payload, timeout=120)
                last_glm_call_ts = time.time()

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message'].get('content', '').strip()
                if content:
                    return content
                reasoning_content = data['choices'][0]['message'].get('reasoning_content', '').strip()
                if reasoning_content:
                    return reasoning_content

            return ""
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < TITLE_MAX_RETRIES:
                backoff_time = TITLE_BACKOFF_FACTOR ** attempt
                print(f"限流重试，等待{backoff_time:.1f}秒...")
                time.sleep(backoff_time)
                continue
            else:
                print(f"GLM API错误: {e}")
                return ""
        except Exception as e:
            print(f"GLM API异常: {e}")
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
    构建智能Prompt - 让GLM自己判断软性内容
    """
    name = product.get('productName', '')
    gender_word = '男士' if gender == '男' else '女士'

    if is_accessory:
        endings_list = ', '.join(ALLOWED_ENDINGS_ACCESSORIES)
        length_req = "25-30个中文字符（严格不超过30字）"
    else:
        endings_list = ', '.join(ALLOWED_ENDINGS_APPAREL)
        length_req = "26-30个中文字符（严格不超过30字）"

    # 智能类型词选择 - 根据商品特征选择精确的类型词
    name_lower = name.lower()
    
    # 步骤1：智能类型词选择（优先级最高）
    if any(kw in name_lower for kw in ['中綿', '中棉']):
        type_word = "棉服"
        feature_words = "保暖舒适"
    elif any(kw in name_lower for kw in ['ダウン', 'down']):
        type_word = "羽绒服"
        feature_words = "保暖轻量"
    elif any(kw in name_lower for kw in ['ニット', 'knit']):
        type_word = "针织衫"
        feature_words = "柔软舒适"
    elif any(kw in name_lower for kw in ['polo', 'ポロ']):
        type_word = "POLO衫"
        feature_words = "透气速干"
    elif any(kw in name_lower for kw in ['tシャツ', 't-shirt', 'tee']):
        type_word = "T恤"
        feature_words = "透气舒适"
    elif any(kw in name_lower for kw in ['ジャケット', 'jacket']):
        type_word = "夹克"
        feature_words = "防风透气"
    elif any(kw in name_lower for kw in ['ベスト', 'vest']):
        type_word = "马甲"
        feature_words = "轻量保暖"
    elif any(kw in name_lower for kw in ['フリース', 'fleece']):
        type_word = "抓绒衫"
        feature_words = "保暖柔软"
    elif any(kw in name_lower for kw in ['パンツ', 'pants']):
        type_word = "长裤"
        feature_words = "舒适修身"
    elif any(kw in name_lower for kw in ['ショート', 'short']):
        type_word = "短裤"
        feature_words = "透气舒适"
    else:
        # 回退到大分类
        type_mapping = {
            "外套": "外套",
            "上衣": "上衣", 
            "下装": "长裤",
            "鞋类": "球鞋",
            "配件": "帽子",
            "雨具": "雨衣"
        }
        type_word = type_mapping.get(category, "外套")
        
        # 步骤2：功能词选择（只有在没有被类型词指定时）
        if any(kw in name_lower for kw in ['メッシュ', 'mesh', 'ドライ', 'dry', 'uvカット', 'uv', '速干']):
            feature_words = "透气速干"
        elif any(kw in name_lower for kw in ['ストレッチ', 'stretch', 'スポーツ', 'sport']):
            feature_words = "弹力舒适"
        elif category == "外套":
            feature_words = "防风透气"
        else:
            feature_words = "保暖舒适" if "秋冬" in season else "透气速干"
    
    prompt = f"""组合成完整的中文标题：

{season}{brand_chinese}高尔夫{gender_word}{feature_words}{type_word}

直接输出："""

    return prompt


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
    
    # 太长 → 截断
    if len(title) > max_len:
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
    print(f"🔍 标题质量验证调试：")
    print(f"   标题: {title}")
    print(f"   品牌: {brand_chinese}")
    print(f"   大分类: {category}")
    print(f"   是否配件: {is_accessory}")
    
    if not title:
        print(f"   ❌ 验证失败: 标题为空")
        return False
    
    # 检查长度
    min_len = ACCESSORY_MIN_LEN if is_accessory else APPAREL_MIN_LEN
    max_len = ACCESSORY_MAX_LEN if is_accessory else APPAREL_MAX_LEN
    
    print(f"   长度要求: {min_len}-{max_len}, 实际长度: {len(title)}")
    
    if not (min_len <= len(title) <= max_len):
        print(f"   ❌ 验证失败: 长度不符合要求")
        return False
    
    # 检查品牌（去掉英文部分，只检查中文）
    brand_cn_part = brand_chinese.split('C')[0] if 'C' in brand_chinese else brand_chinese
    brand_cn_part = brand_cn_part.split('T')[0] if 'T' in brand_cn_part else brand_cn_part
    print(f"   品牌检查: 期待'{brand_cn_part}' 在标题中")
    
    if brand_cn_part not in title:
        print(f"   ❌ 验证失败: 标题中不包含品牌'{brand_cn_part}'")
        return False
    
    # 检查"高尔夫"次数
    golf_count = title.count('高尔夫')
    print(f"   高尔夫次数: {golf_count} (期待1次)")
    
    if golf_count != 1:
        print(f"   ❌ 验证失败: '高尔夫'出现{golf_count}次，期待1次")
        return False
    
    # 检查结尾词
    allowed_endings = ALLOWED_ENDINGS_ACCESSORIES if is_accessory else ALLOWED_ENDINGS_APPAREL
    print(f"   允许的结尾词: {allowed_endings}")
    
    ending_found = None
    for ending in allowed_endings:
        if title.endswith(ending):
            ending_found = ending
            break
    
    if not ending_found:
        print(f"   ❌ 验证失败: 标题结尾不符合要求")
        return False
    else:
        print(f"   ✅ 结尾词检查通过: {ending_found}")
    
    # 检查连续重复
    if REPEAT_PATTERN.search(title):
        print(f"   ❌ 验证失败: 发现连续重复")
        return False
    
    # 检查是否包含错误指示词（说明GLM在复述任务而不是输出标题）
    for indicator in ERROR_INDICATORS:
        if indicator in title:
            print(f"   ❌ 验证失败: 包含错误指示词'{indicator}'")
            return False
    
    print(f"   ✅ 标题质量验证通过")
    return True


# ============================================================================
# 五、回退方案（兜底）
# ============================================================================

def generate_fallback_title(
    product: Dict,
    gender: str,
    category: str,
    brand_chinese: str,
    season: str,
    is_accessory: bool
) -> str:
    """
    回退标题生成（GLM失败时使用）
    
    使用简单模板：
    {季节}{品牌}高尔夫{性别}舒适透气弹力{类型}
    """
    gender_word = '男士' if gender == '男' else '女士'
    
    # 根据大分类选择类型词
    type_map = {
        CATEGORY_OUTERWEAR: '防风夹克外套',
        CATEGORY_TOP: '运动POLO衫',
        CATEGORY_BOTTOM: '修身运动长裤',
        CATEGORY_SHOES: '防滑运动球鞋',
        CATEGORY_ACCESSORY: '帽子',
        CATEGORY_RAINWEAR: '防水轻便雨衣'
    }
    
    type_word = type_map.get(category, '外套')
    
    # 根据季节选择功能词
    if '春夏' in season or 'SS' in season or 'SP' in season:
        feature = '轻量透气' if is_accessory else '速干透气'
    else:
        feature = '保暖舒适' if is_accessory else '保暖舒适'
    
    # 拼接
    title = f"{season}{brand_chinese}高尔夫{gender_word}{feature}{type_word}"
    
    print(f"🔍 回退方案调试信息：")
    print(f"   产品名: {product.get('productName', '')}")
    print(f"   季节: {season}")
    print(f"   品牌: {brand_chinese}")
    print(f"   性别: {gender_word}")
    print(f"   大分类: {category}")
    print(f"   是否配件: {is_accessory}")
    print(f"   功能词: {feature}")
    print(f"   类型词: {type_word}")
    print(f"   拼接后标题: {title}")
    
    # 应用硬性规则
    title = enforce_hard_rules(title, category, is_accessory)
    
    print(f"   硬性规则修正后: {title}")
    print(f"   标题长度: {len(title)} 字符")
    
    return title


# ============================================================================
# 六、主流程（方案C完整流程）
# ============================================================================

def generate_cn_title(product: Dict, glm_client=None) -> str:
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
        glm_client: GLM客户端（可选，如为None则直接使用API）
    
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
    if glm_client:
        # 使用注入的GLM客户端
        raw_title = glm_client.generate_title(prompt)
    else:
        # 使用直接API调用
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
    # 步骤6：如果GLM生成失败，抛出异常
    # ========================================================================
    print(f"❌ 标题生成失败，GLM API无法生成合格标题")
    raise TitleGenerationError(f"GLM API生成标题失败或质量不合格: {raw_title}")



# ============================================================================
# 六、批量处理（并行版本）
# ============================================================================

def generate_titles_parallel(
    products: Dict[str, Dict],
    workers: int = 6,
    progress_callback=None
) -> Dict[str, str]:
    """
    并行生成标题
    
    Args:
        products: {product_id: product_dict}
        workers: 并发线程数
        progress_callback: 进度回调函数
    
    Returns:
        {product_id: title}
    """
    results = {}
    total = len(products)
    completed = 0
    
    def generate_one(item):
        product_id, product = item
        try:
            title = generate_cn_title(product)
            return (product_id, title)
        except Exception as e:
            print(f"产品 {product_id} 标题生成异常: {e}")
            return (product_id, "")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(generate_one, item): item[0]
            for item in products.items()
        }
        
        # 处理完成的任务
        for future in as_completed(futures):
            product_id, title = future.result()
            results[product_id] = title
            
            completed += 1
            
            # 进度回调
            if progress_callback and completed % 10 == 0:
                progress_callback(completed, total)
    
    return results


# ============================================================================
# 八、测试函数
# ============================================================================

