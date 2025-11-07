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
        return '女性'
    elif 'mens' in category_lower:
        return '男性'
    
    # 检查产品名称 - 英文和日文
    if any(word in product_name_lower for word in ['women', 'ladies', 'womens', 'レディース', '女性']):
        return '女性'
    elif any(word in product_name_lower for word in ['men', 'mens', '(mens)', 'メンズ', '男性']):
        return '男性'
    else:
        return '中性'

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
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name
        category = getattr(product_data, 'category', '')
    else:
        return '其他'
    
    # 转换为小写便于匹配
    product_name_lower = product_name.lower()
    category_lower = category.lower()
    
    # 检查外套类 - 英文和日文
    if any(word in product_name_lower for word in [
        'jacket', 'outerwear', 'blouson', 'vest', 'windbreaker',
        'ブルゾン', 'ジャケット', 'アウター', 'ベスト', '外套', '夹克', '马甲', '背心'
    ]):
        return '外套'
    
    # 检查T恤/Polo衫类 - 英文和日文
    elif any(word in product_name_lower for word in [
        'shirt', 'polo', 't-shirt', 'tshirt', 'top',
        'シャツ', 'ポロ', 'ティーシャツ', 'トップス', 'polo衫', 't恤'
    ]):
        return 'T恤/Polo衫'
    
    # 检查裤子类 - 英文和日文  
    elif any(word in product_name_lower for word in [
        'pant', 'trouser', 'short', 'skirt',
        'パンツ', 'ズボン', 'ショーツ', 'スカート', '裤子', '短裤', '裙子'
    ]):
        return '裤子'
        
    # 检查帽子类
    elif any(word in product_name_lower for word in [
        'hat', 'cap', 'beanie',
        'ハット', 'キャップ', '帽子', '球帽'
    ]):
        return '帽子'
        
    # 检查鞋子类  
    elif any(word in product_name_lower for word in [
        'shoe', 'golf shoe', 'spike',
        'シューズ', 'スパイク', '球鞋', '运动鞋'
    ]):
        return '球鞋'
    
    else:
        return '其他'