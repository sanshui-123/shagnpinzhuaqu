"""
字段组装服务
"""

from typing import Dict, List, Optional
from datetime import datetime

from .pricing import calculate_final_price
from ..config import translation, sizes
from .images import build_image_url_multiline, count_total_images
from .translator import Translator
from .title_generator import TitleGenerator
from .size_table_formatter import SizeTableFormatter
from .classifiers import determine_gender, determine_clothing_type
from .classifiers import map_to_taobao_category
from ..config.brands import BRAND_SHORT_NAME, BRAND_MAP
from ..config import brands as brand_module


class FieldAssembler:
    """飞书字段组装器

    负责根据产品数据构建飞书表中的字段内容。
    """

    def __init__(
        self,
        title_generator: Optional[TitleGenerator] = None,
        translator: Optional[Translator] = None,
        size_table_formatter: Optional[SizeTableFormatter] = None,
    ) -> None:
        self.title_generator = title_generator or TitleGenerator()
        self.translator = translator or Translator()
        self.size_table_formatter = size_table_formatter or SizeTableFormatter()

    def build_update_fields(
        self,
        product: Dict,
        pre_generated_title: Optional[str] = None,
        title_only: bool = False,
        product_detail: Optional[Dict] = None
    ) -> Dict[str, any]:
        """构建单个产品的字段"""
        fields: Dict[str, any] = {}

        
        # 标题（支持预生成缓存）
        gender = determine_gender(product)
        clothing_type = determine_clothing_type(product)

        if pre_generated_title:
            fields['商品标题'] = pre_generated_title
        else:
            title = self.title_generator.generate(product)
            if title:
                fields['商品标题'] = title

        if title_only:
            return fields

        # 商品ID
        product_id = product.get('productId') or product.get('product_id')
        if product_id:
            fields['商品ID'] = product_id

        # 价格
        # 首先确保主数据中有价格信息
        if not product.get('priceText'):  # 检查None或空字符串
            # 尝试从 _detail_data 中获取价格信息
            if '_detail_data' in product:
                detail_data = product.get('_detail_data', {})
                detail_product = detail_data.get('product', {})
                if detail_product.get('priceText'):
                    product['priceText'] = detail_product.get('priceText')
                elif detail_product.get('price'):
                    product['priceText'] = detail_product.get('price')
            elif product_detail:
                # 从 productDetail 中获取价格信息到主数据
                detail_product = product_detail.get('product', {})
                if detail_product.get('priceText'):
                    product['priceText'] = detail_product.get('priceText')
                elif detail_product.get('price'):
                    product['priceText'] = detail_product.get('price')

        # 计算最终价格
        final_price = calculate_final_price(product)
        if final_price is not None and final_price != '':
            fields['价格'] = final_price
        else:
            # 如果主数据没有价格，尝试从详情数据中获取
            detail_price = None
            if product_detail:
                # 从 product_detail.product 中获取价格
                detail_product = product_detail.get('product', {})
                detail_price = (
                    detail_product.get('price') or
                    detail_product.get('priceText') or
                    detail_product.get('currentPrice') or
                    detail_product.get('originalPrice', '')
                )

            # 如果还是没有价格，尝试从变体中获取
            if not detail_price and product_detail and 'variants' in product_detail:
                variants = product_detail.get('variants', [])
                for variant in variants:
                    variant_price = variant.get('priceJPY') or variant.get('price')
                    if variant_price:
                        # 清理价格文本，提取数字
                        price_match = re.search(r'([0-9,]+)', str(variant_price))
                        if price_match:
                            # 设置到product中，这样calculate_final_price可以处理
                            product['priceText'] = f"￥{int(price_match.group(1).replace(',', ''))}"
                            break

            # 再次尝试计算最终价格（可能从变体中获取了）
            final_price = calculate_final_price(product)
            if final_price is not None and final_price != '':
                fields['价格'] = final_price
            else:
                fields['价格'] = detail_price or ''

        # 商品链接
        detail_url = product.get('detailUrl') or product.get('detail_url')
        if detail_url:
            fields['商品链接'] = detail_url

        # 性别 / 分类
        if gender:
            fields['性别'] = gender
        if clothing_type:
            fields['衣服分类'] = map_to_taobao_category(product, clothing_type)

        # 品牌名（使用简短中文）
        _, brand_chinese, brand_short = brand_module.extract_brand_from_product(product)
        fields['品牌名'] = brand_short

        # 颜色（优先使用详情数据）
        colors = None
        if product_detail and product_detail.get('colors'):
            # 使用抓取的详情数据，取所有颜色的name和code
            colors = []
            for color in product_detail['colors']:
                name = color.get('name', '') or color.get('code', '')
                if name:
                    colors.append(name)
            # 去重但保持顺序
            colors = list(dict.fromkeys(colors))
        else:
            # 回退到原始数据
            colors = product.get('colors')
            if not colors and product.get('imagesMetadata'):
                colors = [
                    meta.get('colorName') or meta.get('name')
                    for meta in product['imagesMetadata']
                    if meta.get('colorName') or meta.get('name')
                ]
        
        color_multiline = translation.build_color_multiline(colors)
        fields['颜色'] = color_multiline if color_multiline else ''  # 只有真的为空时才为空

        # 尺码（优先使用详情数据）
        sizes_list = None
        if product_detail and product_detail.get('sizes'):
            # 使用抓取的详情数据
            sizes_list = product_detail['sizes']
        else:
            # 回退到原始数据
            sizes_list = product.get('sizes')
        
        if sizes_list:
            size_multiline = sizes.build_size_multiline(sizes_list, gender)
            fields['尺码'] = size_multiline if size_multiline else ''
        else:
            fields['尺码'] = ''

        # 图片URL（优先使用详情数据）
        image_multiline = None
        if product_detail and product_detail.get('images'):
            # 聚合所有图片：product + variants
            all_images = []

            # 先添加 product 图片
            product_images = product_detail['images'].get('product', [])
            if product_images:
                all_images.extend(product_images)

            # 再添加 variants 图片（去重）
            variants_data = product_detail['images'].get('variants', {})
            for color_code, images in variants_data.items():
                if isinstance(images, list):
                    all_images.extend(images)

            # 去重并显示所有图片
            unique_images = []
            seen = set()
            for img in all_images:
                if img not in seen:
                    seen.add(img)
                    unique_images.append(img)

            image_multiline = '\n'.join(unique_images)
        else:
            # 回退到原始数据
            image_multiline = build_image_url_multiline(product)

        fields['图片URL'] = image_multiline if image_multiline else product.get('mainImage', '')

        # 图片数量（优先使用详情数据）
        image_count = None
        if product_detail and product_detail.get('images'):
            # 计算去重后的图片数量
            if image_multiline:
                image_count = len(image_multiline.split('\n')) if image_multiline else 0
        else:
            image_count = count_total_images(product)
        
        fields['图片数量'] = image_count if image_count is not None else 1

        # 库存状态（默认有货）- 已移除，飞书表不需要此字段
        # fields['库存状态'] = '有货'

        # 尺码表（使用DOM抓取或结构化数据）
        size_text_source = None
        if product_detail:
            size_text_source = (
                product_detail.get('sizeSectionText')
                or product_detail.get('sizeSection', {}).get('text')
                or product_detail.get('product', {}).get('sizeSectionText')
            )
        if not size_text_source:
            size_text_source = product.get('sizeSectionText') or ''

        structured_chart = None
        if product_detail:
            structured_chart = (
                product_detail.get('sizeChart')
                or product_detail.get('product', {}).get('sizeChart')
            )
        if not structured_chart:
            structured_chart = product.get('sizeChart')

        size_table_text = self.size_table_formatter.build(size_text_source, structured_chart)
        fields['尺码表'] = size_table_text if size_table_text else ''

        # 描述翻译（优先使用详情数据）
        description = None
        if product_detail and product_detail.get('product', {}).get('description'):
            detail_description = product_detail['product']['description']
            if detail_description:
                temp_product = product.copy()
                temp_product['description'] = detail_description
                description = self.translator.translate_description(temp_product)

        # 设置详情页文字
        if description:
            fields['详情页文字'] = description
        elif product.get('description'):
            # 使用原始描述（如果有）
            fields['详情页文字'] = product.get('description', '')
        else:
            # 兜底：空值
            fields['详情页文字'] = ''

        return fields
