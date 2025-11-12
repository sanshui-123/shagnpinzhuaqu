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
    """确定服装类型

    Args:
        product_data: 产品数据

    Returns:
        str: 服装类型
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

    # 转换为小写便于匹配
    product_name_lower = product_name.lower()
    category_lower = category.lower()
    url_lower = detail_url.lower()

    # 🆕 优先使用URL路径分类 - 最准确的分类源
    if '/outer/' in url_lower or '/jacket/' in url_lower:
        return '外套'
    elif '/shirt/' in url_lower or '/polo/' in url_lower or '/tops/' in url_lower:
        if '/outer/' in url_lower:
            return '外套'  # tops/outer 优先归类为外套
        return 'T恤/Polo衫'
    elif '/pant/' in url_lower or '/trouser/' in url_lower or '/bottom/' in url_lower:
        return '裤子'
    elif '/accessory/' in url_lower:
        return '高尔夫配件'
    elif '/shoe/' in url_lower or '/footwear/' in url_lower:
        return '球鞋'
    
    # 检查外套类 - 英文和日文
    if any(word in product_name_lower for word in [
        'jacket', 'outerwear', 'blouson', 'vest', 'windbreaker',
        'ブルゾン', 'ジャケット', 'アウター', 'ベスト', '外套', '夹克', '马甲', '背心',
        # 🆕 新增日文关键词 - 针对日本网站优化
        'パーカー', 'パーカ', 'スウェット', 'スウェ', 'フルジップ', 'ジップ',
        'カノコ', 'ダブルニット', 'パーカー', 'フルジップパーカー',  # parka, sweat, full zip, 鹿纹, 双织
        'ニット', 'ジップ', 'ジヤケット', 'ウインドブレーカー',  # knit, zip, jacket, windbreaker
        # 🆕 新增中文关键词 - 基于实际产品名称
        '卫衣', '连帽衫', '棉服', '羽绒服', '抓绒', '保暖', '夹克', '棉服', '保暖', '轻便', '弹力', '舒适', '防风'
    ]):
        return '外套'
    
    # 检查T恤/Polo衫类 - 英文和日文
    elif any(word in product_name_lower for word in [
        'shirt', 'polo', 't-shirt', 'tshirt', 'top',
        'シャツ', 'ポロ', 'ティーシャツ', 'トップス', 'polo衫', 't恤',
        # 🆕 新增日文关键词
        'Tシャツ', 'ティーシャツ', 'ポロシャツ', 'トップス', '半袖', '長袖',
        'カッターシャツ', 'ブラウス', 'カーティー',  # T-shirt, polo shirt, tops, short sleeve, long sleeve
        # 🆕 新增中文关键词 - 基于实际产品名称
        '针织衫', '衬衫', '莫克领', '上衣', '舒适', '保暖', '长袖', '短袖', '针织', 'V领', '高领', '内衣'
    ]):
        return 'T恤/Polo衫'
    
    # 检查裤子类 - 英文和日文
    elif any(word in product_name_lower for word in [
        'pant', 'trouser', 'short', 'skirt',
        'パンツ', 'ズボン', 'ショーツ', 'スカート', '裤子', '短裤', '裙子',
        # 🆕 新增日文关键词
        'トラウザー', 'スラックス', 'ショートパンツ', 'ロングパンツ',
        'ボトムス', 'クロップドパンツ', 'プリントパンツ',  # trousers, slacks, shorts, pants, bottoms
        # 🆕 新增中文关键词 - 基于实际产品名称
        '长裤', '半身裙', '运动长裤', '弹力', '保暖', '双面', '针织', '几何', '花印', '裙摆', '中棉', '防泼水', '千鳥', '印花'
    ]):
        return '裤子'
        
    # 检查腰带类
    elif any(word in product_name_lower for word in [
        'belt', 'waist belt', 'seration belt',
        'ベルト', 'ウエストベルト', '腰带', '皮带', 'セレーションベルト'
    ]):
        return '腰带'

    # 检查帽子类
    elif any(word in product_name_lower for word in [
        'hat', 'cap', 'beanie',
        'ハット', 'キャップ', '帽子', '球帽'
    ]):
        return '帽子'

    # 检查球杆头套类
    elif any(word in product_name_lower for word in [
        'head cover', 'headcover', 'club head cover',
        'ヘッドカバー', 'クラブヘッドカバー', '球杆头套', '杆头套'
    ]):
        return '球杆头套'

    # 检查标记夹类
    elif any(word in product_name_lower for word in [
        'marker', 'ball marker', 'divot tool', 'pitchfork',
        'マーカー', 'ボールマーカー', 'ディボットツール', 'マークツール',
        '标记', '标记夹', '球位标记', '果岭叉', '修复叉'
    ]):
        return '高尔夫配件'
        
    # 检查鞋子类  
    elif any(word in product_name_lower for word in [
        'shoe', 'golf shoe', 'spike',
        'シューズ', 'スパイク', '球鞋', '运动鞋'
    ]):
        return '球鞋'
    
    else:
        return '其他'