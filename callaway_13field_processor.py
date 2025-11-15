#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡拉威13字段改写逻辑完整提取
=====================================

基于CallawayJP项目的完整13字段改写系统，包含：
- AI标题生成（完整的GLM提示词）
- 24种细分分类规则
- 产品描述翻译
- 图片处理规则
- 所有配置和依赖

Author: Claude Code
Date: 2025-11-13
Version: 1.0 - 完整提取版
"""

import re
import time
import threading
import requests
import os
from typing import Dict, List, Optional, Tuple
from itertools import combinations, product

# ============================================================================
# 一、品牌配置（完整复制自CallawayJP）
# ============================================================================

BRAND_KEYWORDS = {
    'callawaygolf': ['callaway', 'callaway golf', '卡拉威', '卡拉威高尔夫'],
    'titleist': ['titleist', '泰特利斯', 'titleist golf'],
    'puma': ['puma', 'puma golf', '彪马'],
    'adidas': ['adidas', 'adidas golf', '阿迪达斯'],
    'nike': ['nike', 'nike golf', '耐克'],
    'underarmour': ['under armour', 'ua', '安德玛'],
    'footjoy': ['footjoy', 'fj', 'joy'],
    'cleveland': ['cleveland', 'cleveland golf'],
    'mizuno': ['mizuno', '美津濃', '美津浓'],
    'ping': ['ping', 'ping golf'],
    'taylormade': ['taylor made', 'taylormade', 'tm', '泰勒梅'],
    'lecoqsportifgolf': ['le coq', 'lecoq', 'ル コック', '公鸡', '乐卡克', 'le coq sportif', 'le coq sportif golf']
}

# 品牌中文名映射
BRAND_MAP = {
    'callawaygolf': '卡拉威Callaway',
    'titleist': '泰特利斯Titleist',
    'puma': '彪马Puma',
    'adidas': '阿迪达斯Adidas',
    'nike': '耐克Nike',
    'underarmour': '安德玛UA',
    'footjoy': 'FootJoy',
    'cleveland': 'Cleveland',
    'mizuno': '美津浓Mizuno',
    'ping': 'Ping',
    'taylormade': '泰勒梅TaylorMade',
    'lecoqsportifgolf': 'Le Coq公鸡乐卡克'
}

# 品牌简称
BRAND_SHORT_NAME = {
    'callawaygolf': '卡拉威',
    'titleist': '泰特利斯',
    'puma': '彪马',
    'adidas': '阿迪达斯',
    'nike': '耐克',
    'underarmour': '安德玛',
    'footjoy': 'FootJoy',
    'cleveland': 'Cleveland',
    'mizuno': '美津浓',
    'ping': 'Ping',
    'taylormade': '泰勒梅',
    'lecoqsportifgolf': 'Le Coq公鸡乐卡克'
}

# 品牌别名映射 - 用于识别各种拼写变体和多语言名称
BRAND_ALIASES = {
    'callaway': 'callawaygolf',
    'キャロウェイ': 'callawaygolf',
    'calaway': 'callawaygolf',
    'callawaygolf': 'callawaygolf',
    'titleist': 'titleist',
    'タイトリスト': 'titleist',
    'titelist': 'titleist',
    'taylormade': 'taylormade',
    'テーラーメイド': 'taylormade',
    'taylor made': 'taylormade',
    'ping': 'ping',
    'ピン': 'ping',
    'cobra': 'cobragolf',
    'cobragolf': 'cobragolf',
    'コブラ': 'cobragolf',
    'odyssey': 'odyssey',
    'オデッセイ': 'odyssey',
    'oddysey': 'odyssey',
    'scottycameron': 'scottycameron',
    'スコッティキャメロン': 'scottycameron',
    'cameron': 'scottycameron',
    'pxg': 'pxg',
    'parsonsxtremegolf': 'pxg',
    'mizuno': 'mizuno',
    'ミズノ': 'mizuno',
    'srixon': 'srixon',
    'スリクソン': 'srixon',
    'srxion': 'srixon',
    'cleveland': 'clevelandgolf',
    'クリーブランド': 'clevelandgolf',
    'bridgestone': 'bridgestonegolf',
    'ブリヂストン': 'bridgestonegolf',
    'bridgestonegolf': 'bridgestonegolf',
    'xxio': 'xxio',
    'ゼクシオ': 'xxio',
    'honma': 'honma',
    '本間': 'honma',
    'ホンマ': 'honma',
    'prgr': 'prgr',
    'プロギア': 'prgr',
    'progear': 'prgr',
    'yamaha': 'yamahagolf',
    'ヤマハ': 'yamahagolf',
    'onoff': 'onoff',
    'グローブライド': 'onoff',
    'daiwaonoff': 'onoff',
    'majesty': 'majesty',
    'maruman': 'majesty',
    'マジェスティ': 'majesty',
    'fourteen': 'fourteen',
    'フォーティーン': 'fourteen',
    'epon': 'epon',
    '遠藤': 'epon',
    'エポン': 'epon',
    'miura': 'miura',
    '三浦技研': 'miura',
    'ミウラ': 'miura',
    'vega': 'vega',
    'ヴェガ': 'vega',
    'romaro': 'romaro',
    'ロマロ': 'romaro',
    'katana': 'katanagolf',
    'カタナ': 'katanagolf',
    'sword': 'katanagolf',
    'kasco': 'kasco',
    'キャスコ': 'kasco',
    'yonex': 'yonex',
    'ヨネックス': 'yonex',
    'bettinardi': 'bettinardi',
    'ベティナルディ': 'bettinardi',
    'evnroll': 'evnroll',
    'イーブンロール': 'evnroll',
    'wilson': 'wilsonstaff',
    'wilsonstaff': 'wilsonstaff',
    'touredge': 'touredge',
    'benhogan': 'benhogan',
    'macgregor': 'macgregor',
    'adams': 'adamsgolf',
    'adamsgolf': 'adamsgolf',
    'lynx': 'lynxgolf',
    'bensayers': 'bensayers',
    'snakeeyes': 'snakeeyes',
    'maltby': 'maltby',
    'golfworks': 'maltby',
    'lagolf': 'lagolf',
    'toulon': 'toulon',
    'toulondesign': 'toulon',
    'le coq sportif': 'lecoqsportifgolf',
    'lecoqsportifgolf': 'lecoqsportifgolf',
    'le coq': 'lecoqsportifgolf',
    'lecoq': 'lecoqsportifgolf',
    'ル コック': 'lecoqsportifgolf',
    'ルコック': 'lecoqsportifgolf',
    '公鸡': 'lecoqsportifgolf',
    '乐卡克': 'lecoqsportifgolf',
    'le coq sportif golf': 'lecoqsportifgolf',
    'ルコックスポルティフ': 'lecoqsportifgolf'
}

# ============================================================================
# 二、颜色翻译配置（完整复制）
# ============================================================================

COLOR_NAME_TRANSLATION = {
    # 基础色
    'BLACK': '黑色',
    'WHITE': '白色',
    'BLUE': '蓝色',
    'RED': '红色',
    'NAVY': '藏蓝色',
    'GRAY': '灰色',
    'GREY': '灰色',
    'GREEN': '绿色',
    'YELLOW': '黄色',
    'ORANGE': '橙色',
    'PINK': '粉色',
    'PURPLE': '紫色',
    'BROWN': '棕色',
    'BEIGE': '米色',
    'KHAKI': '卡其色',
    'OLIVE': '橄榄绿',
    'SILVER': '银色',
    'GOLD': '金色',

    # 深浅变化
    'LIGHT BLUE': '浅蓝色',
    'DARK BLUE': '深蓝色',
    'LIGHT GRAY': '浅灰色',
    'DARK GRAY': '深灰色',
    'LIGHT GREY': '浅灰色',
    'DARK GREY': '深灰色',
    'LIGHT GREEN': '浅绿色',
    'DARK GREEN': '深绿色',
    'LIGHT PINK': '浅粉色',
    'DARK PINK': '深粉色',
    'LIGHT BROWN': '浅棕色',
    'DARK BROWN': '深棕色',

    # 复合颜色
    'BLACK/WHITE': '黑白',
    'WHITE/BLACK': '白黑',
    'NAVY/WHITE': '藏蓝色/白',
    'WHITE/NAVY': '白/藏蓝色',
    'RED/WHITE': '红白',
    'WHITE/RED': '白红',
    'BLUE/WHITE': '蓝白',
    'WHITE/BLUE': '白蓝',
    'GRAY/WHITE': '灰白',
    'WHITE/GRAY': '白灰',

    # 高尔夫常见颜色
    'CAMO': '迷彩',
    'CAMOUFLAGE': '迷彩',
    'NEON': '荧光',
    'METALLIC': '金属色',
    'TURQUOISE': '土耳其蓝',
    'LIME': '青柠色',
    'MAGENTA': '洋红色',
    'CYAN': '青色',
    'MAROON': '栗色',
    'TEAL': '深青色',
    'IVORY': '象牙色',
    'CREAM': '奶油色',

    # 小写版本
    'black': '黑色',
    'white': '白色',
    'blue': '蓝色',
    'red': '红色',
    'navy': '藏蓝色',
    'gray': '灰色',
    'grey': '灰色',
    'green': '绿色',
    'yellow': '黄色',
    'orange': '橙色',
    'pink': '粉色',
    'purple': '紫色',
    'brown': '棕色',
    'beige': '米色',
    'khaki': '卡其色',
    'olive': '橄榄绿',
    'silver': '银色',
    'gold': '金色',
    'camo': '迷彩',
    'neon': '荧光',
    'metallic': '金属色',

    # 首字母大写版本
    'Black': '黑色',
    'White': '白色',
    'Blue': '蓝色',
    'Red': '红色',
    'Navy': '藏蓝色',
    'Gray': '灰色',
    'Grey': '灰色',
    'Green': '绿色',
    'Yellow': '黄色',
    'Orange': '橙色',
    'Pink': '粉色',
    'Purple': '紫色',
    'Brown': '棕色',
    'Beige': '米色',
    'Khaki': '卡其色',
    'Olive': '橄榄绿',
    'Silver': '银色',
    'Gold': '金色',
    'Camo': '迷彩',
    'Neon': '荧光',
    'Metallic': '金属色',

    # 日文颜色映射
    'ブラック': '黑色',
    'ホワイト': '白色',
    'ネイビー': '藏青色',
    'ネイビー×グレー': '藏青色×灰色',
    'グレー': '灰色',
    'グレイ': '灰色',
    'ブルー': '蓝色',
    'レッド': '红色',
    'グリーン': '绿色',
    'イエロー': '黄色',
    'オレンジ': '橙色',
    'ピンク': '粉色',
    'パープル': '紫色',
    'ブラウン': '棕色',
    'ベージュ': '米色',
    'カーキ': '卡其色',
    'オリーブ': '橄榄色',
    'シルバー': '银色',
    'ゴールド': '金色',
    'カモ': '迷彩',
    'ネオン': '荧光',
    'メタリック': '金属色',
    'バーガンディ': '酒红色',
    'マルーン': '栗色',
    'ターコイズ': '土耳其蓝',
    'ライム': '青柠色',
    'マゼンタ': '洋红色',
    'シアン': '青色',
    'ティール': '深青色',
    'アイボリー': '象牙色',
    'クリーム': '奶油色',
    'ホワイト': '白色',
    'ブラック': '黑色',
    'レッド': '红色',
    'ブルー': '蓝色',
    'ネイビー': '藏青色',
    'ネイビー×グレー': '藏青色×灰色',
    'グレー': '灰色',
    'グリーン': '绿色',
    'イエロー': '黄色',
    'ピンク': '粉色',
    'パープル': '紫色',
    'オレンジ': '橙色',
    'ブラウン': '棕色',
    'ベージュ': '米色',
    'アイボリー': '象牙色',
    'カーキ': '卡其色',
    'オリーブ': '橄榄色',
    'ターコイズ': '绿松石色',
    'コーラル': '珊瑚色',
    'ローズ': '玫瑰色',
    'ラベンダー': '薰衣草紫',
    'ワイン': '酒红色',
    'モカ': '摩卡色',
    'チャコール': '炭灰色',
    'シルバー': '银色',
    'ゴールド': '金色'
}

# ============================================================================
# 三、全局变量和GLM配置
# ============================================================================

# GLM API调用控制全局变量
glm_call_lock = threading.Lock()
last_glm_call_ts = 0.0

# GLM配置
GLM_MIN_INTERVAL = 0.4  # 最小调用间隔（秒）
GLM_MAX_RETRIES = 3     # 最大重试次数
GLM_BACKOFF_FACTOR = 1.8  # 退避因子

# ============================================================================
# 四、品牌提取功能
# ============================================================================

def extract_brand_from_product(product: Dict) -> Tuple[str, str, str]:
    """
    提取品牌

    Returns:
        (brand_key, brand_chinese, brand_short)
        例如：('callawaygolf', '卡拉威Callaway', '卡拉威')
    """
    name = (product.get('商品标题', '') or
            product.get('productName', '') or
            product.get('标题原文', '')).lower()
    url = (product.get('详情页链接', '') or
           product.get('detailUrl', '')).lower()
    brand_info = (product.get('品牌', '') or
                 product.get('brand', '')).lower()

    # 组合文本用于品牌匹配
    combined_text = f"{name} {url} {brand_info}".lower()

    # 首先尝试通过别名映射匹配
    for alias, brand_key in BRAND_ALIASES.items():
        if alias.lower() in combined_text:
            return (
                brand_key,
                BRAND_MAP.get(brand_key, brand_key),
                BRAND_SHORT_NAME.get(brand_key, brand_key)
            )

    # 如果没有匹配，尝试通过域名匹配（针对 callawaygolf.jp）
    if 'callawaygolf' in url or 'callaway' in combined_text:
        return ('callawaygolf', BRAND_MAP['callawaygolf'], BRAND_SHORT_NAME['callawaygolf'])

    # 默认
    return (
        'callawaygolf',
        BRAND_MAP['callawaygolf'],
        BRAND_SHORT_NAME['callawaygolf']
    )

# ============================================================================
# 五、24种细分分类规则（完整复制）
# ============================================================================

def determine_gender(product_data):
    """确定产品性别分类"""
    if isinstance(product_data, dict):
        product_name = product_data.get('productName', '')
        category = product_data.get('category', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
    else:
        return '男'

    # 转换为小写便于匹配
    product_name_lower = product_name.lower()
    category_lower = category.lower()

    # 检查category字段
    if 'womens' in category_lower or 'ladies' in category_lower:
        return '女'
    elif 'mens' in category_lower:
        return '男'

    # 检查产品名称 - 英文和日文
    if any(word in product_name_lower for word in ['women', 'ladies', 'womens', 'レディース', '女性']):
        return '女'
    elif any(word in product_name_lower for word in ['men', 'mens', '(mens)', 'メンズ', '男性']):
        return '男'
    else:
        return '男'  # 默认男

def determine_clothing_type(product_data):
    """确定服装类型 - 详细分类版本（24种细分）"""
    if isinstance(product_data, dict):
        product_name = (product_data.get('商品标题', '') or
                       product_data.get('productName', '') or
                       product_data.get('标题原文', ''))
        category = product_data.get('category', '')
        detail_url = (product_data.get('详情页链接', '') or
                     product_data.get('detailUrl', ''))
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
        detail_url = getattr(product_data, 'detailUrl', '')
    else:
        return '其他'

    # 转换为小写便于匹配
    product_name_lower = product_name.lower()
    category_lower = category.lower()
    url_lower = detail_url.lower()

    # 🆕 优先使用URL具体路径分类
    if '/jacket/' in url_lower or '/blouson/' in url_lower:
        return '夹克'
    elif '/vest/' in url_lower or '/gilet/' in url_lower:
        return '马甲/背心'
    elif '/parka/' in url_lower or '/hoodie/' in url_lower:
        return '卫衣/连帽衫'
    elif '/down/' in url_lower or '/padding/' in url_lower:
        return '羽绒服/棉服'
    elif '/windbreaker/' in url_lower:
        return '风衣/防风外套'
    elif '/polo/' in url_lower:
        return 'Polo衫'
    elif '/tshirt/' in url_lower or '/t-shirt/' in url_lower:
        return 'T恤'
    elif '/shirt/' in url_lower:
        return '衬衫'
    elif '/knit/' in url_lower or '/sweater/' in url_lower:
        return '针织衫/毛衣'
    elif '/pant/' in url_lower or '/trouser/' in url_lower:
        return '长裤'
    elif '/short/' in url_lower:
        return '短裤'
    elif '/skirt/' in url_lower:
        return '裙装'
    elif '/shoe/' in url_lower or '/footwear/' in url_lower:
        return '高尔夫球鞋'

    # 🎯 详细分类检查 - 按照服装类型细分（24种）

    # 1. 羽绒服/棉服类
    if any(word in product_name_lower for word in [
        'down jacket', 'padded jacket', 'quilted jacket',
        'ダウンジャケット', 'パディングジャケット', 'キルティングジャケット',
        '羽绒服', '棉服', '棉衣', '绗缝', 'quilted', 'padded', 'down'
    ]):
        return '羽绒服/棉服'

    # 2. 卫衣/连帽衫类
    elif any(word in product_name_lower for word in [
        'hoodie', 'sweatshirt', 'pullover', 'fleece', 'sweat', 'crewneck',
        'パーカー', 'スウェット', 'スウェットシャツ', 'プルオーバー', 'フリース', 'クルーネック',
        '卫衣', '连帽衫', '抓绒', 'pullover', 'fleece jacket'
    ]):
        return '卫衣/连帽衫'

    # 3. 夹克类（通用）
    elif any(word in product_name_lower for word in [
        'jacket', 'blouson', 'outer jacket', 'sports jacket',
        'ジャケット', 'ブルゾン', 'アウタージャケット', 'スポーツジャケット',
        '夹克', '外套', '运动夹克', '休闲夹克'
    ]):
        return '夹克'

    # 4. 马甲/背心类
    elif any(word in product_name_lower for word in [
        'vest', 'gilet', 'sleeveless', 'tank top',
        'ベスト', 'ジレ', 'スリーブレス', 'タンクトップ',
        '马甲', '背心', '无袖', 'vest', 'gilet'
    ]):
        return '马甲/背心'

    # 5. 风衣/防风外套类
    elif any(word in product_name_lower for word in [
        'windbreaker', 'wind jacket', 'windcheater', 'coach jacket',
        'ウインドブレーカー', 'ウインドジャケット', 'コーチジャケット',
        '风衣', '防风外套', 'windbreaker', 'wind jacket'
    ]):
        return '风衣/防风外套'

    # 6. Polo衫类
    elif any(word in product_name_lower for word in [
        'polo', 'polo shirt', 'golf shirt',
        'ポロ', 'ポロシャツ', 'ゴルフシャツ',
        'polo衫', '高尔夫衫', 'polo shirt'
    ]):
        return 'Polo衫'

    # 7. T恤类
    elif any(word in product_name_lower for word in [
        't-shirt', 'tshirt', 'tee', 'crew neck',
        'Tシャツ', 'ティーシャツ', 'クルーネック',
        'T恤', 't恤', '圆领T恤', '短袖T恤', 't-shirt'
    ]):
        return 'T恤'

    # 8. 衬衫类
    elif any(word in product_name_lower for word in [
        'shirt', 'button shirt', 'dress shirt', 'casual shirt',
        'シャツ', 'ボタンシャツ', 'ドレスシャツ', 'カジュアルシャツ',
        '衬衫', '衬衣', '翻领衫', 'button shirt', 'dress shirt'
    ]):
        return '衬衫'

    # 9. 针织衫/毛衣类
    elif any(word in product_name_lower for word in [
        'knit', 'knitwear', 'sweater', 'cardigan',
        'ニット', 'ニットウェア', 'セーター', 'カーディガン',
        '针织衫', '毛衣', '开衫', 'cardigan', 'sweater', 'knit'
    ]):
        return '针织衫/毛衣'

    # 10. 长裤类
    elif any(word in product_name_lower for word in [
        'pant', 'trouser', 'long pant', 'full length',
        'ズボン', 'ロングパンツ', 'フルレングス', 'トラウザー', 'ゴルフパンツ',
        '长裤', '全长的', 'trouser', 'long pant', 'trousers'
    ]):
        return '长裤'

    # 11. 短裤类
    elif any(word in product_name_lower for word in [
        'short', 'shorts', 'short pant',
        'ショーツ', 'ショートパンツ',
        '短裤', 'shorts', 'short pant'
    ]):
        return '短裤'

    # 12. 裙装类
    elif any(word in product_name_lower for word in [
        'skirt', 'dress', 'skort',
        'スカート', 'ドレス', 'スコート',
        '裙子', '连衣裙', 'skort', 'skirt', 'dress'
    ]):
        return '裙装'

    # 13. 高尔夫球鞋类
    elif any(word in product_name_lower for word in [
        'golf shoe', 'golf spike', 'golf footwear',
        'ゴルフシューズ', 'ゴルフスパイク', 'ゴルフフットウェア',
        '高尔夫球鞋', '高尔夫鞋', '钉鞋', 'golf shoe', 'spike'
    ]):
        return '高尔夫球鞋'

    # 14. 高尔夫手套类
    elif any(word in product_name_lower for word in [
        'golf glove', 'golf gloves', 'hand glove',
        'ゴルフグローブ', 'ゴルフ手袋', 'ハンドグローブ',
        '高尔夫手套', '手套', 'golf glove'
    ]):
        return '高尔夫手套'

    # 15. 帽子/头饰类
    elif any(word in product_name_lower for word in [
        'hat', 'cap', 'visor', 'beanie', 'headwear',
        'ハット', 'キャップ', 'バイザー', 'ビーニー', 'ヘッドウェア',
        '帽子', '球帽', '遮阳帽', '头饰', 'hat', 'cap', 'visor'
    ]):
        return '帽子/头饰'

    # 16. 腰带类
    elif any(word in product_name_lower for word in [
        'belt', 'waist belt', 'golf belt',
        'ベルト', 'ウエストベルト', 'ゴルフベルト',
        '腰带', '皮带', '高尔夫腰带', 'belt'
    ]):
        return '腰带'

    # 17. 袜子类
    elif any(word in product_name_lower for word in [
        'sock', 'socks', 'golf socks',
        'ソックス', 'ゴルフソックス',
        '袜子', '高尔夫袜', 'socks'
    ]):
        return '袜子'

    # 18. 球杆头套类
    elif any(word in product_name_lower for word in [
        'head cover', 'headcover', 'club head cover', 'wood cover',
        'ヘッドカバー', 'クラブヘッドカバー', 'ウッドカバー',
        '球杆头套', '杆头套', '木杆套', 'head cover'
    ]):
        return '球杆头套'

    # 19. 高尔夫球类
    elif any(word in product_name_lower for word in [
        'golf ball', 'ball', 'golf balls',
        'ゴルフボール', 'ボール',
        '高尔夫球', '球', 'golf ball'
    ]):
        return '高尔夫球'

    # 20. 球包类
    elif any(word in product_name_lower for word in [
        'golf bag', 'bag', 'stand bag', 'cart bag',
        'ゴルフバッグ', 'バッグ', 'スタンドバッグ', 'カートバッグ',
        '高尔夫包', '球包', '支架包', 'golf bag'
    ]):
        return '球包'

    # 21. 伞类
    elif any(word in product_name_lower for word in [
        'umbrella', 'golf umbrella',
        'アンブレラ', 'ゴルフアンブレラ',
        '雨伞', '高尔夫伞', 'umbrella'
    ]):
        return '雨伞'

    # 22. 毛巾类
    elif any(word in product_name_lower for word in [
        'towel', 'golf towel', 'hand towel',
        'タオル', 'ゴルフタオル', 'ハンドタオル',
        '毛巾', '高尔夫毛巾', '手巾', 'towel'
    ]):
        return '毛巾'

    # 23. 标记夹/果岭工具类
    elif any(word in product_name_lower for word in [
        'marker', 'ball marker', 'divot tool', 'pitchfork', 'repair tool',
        'マーカー', 'ボールマーカー', 'ディボットツール', 'ピッチフォーク', 'リペアツール',
        '标记', '标记夹', '球位标记', '果岭叉', '修复叉', 'ball marker'
    ]):
        return '标记夹/果岭工具'

    # 24. 其他高尔夫配件类
    elif any(word in product_name_lower for word in [
        'golf accessory', 'golf gear', 'training aid',
        'ゴルフアクセサリー', 'ゴルフギア', 'トレーニングエイド',
        '高尔夫配件', '高尔夫装备', '训练辅助', 'accessory'
    ]):
        return '其他高尔夫配件'

    # 25. 通用外套类（作为最后的回退）
    elif any(word in product_name_lower for word in [
        'jacket', 'blouson', 'outer jacket', 'sports jacket',
        'ジャケット', 'ブルゾン', 'アウタージャケット', 'スポーツジャケット',
        '夹克', '外套', '运动夹克', '休闲夹克',
        'アウター', 'outer', 'アウター'
    ]):
        return '外套'

    else:
        return '其他'

# ============================================================================
# 六、AI标题生成（完整的GLM提示词）
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
- Le Coq Sportif → "Le Coq公鸡乐卡克"
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

1. 长度要求（最严格！必须遵守）
总长度：26-30个汉字，一个字符都不能多，一个都不能少！

长度计算方法：
- 季节部分（如"25秋冬"）：4字
- 品牌部分（如"卡拉威"）：2-8字
- "高尔夫"：3字（必须且只能出现1次）
- 性别部分（如"男士"）：2字
- 功能词部分：2-6字
- 结尾词部分（如"夹克"）：2字

如果长度不够，必须通过以下方式精确调整：

A. 扩展功能词（2-6字）：
- 基础功能词：保暖、弹力、防泼水、速干、轻量
- 扩展功能词：保暖舒适、弹力全拉链、防泼水防风、速干透气、轻量透气
- 修饰功能词：时尚保暖舒适、专业弹力全拉链、轻便防泼水防风

B. 扩展修饰词（在功能词前）：
- 基础修饰：新款、时尚、轻便、透气、运动、专业、经典
- 组合修饰：新款时尚、时尚轻便、专业经典、运动时尚
- 三字修饰：新款时尚的、专业高品质、轻便快干型

C. 严格长度控制（精确到每个字符）：
- 如果生成后少于26字，必须在功能词前增加修饰词
- 如果生成后超过30字，必须精简功能词或修饰词
- 最终必须确保总字数在26-30字之间

D. 长度精确计算方法：
总字数 = 季节字数 + 品牌字数 + "高尔夫"(3字) + 性别字数 + 功能词字数 + 结尾词字数

对于本产品：
- 季节：25秋冬 = 4字
- 品牌：Le Coq公鸡乐卡克 = 7字
- "高尔夫" = 3字
- 性别：男士 = 2字
- 功能词：保暖棉服可拆卸 = 6字（可调整）
- 结尾词：夹克 = 2字
- 当前总计：24字（需要增加2-6字）

解决方案（精确增加字数）：
- 增加1字：保暖棉服可拆卸轻便夹克 (30字) ✅
- 增加2字：保暖舒适棉服可拆卸夹克 (31字) ❌ 超长
- 精确控制：保暖棉服可拆卸轻便夹克 = 30字 ✅

建议模式：保暖棉服可拆卸 + 1字修饰 = 27-29字

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

输出要求（严格执行）：
- 直接输出标题，不要任何解释、不要"好的"等应答词、不要markdown格式
- 最终标题必须是26-30个汉字，少一个字或多一个字都算失败
- 在输出前，自己先数一遍字数，确保符合要求
- 如果不确定长度，宁可稍长也不要太短

字数验证步骤：
1. 生成标题初稿
2. 计算字数：len(标题)
3. 如果字数 < 26，在功能词前增加修饰词
4. 如果字数 > 30，精简功能词或修饰词
5. 最终输出26-30字的标题

现在严格按照要求生成标题："""

    return prompt


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


