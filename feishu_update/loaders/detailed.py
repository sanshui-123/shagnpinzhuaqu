"""详细产品数据加载器 - 终稿版本

处理详细产品数据，支持两种结构：
1. { "product": {...}, "variants": [...], "scrapeInfo": {...} }
2. { "products": { "": {...} } }
"""

import logging
from typing import Dict, Any, List
from .base import BaseProductLoader
from ..models import Product, Variant, Images

logger = logging.getLogger(__name__)


class DetailedProductLoader(BaseProductLoader):
    """详细产品数据加载器 - 终稿版本
    
    按终稿要求处理详细产品数据，不回退到旧逻辑
    """
    
    def supports(self, data: Dict[str, Any]) -> bool:
        """检查是否为详细产品数据格式
        
        支持格式：
        1. 单个产品格式：包含product、variants、scrapeInfo字段
        2. 多产品格式：包含products字段，值为字典
        """
        if not self.validate_data(data):
            return False
        
        # 格式1: 单个产品格式 {product, variants, scrapeInfo}
        if 'product' in data and 'variants' in data and 'scrapeInfo' in data:
            return True
        
        # 格式2: 多产品格式 {products: {...}}
        if 'products' in data and isinstance(data['products'], dict):
            products = data['products']
            if len(products) > 0:
                # 检查第一个产品是否包含详细信息
                first_product = next(iter(products.values()))
                if isinstance(first_product, dict):
                    # 检查是否包含详细字段
                    detailed_fields = ['description', 'brand', 'category', 'variants']
                    found_fields = sum(1 for field in detailed_fields if field in first_product)
                    return found_fields >= 2
        
        return False
    
    def parse(self, data: Dict[str, Any]) -> List[Product]:
        """解析详细产品数据 - 终稿版本
        
        Args:
            data: 包含products字典或单个产品的数据
            
        Returns:
            List[Product]: 解析后的Product对象列表
        """
        if not self.supports(data):
            raise ValueError("数据格式不受此加载器支持")
        
        products = []
        
        # 格式1: 单个产品格式 {product, variants, scrapeInfo}
        if 'product' in data and 'variants' in data and 'scrapeInfo' in data:
            try:
                product = self._parse_single_product_format(data)
                products.append(product)
            except Exception as e:
                logger.warning(f"解析单个产品时出错: {e}")
        else:
            # 格式2: 多产品格式 {products: {...}}
            products_data = data['products']
            for product_id, product_info in products_data.items():
                try:
                    product = self._parse_product_from_dict(product_id, product_info)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"解析产品 {product_id} 时出错: {e}")
                    continue
        
        logger.info(f"DetailedProductLoader 解析了 {len(products)} 个产品")
        return self.postprocess_products(products)
    
    def _parse_single_product_format(self, data: Dict[str, Any]) -> Product:
        """解析单个产品格式的数据 {product, variants, scrapeInfo} - 终稿版本"""
        product_info = data['product']
        variants_data = data.get('variants', [])
        scrape_info = data.get('scrapeInfo', {})
        images_data = data.get('images', {})
        
        # 解析变体信息
        variants = self._parse_variants(variants_data)
        
        # 从变体中提取颜色和尺码列表
        colors = list(set([v.color_name for v in variants if v.color_name]))
        sizes = list(set([v.size_name for v in variants if v.size_name]))
        
        # 解析图片信息
        images = self._parse_images(images_data)
        
        # 确定库存状态
        stock_status = self._analyze_stock_status(variants)
        
        # 创建Product对象
        return Product(
            product_id=product_info.get('productId', ''),
            product_name=product_info.get('productName', ''),
            description=product_info.get('description', ''),
            brand=product_info.get('brand', ''),
            category=product_info.get('category', ''),
            price=product_info.get('price', ''),
            original_price=product_info.get('originalPrice', ''),
            currency=product_info.get('currency', 'JPY'),
            current_price=product_info.get('price', ''),
            sku=product_info.get('sku', ''),
            status=product_info.get('status', ''),
            detail_url=scrape_info.get('url', ''),
            variants=variants,
            colors=colors,
            sizes=sizes,
            size_chart=product_info.get('sizeChart', {}),
            images=images,
            main_image=self._get_main_image(images),
            stock_status=stock_status,
            scraped_at=scrape_info.get('timestamp', ''),
            processing_time=scrape_info.get('processingTimeMs', 0),
            version=scrape_info.get('version', ''),
            total_images=scrape_info.get('totalImages', len(images.all)),
            extra=product_info.get('extra', {})
        )
    
    def _parse_product_from_dict(self, product_id: str, product_info: Dict[str, Any]) -> Product:
        """从字典解析产品数据 - 处理格式2"""
        # 解析变体信息
        variants = self._parse_variants(product_info.get('variants', []))
        
        # 从变体中提取颜色和尺码列表
        colors = list(set([v.color_name for v in variants if v.color_name]))
        sizes = list(set([v.size_name for v in variants if v.size_name]))
        
        # 解析图片信息
        images = self._parse_images(product_info.get('images', {}))
        
        # 确定库存状态
        stock_status = self._analyze_stock_status(variants)
        
        return Product(
            product_id=product_id,
            product_name=product_info.get('productName', ''),
            description=product_info.get('description', ''),
            brand=product_info.get('brand', ''),
            category=product_info.get('category', ''),
            price=product_info.get('price', ''),
            original_price=product_info.get('originalPrice', ''),
            currency=product_info.get('currency', 'JPY'),
            current_price=product_info.get('price', ''),
            sku=product_info.get('sku', ''),
            status=product_info.get('status', ''),
            detail_url=product_info.get('detailUrl', ''),
            variants=variants,
            colors=colors,
            sizes=sizes,
            size_chart=product_info.get('sizeChart', {}),
            images=images,
            main_image=self._get_main_image(images),
            stock_status=stock_status,
            scraped_at=product_info.get('scrapedAt', ''),
            processing_time=product_info.get('processingTime', 0),
            version=product_info.get('version', ''),
            total_images=product_info.get('totalImages', len(images.all)),
            extra=product_info.get('extra', {})
        )
    
    def _parse_variants(self, variants_data: List[Dict[str, Any]]) -> List[Variant]:
        """解析变体数据 - 终稿版本"""
        if not isinstance(variants_data, list):
            return []
        
        variants = []
        for variant_data in variants_data:
            if isinstance(variant_data, dict):
                variant = Variant(
                    variant_id=variant_data.get('variantId', ''),
                    color_name=variant_data.get('colorName', variant_data.get('color', '')),
                    size_name=variant_data.get('sizeName', variant_data.get('size', '')),
                    price=variant_data.get('price', ''),
                    is_available=variant_data.get('isAvailable', True),
                    stock=variant_data.get('stock', {})
                )
                variants.append(variant)
        
        return variants
    
    def _parse_images(self, images_data: Dict[str, Any]) -> Images:
        """解析图片数据 - 终稿版本"""
        if not isinstance(images_data, dict):
            return Images()
        
        main_image = images_data.get('mainImage') or images_data.get('main_image', '')
        gallery_images = images_data.get('galleryImages', images_data.get('gallery_images', []))

        # 如果未提供主图，尝试从其他字段推断
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
    
    def _analyze_stock_status(self, variants: List[Variant]) -> str:
        """分析库存状态"""
        if not variants:
            return "unknown"
        
        available_count = sum(1 for v in variants if v.is_available)
        total_count = len(variants)
        
        if available_count == 0:
            return "out_of_stock"
        elif available_count == total_count:
            return "in_stock"
        else:
            return "limited_stock"
