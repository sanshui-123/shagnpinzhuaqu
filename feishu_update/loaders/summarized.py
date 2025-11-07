"""汇总产品数据加载器 - 终稿版本

处理汇总产品数据，支持基本产品信息但缺少详细变体的格式
"""

import logging
from typing import Dict, Any, List
from .base import BaseProductLoader
from ..models import Product, Images

logger = logging.getLogger(__name__)


class SummarizedProductLoader(BaseProductLoader):
    """汇总产品数据加载器 - 终稿版本
    
    按终稿要求处理汇总产品数据，不回退到旧逻辑
    """
    
    def supports(self, data: Dict[str, Any]) -> bool:
        """检查是否为汇总产品数据格式
        
        汇总格式特征：
        - 包含products字段，值为字典或列表
        - 每个产品有基本字段但缺少详细信息
        - 不是 DetailedProductLoader 的两种格式
        - 不是 LinkOnlyProductLoader 的格式
        """
        if not self.validate_data(data):
            return False
        
        # 必须有products字段且为字典或列表
        if 'products' not in data:
            return False
        
        products = data['products']
        
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
        
        # 排除 DetailedProductLoader 的格式1：{product, variants, scrapeInfo}
        if 'product' in data and 'variants' in data and 'scrapeInfo' in data:
            return False
        
        # 检查第一个产品
        if not isinstance(first_product, dict):
            return False
        
        # 排除 DetailedProductLoader 的格式2：包含详细字段的多产品格式
        detailed_fields = ['description', 'variants', 'category']
        detailed_count = sum(1 for field in detailed_fields if field in first_product)
        if detailed_count >= 2:  # 如果有足够的详细字段，则可能是详细格式
            return False
        
        # 排除 LinkOnlyProductLoader 的格式：只有链接和名称，没有任何其他信息
        has_url = any(field in first_product for field in ['productUrl', 'url', 'link', 'detailUrl'])
        has_name = any(field in first_product for field in ['productName', 'name', 'title', 'productId', 'itemName'])
        detailed_info_fields = ['description', 'variants', 'images', 'brand', 'brandName', 'category', 'price', 'currentPrice', 'priceText', 'mainPrice', 'salePrice']
        has_detailed_info = sum(1 for field in detailed_info_fields if field in first_product and first_product[field])
        
        # 如果只有URL和名称，没有其他详细信息（包括价格），则是仅链接格式
        if has_url and has_name and has_detailed_info == 0:
            return False
        
        # 汇总格式：有价格或品牌或详情链接即可
        has_price = any(field in first_product for field in ['price', 'currentPrice', 'priceText', 'mainPrice', 'salePrice'])
        has_brand = any(field in first_product for field in ['brand', 'brandName'])
        has_detail_url = any(field in first_product for field in ['detailUrl', 'productUrl', 'url', 'link'])
        
        return has_price or has_brand or has_detail_url
    
    def parse(self, data: Dict[str, Any]) -> List[Product]:
        """解析汇总产品数据 - 终稿版本
        
        Args:
            data: 包含products字典或列表的数据
            
        Returns:
            List[Product]: 解析后的Product对象列表
        """
        if not self.supports(data):
            raise ValueError("数据格式不受此加载器支持")
        
        products_data = data['products']
        products = []
        
        if isinstance(products_data, dict):
            # 字典格式：{product_id: product_info, ...}
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
        
        logger.info(f"SummarizedProductLoader 解析了 {len(products)} 个产品")
        return self.postprocess_products(products)
    
    def _parse_single_product(self, product_id: str, product_info: Dict[str, Any]) -> Product:
        """解析单个汇总产品数据 - 终稿版本"""
        # 解析图片信息
        images = self._parse_images(product_info.get('images', {}))
        
        # 支持多种字段名变体
        # 品牌：从 brand 或 brandName 读取
        brand = product_info.get('brand') or product_info.get('brandName', '')
        
        # 价格：从多种价格字段读取
        price = (
            product_info.get('price') or 
            product_info.get('currentPrice') or 
            product_info.get('priceText') or 
            product_info.get('mainPrice') or 
            product_info.get('salePrice', '')
        )
        
        # URL：从多种 URL 字段读取
        detail_url = (
            product_info.get('productUrl') or 
            product_info.get('detailUrl') or 
            product_info.get('url') or 
            product_info.get('link', '')
        )
        
        # 名称：从多种名称字段读取
        product_name = (
            product_info.get('productName') or 
            product_info.get('name') or 
            product_info.get('title') or 
            product_info.get('productId') or 
            product_info.get('itemName', '')
        )
        
        # 创建Product对象（按终稿字段结构）
        return Product(
            product_id=product_id,
            product_name=product_name,
            description=product_info.get('description', ''),
            brand=brand,
            category=product_info.get('category', ''),
            price=price,
            original_price=product_info.get('originalPrice', ''),
            currency=product_info.get('currency', 'JPY'),
            current_price=price,
            sku=product_info.get('sku', ''),
            status=product_info.get('status', ''),
            detail_url=detail_url,
            variants=[],  # 汇总数据通常不包含变体信息
            colors=[],
            sizes=[],
            size_chart={},
            images=images,
            main_image=self._get_main_image(images),
            stock_status='unknown',
            scraped_at=product_info.get('scrapeTimestamp', ''),
            processing_time=0,
            version='',
            total_images=len(images.all),
            extra=product_info.get('extraData', {})
        )
    
    def _parse_images(self, images_data: Dict[str, Any]) -> Images:
        """解析图片数据 - 终稿版本"""
        if not isinstance(images_data, dict):
            return Images()
        
        main_image = images_data.get('mainImage') or images_data.get('main_image', '')
        gallery_images = images_data.get('galleryImages', images_data.get('gallery_images', []))

        if not main_image:
            if gallery_images:
                main_image = gallery_images[0]
            elif images_data.get('product'):
                main_image = images_data['product'][0]
            elif images_data.get('all'):
                main_image = images_data['all'][0]

        return Images(
            main_image=main_image or '',
            gallery_images=gallery_images if isinstance(gallery_images, list) else [],
            product=images_data.get('product', []),
            variants=images_data.get('variants', []),
            by_color=images_data.get('byColor', {}),
            all=images_data.get('all', []),
            metadata=images_data.get('metadata', []),
            oss_product_images=images_data.get('ossProductImages', []),
            oss_variant_images=images_data.get('ossVariantImages', {})
        )
    
    def _get_main_image(self, images: Images) -> str:
        """获取主图片URL"""
        if images.main_image:
            return images.main_image
        if images.oss_product_images:
            return images.oss_product_images[0]
        elif images.product:
            return images.product[0]
        elif images.all:
            return images.all[0]
        return ""