def clean_title(title: str) -> str:
    """
    清理标题中的常见问题，并自动调整长度到26-30字
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

    # 长度自动调整
    title = adjust_title_length(title)

    return title


def adjust_title_length(title: str) -> str:
    """
    自动调整标题长度到26-30字范围
    """
    if not title:
        return title

    current_length = len(title)

    # 如果长度刚好，直接返回
    if 26 <= current_length <= 30:
        return title

    # 如果太长，需要缩短
    if current_length > 30:
        return shorten_title(title, current_length)

    # 如果太短，需要加长
    if current_length < 26:
        return lengthen_title(title, current_length)

    return title


def shorten_title(title: str, current_length: int) -> str:
    """
    缩短标题到30字以内
    """
    excess = current_length - 30

    # 策略1: 删除多余的修饰词
    modifiers_to_remove = ['轻便', '时尚', '新款', '专业', '舒适']
    for modifier in modifiers_to_remove:
        if excess <= 0:
            break
        if modifier in title:
            title = title.replace(modifier, '', 1)
            excess -= len(modifier)

    # 策略2: 精简功能词
    if excess > 0:
        function_word_replacements = {
            '保暖棉服': '保暖',
            '弹力全拉链': '全拉链',
            '防泼水防风': '防泼水',
            '速干透气': '速干'
        }
        for long_word, short_word in function_word_replacements.items():
            if excess <= 0:
                break
            if long_word in title:
                title = title.replace(long_word, short_word, 1)
                excess -= len(long_word) - len(short_word)

    # 如果还是太长，直接截断
    if len(title) > 30:
        title = title[:30]

    return title


def lengthen_title(title: str, current_length: int) -> str:
    """
    加长标题到26字以上
    """
    needed = 26 - current_length

    # 策略1: 在功能词前添加修饰词
    function_words = ['保暖', '弹力', '防泼水', '速干', '轻量', '舒适']
    modifiers = {
        1: ['新', '轻', '专'],
        2: ['新款', '时尚', '专业', '轻便'],
        3: ['高品质', '新款时尚', '专业经典']
    }

    for word in function_words:
        if word in title and needed > 0:
            # 选择合适的修饰词长度
            if needed in modifiers:
                modifier_list = modifiers[needed]
            else:
                modifier_list = modifiers[2]  # 用3字修饰词然后调整

            for modifier in modifier_list:
                new_word = modifier + word
                if new_word in title:
                    continue  # 避免重复添加

                title = title.replace(word, new_word, 1)
                needed -= len(modifier)

                if needed <= 0:
                    break

            if needed <= 0:
                break

    # 如果还是不够长，在结尾词前添加修饰
    if needed > 0:
        endings = ['夹克', '上衣', '长裤', '短裤', '帽子', '手套']
        for ending in endings:
            if ending in title and needed > 0:
                if needed >= 2:
                    modifier = '时尚'
                elif needed >= 1:
                    modifier = '新'
                else:
                    break

                title = title.replace(ending, modifier + ending, 1)
                needed -= len(modifier)
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

    # 去除特殊符号（保留必要的空格）
    title = re.sub(r'[/／\\|｜×＋\+\-\*•·]+', '', title)
    # 只删除连续的空格，保留单个空格
    title = re.sub(r'\s{2,}', ' ', title)
    # 删除首尾空格
    title = title.strip()

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
# 七、产品描述翻译（完整GLM提示词）
# ============================================================================

def clean_description_text(description: str) -> str:
    """清理日文描述文本，提取真正的商品描述内容"""
    if not description:
        return ""

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', description)

    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()

    # 移除常见的无关信息
    unwanted_patterns = [
        r'※.*?。',  # 注意事项
        r'お客様.*?。',  # 客户相关
        r'返品.*?。',  # 退货相关
        r'配送.*?。',  # 配送相关
    ]

    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text)

    return text.strip()

def build_enhanced_translation_prompt(description: str) -> str:
    """构建增强的商品描述翻译提示词"""
    return f"""请将以下日文服装产品描述翻译成中文，具体要求：

