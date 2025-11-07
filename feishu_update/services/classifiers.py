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
    # 简单实现
    if isinstance(product_data, dict):
        product_name = product_data.get('productName', '').lower()
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name.lower()
    else:
        return '中性'
    
    if 'women' in product_name or 'ladies' in product_name:
        return '女性'
    elif 'men' in product_name or 'mens' in product_name:
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
    # 简单实现
    if isinstance(product_data, dict):
        product_name = product_data.get('productName', '').lower()
    elif hasattr(product_data, 'product_name'):
        product_name = product_data.product_name.lower()
    else:
        return '其他'
    
    if 'shirt' in product_name or 'polo' in product_name:
        return 'T恤/Polo衫'
    elif 'pant' in product_name or 'trouser' in product_name:
        return '裤子'
    elif 'jacket' in product_name or 'outerwear' in product_name:
        return '外套'
    else:
        return '其他'