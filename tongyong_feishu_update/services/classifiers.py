"""产品分类服务

提供产品性别和服装类型的分类功能
"""

def determine_gender(product_data):
    """确定产品性别分类

    Args:
        product_data: 产品数据

    Returns:
        str: 性别分类（男性/女性/中性等）
    """
    if isinstance(product_data, dict):
        product_name = (
            product_data.get('productName')
            or product_data.get('title')
            or product_data.get('name')
            or ''
        )
        category = product_data.get('category', '')
        # 优先使用明确的gender字段
        explicit_gender = product_data.get('gender', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
        explicit_gender = getattr(product_data, 'gender', '')
    else:
        return '中性'

    # 1. 优先使用明确的gender字段
    if explicit_gender:
        if explicit_gender.lower() in ['女', '女性', 'womens', 'ladies']:
            return '女'
        elif explicit_gender.lower() in ['男', '男性', 'mens', 'men']:
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
        return '中性'  # 默认中性，避免误判男

def determine_clothing_type(product_data):
    """根据标题/分类/URL 粗分服装类型（直接对接淘宝类目映射前的内部类型）"""
    if isinstance(product_data, dict):
        product_name = (
            product_data.get('productName')
            or product_data.get('title')
            or product_data.get('name')
            or ''
        )
        category = product_data.get('category', '')
        detail_url = product_data.get('detailUrl', '') or product_data.get('url', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name or ''
        category = getattr(product_data, 'category', '') or ''
        detail_url = getattr(product_data, 'detailUrl', '') or getattr(product_data, 'url', '')
    else:
        return '其他'

    name_lower = product_name.lower()
    category_lower = category.lower()
    url_lower = detail_url.lower()

    def has_any(words):
        return any(w in name_lower or w in category_lower or w in url_lower for w in words)

    # 卫衣/连帽衫/抓绒（名称优先于 URL 模糊路径）
    if has_any(['hoodie', 'sweatshirt', 'sweat', 'crewneck', 'pullover', 'fleece', 'パーカー', 'スウェット', 'フリース']):
        return '卫衣'

    # 外套：羽绒/棉服/中綿/ブルゾン/ジャケット 等
    if has_any(['down', 'padded', 'quilted', '中綿', 'ブルゾン', 'ジャケット', 'coat']):
        return '外套'
    if has_any(['windbreaker', 'wind jacket', '防风', '风衣']):
        return '外套'

    # 马甲/背心
    if has_any(['vest', 'gilet', 'ベスト', 'ジレ', '無袖', '无袖']):
        return '马甲'

    # Polo
    if has_any(['polo', 'ポロ']):
        return 'POLO'

    # 短袖 / T恤
    if has_any(['t-shirt', 'tshirt', 'tee', '短袖', '半袖', 't恤']):
        return '短袖'

    # 长袖上衣（针织、衬衫、毛衣、开衫）
    if has_any(['long sleeve', '長袖', '长袖', 'shirt', 'シャツ', 'knit', 'sweater', 'cardigan', 'カーディガン']):
        return '长袖'

    # 紧身/打底
    if has_any(['紧身', '压缩', '打底', 'compression']):
        return '紧身衣裤'

    # 训练服
    if has_any(['训练', 'training', '场训']):
        return '训练服'

    # 下装：短裤优先于长裤
    if has_any(['shorts', 'short pant', 'ショーツ', 'ハーフパンツ', '短裤']):
        return '短裤'
    if has_any(['pant', 'trouser', 'ロングパンツ', '长裤']):
        return '长裤'

    # 裙装
    if has_any(['skirt', 'skort', 'dress', 'スカート', '裙']):
        return '短裙'

    # 腰带/袜子
    if has_any(['belt', '腰带', '皮带', 'ベルト']):
        return '腰带'
    if has_any(['sock', 'socks', 'ソックス', '袜']):
        return '袜子'

    # 配件类
    if has_any(['glove', 'グローブ', '手套']):
        return '手套'
    if has_any(['cap', 'hat', 'ハット', 'キャップ', 'バイザー', '帽']):
        return '帽子'
    if has_any(['ball', 'ボール', '高尔夫球']):
        return '高尔夫球'
    if has_any(['bag', 'バッグ', 'キャディ', 'caddy', 'tote', 'トート', 'pouch', 'ポーチ']):
        return '球包'

    return '其他'

def map_to_taobao_category(product_data, clothing_type: str) -> str:
    """
    将内部服装细分类映射到淘宝类目（飞书写入直接使用淘宝分类）
    """
    if isinstance(product_data, dict):
        product_name = product_data.get('productName', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
    else:
        product_name = ''

    name_lower = product_name.lower()
    ctype = clothing_type or '其他'

    # 特殊关键词优先
    if any(k in name_lower for k in ['紧身', '压缩', '打底', 'compression']):
        return '紧身衣裤'
    if '训练' in name_lower or '场训' in name_lower or 'training' in name_lower:
        return '训练服'
    if any(k in name_lower for k in ['short sleeve', '短袖', '半袖']):
        return '短袖'
    if any(k in name_lower for k in ['长袖', 'long sleeve', '長袖']):
        return '长袖'

    mapping = {
        'POLO': 'POLO',
        'Polo衫': 'POLO',
        'T恤': 'T恤',
        '卫衣/连帽衫': '卫衣',
        '卫衣': '卫衣',
        '夹克': '外套',
        '风衣/防风外套': '外套',
        '羽绒服/棉服': '外套',
        '外套': '外套',
        '马甲/背心': '马甲',
        '马甲': '马甲',
        '针织衫/毛衣': '长袖',
        '衬衫': '长袖',
        '长裤': '长裤',
        '短裤': '短裤',
        '裙装': '短裙',
        '短裙': '短裙',
        '腰带': '腰带',
        '袜子': '袜子',
        '短袖': '短袖',
        '长袖': '长袖',
        '训练服': '训练服',
        '紧身衣裤': '紧身衣裤',
        '手套': '手套',
        '帽子': '帽子',
        '高尔夫球': '高尔夫球',
        '球包': '球包',
        '包': '球包'
    }

    return mapping.get(ctype, '其他')