【翻译要求】
- 语言流畅自然，避免机翻腔
- 专业术语准确（如面料名称、工艺）
- 保持营销文案的吸引力

【格式要求】
- 产品描述：分段落展示，每个特点单独一段
- 产品亮点：用【】突出显示，如【8向弹力】
- 材质信息：单独成行
- 产地和洗涤：单独标注
- 尺码表：必须格式化为Markdown表格

【尺码表格式示例】
| 尺码 | 胸围 | 衣长 | 袖长 |
|------|------|------|------|
| S    | 106cm| 58cm | 77.5cm|
| M    | 110cm| 60cm | 79cm|

【期望输出格式】
注意：只输出指定结构内容，禁止写开场白、致谢、解释等额外文字，直接从【产品描述】开头输出。

【产品描述】
采用塔夫塔面料，具有全方向弹力和适度挺括感。融入运动风格设计的茄克式外套。为应对温差变化，袖子采用可拆卸设计，可在短袖⇔长袖之间切换。下摆配有抽绳，可调节版型。

【产品亮点】
半袖风格 - 本季必备的半袖款式
8向弹力 - 全方向伸缩面料
2WAY设计 - 可拆卸袖子

【材质信息】
面料：100%聚酯纤维
辅料：100%聚酯纤维

【产地与洗涤】
产地：越南制造
洗涤：按标签说明

