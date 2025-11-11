"""价格计算服务

提供产品价格相关的计算功能
"""
import re
import math

def calculate_final_price(product_data):
    """计算最终价格
    
    按照公式：日元价格 * 0.055 + 250，然后向上取整到10
    
    Args:
        product_data: 产品数据
        
    Returns:
        str: 最终价格字符串 (如: "380")
    """
    price_text = ""
    
    # 尝试从不同字段获取价格文本
    if isinstance(product_data, dict):
        price_text = (product_data.get('priceText') or 
                     product_data.get('price') or 
                     product_data.get('currentPrice') or '')
    elif hasattr(product_data, 'price_text'):
        price_text = product_data.price_text or ''
    elif hasattr(product_data, 'price'):
        price_text = str(product_data.price or '')
    
    if not price_text:
        return ''
    
    # 从价格文本中提取数字 (例如: "￥27,500 (税込)" -> 27500)
    # 匹配 ￥ 符号后的数字，包括逗号
    price_match = re.search(r'￥([0-9,]+)', str(price_text))
    if not price_match:
        return ''
    
    try:
        # 移除逗号并转换为数字
        yen_price = int(price_match.group(1).replace(',', ''))
        
        # 应用公式: 日元 * 0.055 + 250
        calculated_price = yen_price * 0.055 + 250

        # 截断到10的倍数 (例如: 1523.5 -> 1520)
        final_price = int(calculated_price / 10) * 10
        
        return str(int(final_price))
        
    except (ValueError, AttributeError):
        return ''