"""飞书产品更新系统 - 数据加载器

本模块提供不同格式产品数据的加载器，包括：
- BaseProductLoader: 抽象基类
- DetailedProductLoader: 详细产品数据加载器（product_details_* 格式）
- SummarizedProductLoader: 汇总产品数据加载器（all_products_dedup_* 格式）
- LinkOnlyProductLoader: 链接数据加载器（raw_links_* 格式）
- LoaderFactory: 加载器工厂（自动格式检测）
"""

from .base import BaseProductLoader
from .detailed import DetailedProductLoader
from .summarized import SummarizedProductLoader
from .link_only import LinkOnlyProductLoader
from .factory import LoaderFactory

__all__ = [
    'BaseProductLoader',
    'DetailedProductLoader',
    'SummarizedProductLoader', 
    'LinkOnlyProductLoader',
    'LoaderFactory'
]