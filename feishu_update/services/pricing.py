"""价格计算服务

提供产品价格相关的计算功能
"""

def calculate_final_price(product_data):
    """计算最终价格
    
    Args:
        product_data: 产品数据
        
    Returns:
        str: 最终价格字符串
    """
    # 简单实现，返回基础价格
    if isinstance(product_data, dict):
        return product_data.get('price', '')
    elif hasattr(product_data, 'price'):
        return product_data.price
    else:
        return ''