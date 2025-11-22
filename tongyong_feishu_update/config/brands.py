"""品牌配置

本模块包含品牌相关的配置常量和映射关系。
主要包括：
- 品牌名称标准化
- 品牌ID映射
- 品牌分类配置
- 品牌别名映射
"""

# 品牌关键词（英文+日文）
BRAND_KEYWORDS = {
    'callawaygolf': ['callaway', 'キャロウェイ', 'calaway'],
    'titleist': ['titleist', 'タイトリスト'],
    'taylormade': ['taylormade', 'テーラーメイド', 'taylor made'],
    'pearlygates': ['pearly gates', 'パーリーゲイツ', 'pg is pg', 'pearlygates'],
    'lecoqsportif': ['le coq', 'ルコック', 'lecoq'],
    'munsingwear': ['munsingwear', 'マンシングウェア', 'penguin'],
}

# 品牌完整中文名（用于标题）
BRAND_MAP = {
    'callawaygolf': 'Callaway/卡拉威',
    'titleist': '泰特利斯Titleist',
    'taylormade': '泰勒梅TaylorMade',
    'ping': 'PING',
    'cobragolf': '眼镜蛇Cobra',
    'odyssey': '奥德赛Odyssey',
    'scottycameron': '斯科蒂·卡梅伦Scotty Cameron',
    'pxg': '帕森斯PXG',
    'mizuno': '美津浓Mizuno',
    'srixon': '史力胜Srixon',
    'clevelandgolf': '克利夫兰Cleveland',
    'bridgestonegolf': '普利司通Bridgestone',
    'xxio': '尊悦XXIO',
    'honma': '本间Honma',
    'prgr': '普罗基亚PRGR',
    'yamahagolf': '雅马哈Yamaha',
    'onoff': '奥纳夫OnOff',
    'majesty': '马捷斯帝Majesty',
    'fourteen': '飒汀Fourteen',
    'epon': '远藤EPON',
    'miura': '三浦Miura',
    'vega': '维嘉Vega',
    'romaro': '罗马罗Romaro',
    'katanagolf': '武士刀Katana',
    'kasco': '卡司科Kasco',
    'yonex': '尤尼克斯Yonex',
    'bettinardi': '贝丁拿迪Bettinardi',
    'evnroll': 'Evnroll',
    'wilsonstaff': '威尔胜Wilson',
    'touredge': '途锐致Tour Edge',
    'benhogan': '本·霍根Ben Hogan',
    'macgregor': '麦格雷戈MacGregor',
    'adamsgolf': '亚当斯Adams',
    'lynxgolf': '山猫Lynx',
    'bensayers': '本·塞耶斯Ben Sayers',
    'snakeeyes': '蛇眼Snake Eyes',
    'maltby': '马尔特比Maltby',
    'lagolf': 'LA高尔夫LA Golf',
    'toulon': '图伦Toulon',
    'lecoqsportif': 'Le Coq公鸡乐卡克',  # 新增Le Coq品牌
    'lecoqsportifgolf': 'Le Coq公鸡乐卡克',  # 新增Le Coq Golf
    'munsingwear': '万星威Munsingwear',  # 新增Munsingwear品牌
    'pearlygates': 'PEARLY GATES',  # 新增PEARLY GATES品牌
}

# 品牌简短名（用于飞书"品牌名"字段）
BRAND_SHORT_NAME = {
    'callawaygolf': 'Callaway/卡拉威',
    'titleist': '泰特利斯',
    'taylormade': '泰勒梅',
    'ping': 'PING',
    'cobragolf': '眼镜蛇',
    'odyssey': '奥德赛',
    'scottycameron': '斯科蒂·卡梅伦',
    'pxg': '帕森斯',
    'mizuno': '美津浓',
    'srixon': '史力胜',
    'clevelandgolf': '克利夫兰',
    'bridgestonegolf': '普利司通',
    'xxio': '尊悦',
    'honma': '本间',
    'prgr': '普罗基亚',
    'yamahagolf': '雅马哈',
    'onoff': '奥纳夫',
    'majesty': '马捷斯帝',
    'fourteen': '飒汀',
    'epon': '远藤',
    'miura': '三浦',
    'vega': '维嘉',
    'romaro': '罗马罗',
    'katanagolf': '武士刀',
    'kasco': '卡司科',
    'yonex': '尤尼克斯',
    'bettinardi': '贝丁拿迪',
    'evnroll': 'Evnroll',
    'wilsonstaff': '威尔胜',
    'touredge': '途锐致',
    'benhogan': '本·霍根',
    'macgregor': '麦格雷戈',
    'adamsgolf': '亚当斯',
    'lynxgolf': '山猫',
    'bensayers': '本·塞耶斯',
    'snakeeyes': '蛇眼',
    'maltby': '马尔特比',
    'lagolf': 'LA高尔夫',
    'toulon': '图伦',
    'lecoqsportif': 'Le Coq公鸡乐卡克',  # 新增Le Coq品牌
    'lecoqsportifgolf': 'Le Coq公鸡乐卡克',  # 新增Le Coq Golf
    'munsingwear': '万星威',  # 新增Munsingwear品牌
    'pearlygates': 'PEARLY GATES',  # 新增PEARLY GATES品牌
}

