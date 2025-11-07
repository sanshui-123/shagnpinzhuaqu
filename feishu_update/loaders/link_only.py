"""仅链接数据加载器 - 终稿版本

处理仅包含链接和最基本信息的简化产品数据
"""

import logging
from typing import Dict, Any, List
from .base import BaseProductLoader
from ..models import Product, Images

logger = logging.getLogger(__name__)


class LinkOnlyProductLoader(BaseProductLoader):
    """仅链接产品数据加载器 - 终稿版本
    
    按终稿要求处理仅包含链接的数据，不回退到旧逻辑
    """
    
    def supports(self, data: Dict[str, Any]) -> bool:
        """检查是否为仅链接数据格式
        
        仅链接格式特征：
        - 包含products或links字段，值为字典或列表
        - 每个产品主要包含URL和基本标识信息
        - 缺少详细的产品描述、特性等信息
        - 只有基础字段如productId、detailUrl、category、brandName等
        """
        if not self.validate_data(data):
            return False
        
        # 检查是否有products或links字段（同时支持两种格式）
        if 'products' not in data and 'links' not in data:
            return False
        
        # 优先使用products，回退到links
        products = data.get('products') or data.get('links')
        
        # 支持字典和列表两种格式
        if isinstance(products, dict):
            if len(products) == 0:
                return False
            first_product = next(iter(products.values()))
        elif isinstance(products, list):
            if len(products) == 0:
                return False
            first_product = products[0]
        else:
            return False
        
        if not isinstance(first_product, dict):
            return False
        
        # 检查必须有URL字段（支持多种字段名）
        has_url = any(field in first_product for field in ['productUrl', 'url', 'link', 'detailUrl'])
        
        # 检查必须有标识字段（支持多种字段名）
        has_name = any(field in first_product for field in ['productName', 'name', 'title', 'productId'])
        
        # 检查是否缺少详细信息（仅检查真正的详细字段，不包括基础的brand、category等）
        detailed_fields = ['description', 'variants', 'images', 'sizeChart']
        has_detailed = sum(1 for field in detailed_fields if field in first_product and first_product[field])
        
        # 仅链接格式：有URL和标识字段，但缺少详细信息
        return has_url and has_name and has_detailed == 0
    
    def parse(self, data: Dict[str, Any]) -> List[Product]:
        """解析仅链接产品数据 - 终稿版本
        
        Args:
            data: 包含products字典或列表的数据
            
        Returns:
            List[Product]: 解析后的Product对象列表
        """
        if not self.supports(data):
            raise ValueError("数据格式不受此加载器支持")
        
        products_data = data.get('products') or data.get('links')
        products = []
        
        if isinstance(products_data, dict):
            # 字典格式：product_id -> product_info
            for product_id, product_info in products_data.items():
                try:
                    product = self._parse_single_product(product_id, product_info)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"解析产品 {product_id} 时出错: {e}")
                    continue
        elif isinstance(products_data, list):
            # 列表格式：[product_info, ...]
            for i, product_info in enumerate(products_data):
                try:
                    # 尝试从产品信息中获取ID，否则使用索引
                    product_id = product_info.get('productId', '') or product_info.get('id', '') or str(i)
                    product = self._parse_single_product(product_id, product_info)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"解析产品索引 {i} 时出错: {e}")
                    continue
        
        logger.info(f"LinkOnlyProductLoader 解析了 {len(products)} 个产品")
        return self.postprocess_products(products)
    
    def _parse_single_product(self, product_id: str, product_info: Dict[str, Any]) -> Product:
        """解析单个仅链接产品数据 - 终稿版本"""
        # 获取产品URL（可能使用不同的字段名）
        product_url = (product_info.get('productUrl', '') or 
                      product_info.get('url', '') or
                      product_info.get('link', '') or
                      product_info.get('detailUrl', ''))
        
        # 获取产品名称（可能使用不同的字段名）
        product_name = (product_info.get('productName', '') or
                       product_info.get('name', '') or
                       product_info.get('title', '') or
                       product_info.get('productId', ''))
        
        # 获取品牌信息（可能使用不同的字段名）
        brand = (product_info.get('brand', '') or
                product_info.get('brandName', '') or
                '')
        
        # 获取分类信息（可能使用不同的字段名）
        category = (product_info.get('category', '') or
                   product_info.get('categoryName', '') or
                   '')
        
        # 获取价格信息（可能使用不同的字段名）
        price = (product_info.get('price', '') or
                product_info.get('currentPrice', '') or
                product_info.get('priceText', '') or
                product_info.get('salePrice', '') or
                product_info.get('mainPrice', '') or
                '')
        
        # 创建基本的图片信息
        images = self._parse_minimal_images(product_info)
        
        # 创建Product对象（按终稿字段结构）
        return Product(
            product_id=product_id,
            product_name=product_name,
            description='',
            brand=brand,
            category=category,
            price=price,
            original_price='',
            currency='JPY',
            current_price='',
            sku='',
            status='',
            detail_url=product_url,
            variants=[],  # 仅链接数据不包含变体
            colors=[],
            sizes=[],
            size_chart={},
            images=images,
            main_image=self._get_main_image(images),
            stock_status='unknown',
            scraped_at='',
            processing_time=0,
            version='',
            total_images=len(images.all),
            extra=product_info.get('extra', {})
        )
    
    
    def _parse_minimal_images(self, product_info: Dict[str, Any]) -> Images:
        """解析最小图片信息 - 终稿版本"""
        # 仅链接数据可能只有一个主图片
        main_image = (product_info.get('mainImage', '') or
                     product_info.get('image', '') or
                     product_info.get('imageUrl', '') or
                     product_info.get('thumbnail', ''))
        
        # 如果有主图，放入all列表
        all_images = [main_image] if main_image else []
        
        return Images(
            main_image=main_image,
            gallery_images=[],
            product=[],
            variants=[],
            by_color={},
            all=all_images,
            metadata=[],
            oss_product_images=[],
            oss_variant_images={}
        )
    
    def _get_main_image(self, images: Images) -> str:
        """获取主图片URL"""
        if images.all:
            return images.all[0]
        return ""
