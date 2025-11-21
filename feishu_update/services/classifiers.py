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
        product_name = product_data.get('productName', '')
        category = product_data.get('category', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
    else:
        return '中性'
    
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
    """确定服装类型 - 详细分类版本

    Args:
        product_data: 产品数据

    Returns:
        str: 详细服装类型（24个细分类别）
    """
    if isinstance(product_data, dict):
        product_name = product_data.get('productName', '')
        category = product_data.get('category', '')
        detail_url = product_data.get('detailUrl', '')
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
        detail_url = getattr(product_data, 'detailUrl', '')
    else:
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
    if any(k in name_lower for k in ['紧身', '压缩', '打底']):
        return '紧身衣裤'
    if '训练' in name_lower or '场训' in name_lower:
        return '训练服'
    if any(k in name_lower for k in ['短袖', '半袖', 'short sleeve']):
        return '短袖'
    if any(k in name_lower for k in ['长袖', 'long sleeve']):
        return '长袖'

    # 直接映射表到淘宝类目
    mapping = {
        'Polo衫': 'POLO',
        'T恤': 'T恤',
        '卫衣/连帽衫': '卫衣',
        '夹克': '外套',
        '风衣/防风外套': '外套',
        '羽绒服/棉服': '外套',
        '外套': '外套',
        '马甲/背心': '马甲',
        '针织衫/毛衣': '长袖',
        '衬衫': '长袖',
        '长裤': '长裤',
        '短裤': '短裤',
        '裙装': '短裙',
        '腰带': '腰带',
        '袜子': '袜子'
    }

    return mapping.get(ctype, '其他')
    # 转换为小写便于匹配
    product_name_lower = product_name.lower()
    category_lower = category.lower()
    url_lower = detail_url.lower()

    # 🆕 优先使用URL具体路径分类 - 只匹配明确的服装类型
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
    # 移除通用配件URL匹配，让具体的产品名称分类优先处理
    # 注意：移除了 '/outer/' 的优先匹配，因为它会覆盖更精确的产品名称匹配

    # 🎯 详细分类检查 - 按照服装类型细分，顺序更重要（产品名称优先级最高）

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
        '长裤', '长裤', '全长的', 'trouser', 'long pant', 'trousers'
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
