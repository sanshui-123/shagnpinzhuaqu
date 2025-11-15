"""转换JSON格式加载器 - 支持你的JSON格式

处理从convert_to_feishu_format.py转换后的JSON数据
"""

import logging
from typing import Dict, Any, List
from .base import BaseProductLoader
from ..models import Product, Variant, Images

logger = logging.getLogger(__name__)


class ConvertedJsonProductLoader(BaseProductLoader):
    """转换JSON格式产品数据加载器

    专门处理convert_to_feishu_format.py生成的JSON数据
    """

    def supports(self, data: Dict[str, Any]) -> bool:
        """检查是否为转换JSON格式

        支持格式：{products: {"productId": {...}}}
        """
        if not self.validate_data(data):
            return False

        # 检查是否包含products字段
        if 'products' not in data:
            return False

        products = data['products']
        if not isinstance(products, dict):
            return False

        if len(products) == 0:
            return False

        # 检查第一个产品是否包含你的JSON格式特征
        first_product_id = next(iter(products.keys()))
        first_product = products[first_product_id]

        if not isinstance(first_product, dict):
            return False

        # 检查是否包含你的JSON格式特征字段
        required_fields = ['brand', 'price', 'colors', 'sizes', 'imageUrls']
        found_fields = sum(1 for field in required_fields if field in first_product)

        return found_fields >= 4  # 至少包含4个字段认为是你的格式

    def parse(self, data: Dict[str, Any]) -> List[Product]:
        """解析转换JSON数据为Product对象列表"""
        products = []

        try:
            products_data = data['products']

            for product_id, product_info in products_data.items():
                logger.info(f"解析产品: {product_id}")

                # 获取品牌信息（直接使用JSON中的品牌，不进行映射）
                brand = product_info.get('brand', '')

                # 创建产品对象
                product = Product(
                    productId=product_id,
                    productName=product_info.get('productName', ''),
                    detailUrl=product_info.get('detailUrl', ''),
                    price=product_info.get('price', ''),
                    brand=brand,  # 直接使用JSON中的品牌信息
                    category=product_info.get('category', ''),
                    gender=product_info.get('gender', ''),
                    description=product_info.get('description', ''),

                    # 处理变体（颜色和尺码）
                    variants=self._parse_variants(product_info)
                )

                # 处理图片
                product.images = self._parse_images(product_info)

                # 设置imageUrls（用于兼容性检查）
                image_urls = product_info.get('imageUrls', [])
                if image_urls:
                    if isinstance(image_urls, list):
                        product.imageUrls = image_urls
                    elif isinstance(image_urls, str):
                        product.imageUrls = [url.strip() for url in image_urls.split(',') if url.strip()]
                    else:
                        product.imageUrls = list(image_urls) if image_urls else []
                else:
                    product.imageUrls = []

                # 设置颜色列表（用于兼容性检查）
                colors_data = product_info.get('colors', [])
                if colors_data:
                    if isinstance(colors_data, list) and all(isinstance(c, dict) for c in colors_data):
                        # 从对象格式提取颜色名称
                        product.colors = [c.get('name', '') for c in colors_data if c.get('name', '')]
                    else:
                        # 直接使用列表
                        product.colors = [str(c) for c in colors_data if c]
                else:
                    product.colors = []

                # 设置尺码列表（用于兼容性检查）
                sizes_data = product_info.get('sizes', [])
                if sizes_data:
                    if isinstance(sizes_data, list):
                        product.sizes = [str(s) for s in sizes_data if s]
                    else:
                        product.sizes = [str(sizes_data)]
                else:
                    product.sizes = []

                # 处理尺码表
                product.sizeChart = product_info.get('sizeChart', {})

                # 添加抓取信息
                if 'scrapeInfo' in product_info:
                    product.scrapeInfo = product_info['scrapeInfo']

                products.append(product)

        except Exception as e:
            logger.error(f"解析产品数据失败: {e}")
            raise

        logger.info(f"成功解析 {len(products)} 个产品")
        return products

    def _parse_variants(self, product_info: Dict[str, Any]) -> List[Variant]:
        """解析变体信息（颜色和尺码）"""
        variants = []

        try:
            # 处理颜色
            colors_data = product_info.get('colors', [])
            if colors_data:
                if isinstance(colors_data, list) and all(isinstance(c, dict) for c in colors_data):
                    # 处理颜色对象列表
                    for i, color_info in enumerate(colors_data):
                        variant = Variant(
                            colorId=str(i),
                            colorName=color_info.get('name', ''),
                            isFirstColor=color_info.get('isFirstColor', False)
                        )
                        variants.append(variant)
                else:
                    # 处理简单颜色列表
                    for i, color in enumerate(colors_data):
                        if color:  # 跳过空值
                            variant = Variant(
                                colorId=str(i),
                                colorName=str(color),
                                isFirstColor=(i == 0)
                            )
                            variants.append(variant)

            # 处理尺码 - 添加到第一个变体或创建新变体
            sizes_data = product_info.get('sizes', [])
            if sizes_data and variants:
                variants[0].sizes = list(sizes_data) if isinstance(sizes_data, list) else [str(sizes_data)]
            elif sizes_data and not variants:
                # 如果有尺码但没有颜色，创建默认变体
                variant = Variant(
                    colorId='default',
                    colorName='默认',
                    isFirstColor=True,
                    sizes=list(sizes_data) if isinstance(sizes_data, list) else [str(sizes_data)]
                )
                variants.append(variant)

        except Exception as e:
            logger.warning(f"解析变体信息失败: {e}")

        return variants

    def _parse_images(self, product_info: Dict[str, Any]) -> Images:
        """解析图片信息"""
        try:
            image_urls = product_info.get('imageUrls', [])

            if not image_urls:
                return Images(totalCount=0, mainImages=[], imagesByColor={})

            # 如果是字符串，分割为列表
            if isinstance(image_urls, str):
                image_urls = [url.strip() for url in image_urls.split(',') if url.strip()]

            return Images(
                totalCount=len(image_urls),
                mainImages=image_urls[:3] if image_urls else [],  # 前3张作为主图
                imagesByColor={
                    'default': image_urls if image_urls else []
                }
            )

        except Exception as e:
            logger.warning(f"解析图片信息失败: {e}")
            return Images(totalCount=0, mainImages=[], imagesByColor={})