# 品牌别名映射 - 用于识别各种拼写变体和多语言名称
BRAND_ALIASES = {
    # Callaway 别名
    'callaway': 'callawaygolf',
    'キャロウェイ': 'callawaygolf',
    'calaway': 'callawaygolf',
    'callawaygolf': 'callawaygolf',

    # Le Coq Sportif 别名
    'le coq sportif': 'lecoqsportif',
    'ルコックスポルティフ': 'lecoqsportif',
    'le coq': 'lecoqsportif',
    'lecoqgolf': 'lecoqsportifgolf',
    'le coq sportif golf': 'lecoqsportifgolf',
    'le coqsportif': 'lecoqsportif',
    '公鸡乐卡克': 'lecoqsportif',
    '乐卡克': 'lecoqsportif',

    # Titleist 别名
    'titleist': 'titleist',
    'タイトリスト': 'titleist',
    'titelist': 'titleist',
    'titleist': 'titleist',
    
    # TaylorMade 别名
    'taylormade': 'taylormade',
    'テーラーメイド': 'taylormade',
    'taylormade': 'taylormade',
    'taylormade': 'taylormade',
    
    # PING 别名
    'ping': 'ping',
    'ピン': 'ping',
    'ping': 'ping',
    
    # Cobra 别名
    'cobra': 'cobragolf',
    'cobragolf': 'cobragolf',
    'コブラ': 'cobragolf',
    
    # Odyssey 别名
    'odyssey': 'odyssey',
    'オデッセイ': 'odyssey',
    'oddysey': 'odyssey',
    
    # Scotty Cameron 别名
    'scottycameron': 'scottycameron',
    'スコッティキャメロン': 'scottycameron',
    'cameron': 'scottycameron',
    
    # PXG 别名
    'pxg': 'pxg',
    'parsonsxtremegolf': 'pxg',
    
    # Mizuno 别名
    'mizuno': 'mizuno',
    'ミズノ': 'mizuno',
    
    # Srixon 别名
    'srixon': 'srixon',
    'スリクソン': 'srixon',
    'srxion': 'srixon',
    
    # Cleveland 别名
    'cleveland': 'clevelandgolf',
    'クリーブランド': 'clevelandgolf',
    
    # Bridgestone 别名
    'bridgestone': 'bridgestonegolf',
    'ブリヂストン': 'bridgestonegolf',
    'bridgestonegolf': 'bridgestonegolf',
    
    # XXIO 别名
    'xxio': 'xxio',
    'ゼクシオ': 'xxio',
    
    # Honma 别名
    'honma': 'honma',
    '本間': 'honma',
    'ホンマ': 'honma',
    
    # PRGR 别名
    'prgr': 'prgr',
    'プロギア': 'prgr',
    'progear': 'prgr',
    
    # Yamaha 别名
    'yamaha': 'yamahagolf',
    'ヤマハ': 'yamahagolf',
    
    # OnOff 别名
    'onoff': 'onoff',
    'グローブライド': 'onoff',
    'daiwaonoff': 'onoff',
    
    # Majesty 别名
    'majesty': 'majesty',
    'maruman': 'majesty',
    'マジェスティ': 'majesty',
    
    # Fourteen 别名
    'fourteen': 'fourteen',
    'フォーティーン': 'fourteen',
    
    # Epon 别名
    'epon': 'epon',
    '遠藤': 'epon',
    'エポン': 'epon',
    
    # Miura 别名
    'miura': 'miura',
    '三浦技研': 'miura',
    'ミウラ': 'miura',
    
    # Vega 别名
    'vega': 'vega',
    'ヴェガ': 'vega',
    
    # Romaro 别名
    'romaro': 'romaro',
    'ロマロ': 'romaro',
    
    # Katana 别名
    'katana': 'katanagolf',
    'カタナ': 'katanagolf',
    'sword': 'katanagolf',
    
    # Kasco 别名
    'kasco': 'kasco',
    'キャスコ': 'kasco',
    
    # Yonex 别名
    'yonex': 'yonex',
    'ヨネックス': 'yonex',
    
    # Bettinardi 别名
    'bettinardi': 'bettinardi',
    'ベティナルディ': 'bettinardi',
    
    # Evnroll 别名
    'evnroll': 'evnroll',
    'イーブンロール': 'evnroll',
    
    # Wilson 别名
    'wilson': 'wilsonstaff',
    'wilsonstaff': 'wilsonstaff',
    
    # Tour Edge 别名
    'touredge': 'touredge',
    
    # Ben Hogan 别名
    'benhogan': 'benhogan',
    
    # MacGregor 别名
    'macgregor': 'macgregor',
    
    # Adams 别名
    'adams': 'adamsgolf',
    'adamsgolf': 'adamsgolf',
    
    # Lynx 别名
    'lynx': 'lynxgolf',
    
    # Ben Sayers 别名
    'bensayers': 'bensayers',
    
    # Snake Eyes 别名
    'snakeeyes': 'snakeeyes',
    
    # Maltby 别名
    'maltby': 'maltby',
    'golfworks': 'maltby',
    
    # LA Golf 别名
    'lagolf': 'lagolf',
    
    # Toulon 别名
    'toulon': 'toulon',
    'toulondesign': 'toulon',

    # Munsingwear 别名
    'munsingwear': 'munsingwear',
    'マンシングウェア': 'munsingwear',
    'penguin by munsingwear': 'munsingwear',
    'ペンギン バイ マンシングウェア': 'munsingwear',
    'penguin': 'munsingwear',
    '万星威': 'munsingwear',

    # PEARLY GATES 别名
    'pearly gates': 'pearlygates',
    'pearlygates': 'pearlygates',
    'pg is pg': 'pearlygates',
    'パーリーゲイツ': 'pearlygates',

    # 添加缺失的原始清单别名和规范化变体
    'titleist': 'titleist',  # title ist 规范化后
    'ping': 'ping',  # p i n g 规范化后
    'taylormade': 'taylormade',  # taylor made 规范化后  
    'cobragolf': 'cobragolf',  # cobra golf 规范化后
    'callawaygolf': 'callawaygolf',  # callaway golf 规范化后
    'parsonsxtremegolf': 'pxg',  # Parsons Xtreme Golf 规范化后
    'xxio': 'xxio',  # x x i o 规范化后
    'srxion': 'srixon',  # sr xion 规范化后 
    'touredge': 'touredge',  # tour edge 规范化后
    'benhogan': 'benhogan',  # ben hogan 规范化后
    'bensayers': 'bensayers',  # ben sayers 规范化后
    'snakeeyes': 'snakeeyes',  # snake eyes 规范化后
    'lagolf': 'lagolf',  # la golf 规范化后
    'scottycameron': 'scottycameron',  # scotty cameron 规范化后
    'adamsgolf': 'adamsgolf',  # adams golf 规范化后
    'bridgestonegolf': 'bridgestonegolf',  # bridgestone golf 规范化后
    'wilsonstaff': 'wilsonstaff',  # wilson staff 规范化后
    'progear': 'prgr',  # pro gear 规范化后
    'daiwaonoff': 'onoff',  # daiwa onoff 规范化后
    'toulondesign': 'toulon',  # toulon design 规范化后
}


