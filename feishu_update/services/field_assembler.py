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
from .classifiers import determine_gender, determine_clothing_type
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
    ) -> None:
        self.title_generator = title_generator or TitleGenerator()
        self.translator = translator or Translator()

    def build_update_fields(
        self,
        product: Dict,
        pre_generated_title: Optional[str] = None,
        title_only: bool = False
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
        final_price = calculate_final_price(product)
        if final_price is not None:
            fields['价格'] = final_price

        # 商品链接
        detail_url = product.get('detailUrl') or product.get('detail_url')
        if detail_url:
            fields['商品链接'] = detail_url

        # 性别 / 分类
        if gender:
            fields['性别'] = gender
        if clothing_type:
            fields['衣服分类'] = clothing_type

        # 品牌名（使用简短中文）
        _, brand_chinese, brand_short = brand_module.extract_brand_from_product(product)
        fields['品牌名'] = brand_short

        # 颜色
        colors = product.get('colors')
        if not colors and product.get('imagesMetadata'):
            colors = [
                meta.get('colorName') or meta.get('name')
                for meta in product['imagesMetadata']
                if meta.get('colorName') or meta.get('name')
            ]
        color_multiline = translation.build_color_multiline(colors)
        if color_multiline:
            fields['颜色'] = color_multiline

        # 尺码
        sizes_list = product.get('sizes')
        if sizes_list:
            size_multiline = sizes.build_size_multiline(sizes_list, gender)
            if size_multiline:
                fields['尺码'] = size_multiline

        # 图片URL
        image_multiline = build_image_url_multiline(product)
        if image_multiline:
            fields['图片URL'] = image_multiline

        # 图片数量
        image_count = count_total_images(product)
        if image_count is not None:
            fields['图片数量'] = image_count

        # 描述翻译
        translated_description = self.translator.translate_description(product)
        if translated_description:
            fields['详情页文字'] = translated_description

        return fields