【尺码对照表】
| 尺码 | 胸围 | 衣长 | 袖长 |
|------|------|------|------|
| S    | 106cm| 58cm | 77.5cm|
| M    | 110cm| 60cm | 79cm|
| L    | 114cm| 62cm | 80cm|
| LL   | 118cm| 63cm | 81cm|

【尺码说明】
※ 以上尺寸为成品实测尺寸（包含松量）
※ 因面料特性，可能存在1-2cm误差
※ 商品标签标注的为净体尺寸，请参考尺码表选择

原文：
{description}
"""

def call_glm_api_internal(prompt: str) -> str:
    """内部 GLM API 调用实现"""
    global last_glm_call_ts

    api_key = os.environ.get('ZHIPU_API_KEY') or os.environ.get('GLM_API_KEY')
    if not api_key:
        print("错误：ZHIPU_API_KEY 环境变量未设置")
        return ""

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"{api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-4.6",  # 使用 GLM-4.6 模型进行翻译
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }

    # 限流控制和重试逻辑
    for attempt in range(GLM_MAX_RETRIES + 1):
        try:
            # 使用锁控制最小间隔
            with glm_call_lock:
                current_time = time.time()
                time_since_last_call = current_time - last_glm_call_ts
                sleep_time = max(0, GLM_MIN_INTERVAL - time_since_last_call)

                if sleep_time > 0:
                    time.sleep(sleep_time)

                # 发起请求
                response = requests.post(url, headers=headers, json=payload, timeout=180)
                last_glm_call_ts = time.time()

            response.raise_for_status()
            data = response.json()
            print(f"GLM API响应状态: {response.status_code}")

            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]['message']
                content = choice.get('content', '').strip()

                print(f"提取的content: {content[:200]}...")
                return content
            else:
                print(f"API响应格式异常: choices不存在或为空")
                return ""

        except requests.exceptions.HTTPError as e:
            print(f"GLM API HTTP错误 (尝试{attempt+1}/{GLM_MAX_RETRIES+1}): {e}")

            # 检查是否是429错误
            if e.response.status_code == 429 or "Too Many Requests" in str(e):
                if attempt < GLM_MAX_RETRIES:
                    # 指数退避策略
                    backoff_time = 1.0 * (GLM_BACKOFF_FACTOR ** attempt)
                    print(f"限流重试，等待{backoff_time}秒...")
                    time.sleep(backoff_time)
                    continue
                else:
                    print("达到最大重试次数，放弃请求")
                    return ""
            else:
                print("非429错误，放弃请求")
                return ""

        except requests.exceptions.ConnectionError as e:
            print(f"GLM API连接错误 (尝试{attempt+1}/{GLM_MAX_RETRIES+1}): {e}")
            print("连接被重置或网络不稳定，准备重试...")

            if attempt < GLM_MAX_RETRIES:
                # 指数退避策略
                backoff_time = 1.0 * (GLM_BACKOFF_FACTOR ** attempt)
                print(f"连接重试，等待{backoff_time}秒...")
                time.sleep(backoff_time)
                continue
            else:
                print("达到最大重试次数，放弃请求")
                return ""

        except Exception as e:
            print(f"GLM API其他错误 (尝试{attempt+1}/{GLM_MAX_RETRIES+1}): {e}")

            # 其他类型的错误
            if "Too Many Requests" in str(e) or "429" in str(e):
                if attempt < GLM_MAX_RETRIES:
                    backoff_time = 1.0 * (GLM_BACKOFF_FACTOR ** attempt)
                    print(f"限流重试，等待{backoff_time}秒...")
                    time.sleep(backoff_time)
                    continue
                else:
                    print("达到最大重试次数，放弃请求")
                    return ""
            else:
                print("其他错误，放弃请求")
                return ""

    return ""

def validate_translation_format(translated: str) -> bool:
    """验证翻译结果是否符合预期格式"""
    if not translated:
        return False

    # 降低要求，只检查必需的核心部分
    required_sections = [
        '【产品描述】',
        '【产品亮点】'
    ]

    # 检查是否包含所有必需的部分
    for section in required_sections:
        if section not in translated:
            print(f"验证失败：缺少必需部分 {section}")
            return False

    # 检查是否包含中文（确保是中文翻译）
    if not re.search(r'[\u4e00-\u9fff]', translated):
        print("验证失败：翻译结果不包含中文字符")
        return False

    print("翻译格式验证通过")
    return True

def extract_source_description(product: Dict) -> str:
    """提取并清理用于翻译的描述文本"""
    if not product:
        return ""

    # 尝试从多个字段获取描述信息
    description = (product.get('description', '') or
                  product.get('promotionText', '') or
                  product.get('promotion_text', '') or
                  product.get('productDescription', '') or
                  product.get('product_description', '') or
                  product.get('tags', ''))

    if not description:
        return ""

    cleaned_description = clean_description_text(description)
    if not cleaned_description:
        print("警告：description 清理后为空，跳过翻译")
        return ""

    return cleaned_description

def translate_description(product: Dict) -> str:
    """将商品描述翻译成结构化中文格式"""
    cleaned_description = extract_source_description(product)
    if not cleaned_description:
        return ""

    print(f"清理后的描述内容（前100字符）：{cleaned_description[:100]}...")

    prompt = build_enhanced_translation_prompt(cleaned_description)
    print(f"准备调用 GLM 翻译，提示词长度：{len(prompt)}")

    try:
        translated = call_glm_api_internal(prompt)
        print(f"GLM 翻译返回结果长度：{len(translated) if translated else 0}")
        print(f"翻译结果（前100字符）：{translated[:100] if translated else 'None'}...")

        if not translated:
            print("GLM 翻译返回空结果")
            return ""

        # 4. 验证翻译结果格式
        if not validate_translation_format(translated):
            print("翻译结果格式验证失败，返回空字符串")
            return ""

        print("翻译成功完成")
        return translated.strip()

    except Exception as e:
        print(f"翻译过程出现异常：{e}")
        return ""

# ============================================================================
# 八、颜色处理功能（完整翻译）
# ============================================================================

def translate_color_name(color_name: str) -> str:
    """将英文颜色名称翻译成中文"""
    if not color_name:
        return color_name

    # 先尝试直接匹配
    if color_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[color_name]

    # 尝试转大写匹配
    upper_name = color_name.upper()
    if upper_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[upper_name]

    # 尝试转首字母大写匹配
    title_name = color_name.title()
    if title_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[title_name]

    # 找不到就返回原值
    return color_name

def build_color_multiline(colors) -> str:
    """构建颜色多行字符串，只输出中文名称"""
    if not colors:
        return ""

    # 如果是字符串，尝试分割
    if isinstance(colors, str):
        colors = [c.strip() for c in colors.split(',') if c.strip()]

    # 如果不是列表，转换为列表
    if not isinstance(colors, (list, tuple)):
        colors = [str(colors)]

    lines = []
    for color in colors:
        if not color:
            continue
        # 如果是字典格式
        if isinstance(color, dict):
            color_name = color.get('name', '') or color.get('colorName', '')
        else:
            color_name = str(color)

        chinese = translate_color_name(color_name.strip())
        if chinese:
            lines.append(chinese)

    return "\n".join(lines)

# ============================================================================
# 九、图片处理规则（完整实现：第一个颜色全部，其他颜色前6张）
# ============================================================================

def process_images_by_color(image_groups: List[Dict]) -> List[Dict]:
    """
    图片处理规则：第一个颜色保留所有图片，其他颜色只保留前6张
    """
    if not image_groups:
        return []

    processed_groups = []

    for i, group in enumerate(image_groups):
        processed_group = group.copy()

        if i == 0:
            # 第一个颜色：保留所有图片
            processed_group['images'] = group.get('images', [])
            print(f"第一个颜色 {group.get('colorName', 'Unknown')} 保留全部 {len(processed_group['images'])} 张图片")
        else:
            # 其他颜色：只保留前6张
            images = group.get('images', [])
            processed_group['images'] = images[:6] if len(images) > 6 else images
            print(f"颜色 {group.get('colorName', 'Unknown')} 保留前6张图片（共{len(processed_group['images'])}张）")

        processed_groups.append(processed_group)

    return processed_groups

# ============================================================================
# 十、13字段处理器主类
# ============================================================================

class Callaway13FieldProcessor:
    """
    卡拉威13字段改写处理器

    完整实现以下功能：
    1. AI标题生成（完整GLM提示词）
    2. 24种细分分类
    3. 产品描述翻译
    4. 颜色翻译
    5. 图片处理规则
    """

    def __init__(self):
        self.processor_name = "Callaway13FieldProcessor"
        self.version = "1.0"

    def process_product(self, product: Dict) -> Dict:
        """
        处理单个产品，返回包含13个字段的结果

        Args:
            product: 输入产品数据

        Returns:
            Dict: 包含13个字段的处理结果
        """
        print(f"\n🔄 开始处理产品: {product.get('商品标题', product.get('productName', 'Unknown'))}")

        result = {
            # 基础字段
            '商品ID': product.get('商品编号', product.get('productId', '')),
            '商品名称': product.get('商品标题', product.get('productName', '')),
            '品牌': product.get('品牌名', product.get('brand', '')),  # 修复：支持中文字段名
            '商品链接': product.get('商品链接', product.get('详情页链接', product.get('detailUrl', ''))),
            '分类': product.get('分类', product.get('category', '')),
            '价格': product.get('价格', product.get('priceText', '')),

            # 改写字段
            '生成标题': '',
            '性别': '',
            '服装类型': '',
            '颜色': '',
            '尺寸': '',
            '描述翻译': '',
            '图片链接': ''
        }

        try:
            # 1. 品牌识别 - 如果第一步已经识别了品牌，直接使用
            if result['品牌']:
                brand_chinese = result['品牌']
                print(f"✓ 品牌识别: {brand_chinese} (来自第一步)")
            else:
                brand_key, brand_chinese, brand_short = extract_brand_from_product(product)
                result['品牌'] = brand_chinese
                print(f"✓ 品牌识别: {brand_chinese} (自动识别)")

            # 2. 性别分类
            result['性别'] = determine_gender(product)
            print(f"✓ 性别分类: {result['性别']}")

            # 3. 服装类型分类（24种细分）
            result['服装类型'] = determine_clothing_type(product)
            print(f"✓ 服装类型: {result['服装类型']}")

            # 4. AI标题生成
            print("🤖 开始AI标题生成...")
            result['生成标题'] = generate_cn_title(product)
            if result['生成标题']:
                print(f"✓ AI标题生成成功: {result['生成标题']}")
            else:
                print("❌ AI标题生成失败")

            # 5. 颜色翻译
            colors = (product.get('colors', []) or
                     product.get('颜色选项', '') or
                     product.get('颜色', []))
            if colors:
                # 如果是字符串，分割处理
                if isinstance(colors, str):
                    color_list = [c.strip() for c in colors.split(',') if c.strip()]
                    # 处理中文颜色名
                    color_list = [color.split('（')[0].strip() for color in color_list]
                    result['颜色'] = build_color_multiline(color_list)
                    print(f"✓ 颜色翻译完成: {len(color_list)}种颜色")
                else:
                    result['颜色'] = build_color_multiline(colors)
                    print(f"✓ 颜色翻译完成: {len(colors)}种颜色")
            else:
                result['颜色'] = ''
                print("⚠️ 无颜色信息")

            # 6. 尺寸处理
            sizes = (product.get('sizes', []) or
                   product.get('尺寸选项', '') or
                   product.get('尺码', []))
            if sizes:
                # 如果是字符串，分割处理
                if isinstance(sizes, str):
                    size_list = [s.strip() for s in sizes.split(',') if s.strip()]
                    result['尺寸'] = ', '.join(size_list)
                    print(f"✓ 尺寸处理完成: {len(size_list)}种尺码")
                elif isinstance(sizes, list):
                    result['尺寸'] = ', '.join(str(s) for s in sizes)
                    print(f"✓ 尺寸处理完成: {len(sizes)}种尺码")
                else:
                    result['尺寸'] = str(sizes)
                    print(f"✓ 尺寸处理完成")
            else:
                result['尺寸'] = ''
                print("⚠️ 无尺码信息")

            # 7. 描述翻译
            print("📝 开始描述翻译...")
            result['描述翻译'] = translate_description(product)
            if result['描述翻译']:
                print(f"✓ 描述翻译完成: {len(result['描述翻译'])}字符")
            else:
                print("⚠️ 描述翻译失败或无内容")

            # 8. 图片处理
            image_groups = (product.get('imageGroups', []) or
                           product.get('图片链接', []))
            if image_groups:
                # 检查数据格式
                if isinstance(image_groups, list) and len(image_groups) > 0:
                    if isinstance(image_groups[0], str):
                        # 如果是字符串数组，直接拼接
                        result['图片链接'] = ', '.join(image_groups[:10])
                        print(f"✓ 图片处理完成: {len(image_groups)}张图片")
                    else:
                        # 如果是对象数组，按原有逻辑处理
                        processed_groups = process_images_by_color(image_groups)
                        # 收集所有图片链接
                        all_images = []
                        for group in processed_groups:
                            all_images.extend(group.get('images', []))
                        result['图片链接'] = ', '.join(all_images[:10])  # 只保留前10张
                        print(f"✓ 图片处理完成: {len(processed_groups)}个颜色组，共{len(all_images)}张图片")
                else:
                    result['图片链接'] = str(image_groups)
                    print("✓ 图片处理完成")
            else:
                # 尝试从其他字段获取图片
                main_image = product.get('mainImage', '')
                if main_image:
                    result['图片链接'] = main_image
                    print("✓ 使用主图")
                else:
                    result['图片链接'] = ''
                    print("⚠️ 无图片信息")

            print(f"✅ 产品处理完成: {product.get('productId', 'Unknown')}")

        except Exception as e:
            print(f"❌ 产品处理失败: {e}")
            import traceback
            traceback.print_exc()

        return result

    def process_products_batch(self, products: List[Dict]) -> List[Dict]:
        """
        批量处理产品

        Args:
            products: 产品列表

        Returns:
            List[Dict]: 处理结果列表
        """
        results = []

        print(f"\n🚀 开始批量处理 {len(products)} 个产品")

        for i, product in enumerate(products):
            print(f"\n📦 处理进度: {i+1}/{len(products)}")
            result = self.process_product(product)
            results.append(result)

        print(f"\n✅ 批量处理完成: {len(results)} 个产品")
        return results

    def get_processing_summary(self, results: List[Dict]) -> Dict:
        """
        获取处理结果汇总

        Args:
            results: 处理结果列表

        Returns:
            Dict: 汇总信息
        """
        if not results:
            return {}

        summary = {
            '总产品数': len(results),
            '成功标题生成': sum(1 for r in results if r.get('生成标题')),
            '成功描述翻译': sum(1 for r in results if r.get('描述翻译')),
            '品牌分布': {},
            '性别分布': {},
            '服装类型分布': {}
        }

        # 统计分布
        for result in results:
            # 品牌分布
            brand = result.get('品牌', '未知')
            summary['品牌分布'][brand] = summary['品牌分布'].get(brand, 0) + 1

            # 性别分布
            gender = result.get('性别', '未知')
            summary['性别分布'][gender] = summary['性别分布'].get(gender, 0) + 1

            # 服装类型分布
            clothing_type = result.get('服装类型', '未知')
            summary['服装类型分布'][clothing_type] = summary['服装类型分布'].get(clothing_type, 0) + 1

        return summary

# ============================================================================
# 十一、错误处理
# ============================================================================

class TitleGenerationError(Exception):
    """标题生成异常"""
    pass

class TranslationError(Exception):
    """翻译异常"""
    pass

class ProcessingError(Exception):
    """处理异常"""
    pass

# ============================================================================
# 十二、导出接口
# ============================================================================

# 创建全局处理器实例
processor = Callaway13FieldProcessor()

# 导出的便捷函数
def process_single_product(product: Dict) -> Dict:
    """处理单个产品的便捷函数"""
    return processor.process_product(product)

def process_multiple_products(products: List[Dict]) -> List[Dict]:
    """批量处理产品的便捷函数"""
    return processor.process_products_batch(products)

# 主要导出
__all__ = [
    'Callaway13FieldProcessor',
    'process_single_product',
    'process_multiple_products',
    'processor',
    'generate_cn_title',
    'translate_description',
    'determine_clothing_type',
    'determine_gender',
    'translate_color_name',
    'build_color_multiline',
    'process_images_by_color'
]

# ============================================================================
# 十三、使用示例
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json
    from datetime import datetime

    parser = argparse.ArgumentParser(description='第二步：通用字段改写处理器 (所有品牌统一)')
    parser.add_argument('--input', '-i', type=str, help='第一步抓取的JSON数据文件路径')
    parser.add_argument('--output', '-o', type=str, help='处理后的JSON输出文件路径 (可选)')
    parser.add_argument('--example', '-e', action='store_true', help='运行示例处理')
    parser.add_argument('--version', '-v', action='version', version='Callaway 13-Field Processor v2.0')

    args = parser.parse_args()

    if args.input:
        # 从文件读取第一步抓取的数据
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                step1_data = json.load(f)

            print(f"📥 从文件读取数据: {args.input}")

            # 处理数据
            print("🔄 开始处理抓取数据...")
            result = process_single_product(step1_data)

            # 输出结果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"💾 处理结果已保存: {args.output}")
            else:
                # 输出到标准输出
                filename = f"step2_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"💾 处理结果已保存: {filename}")

            print("\n📋 处理结果:")
            print(f"商品ID: {result.get('商品ID', 'N/A')}")
            print(f"生成标题: {result.get('生成标题', 'N/A')}")
            print(f"品牌: {result.get('品牌', 'N/A')}")
            print(f"性别: {result.get('性别', 'N/A')}")
            print(f"服装类型: {result.get('服装类型', 'N/A')}")

        except FileNotFoundError:
            print(f"❌ 文件未找到: {args.input}")
        except json.JSONDecodeError:
            print(f"❌ JSON格式错误: {args.input}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")

    elif args.example:
        # 示例使用
        example_product = {
            'productId': 'C25215200',
            'productName': '25FW メンズ ストレッチPOLOシャツ',
            'detailUrl': 'https://www.callawaygolf.jp/mens/tops/polo/C25215200.html',
            'priceText': '¥7,700 (税込)',
            'colors': [
                {'name': 'WHITE', 'code': '1000'},
                {'name': 'NAVY', 'code': '1031'},
                {'name': 'BLACK', 'code': '1040'}
            ],
            'sizes': ['S', 'M', 'L', 'LL'],
            'description': '今シーズンのスターストレッチPOLO。ストレッチ性に優れた素材で、動きやすさ抜群。',
            'mainImage': 'https://example.com/image.jpg'
        }

        print("🎯 开始示例处理...")
        result = process_single_product(example_product)

        print("\n📋 处理结果:")
        for key, value in result.items():
            print(f"{key}: {value}")

    else:
        print("第二步：通用字段改写处理器")
        print("\n使用方法:")
        print("  # 处理第一步抓取的数据")
        print("  python3 callaway_13field_processor.py --input step1_data.json")
        print("")
        print("  # 指定输出文件")
        print("  python3 callaway_13field_processor.py --input step1_data.json --output step2_processed.json")
        print("")
        print("  # 运行示例")
        print("  python3 callaway_13field_processor.py --example")
        print("")
        print("  # 查看帮助")
        print("  python3 callaway_13field_processor.py --help")