def extract_brand_from_product(product):
    """
    从商品信息中提取品牌信息
    
    Args:
        product: 产品数据字典
        
    Returns:
        tuple: (brand_key, brand_chinese, brand_short)
    """
    import re
    from typing import Tuple
    
    # 获取产品名称，用于品牌识别
    product_name = product.get('productName', '').lower()
    detail_url = product.get('detailUrl', '').lower()
    brand_info = product.get('brand', '').lower()
    
    # 组合文本用于品牌匹配
    combined_text = f"{product_name} {detail_url} {brand_info}".lower()
    
    # 首先尝试通过别名映射匹配
    for alias, brand_key in BRAND_ALIASES.items():
        if alias.lower() in combined_text:
            return (
                brand_key,
                BRAND_MAP.get(brand_key, brand_key),
                BRAND_SHORT_NAME.get(brand_key, brand_key)
            )
    
    # 兜底：如果 product 带有品牌字段/brandId/_scraper_info.brand，直接使用
    fallback_brand = (
        product.get('brand') or
        product.get('brandId') or
        product.get('brand_id') or
        product.get('brandId', '')
    )
    if not fallback_brand and isinstance(product, dict):
        fallback_brand = product.get('brandId')
    if not fallback_brand:
        info = product.get('_scraper_info', {})
        if isinstance(info, dict):
            fallback_brand = info.get('brand', '')

    if fallback_brand:
        brand_key = BRAND_ALIASES.get(fallback_brand.lower(), fallback_brand.lower())
        return (
            brand_key,
            BRAND_MAP.get(brand_key, brand_key),
            BRAND_SHORT_NAME.get(brand_key, brand_key)
        )

    # 如果没有匹配，尝试通过域名匹配（针对 callawaygolf.jp）
    if 'callawaygolf' in detail_url or 'callaway' in combined_text:
        return ('callawaygolf', BRAND_MAP['callawaygolf'], BRAND_SHORT_NAME['callawaygolf'])
    
    # 未匹配到品牌时，返回 unknown，避免误判成卡拉威
    return ('unknown', '未知品牌', '')
