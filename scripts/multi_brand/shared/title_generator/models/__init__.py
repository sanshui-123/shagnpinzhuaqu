"""飞书产品更新系统 - 数据模型

本模块提供核心数据模型，包括：
- Product: 产品数据模型
- Variant: 产品变体模型  
- Images: 图片数据模型
- UpdateResult: 更新结果模型
- ProgressEvent: 进度事件模型
"""

from .product import Product, Variant, Images
from .update_result import UpdateResult
from .progress import ProgressEvent

__all__ = [
    'Product',
    'Variant', 
    'Images',
    'UpdateResult',
    'ProgressEvent'
]