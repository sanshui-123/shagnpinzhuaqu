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
        final_price = calculate_final_price(product)
        if final_price is not None and final_price != '':
            fields['价格'] = final_price
        else:
            fields['价格'] = ''

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
        if product_detail and product_detail.get('images', {}).get('product'):
            # 使用抓取的详情数据构建图片URL多行字符串
            product_images = product_detail['images']['product']
            # 去重并显示所有图片
            unique_images = list(dict.fromkeys(product_images))  # 保持顺序的去重
            image_multiline = '\n'.join(unique_images)
        else:
            # 回退到原始数据
            image_multiline = build_image_url_multiline(product)
        
        fields['图片URL'] = image_multiline if image_multiline else product.get('mainImage', '')

        # 图片数量（优先使用详情数据）
        image_count = None
        if product_detail and product_detail.get('images', {}).get('product'):
            # 使用去重后的图片数量
            product_images = product_detail['images']['product']
            unique_images = list(dict.fromkeys(product_images))
            image_count = len(unique_images)
        else:
            image_count = count_total_images(product)
        
        fields['图片数量'] = image_count if image_count is not None else 1

        # 库存状态（默认有货）
        fields['库存状态'] = '有货'

        # 尺码表（暂时留空，可以后续添加爬取逻辑）
        fields['尺码表'] = ''

        # 描述翻译（优先使用详情数据）
        description = None
        if product_detail and product_detail.get('product', {}).get('description'):
            # 使用抓取的详情数据，先尝试翻译
            detail_description = product_detail['product']['description']
            if detail_description:
                # 创建一个临时产品对象用于翻译
                temp_product = product.copy()
                temp_product['description'] = detail_description
                translated_description = self.translator.translate_description(temp_product)
                description = translated_description if translated_description else detail_description

        # 如果没有描述，尝试使用产品标题生成
        if not description and product_detail and product_detail.get('product', {}).get('title'):
            product_title = product_detail['product']['title']
            if product_title:
                # 基于产品标题生成描述
                description = f"Callaway Golf {product_title}。高品质高尔夫{clothing_type}，采用先进面料科技，提供卓越的舒适性和运动表现。适合高尔夫运动及日常休闲穿着。"

        # 如果仍然没有描述，使用颜色信息增强
        if not description and product_detail and product_detail.get('colors_cn_text'):
            colors_text = product_detail['colors_cn_text'].strip()
            if colors_text:
                description = f"Callaway Golf 高品质高尔夫{clothing_type}。可选颜色：{colors_text.replace(chr(10), '、')}。采用专业面料科技，设计精良，适合高尔夫运动及日常休闲穿着。"

        # 回退到传统方式
        if not description:
            # 回退到翻译描述
            translated_description = self.translator.translate_description(product)
            if translated_description:
                description = translated_description
            else:
                # 使用原始描述或产品名称
                description = product.get('description', '')
                if not description:
                    # 如果没有描述，使用产品名称作为默认描述
                    product_name = product.get('productName', '')
                    if product_name:
                        description = f"高品质高尔夫{clothing_type}，{product_name}"
                    else:
                        description = f"高品质高尔夫{clothing_type}，适合运动时穿着"

        fields['详情页文字'] = description if description else f"高品质高尔夫{clothing_type}"


        return fields